#!/usr/bin/env python3
"""Check the one-shot startup integration, early byte cohort and exact native bridge."""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from ep7_far_call_check import ROOT, REFERENCE, PRELUDE, body
from ep7_request_ownership import require_instruction
from ep7_queue_kernel_gate import W as KERNEL_W

CORE = ROOT/'prototypes/ep7_volatile_hl'
NATIVE = CORE/'runtime'
EXPECTED = bytes.fromhex('f8fed8420c4610431447184a20f2e24a1cf2e64a24dd000000000000'
                         '5a24f2fb5a1cf2fa5a20580c59105c145d18f8fe28dc00000000')


def semantic_step(source):
    cases = [
        ('p[0]==0xf8', 'OP_F8FE00', 3, 'assert(p[1]==0xfe);unsigned IMM8=p[2];'),
        ('p[0]==0x42||p[0]==0x46||p[0]==0x4a', 'OP_4200', 2, 'unsigned DM1=(p[0]-0x42)/4,D8=p[1];'),
        ('p[0]==0x43||p[0]==0x47', 'OP_4300', 2, 'unsigned AM1=(p[0]-0x43)/4,D8=p[1];'),
        ('p[0]==0xf2&&p[1]==0xe2', 'OP_F2E0', 2, 'unsigned DN0=2;'),
        ('p[0]==0xf2&&p[1]==0xe6', 'OP_F2E4', 2, 'unsigned DN0=2;'),
        ('p[0]==0xf2&&p[1]==0xfb', 'OP_F2F3', 2, 'unsigned DM1=2;'),
        ('p[0]==0xf2&&p[1]==0xfa', 'OP_F2F2', 2, 'unsigned DM1=2;'),
        ('p[0]>=0x58&&p[0]<=0x5a', 'OP_5800', 2, 'unsigned DN0=p[0]-0x58,D8=p[1];'),
        ('p[0]==0x5c||p[0]==0x5d', 'OP_5C00', 2, 'unsigned AN0=p[0]-0x5c,D8=p[1];'),
        ('p[0]==0xdd', 'OP_DD000000', 7,
         'unsigned D32A=p[1],D32B=p[2],D32C=p[3],D32D=p[4],REGS=p[5],IMM8=p[6];'),
        ('p[0]==0xdc', 'OP_DC000000', 5,
         'unsigned D32A=p[1],D32B=p[2],D32C=p[3],D32D=p[4];'),
    ]
    rows = ['static void step(const unsigned char *p) { uint32_t cia=PC,nia=0;']
    for i, (condition, marker, length, fields) in enumerate(cases):
        rows += [('if' if not i else 'else if')+f'({condition}){{nia=cia+{length};{fields}', body(source, marker), '}']
    rows += ['else {assert(!"unreviewed opcode");}', 'PC=nia;}']
    return '\n'.join(rows), [r[1] for r in cases]


