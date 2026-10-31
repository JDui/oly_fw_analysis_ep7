#!/usr/bin/env python3
"""Check cold-context admission and the no-trap terminal body; refresh only changed target objects."""
import argparse
import json
import re
import struct
import subprocess
import tempfile
from pathlib import Path

from ep7_far_call_check import ROOT, REFERENCE, PRELUDE, body
from ep7_installation_manifest import CORE, inspect_stock, inspect_objects
from ep7_native_stack import BASE, NativeGraph, CONTEXT_WITNESSES
from ep7_descriptor_frames import instructions

# This is the previously built unified inventory, not a firmware identity hash.
INVENTORY_BASE='00b658e'
REFRESH=['runtime/cold_bootstrap.c','runtime/cold_cohort.c','runtime/quarantine.s']
ALLOWED_CHANGES=set(REFRESH)|{'runtime/cold_bootstrap.h'}


def verify_source_reuse():
    def git(*args):
        # Match this Windows worktree's existing newline normalization when
        # reading it from Linux; no repository/global configuration is changed.
        return subprocess.check_output(['git','-c','safe.directory='+str(ROOT),
            '-c','core.autocrlf=true','-c','core.safecrlf=false',*args],cwd=ROOT,text=True)
    prior=json.loads(git('show',INVENTORY_BASE+':research/ep7/installation-manifest.json').lstrip('\ufeff'))
    prefix='prototypes/ep7_volatile_hl/'
    changes=set(git('diff','--name-only',INVENTORY_BASE,'--',prefix).splitlines())
    changes|=set(git('ls-files','--others','--exclude-standard','--',prefix).splitlines())
    relevant=set()
    for name in changes:
        relative=name.removeprefix(prefix);path=Path(relative)
        if path.name.startswith('test_'):continue
        if path.suffix in {'.c','.s','.S','.h','.inc','.txt'}:relevant.add(relative)
    if not relevant<=ALLOWED_CHANGES:
        raise ValueError('additional source/header changes require a broader inventory refresh: '+str(sorted(relevant-ALLOWED_CHANGES)))
    consumers={p.relative_to(CORE).as_posix() for p in CORE.rglob('*') if p.suffix in {'.c','.h'} and
        not p.name.startswith('test_') and '#include "cold_bootstrap.h"' in p.read_text()}
    if consumers!=set(REFRESH[:2]):
        raise ValueError('cold header gained an unrefreshed consumer '+str(consumers))
    return prior,dict(base_commit=INVENTORY_BASE,changed_production_files=sorted(relevant),
        changed_header_consumers=sorted(consumers),unchanged_production_source_and_header_diff_checked=True,
        git_newlines_normalized_for_windows_worktree=True,source_content_hashes_computed=False)


def check_quarantine(prefix,reference):
    with tempfile.TemporaryDirectory(prefix='ep7-terminal-') as temp:
        out=Path(temp);obj=out/'quarantine.o';elf=out/'quarantine.elf';binary=out/'quarantine.bin'
        subprocess.run([prefix+'as','-I',str(CORE/'target'),str(CORE/'runtime/quarantine.s'),'-o',str(obj)],check=True)
        if subprocess.check_output([prefix+'nm','-u',str(obj)],text=True).strip():
            raise ValueError('terminal body acquired an external dependency')
        subprocess.run([prefix+'ld','--no-relax','-Ttext=0x19010000','-e','_ep7_gcc_quarantine',
                        str(obj),'-o',str(elf)],check=True)
        subprocess.run([prefix+'objcopy','-O','binary','-j','.text',str(elf),str(binary)],check=True)
        code=binary.read_bytes()
        asm=subprocess.check_output([prefix+'objdump','-d','--insn-width=16',str(elf)],text=True)
        rows=instructions(asm)
        if code!=bytes.fromhex('fafcfff7ca00') or len(rows)!=2 or rows[0]!=(0x19010000,4,'and','63487,psw') or \
           rows[1][:3]!=(0x19010004,2,'bra') or int(rows[1][3].split()[0],16)!=0x19010004:
            raise ValueError('terminal body must mask IE and branch to itself without stack/call/trap')
        source=reference.read_text()
        decoder='''static void step(const unsigned char *p) {
 uint32_t cia=PC,nia=PC+4;
 if(p[0]==0xfa) { assert(p[1]==0xfc);uint32_t IMM16A=p[2],IMM16B=p[3];
'''+body(source,'OP_FAFC0000')+'''
 } else if(p[0]==0xca) { uint32_t D8=p[1];
'''+body(source,'OP_CA00')+'''
 } else { assert(!"unexpected terminal instruction"); }
 PC=nia;
}
'''
        driver='''int main(void) {
 const uint32_t psw[]={0x8fff,0xf7ff};
 for(unsigned n=0;n<2;n++) {
  memset(&State,0xa5,sizeof State);
  for(unsigned i=0;i<32;i++)State.regs[i]=0x11000000u+0x010101u*i;
  PC=VENEERS;PSW=psw[n];State.regs[REG_SP]=ENTRY_SP;State.regs[0]=0xf06;
  lowest=UINT32_MAX;store_word(RAM,0x76543210);writes=0;
  struct machine expected=State;expected.regs[REG_PC]=VENEERS+4;expected.regs[11]&=0xf7ff;
  for(unsigned i=0;i<6;i++)step(production_code+(PC-VENEERS));
  assert(!memcmp(&State,&expected,sizeof State));assert(writes==0&&load_word(RAM)==0x76543210);
 }
 puts("{\\\"psw_cases\\\":2,\\\"steps_per_case\\\":6,\\\"reason_and_sp_preserved\\\":true,\\\"memory_writes\\\":0}");
 return 0;
}
'''
        c=out/'terminal.c';exe=out/'terminal'
        c.write_text(PRELUDE+'\n'+decoder+'\nstatic const unsigned char production_code[]={'+','.join(map(str,code))+'};\n'+driver)
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],check=True)
        semantic=json.loads(subprocess.check_output([str(exe)],text=True))
    return dict(text_bytes=len(code),body_stack_bytes=0,explicit_trap=False,external_calls=False,
        maskable_interrupts_disabled_on_current_core=True,terminal_reason_kept_in_d0=True,
        gnu_body_semantics=semantic,gnu_reference=REFERENCE,
        reused_gnu_bodies=['OP_FAFC0000','OP_CA00'],synthetic_single_object_linked=True,
        production_firmware_linked=False,hardware_executed=False)


