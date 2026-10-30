#!/usr/bin/env python3
"""Compile self-authored sources only; never link/execute target code or load firmware."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 manifest=json.loads((HERE/'build-manifest.json').read_text())
 for name,expected in manifest['tools'].items():
  if digest(ROOT/name)!=expected:raise ValueError('trusted local tool hash mismatch: '+name)
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc'
 gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new'
 od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 flags=['-B'+str(gcc.parent)+'/', '-std=c11','-O2','-ffreestanding','-fno-builtin','-fno-tree-loop-distribute-patterns','-mno-setlb','-mno-liw','-fno-tree-loop-distribute-patterns','-Wall','-Wextra','-Werror','-I'+str(HERE/'include')]
 sources={'probe':HERE/'probe.c','ep7p':ROOT/'prototypes/ep7_volatile_hl/ep7p.c','ep7p_ui':ROOT/'prototypes/ep7_volatile_hl/ep7p_ui.c','ep7p_decode':ROOT/'prototypes/ep7_volatile_hl/ep7p_decode.c','memory':HERE/'memory.c','ep7p_lifecycle':ROOT/'prototypes/ep7_volatile_hl/ep7p_lifecycle.c','ep7p_ui_raw':ROOT/'prototypes/ep7_volatile_hl/ep7p_ui_raw.c'}
 expected_undef={'probe':{'_foreign_query_unresolved','_foreign_mix_unresolved','_foreign_pointer_unresolved'},'ep7p':{'_memcpy','_memset','_ep7p_decode'},'ep7p_ui':{'_memset','_ep7p_axis_read','_ep7p_axis_adjust_result'},'ep7p_decode':set(),'memory':set(),'ep7p_ui_raw':{'_ep7p_ui_ops'},'ep7p_lifecycle':{'_ep7p_direct_apply','_ep7p_register_job','_ep7p_release_job','_memcpy'}}
 results={}
 with tempfile.TemporaryDirectory(prefix='ep7-compile-target-') as temp:
  for name,source in sources.items():
   asm=Path(temp)/(name+'.s');obj=Path(temp)/(name+'.o')
   subprocess.run([str(gcc),*flags,'-S',str(source),'-o',str(asm)],check=True)
   subprocess.run([str(gas),'-o',str(obj),str(asm)],check=True)
   symbols=subprocess.check_output([str(od),'-t',str(obj)],text=True)
   undefined={line.split()[-1] for line in symbols.splitlines() if '*UND*' in line}
   if undefined!=expected_undef[name]:raise ValueError('unexpected unresolved symbols: '+repr(undefined))
   headers=subprocess.check_output([str(od),'-f',str(obj)],text=True)
   if 'elf32-mn10300' not in headers:raise ValueError('wrong object format')
   if name=='probe':
    text=asm.read_text()
    for witness in ['mov d0,a0','mov (12,sp),a0','mov (16,sp),a1','call _foreign_query_unresolved,[],0','mov d2,mdr','ret [d2],4','retf [],0','movm [d2,d3,a2],(sp)']:
     if witness not in text:raise ValueError('probe ABI witness missing: '+witness)
   results[name]=dict(source_sha256=digest(source),assembly_sha256=digest(asm),object_sha256=digest(obj),object_size=obj.stat().st_size,undefined_symbols=sorted(undefined))
 return dict(compiler='GNU GCC13.4.0 mn10300-elf',tool_hashes=manifest['tools'],compile_flags=[v.replace(str(ROOT)+'/', '') for v in flags[1:]],inputs={str(p.relative_to(ROOT)):digest(p) for p in [HERE/'include/string.h',ROOT/'prototypes/ep7_volatile_hl/ep7p_direct.h',ROOT/'prototypes/ep7_volatile_hl/ep7p_lifecycle.h',ROOT/'prototypes/ep7_volatile_hl/ep7p.h',ROOT/'prototypes/ep7_volatile_hl/ep7p_decode.h',ROOT/'prototypes/ep7_volatile_hl/ep7p_ui.h',ROOT/'prototypes/ep7_volatile_hl/ep7p_ui_raw.h',ROOT/'prototypes/ep7_volatile_hl/ep7_ui_adapter_contract.h']},results=results,target_linked=False,target_executed=False,firmware_input_used=False,native_ABI_compatible=False,flash_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
