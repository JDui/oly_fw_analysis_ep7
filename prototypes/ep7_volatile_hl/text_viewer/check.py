#!/usr/bin/env python3
"""Self-authored text payload host tests + unlinked target object checks only."""
from pathlib import Path
import hashlib,json,subprocess,tempfile,os,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(dis,sections):
 ops=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
 expected=[('add','-12,sp'),('mov','d0,a0'),('mov','d1,a1'),('call',None),('ret','[],12')]
 if len(ops)!=5:raise ValueError('instruction count')
 for (op,arg),(want,operand) in zip(ops,expected):
  if op!=want or (operand is not None and operand!=arg.strip()):raise ValueError('bridge operand')
 if ',[d2,d3,a2,a3],24' not in ops[3][1]:raise ValueError('native frame')
 relocs=re.findall(r'^\s*([0-9a-f]+):\s+(R_MN10300_\w+)\s+([^\n]+)',dis,re.M)
 if relocs!=[('8','R_MN10300_PCREL32','ep7_stock_text_setter_unresolved+0x1')]:raise ValueError('relocation')
 if not re.search(r'\.text\s+00000011\s',sections):raise ValueError('text size')
 return True
def stack_model():
 for result in (0,1):
  s=0x1000;mem={s:0x12345678};sp=s-12;callsp=sp;mem[sp]=0xabcdef
  regs=[0x22,0x33,0xa2,0xa3]
  for i,v in enumerate(regs):mem[callsp-4-4*i]=v
  sp-=24;sp+=24 # Native frame owns RETURN24 after synchronous setter.
  assert [mem[sp-4-4*i] for i in range(4)]==regs and mem[sp]==0xabcdef
  sp+=12
  assert sp==s and mem[sp]==0x12345678 and result in (0,1)
 return True
def check():
 manifest=json.loads((ROOT/'prototypes/ep7_volatile_hl/target/build-manifest.json').read_text())
 for p,h in manifest['tools'].items():
  if sha(ROOT/p)!=h:raise ValueError('trusted tool hash')
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump';inc=ROOT/'prototypes/ep7_volatile_hl'
 with tempfile.TemporaryDirectory(prefix='ep7-text-') as t:
  t=Path(t);bo=t/'bridge.o';co=t/'text.o';asm=t/'text.s';host=t/'host'
  subprocess.run([str(gas),'-o',str(bo),str(HERE/'set_text.s')],check=True)
  dis=subprocess.check_output([str(od),'-dr','--insn-width=16',str(bo)],text=True);sec=subprocess.check_output([str(od),'-h',str(bo)],text=True);validate(dis,sec)
  mutations=[dis.replace('-12,sp','-8,sp'),dis.replace('d0,a0','d0,a1'),dis.replace('],24','],20'),dis.replace('[],12','[],8'),dis.replace('setter_unresolved+0x1','setter_unresolved+0x2')]
  for bad in mutations:
   try:validate(bad,sec)
   except ValueError:pass
   else:raise ValueError('negative bridge validation failed')
  flags=['-B'+str(gcc.parent)+'/', '-std=c11','-O2','-Wall','-Wextra','-Werror','-mno-setlb','-mno-liw','-ffreestanding','-fno-builtin','-nostdinc','-I'+str(inc/'target/include'),'-I'+str(gcc.parent/'include'),'-I'+str(inc)]
  subprocess.run([str(gcc),*flags,'-S',str(HERE/'text.c'),'-o',str(asm)],check=True)
  if re.search(r'^\s*setlb\b',asm.read_text(),re.M):raise ValueError('unexpected loop buffer instruction')
  subprocess.run([str(gas),'-o',str(co),str(asm)],check=True)
  und={}
  for name,o,want in [('bridge',bo,{'ep7_stock_text_setter_unresolved'}),('text',co,{'_ep7_gcc_set_text_unresolved_binding'})]:
   sym=subprocess.check_output([str(od),'-t',str(o)],text=True);got={x.split()[-1] for x in sym.splitlines() if '*UND*' in x}
   if got!=want:raise ValueError('unresolved symbols')
   und[name]=sorted(got)
  for san in (False,True):
   flags=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if san else []
   subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-pedantic',*flags,'-I'+str(inc),str(HERE/'text.c'),str(HERE/'test_text.c'),'-o',str(host)],check=True)
   subprocess.run([str(host)],env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'),check=True)
  return dict(sources={p.name:sha(p) for p in [HERE/'text.c',HERE/'text.h',HERE/'set_text.s',HERE/'test_text.c',HERE/'check.py']},dependency_sha256=sha(inc/'ep7_ui_adapter_contract.h'),tool_hashes=manifest['tools'],objects={'bridge':sha(bo),'text':sha(co)},undefined_symbols=und,target_codegen_flags=['-O2','-mno-setlb','-mno-liw','-ffreestanding','-fno-builtin'],bridge_text_bytes=17,bridge_instructions=5,negative_mutations=5,stack_arithmetic_passed=stack_model(),stack_model_not_emulation=True,host_strict_asan_ubsan=True,host_native_setter_is_stub_copy=True,lsan_disabled_ptrace_environment=True,target_linked=False,target_executed=False,native_widget_created=False,renderer_ready=False,flash_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
