#!/usr/bin/env python3
"""Compile/assemble self-authored unresolved veneers only; no target link/run."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
CORE=ROOT/'prototypes/ep7_volatile_hl';TARGET=CORE/'target'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stack_model():
 for frame,regs in [(24,['d2','d3','a2','a3']),(16,['d2','d3','a2'])]:
  for status in [0,-18,-25,-42,-43,-50]:
   entry=0x1000;sp=entry;original={r:i+0x100 for i,r in enumerate(['d2','d3','a2','a3'])};r=original.copy();mem={sp:0x12345678}
   sp-=4;mem[sp]=r['a2'];sp-=12;call_sp=sp;mem[sp]=0x87654321
   for i,reg in enumerate(regs):mem[sp-4*(i+1)]=r[reg]
   sp-=frame
   for reg in regs:r[reg]=0xbad
   # Unmasked native a3 is not clobbered by admitted raw signal path.
   d0=status
   sp+=frame
   for i,reg in enumerate(regs):r[reg]=mem[sp-4*(i+1)]
   assert mem[sp]==0x87654321 and sp==call_sp and r==original
   sp+=16;r['a2']=mem[sp-4];assert sp==entry and mem[sp]==0x12345678 and r==original and d0==status
 return True
def check():
 manifest=json.loads((TARGET/'build-manifest.json').read_text())
 for path,digest in manifest['tools'].items():
  if sha(ROOT/path)!=digest:raise ValueError('untrusted tool')
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 flags=['-B'+str(gcc.parent)+'/','-std=c11','-O2','-ffreestanding','-fno-builtin','-mno-setlb','-mno-liw','-Wall','-Wextra','-Werror','-I'+str(CORE),'-I'+str(TARGET/'include'),'-I'+str(CORE/'poll_lock_provider')]
 objects={}
 with tempfile.TemporaryDirectory(prefix='ep7-raw-sem-abi-') as tmp:
  temp=Path(tmp);obj=temp/'bridge.o'
  subprocess.run([str(gas),'-o',str(obj),str(HERE/'sem_bridges.s')],check=True)
  dis=subprocess.check_output([str(od),'-dr','--insn-width=16',str(obj)],text=True)
  ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
  expect=[('movm','[a2],(sp)'),('add','-12,sp'),('clr','d1'),('call',None),('ret','[a2],16'),('movm','[a2],(sp)'),('add','-12,sp'),('call',None),('ret','[a2],16')]
  if len(ins)!=9:raise ValueError('wrong instruction count')
  for (op,args),(eop,eargs) in zip(ins,expect):
   if op!=eop or (eargs is not None and args.strip()!=eargs):raise ValueError('wrong bridge instruction')
  if ',[d2,d3,a2,a3],24' not in ins[3][1] or ',[d2,d3,a2],16' not in ins[7][1]:raise ValueError('wrong native frame')
  if dis.count('R_MN10300_PCREL32')!=2:raise ValueError('wrong relocations')
  for name in ['ep7_stock_raw_sem_wait_unresolved','ep7_stock_raw_sem_signal_unresolved']:
   if name+'+0x1' not in dis:raise ValueError('wrong native target')
  sections=subprocess.check_output([str(od),'-h',str(obj)],text=True)
  if not re.search(r'\.text\s+0000001f\s',sections):raise ValueError('wrong bridge text size')
  objects['bridge']=dict(sha256=sha(obj),text_bytes=31,unresolved_native_calls=2)
  for name,source,expected in [('callbacks',HERE/'raw_callbacks.c',{'_ep7_gcc_get_tid','_ep7_gcc_raw_sem_poll','_ep7_gcc_raw_sem_signal'}),('caller',HERE/'bridge_caller.c',{'_ep7_gcc_raw_sem_poll','_ep7_gcc_raw_sem_signal'})]:
   asm=temp/(name+'.s');obj=temp/(name+'.o')
   subprocess.run([str(gcc),*flags,'-S',str(source),'-o',str(asm)],check=True)
   subprocess.run([str(gas),'-o',str(obj),str(asm)],check=True)
   symbols=subprocess.check_output([str(od),'-t',str(obj)],text=True)
   undefined={line.split()[-1] for line in symbols.splitlines() if '*UND*' in line}
   if undefined!=expected:raise ValueError('unexpected undefined set '+repr(undefined))
   text=asm.read_text()
   if name=='callbacks':
    for witness in ['mov d1,d0\n\texthu d0\n\tcall _ep7_gcc_raw_sem_poll,[],0','mov d1,d0\n\texthu d0\n\tcall _ep7_gcc_raw_sem_signal,[],0','mov d1,d0\n\tcall _ep7_gcc_get_tid,[],0']:
     if witness not in text:raise ValueError('callback argument translation changed')
   else:
    for witness in ['movm [d2],(sp)','mov d0,d2','call _ep7_gcc_raw_sem_poll,[],0','mov d2,d0','call _ep7_gcc_raw_sem_signal,[],0','ret [d2],16']:
     if witness not in text:raise ValueError('GCC callee-save caller probe changed')
   objects[name]=dict(sha256=sha(obj),assembly_sha256=sha(asm),undefined_symbols=sorted(undefined))
  # This adapter must not accidentally become a host native-pointer emulator.
  host=subprocess.run(['cc','-std=c11','-I'+str(CORE),'-I'+str(CORE/'poll_lock_provider'),'-fsyntax-only',str(HERE/'raw_callbacks.c')],capture_output=True,text=True)
  if host.returncode==0 or 'target-only 32-bit' not in host.stderr:raise ValueError('64-bit host adapter guard absent')
 return dict(sources={str(p.relative_to(ROOT)):sha(p) for p in [HERE/'sem_bridges.s',HERE/'raw_callbacks.c',HERE/'bridge_caller.c',CORE/'poll_lock_provider/ep7_sem_provider.h',CORE/'ep7p.h']},objects=objects,tool_hashes=manifest['tools'],stack_arithmetic_passed=stack_model(),model_is_not_instruction_emulation=True,host_64bit_adapter_compile_rejected=True,own_wrapper_frame=16,nested_native_wait_frame=24,nested_native_signal_frame=16,target_linked=False,target_executed=False,native_api_called=False,private_semaphore_created=False,native_stack_headroom_qualified=False,flash_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
