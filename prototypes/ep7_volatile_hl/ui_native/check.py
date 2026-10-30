#!/usr/bin/env python3
"""Compile self-authored glue only; target code remains unlinked and unexecuted."""
from pathlib import Path
import hashlib,json,subprocess,tempfile,os,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stack_model():
 for delegate in (False,True):
  entry=0x1000;mem={entry:0x12345678};regs=[0x22,0x33,0xa2,0xa3]
  for i,v in enumerate(regs):mem[entry-4-4*i]=v
  sp=entry-48
  for i,v in enumerate([0x9032,1,0x12340000]):mem[sp+12+4*i]=v
  mem[sp]=0xabcd # nested GCC CALL([],0) return slot; callee returns SP unchanged
  if delegate:
   assert [mem[sp+12+4*i] for i in range(3)]==[0x9032,1,0x12340000]
   mem[sp]=0xbcde # native CALLS return slot, target owns its nested frame
  sp+=48
  assert sp==entry and mem[sp]==0x12345678
  assert [mem[sp-4-4*i] for i in range(4)]==regs
 return True
def validate_assembly(dis,sections):
 expected=[('movm','[d2,d3,a2,a3],(sp)'),('add','-32,sp'),('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),('mov','a0,(20,sp)'),('mov','sp,a0'),('add','12,a0'),('mov','a0,d0'),('call',None),('cmp','256,d0'),('bne',None),('mov','(12,sp),d0'),('mov','(16,sp),d1'),('mov','(20,sp),a0'),('mov','0,a1'),('calls','(a1)'),('ret','[d2,d3,a2,a3],48')]
 ops=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
 if len(ops)!=len(expected):raise ValueError('instruction count')
 for (op,arg),(want,val) in zip(ops,expected):
  if op!=want or (val is not None and arg.strip()!=val):raise ValueError('bridge contract')
 if not re.search(r'\.text\s+0000002e\s',sections):raise ValueError('text size')
 if not re.search(r'^0000002b <\.Ldone>:',dis,re.M):raise ValueError('branch label offset')
 relocs=re.findall(r'^\s*([0-9a-f]+):\s+(R_MN10300_\w+)\s+([^\n]+)',dis,re.M)
 if relocs!=[('11','R_MN10300_PCREL32','_ep7_gcc_ui_route+0x1'),('1c','R_MN10300_PCREL8','.Ldone+0x1'),('25','R_MN10300_32','ep7_stock_ui_event_unresolved')]:raise ValueError('relocation contract')
 if ',[],0' not in ops[8][1]:raise ValueError('GCC call frame')
 return len(ops)
def check():
 manifest=json.loads((ROOT/'prototypes/ep7_volatile_hl/target/build-manifest.json').read_text())
 for n,d in manifest['tools'].items():
  if sha(ROOT/n)!=d:raise ValueError('tool hash mismatch')
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 inc=ROOT/'prototypes/ep7_volatile_hl'
 with tempfile.TemporaryDirectory(prefix='ep7-ui-bridge-') as t:
  t=Path(t);obj=t/'bridge.o';route=t/'route.o';asm=t/'route.s';host=t/'host'
  subprocess.run([str(gas),'-o',str(obj),str(HERE/'bridge.s')],check=True)
  dis=subprocess.check_output([str(od),'-dr','--insn-width=16',str(obj)],text=True)
  count=validate_assembly(dis,subprocess.check_output([str(od),'-h',str(obj)],text=True))
  flags=['-B'+str(gcc.parent)+'/', '-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-mno-setlb','-mno-liw','-nostdinc','-I'+str(inc/'target/include'),'-I'+str(gcc.parent/'include'),'-I'+str(inc)]
  subprocess.run([str(gcc),*flags,'-S',str(HERE/'bridge.c'),'-o',str(asm)],check=True)
  subprocess.run([str(gas),'-o',str(route),str(asm)],check=True)
  und={}
  for name,o,want in [('bridge',obj,{'_ep7_gcc_ui_route','ep7_stock_ui_event_unresolved'}),('route',route,{'_ep7_ui_native_admit_unresolved','_ep7p_ui_raw_dispatch'})]:
   sym=subprocess.check_output([str(od),'-t',str(o)],text=True)
   got={line.split()[-1] for line in sym.splitlines() if '*UND*' in line}
   if got!=want:raise ValueError('undefined symbols '+repr(got))
   und[name]=sorted(got)
  for sanitizer in (False,True):
   options=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitizer else []
   subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-pedantic',*options,'-I'+str(inc),str(HERE/'bridge.c'),str(HERE/'test_bridge.c'),'-o',str(host)],check=True)
   subprocess.run([str(host)],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
  return dict(sources={p.name:sha(p) for p in [HERE/'bridge.h',HERE/'bridge.c',HERE/'bridge.s',HERE/'test_bridge.c',HERE/'check.py']},dependencies={str(q.relative_to(ROOT)):sha(q) for q in [inc/'ep7p_ui_raw.h',inc/'ep7p_ui.h',inc/'ep7p.h',inc/'ep7_ui_adapter_contract.h',inc/'ep7p_ui_raw.c']},objects={'bridge':sha(obj),'router':sha(route)},tool_hashes=manifest['tools'],undefined_symbols=und,assembly_instructions=count,bridge_text_bytes=46,relocations_verified=True,stack_arithmetic_pass=stack_model(),stack_model_not_emulation=True,host_strict_and_asan_ubsan=True,host_test_scope='Routing policy with stubbed admission and raw dispatcher; not raw/core end-to-end',lsan_disabled_due_ptrace_environment=True,target_linked=False,target_executed=False,native_provider_bound=False,viewer_bound=False,flash_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