DRIVER = r'''
static struct machine initial;
static void reset(uint32_t psw) {
 memset(&State,0xa5,sizeof State);
 for(unsigned i=0;i<32;i++)State.regs[i]=0x11000000u+0x010101u*i;
 State.regs[REG_SP]=ENTRY_SP;PC=VENEERS;PSW=psw;
 State.regs[REG_MDR]=0x60191378u;
 uint32_t original_return=0x60191378u;memcpy(State.ram+ENTRY_SP+4-RAM,&original_return,4);
 writes=0;lowest=UINT32_MAX;initial=State;
}
static void run(unsigned broken) {
 unsigned calls=0,steps=0;
 while(PC!=0x18012000u) {
  assert(++steps<30);
  if(PC==DEST) {
   calls++;assert(State.regs[REG_SP]==ENTRY_SP-40);
   uint32_t resume=load_word(State.regs[REG_SP]);assert(resume==VENEERS+0x1c);
   /* Returning GCC callback model, not execution of the C/native APIs. Its
    * permitted volatile clobbers include d2/MDR/PSW and outgoing words4/8. */
   for(unsigned i=0;i<3;i++)State.regs[i]^=0x55555555u;
   State.regs[4]^=0x66666666u;State.regs[5]^=0x77777777u;
   State.regs[REG_MDR]=0x12345678u;PSW=0x1357u;
   store_word(State.regs[REG_SP]+4,0x1234);store_word(State.regs[REG_SP]+8,0x5678);
   PC=resume;continue;
  }
  assert(PC>=VENEERS&&PC<VENEERS+sizeof production_code);
  unsigned offset=PC-VENEERS;
  if((broken==1&&offset==0x1e)||(broken==2&&offset==0x22)||(broken==3&&offset==0x24)){
   PC+=2;continue;
  }
  step(production_code+offset);
 }
 assert(calls==1);
}
int main(void) {
 const uint32_t patterns[]={0x750fu,0x8000u};
 for(unsigned n=0;n<2;n++) {
  reset(patterns[n]);run(0);struct machine expected=initial;expected.regs[REG_PC]=0x18012000u;
  assert(memcmp(expected.regs,State.regs,sizeof expected.regs)==0);
  assert(lowest==ENTRY_SP-40&&writes==10&&load_word(ENTRY_SP+4)==0x60191378u);
  for(unsigned i=0;i<sizeof State.ram;i++)if(i<ENTRY_SP-40-RAM||i>=ENTRY_SP-RAM)
   assert(State.ram[i]==initial.ram[i]);
 }
 reset(0x750f);run(1);assert(PSW!=initial.regs[11]);
 reset(0x750f);run(2);assert(State.regs[REG_MDR]!=initial.regs[REG_MDR]);
 reset(0x750f);run(3);assert(State.regs[2]!=initial.regs[2]);
 puts("{\"positive_state_checks\":2,\"negative_controls\":3,\"extra_bridge_stack_bytes\":40}");
 return 0;
}
'''


