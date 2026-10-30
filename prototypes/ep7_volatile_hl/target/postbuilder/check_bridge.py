#!/usr/bin/env python3
"""Compile-only postbuilder seam and host arithmetic stack model; no target execution."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stack_model():
 # Symbolic host model, not an emulator: all native/observer work is represented
 # by arbitrary outputs/clobbers with the reviewed save/return contracts.
 C=0x2000;S=C-96;regs=['d2','d3','a2','a3'];old={r:i+100 for i,r in enumerate(regs)}
 mem={C:'outer-return'}
 for i,r in enumerate(regs):mem[C-4*(i+1)]=old[r]
 sp=S;mem[sp]='builder-return'
 for i,r in enumerate(regs):mem[sp-4*(i+1)]=old[r]
 sp-=96
 # Original RET96 restores callee registers and returns to wrapper.
 sp+=96;restored={r:mem[sp-4*(i+1)] for i,r in enumerate(regs)}
 assert sp==S and mem[sp]=='builder-return' and restored==old
 post={'d0':10,'d1':11,'a0':12,'a1':13,'mdr':14}
 for off,r in zip([12,16,20,24,28],post):mem[S+off]=post[r]
 assert restored['a2']==old['a2'] # setup is passed in d0
 # Model the actual generated observer: save d2/d3, reserve20, return28.
 mem[S]='observer-return';mem[S-4]=post['mdr'];mem[S-8]=old['d3'];sp=S-28
 mem[sp]='direct-return';sp+=28
 assert sp==S and mem[sp]=='observer-return'
 got={r:mem[S+off] for off,r in zip([12,16,20,24,28],post)}
 sp+=96;final={r:mem[sp-4*(i+1)] for i,r in enumerate(regs)}
 assert sp==C and mem[sp]=='outer-return' and got==post and final==old
 assert set(range(12,32)).isdisjoint(range(80,100))
 return True
def check():
 manifest=json.loads((ROOT/'prototypes/ep7_volatile_hl/target/build-manifest.json').read_text())
 for name,h in manifest['tools'].items():
  if sha(ROOT/name)!=h:raise ValueError('tool hash mismatch')
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 with tempfile.TemporaryDirectory(prefix='ep7-postbuilder-compile-') as tmp:
  b=Path(tmp)/'bridge.o';s=Path(tmp)/'observer.s';o=Path(tmp)/'observer.o'
  subprocess.run([str(gas),'-o',str(b),str(HERE/'postbuilder_bridge.s')],check=True)
  dis=subprocess.check_output([str(od),'-dr','--insn-width=16',str(b)],text=True)
  for witness in ['[d2,d3,a2,a3],96','_ep7_gcc_postbuilder_observer+0x1','ep7_stock_color_builder_unresolved+0x1','a2,d0','d2,mdr']:
   if witness not in dis:raise ValueError('bridge witness missing: '+witness)
  if dis.count('R_MN10300_PCREL32')!=2:raise ValueError('relocation count')
  ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
  expected=[('call',None),('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),('mov','a0,(20,sp)'),('mov','a1,(24,sp)'),('mov','mdr,d2'),('mov','d2,(28,sp)'),('mov','a2,d0'),('call',None),('mov','(12,sp),d0'),('mov','(16,sp),d1'),('mov','(20,sp),a0'),('mov','(24,sp),a1'),('mov','(28,sp),d2'),('mov','d2,mdr'),('ret','[d2,d3,a2,a3],96')]
  if len(ins)!=len(expected):raise ValueError('bridge instruction count')
  for (op,arg),(want,args) in zip(ins,expected):
   if op!=want or (args is not None and arg.strip()!=args):raise ValueError('bridge instruction mismatch')
  if not ins[0][1].endswith(',[d2,d3,a2,a3],96') or not ins[8][1].endswith(',[],0'):raise ValueError('call frame mismatch')

  subprocess.run([str(gcc),'-B'+str(gcc.parent)+'/','-O2','-std=c11','-ffreestanding','-fno-builtin','-mno-setlb','-mno-liw','-S',str(HERE/'observer_probe.c'),'-o',str(s)],check=True)
  subprocess.run([str(gas),'-o',str(o),str(s)],check=True)
  a=s.read_text()
  for witness in ['mov d0,d2','call _ep7_observer_sink_unresolved,[],0','ret [d2],16']:
   if witness not in a:raise ValueError('observer ABI mismatch')
  if re.search(r'\b(?:setlb|lir|lar)\b',a):raise ValueError('observer loop-state dependency')
  return dict(bridge_source_sha256=sha(HERE/'postbuilder_bridge.s'),bridge_object_sha256=sha(b),observer_source_sha256=sha(HERE/'observer_probe.c'),observer_object_sha256=sha(o),observer_assembly_sha256=sha(s),tool_hashes=manifest['tools'],stack_arithmetic_model_passed=stack_model(),target_linked=False,target_executed=False,real_observer_adapter_implemented=True,live_runtime_binding_supplied=False,native_installation=False,flash_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
