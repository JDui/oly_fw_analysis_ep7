#!/usr/bin/env python3
"""Compile target-only observer, never link/execute or dereference native memory."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 manifest=json.loads((ROOT/'prototypes/ep7_volatile_hl/target/build-manifest.json').read_text())
 for p,h in manifest['tools'].items():
  if sha(ROOT/p)!=h:raise ValueError('tool hash mismatch')
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 flags=['-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-mno-setlb','-mno-liw']
 with tempfile.TemporaryDirectory(prefix='ep7-native-observer-') as tmp:
  asm=Path(tmp)/'observer.s';obj=Path(tmp)/'observer.o'
  subprocess.run([str(gcc),'-B'+str(gcc.parent)+'/',*flags,'-I'+str(ROOT/'prototypes/ep7_volatile_hl'),'-S',str(HERE/'native_observer.c'),'-o',str(asm)],check=True)
  subprocess.run([str(gas),'-o',str(obj),str(asm)],check=True)
  symbols=subprocess.check_output([str(od),'-t',str(obj)],text=True)
  undefined={line.split()[-1] for line in symbols.splitlines() if '*UND*' in line}
  if undefined!={'_ep7_native_runtime_unresolved','_ep7p_direct_apply'}:raise ValueError('unexpected undefined symbols')
  text=asm.read_text()
  for offset in [4,5,6,7,12,13,14,15]:
   if not re.search(r'\bmovbu \('+str(offset)+r',a0\),d[0-3]',text):raise ValueError('missing setup byte read')
  for witness in ['mov _ep7_native_runtime_unresolved,d0','call _ep7p_direct_apply,[],0','mov 976,a1','mov a1,(16,sp)','mov d2,(12,sp)','ret [d2,d3],28']:
   if witness not in text:raise ValueError('observer boundary mismatch')
  if re.search(r'\b(?:setlb|lir|lar|llt|lne)\b',text):raise ValueError('loop register operation')
  # Negative host syntax check only: the pointer adapter must not silently compile
  # for the current 64-bit host. No resulting executable is generated or run.
  host=subprocess.run(['cc','-std=c11','-fsyntax-only','-I'+str(ROOT/'prototypes/ep7_volatile_hl'),str(HERE/'native_observer.c')],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if host.returncode==0 or 'adapter requires 32-bit target pointers' not in host.stderr:raise ValueError('host pointer-width guard not enforced')
  return dict(source_sha256=sha(HERE/'native_observer.c'),header_sha256=sha(ROOT/'prototypes/ep7_volatile_hl/ep7p_direct.h'),core_header_sha256=sha(ROOT/'prototypes/ep7_volatile_hl/ep7p.h'),assembly_sha256=sha(asm),object_sha256=sha(obj),tool_hashes=manifest['tools'],compile_flags=flags,undefined_symbols=sorted(undefined),host_64bit_compile_rejected=True,setup_offsets=[4,12],output_length=976,current_task_query_used=False,last_job_global_used=False,target_linked=False,target_executed=False,native_memory_read=False,native_installation=False,flash_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