def inspect(decoded,reference,prefix):
    prior,reuse=verify_source_reuse()
    data=decoded.read_bytes()
    if len(data)!=26214336:raise ValueError('unsupported decoded main length')
    # Bind the production comparisons to current stock root words, rather than
    # merely checking a fixture that repeated the same mistaken constants.
    source=(CORE/'runtime/cold_cohort.c').read_text();root_fields=[]
    for address,_,expected in re.findall(r'word\((0x[0-9a-f]+)u\)(==|!=)(0x[0-9a-f]+u?|0)\b',source):
        pc=int(address,16);value=int(expected.rstrip('u'),0)
        if 0x600411a4<=pc<0x60041330:
            actual=struct.unpack_from('<I',data,pc-BASE)[0]
            if actual!=value:raise ValueError('context comparison differs from stock root '+address)
            root_fields.append(dict(address=address,stock_value=hex(actual)))
    if len(root_fields)!=10:raise ValueError('cold context root comparison set changed')
    g=NativeGraph(decoded,prefix+'objdump')
    witnesses=[0x60032245,0x6003435c,0x6003435f,0x60034361,0x60034363,
               0x60034364,0x6003862c,0x60038633,0x6003863f]
    try:
        for pc in witnesses:
            if g.instruction(pc)[2:]!=CONTEXT_WITNESSES[pc]:raise ValueError('task exception gate changed '+hex(pc))
    finally:g.close()
    manifest=inspect_stock(decoded)
    if manifest['patches']!=prior['patches']:
        raise ValueError('installation layout changed beyond this cold-context update')
    manifest.update({k:v for k,v in prior.items() if k not in manifest and k!='object_inventory'})
    inventory=inspect_objects(prefix,manifest['patches'],REFRESH,prior['object_inventory']['objects'])
    if inventory['compiler']!=prior['object_inventory']['compiler']:
        raise ValueError('cannot reuse object metadata across a compiler change')
    inventory['reuse_validation']=reuse;manifest['object_inventory']=inventory
    manifest['incremental_update']='Cold context and terminal body: 3 objects rebuilt; unchanged source/header set compared with '+INVENTORY_BASE+'. Stock patch preimages freshly checked.'
    terminal=check_quarantine(prefix,reference)
    with tempfile.TemporaryDirectory(prefix='ep7-cold-context-') as temp:
        out=Path(temp);flags=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-pedantic','-fno-pie','-no-pie','-I'+str(CORE)]
        subprocess.run([*flags,str(CORE/'runtime/test_cold_context.c'),'-o',str(out/'context')],check=True)
        context=json.loads(subprocess.check_output([str(out/'context')],text=True))
        sources=['runtime/test_cold_bootstrap.c','runtime/runtime.c','runtime/queue_context.c',
                 'poll_lock_provider/bootstrap/bootstrap.c','poll_lock_provider/ep7_sem_provider.c',
                 'ep7p.c','ep7p_decode.c','snapshot_transport/transport.c']
        subprocess.run([*flags,*[str(CORE/p) for p in sources],'-o',str(out/'startup')],check=True)
        startup=[json.loads(subprocess.check_output([str(out/'startup'),str(i)],text=True)) for i in [0,15]]
    report=dict(scope=__doc__,stock_root_fields_checked=root_fields,
        task_exception_gate_instructions_checked=len(witnesses),context_host=context,
        startup_scenarios=startup,quarantine=terminal,source_reuse_validation=reuse,
        objects={p:inventory['objects'][p] for p in REFRESH},
        aggregate=dict(implementation_sources=inventory['implementation_sources'],
            global_definitions=inventory['global_definition_count'],externals=inventory['external_count'],
            unlinked_text_data_bss=inventory['unlinked_text_data_bss'],
            production_sources_recompiled=3,unchanged_object_metadata_reused=inventory['reused_object_count']),
        complete_stack_bound_proven=False,firmware_modified=False,firmware_built=False,
        target_executed=False,hash_checks_performed=False,
        limits=['Context admission is read-only and does not prove later callback/TCB immutability, cancellation exclusion or absence of IRQ before the check.',
                'Host context pages and startup native APIs are synthetic; only the production admission algorithm and C startup flow execute there.',
                'GNU instruction bodies verify the owned terminal mask/loop only; NMI, reset, watchdog and other cores are not modeled.',
                'Kernel BREAK paths, UDF effects, complete IRQ/task bounds, code/RAM/loader and remaining lifecycle qualification remain open.',
                'Only the 3 changed target objects and this cold-path host fixture are compiled; earlier full business/sanitizer suites are not rerun.'])
    return dict(report=report,manifest=manifest)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decoded',type=Path,required=True);p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--tool-prefix',required=True);args=p.parse_args()
    print(json.dumps(inspect(args.decoded,args.reference,args.tool_prefix),indent=2))
