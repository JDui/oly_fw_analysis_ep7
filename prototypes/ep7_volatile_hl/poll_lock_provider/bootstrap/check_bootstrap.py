#!/usr/bin/env python3
"""Self-authored host bootstrap tests and target object inspection. No native calls."""
import hashlib,importlib.util,json,os,re,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CORE=ROOT/'prototypes/ep7_volatile_hl';TARGET=CORE/'target'
spec=importlib.util.spec_from_file_location('closure',CORE/'poll_lock_provider/native/check_dependency_closure.py');closure=importlib.util.module_from_spec(spec);spec.loader.exec_module(closure)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(dis,sections):
 ops=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
 expect=[('movm','[a2],(sp)'),('add','-12,sp'),('mov','d0,a0'),('call',None),('ret','[a2],16'),('movm','[a2],(sp)'),('add','-12,sp'),('call',None),('ret','[a2],16')]
 if len(ops)!=len(expect):raise ValueError('instruction count')
 for (op,arg),(want,val) in zip(ops,expect):
  if op!=want or(val is not None and arg.strip()!=val):raise ValueError('instruction contract')
 if ',[d2,a2],16' not in ops[3][1] or ',[d2,d3,a2,a3],20' not in ops[7][1]:raise ValueError('native frame contract')
 rel=re.findall(r'^\s*([0-9a-f]+):\s+(R_MN10300_\w+)\s+(\S+)',dis,re.M)
 if rel!=[('8','R_MN10300_PCREL32','ep7_stock_raw_sem_create_unresolved+0x1'),('17','R_MN10300_PCREL32','ep7_stock_raw_sem_delete_unresolved+0x1')]:raise ValueError('relocations')
 if not re.search(r'\.text\s+00000020\s',sections):raise ValueError('text size')
def stack_model():
 for frame,mask in [(16,['d2','a2']),(20,['d2','d3','a2','a3'])]:
  for status in [0,0x1001,-25,-34,-42]:
   entry=0x1000;sp=entry;original={r:0x100+i for i,r in enumerate(['d2','d3','a2','a3'])};regs=original.copy();mem={entry:0x12345678}
   sp-=4;mem[sp]=regs['a2'];sp-=12;mem[sp]=0x87654321
   for i,reg in enumerate(mask):mem[sp-4*(i+1)]=regs[reg]
   sp-=frame
   for reg in mask:regs[reg]=0xbad
   d0=status;sp+=frame
   for i,reg in enumerate(mask):regs[reg]=mem[sp-4*(i+1)]
   assert mem[sp]==0x87654321
   sp+=16;regs['a2']=mem[sp-4]
   assert sp==entry and mem[sp]==0x12345678 and regs==original and d0==status
 return True
def check():
 baseline=closure.check() # hashes tools; compiles selected9 objects, no linking
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 objects={};host=[]
 with tempfile.TemporaryDirectory(prefix='ep7-bootstrap-') as tmp:
  temp=Path(tmp)
  for config,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
   exe=temp/config
   subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-pedantic',*extra,'-I'+str(CORE),'-I'+str(CORE/'poll_lock_provider'),str(HERE/'bootstrap.c'),str(HERE/'test_bootstrap.c'),str(CORE/'poll_lock_provider/ep7_sem_provider.c'),str(CORE/'ep7p.c'),str(CORE/'ep7p_decode.c'),'-o',str(exe)],check=True)
   output=subprocess.check_output([str(exe)],text=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
   host.append(dict(configuration=config,passed=True,output=output.strip()))
  flags=['-B'+str(gcc.parent)+'/','-std=c11','-O2','-ffreestanding','-fno-builtin','-mno-setlb','-mno-liw','-Wall','-Wextra','-Werror','-I'+str(TARGET/'include'),'-I'+str(CORE),'-I'+str(CORE/'poll_lock_provider')]
  for name,source,want in [('bootstrap',HERE/'bootstrap.c',{'_memcpy','_ep7s_init','_ep7s_ops','_ep7p_init'}),('bootstrap_callbacks',HERE/'native_callbacks.c',{'_ep7_gcc_raw_sem_delete_unpublished','_ep7_gcc_raw_sem_create','_ep7s_unresolved_raw_callbacks'}),('create_delete_bridges',HERE/'create_delete_bridges.s',{'ep7_stock_raw_sem_create_unresolved','ep7_stock_raw_sem_delete_unresolved'})]:
   asm=source;obj=temp/(name+'.o')
   if source.suffix=='.c':
    asm=temp/(name+'.s');subprocess.run([str(gcc),*flags,'-S',str(source),'-o',str(asm)],check=True)
   subprocess.run([str(gas),'-o',str(obj),str(asm)],check=True)
   if source.suffix=='.s':validate(subprocess.check_output([str(od),'-dr','--insn-width=16',str(obj)],text=True),subprocess.check_output([str(od),'-h',str(obj)],text=True))
   defs,undef=closure.symbols(subprocess.check_output([str(od),'-t',str(obj)],text=True))
   if undef!=want:raise ValueError('unexpected object UND '+repr(undef))
   objects[name]=dict(source=str(source.relative_to(ROOT)),source_sha256=sha(source),object_sha256=sha(obj),global_definitions=sorted(defs),undefined_symbols=sorted(undef))
 combined={**baseline['objects'],**objects};old=closure.EXPECTED_EXTERNAL
 try:
  closure.EXPECTED_EXTERNAL=old|{'ep7_stock_raw_sem_create_unresolved','ep7_stock_raw_sem_delete_unresolved'}
  external,edges=closure.resolve(combined)
 finally:closure.EXPECTED_EXTERNAL=old
 return dict(host_tests=host,bootstrap_sources={p.name:sha(p) for p in [HERE/'bootstrap.c',HERE/'bootstrap.h',HERE/'native_callbacks.c',HERE/'create_delete_bridges.s',HERE/'test_bootstrap.c',HERE/'check_bootstrap.py']},objects=combined,internal_reference_edges=edges,remaining_external_symbols=external,tool_hashes=baseline['tool_hashes'],selected_objects=12,create_delete_text_bytes=32,create_delete_instructions=9,stack_arithmetic_passed=stack_model(),stack_model_not_instruction_execution=True,caller_serialization_required=True,published_shutdown_supported=False,runtime_object_bound=False,native_api_invoked=False,target_linked=False,target_executed=False,firmware_input_used=False,flash_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
