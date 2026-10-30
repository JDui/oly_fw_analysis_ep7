from pathlib import Path
import json,hashlib,subprocess,tempfile,os,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(a,**kw):return subprocess.check_output([str(x) for x in a],text=True,**kw)
def validate(dis,sections):
 ops=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
 expected=[('movm','[d2,d3,a2,a3],(sp)'),('add','-16,sp'),('mov','d0,(12,sp)'),('mov','d0,a0'),('mov','0,a1'),('calls','(a1)'),('mov','(12,sp),a0'),('mov','0,a1'),('calls','(a1)'),('mov','a0,a1'),('mov','(12,sp),a0'),('calls','(a1)'),('ret','[d2,d3,a2,a3],32')]
 if [(a,b.strip()) for a,b in ops]!=expected:raise ValueError('veneer instruction mismatch')
 relocs=re.findall(r'^\s*([0-9a-f]+):\s+(R_MN10300_\w+)\s+([^\n]+)',dis,re.M)
 if relocs!=[('b','R_MN10300_32','ep7_stock_text_cleanup_unresolved'),('15','R_MN10300_32','ep7_stock_text_destructor_unresolved')]:raise ValueError('relocations')
 if not re.search(r'\.text\s+00000023\s',sections):raise ValueError('text size')
def stack_model():
 s=0x1000;mem={s:0x1234};regs=[22,33,0xa2,0xa3]
 for i,v in enumerate(regs):mem[s-4-4*i]=v
 sp=s-32;mem[sp+12]=0xfeed
 for n in range(3):
  mem[sp]=0x100+n # CALLS return slot; callee's self-prologue is below this.
  assert mem[sp+12]==0xfeed
 assert mem[s]==0x1234 and [mem[s-4-4*i] for i in range(4)]==regs
 return True

def main():
 manifest=json.loads((ROOT/'prototypes/ep7_volatile_hl/target/build-manifest.json').read_text())
 for p,h in manifest['tools'].items():
  if sha(ROOT/p)!=h:raise ValueError('trusted tool hash')
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 with tempfile.TemporaryDirectory(prefix='ep7-rollback-') as temp:
  t=Path(temp);host=t/'host';obj=t/'bridge.o'
  flags=['-std=c11','-Wall','-Wextra','-Werror','-pedantic']
  run(['cc',*flags,'-fsanitize=address,undefined','-fno-sanitize-recover=all',HERE/'rollback.c',HERE/'test_rollback.c','-o',host])
  run([host],env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'})
  run([gas,'-o',obj,HERE/'cleanup_destroy.s'])
  dis=run([od,'-dr','--insn-width=16',obj]);sec=run([od,'-h',obj]);validate(dis,sec)
  for bad in [dis.replace('-16,sp','-12,sp'),dis.replace('(12,sp),a0','(8,sp),a0'),dis.replace('a0,a1','a0,a2'),dis.replace('cleanup_unresolved','wrong_unresolved')]:
   try:validate(bad,sec)
   except ValueError:pass
   else:raise ValueError('mutation accepted')
  target=['-mno-setlb','-mno-liw','-ffreestanding','-fno-builtin','-nostdinc']
  run([gcc/'xgcc',f'-B{gcc}/',*flags,*target,f'-I{ROOT}/prototypes/ep7_volatile_hl/target/include',f'-I{gcc}/include','-S',HERE/'rollback.c','-o',t/'rollback.s'])
  run([gas,'-o',t/'rollback.o',t/'rollback.s'])
  und=run([ROOT/'toolchains/binutils-2.45-build/binutils/nm-new','-u',t/'rollback.o']).split()
  if und!=['U','_ep7_gcc_text_cleanup_destroy_unresolved']:raise ValueError('C undefined symbols')
  return dict(sources={p.name:sha(p) for p in [HERE/'rollback.h',HERE/'rollback.c',HERE/'cleanup_destroy.s',HERE/'test_rollback.c',HERE/'check.py',HERE/'CONTRACT.md']},tool_hashes=manifest['tools'],host_mock_cases=9,host_asan_ubsan_passed=True,lsan_disabled=True,target_flags=target,bridge_bytes=35,bridge_instructions=13,exact_relocations=2,negative_mutations=4,stack_arithmetic_passed=stack_model(),stack_model_not_emulation=True,target_executed=False,native_context_callbacks_unbound=True,native_cleanup_binding_unresolved=True,flash_ready=False)
if __name__=='__main__':print(json.dumps(main(),indent=2))