def inspect(decoded, reference, prefix):
    main = decoded.read_bytes()
    if len(main) != 26214336:
        raise ValueError('unsupported decoded main length')
    # Match complete original inline spans, reusing the previously reviewed
    # operands; an arbitrary raw JMP match is never an original-instruction proof.
    spans = [(0x600201fe, 6, {0x600201fe: ('mov', '(0x6218d984),d0')}),
             (0x60036d3c, 10, {p: KERNEL_W[p] for p in [0x60036d3c, 0x60036d3f, 0x60036d40]}),
             (0x60036f93, 6, {p: KERNEL_W[p] for p in [0x60036f93, 0x60036f95, 0x60036f97]}),
             (0x60031072, 6, {p: KERNEL_W[p] for p in [0x60031072, 0x60031074, 0x60031076]}),
             (0x602897d7, 6, {0x602897d7: ('movhu', 'd0,(0x62234fc0)')})]
    source = (NATIVE/'cold_cohort.c').read_text()
    declared = [(int(pc, 16), int(size)) for pc, _, size in re.findall(
        r'\{(0x[0-9a-f]+),(\w+),(\d+)\}', source)]
    if declared != [(pc, size) for pc, size, _ in spans]:
        raise ValueError('inline cohort does not match reviewed whole-instruction spans')
    inline_report = []
    for pc, size, rows in spans:
        asm = subprocess.check_output([prefix+'objdump', '-D', '-z', '-b', 'binary', '-m', 'mn10300',
            '--insn-width=16', '--adjust-vma=0x60020020', f'--start-address={pc:#x}',
            f'--stop-address={pc+size:#x}', str(decoded)], text=True)
        for address, (mn, operands) in rows.items():
            require_instruction(asm, address, mn, operands)
        lines = [x for x in asm.splitlines() if re.match(r'^[0-9a-f]+:', x)]
        widths = [len(re.search(r':\s*((?:[0-9a-f]{2}[ \t]+)+)', x).group(1).split()) for x in lines]
        if sum(widths) != size or len(lines) != len(rows):
            raise ValueError('inline span cuts an instruction or includes an unreviewed instruction')
        inline_report.append(dict(address=hex(pc), bytes=size, original=main[pc-0x60020020:pc-0x60020020+size].hex(),
                                  replacement='JMP32 and '+str(size-5)+' NOP bytes'))
    bounds = [(0x600229b9, '8020', '801f'), (0x60022c28, '8f20', '8f1f')]
    for pc, old, _ in bounds:
        if main[pc-0x60020020:pc-0x60020020+2] != bytes.fromhex(old):
            raise ValueError('pool bound differs from original proposal')
    if main[0x60191371-0x60020020:0x60191378-0x60020020] != bytes.fromhex('ddafe2f8ff0004'):
        raise ValueError('bootstrap original CALL changed')
    prefix_asm = subprocess.check_output([prefix+'objdump', '-D', '-z', '-b', 'binary', '-m', 'mn10300',
        '--insn-width=16', '--adjust-vma=0x60020020', '--start-address=0x601912fb',
        '--stop-address=0x60191371', str(decoded)], text=True)
    if re.search(r'\t(?:setlb|liw|leq|lne|lgt|lge|llt|lle|lcs|lcc)\b', prefix_asm):
        raise ValueError('Usr3 prefix acquired an unreviewed native loop-register dependency')
    objects = {}
    with tempfile.TemporaryDirectory(prefix='ep7-cold-bootstrap-') as tmp:
        out = Path(tmp)
        include = subprocess.check_output([prefix+'gcc', '-print-file-name=include'], text=True).strip()
        flags = ['-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-ffreestanding', '-fno-builtin',
                 '-mno-setlb', '-mno-liw', '-nostdinc', '-I'+str(CORE/'target/include'),
                 '-I'+include, '-I'+str(CORE), '-fstack-usage']
        for name in ['cold_bootstrap.c', 'cold_cohort.c', 'cold_bootstrap_bridge.s']:
            src = NATIVE/name;obj = out/(src.stem+'.o')
            subprocess.run([prefix+'gcc', *flags, '-c', str(src), '-o', str(obj)], check=True)
            size = subprocess.check_output([prefix+'size', str(obj)], text=True).splitlines()[-1].split()[:3]
            nm = subprocess.check_output([prefix+'nm', '-g', str(obj)], text=True)
            objects[src.stem] = dict(source=str(src.relative_to(ROOT)), size_output=size,
                definitions=[l.split()[-1] for l in nm.splitlines() if l.split()[-2] != 'U'],
                undefined=[l.split()[-1] for l in nm.splitlines() if l.split()[-2] == 'U'],
                stack_usage=obj.with_suffix('.su').read_text().splitlines() if obj.with_suffix('.su').exists() else [])
        obj = out/'cold_bootstrap_bridge.o'
        subprocess.run([prefix+'objcopy', '-O', 'binary', '-j', '.text', str(obj), str(out/'bridge.bin')], check=True)
        if (out/'bridge.bin').read_bytes() != EXPECTED:
            raise ValueError('native bootstrap bridge instruction shape changed')
        relocs = subprocess.check_output([prefix+'objdump', '-r', str(obj)], text=True)
        found = re.findall(r'^([0-9a-f]+)\s+(R_MN10300_\w+)\s+(\S+)$', relocs, re.M)
        if [(int(a, 16), kind, name) for a, kind, name in found] != [
            (0x16, 'R_MN10300_PCREL32', '_ep7r_bootstrap_initialize+0x00000001'),
            (0x32, 'R_MN10300_PCREL32', 'ep7_stock_bootstrap_original_unresolved+0x00000001')]:
            raise ValueError('bootstrap bridge relocation changed')
        subprocess.run([prefix+'ld', '--no-relax', '-Ttext=0x19010000', '-e', 'ep7_native_cold_bootstrap_bridge',
            '--defsym=_ep7r_bootstrap_initialize=0x18011000',
            '--defsym=ep7_stock_bootstrap_original_unresolved=0x18012000', str(obj), '-o', str(out/'fixture.elf')], check=True)
        subprocess.run([prefix+'objcopy', '-O', 'binary', '-j', '.text', str(out/'fixture.elf'), str(out/'fixture.bin')], check=True)
        code = (out/'fixture.bin').read_bytes();expected = bytearray(EXPECTED)
        expected[0x16:0x1a] = (0x18011000-0x19010015).to_bytes(4, 'little', signed=True)
        expected[0x32:0x36] = (0x18012000-0x19010031).to_bytes(4, 'little', signed=True)
        if code != expected:
            raise ValueError('synthetic link changed bridge shape or targets')
        step, markers = semantic_step(reference.read_text())
        harness = PRELUDE+'\n'+step+'\nstatic const unsigned char production_code[]={'+','.join(map(str, code))+'};\n'+DRIVER
        (out/'semantic.c').write_text(harness)
        host_flags = ['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-fno-pie', '-no-pie']
        subprocess.run([*host_flags, str(out/'semantic.c'), '-o', str(out/'semantic')], check=True)
        semantics = json.loads(subprocess.check_output([str(out/'semantic')], text=True))
        host_sources = ['runtime/test_cold_bootstrap.c', 'runtime/runtime.c', 'runtime/queue_context.c',
                        'poll_lock_provider/bootstrap/bootstrap.c', 'poll_lock_provider/ep7_sem_provider.c',
                        'ep7p.c', 'ep7p_decode.c', 'snapshot_transport/transport.c']
        subprocess.run([*host_flags, '-pedantic', '-I'+str(CORE), *[str(CORE/p) for p in host_sources],
                        '-o', str(out/'startup')], check=True)
        startup = [json.loads(subprocess.check_output([str(out/'startup'), str(i)], text=True)) for i in range(15)]
        subprocess.run([*host_flags, '-pedantic', str(NATIVE/'test_cold_cohort.c'), '-o', str(out/'cohort')], check=True)
        cohort = json.loads(subprocess.check_output([str(out/'cohort')], text=True))
        nm = subprocess.check_output([prefix+'nm', '-S', str(out/'cold_bootstrap.o')], text=True)
        storage = {name: int(size, 16) for _, size, kind, name in re.findall(r'^(\w+)\s+(\w+)\s+(\w)\s+(\w+)$', nm, re.M)
                   if kind.lower() == 'b'}
        if storage != {'_entered': 4, '_storage': 5704}:
            raise ValueError('permanent startup storage shape changed: '+str(storage))
    prior_reports = ['research/ep7/pipeline-far-call-target.json', 'research/ep7/ui-far-call-target.json']
    available = {'ep7_native_cold_clear', '_ep7q_native_cohort_present'}
    for name in prior_reports:
        prior = json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
        available |= {s for row in prior['objects'].values() for s in row['definitions']}
    available |= {s for row in objects.values() for s in row['definitions']}
    unresolved = {s for row in objects.values() for s in row['undefined']} - available
    if unresolved != {'ep7_stock_bootstrap_original_unresolved'}:
        raise ValueError('unexpected new startup dependency: '+str(sorted(unresolved)))
    return dict(scope=__doc__, objects=objects, inline_spans=inline_report,
        changed_pool_bounds=[dict(site=hex(pc), original=old, proposed=new) for pc, old, new in bounds],
        cohort_host_checks=cohort, startup_host_scenarios=startup, bridge_semantics=semantics,
        gnu_reference=REFERENCE, reused_gnu_instruction_bodies=markers,
        new_external_native_bindings={'ep7_stock_bootstrap_original_unresolved': '0x6011f620'},
        production_runtime_storage_bytes=5704, production_once_flag_bytes=4,
        bootstrap_local_stack_bytes=next(int(line.split('\t')[1]) for line in objects['cold_bootstrap']['stack_usage']
                                        if ':ep7r_bootstrap_initialize\t' in line),
        bridge_extra_stack_bytes=40, complete_stack_bound_proven=False,
        existing_definition_reports_reused=prior_reports, whole_implementation_recompiled=False,
        early_publication_reads_later_ui_tables=False, bootstrap_failure_returns_to_stock=False,
        local_usr3_prefix_has_no_hardware_loop_instructions=True,
        development_harness_build_issues_resolved=[
            'Added the existing queue_context.c to the host link for ep7n_same_queue.',
            'Braced the generated semantic decoder else to satisfy strict misleading-indentation warning.'],
        synthetic_bridge_linked=True, production_image_linked=False, native_apis_mocked_in_host_tests=True,
        gnu_libsim_full_engine_run=False, firmware_modified=False, firmware_built=False,
        camera_executed=False, hash_checks_performed=False,
        limits=['Current task and native semaphore/queue operations are mocked only in the startup host fixture.',
            'GNU body harness executes the bridge with a modeled returning GCC callback, not target bootstrap C.',
            'Installation bytes and flags are observations, not proof of initial loading, exclusivity or cache visibility.',
            'Private BSS placement, full native stack, all startup/task/callee paths and later UI closure remain open.',
            'No production link or firmware rewrite; three new objects and a synthetic assembly fixture only.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.decoded, args.reference, args.tool_prefix), indent=2))
