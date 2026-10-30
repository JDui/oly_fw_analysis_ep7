#!/usr/bin/env python3
"""Compile only self-authored sources; no target link or execution."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def stack_model():
 entry=0x1000;sp=entry-32;mem={entry:0x12345678}
 regs=[0xd2,0xd3,0xa2,0xa3]
 for i,v in enumerate(regs):mem[entry-4-4*i]=v
 # Native original CALL32 stores nested RA at wrapper SP, regs below it.
 mem[sp]=0xabcdef
 for i,v in enumerate(regs):mem[sp-4-4*i]=v
 inner=sp-32;assert inner+32==sp
 # Original RET32 restores SP; extra scratch lies below incoming frame.
 sp-=32
 values=[0x10,0x11,0xa0,0xa1,0xdead]
 for i,v in enumerate(values):mem[sp+12+4*i]=v
 # GCC outgoing return plus two argument-register spill slots may be written.
 for i in (0,4,8):mem[sp+i]=0xfeed
 assert [mem[sp+12+4*i] for i in range(5)]==values
 sp+=32
 assert [mem[entry-4-4*i] for i in range(4)]==regs
 sp+=32
 assert sp==entry and mem[sp]==0x12345678
 return True
def validate(dis,sections):
 expected=[('call',None),('add','-32,sp'),('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),('mov','a0,(20,sp)'),('mov','a1,(24,sp)'),('mov','mdr,d2'),('mov','d2,(28,sp)'),('call',None),('mov','(12,sp),d0'),('mov','(16,sp),d1'),('mov','(20,sp),a0'),('mov','(24,sp),a1'),('mov','(28,sp),d2'),('mov','d2,mdr'),('add','32,sp'),('ret','[d2,d3,a2,a3],32')]
 ops=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
 if len(ops)!=len(expected):raise ValueError('instruction count')
 for (op,arg),(want,val) in zip(ops,expected):
  if op!=want or val is not None and arg.strip()!=val:raise ValueError('bridge operands')
 if ',[d2,d3,a2,a3],32' not in ops[0][1] or ',[],0' not in ops[8][1]:raise ValueError('call frame')
 relocs=re.findall(r'^\s*([0-9a-f]+):\s+(R_MN10300_\w+)\s+([^\n]+)',dis,re.M)
 if relocs!=[('1','R_MN10300_PCREL32','ep7_stock_state_service_unresolved+0x1'),('17','R_MN10300_PCREL32','_ep7_gcc_state_transition_observer+0x1')]:raise ValueError('relocations '+repr(relocs))
 size=re.search(r'\.text\s+([0-9a-f]+)\s',sections)
 if not size or int(size[1],16)!=47:raise ValueError('text size '+str(size[1] if size else None))
 return len(ops)
def check(diagnostics=None):
 manifest=json.loads((ROOT/'prototypes/ep7_volatile_hl/target/build-manifest.json').read_text())
 for n,d in manifest['tools'].items():
  if sha(ROOT/n)!=d:raise ValueError('tool hash mismatch')
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 inc=ROOT/'prototypes/ep7_volatile_hl'
 with tempfile.TemporaryDirectory(prefix='ep7-state-service-') as t:
  t=Path(t);obj=t/'bridge.o';o=t/'observer.o';asm=t/'observer.s'
  subprocess.run([str(gas),'-o',str(obj),str(HERE/'bridge.s')],check=True)
  dis=subprocess.check_output([str(od),'-dr','--insn-width=16',str(obj)],text=True)
  count=validate(dis,subprocess.check_output([str(od),'-h',str(obj)],text=True))
  flags=['-B'+str(gcc.parent)+'/','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-mno-setlb','-mno-liw','-nostdinc','-I'+str(inc/'target/include'),'-I'+str(gcc.parent/'include')]
  subprocess.run([str(gcc),*flags,'-S',str(HERE/'observer.c'),'-o',str(asm)],check=True)
  subprocess.run([str(gas),'-o',str(o),str(asm)],check=True)
  und={}
  for name,p,want in [('bridge',obj,{'ep7_stock_state_service_unresolved','_ep7_gcc_state_transition_observer'}),('observer',o,{'_ep7_sidecar_transition_unresolved'})]:
   sym=subprocess.check_output([str(od),'-t',str(p)],text=True);got={line.split()[-1] for line in sym.splitlines() if '*UND*' in line}
   if got!=want:raise ValueError('undefined '+repr(got))
   und[name]=sorted(got)
  code=asm.read_text()
  if not re.search(r'movm \[d2,d3\],\(sp\)',code) or not re.search(r'add -12,sp',code) or code.count('ret [d2,d3],20')!=2:raise ValueError('observer frame')
  if re.search(r'\b(setlb|lne|leq|llt|liw)\b',code):raise ValueError('observer loop state')
  if diagnostics is not None:
   (diagnostics/'bridge.local.asm').write_text(dis)
  return dict(sources={p.name:sha(p) for p in [HERE/'bridge.s',HERE/'observer.c',HERE/'check.py',HERE/'test_check.py',HERE/'README.md']},tools=manifest['tools'],undefined_symbols=und,assembly_instructions=count,text_bytes=47,observer_static_frame_bytes=20,observer_extra_callback_depth_unknown=True,stack_model_pass=stack_model(),model_not_emulation=True,native_call_sites=['0x60289c5e','0x60289d02'],original_native_service='0x6028a882',current_state='0x62234fc0',pending_state='0x62234fc2',state_width=16,pending_sentinel=255,old33_self_transition_included=True,callback_failure_policy_bound=False,controller_exclusion_proven=False,target_linked=False,target_executed=False,installed=False)
if __name__=='__main__': print(json.dumps(check(),indent=2))
