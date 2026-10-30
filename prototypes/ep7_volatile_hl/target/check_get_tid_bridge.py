#!/usr/bin/env python3
"""Unresolved bridge assembly + host arithmetic stack contract; no target execution."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stack_contract():
 # Host arithmetic model of ONLY the reviewed save/restore operations.
 # Native query replaced by status/sentinel values, not decoded/executed.
 for status in [0,-25]:
  sp=0x1000;entry=sp;caller_return=0x12345678;old_a2=0xa2a2a2a2
  mem={sp:caller_return};a2=old_a2
  sp-=4;mem[sp]=a2            # generated movm[a2]
  sp-=12                     # generated nonleaf local/outgoing reservation
  call_sp=sp;native_return=0x89abcdef
  mem[call_sp]=native_return;mem[call_sp-4]=a2;sp-=4 # CALL[a2],4
  a2=0x8ff00004;mdr=native_return                 # known query scratch, no execution
  sp+=4;a2=mem[sp-4];pc=mdr                      # native RETF[a2],4
  assert sp==entry-16 and pc==native_return and a2==old_a2
  d0=status
  sp+=16;a2=mem[sp-4];pc=mem[sp]                 # bridge RET[a2],16
  assert sp==entry and a2==old_a2 and pc==caller_return and d0==status
 return True
def check():
 manifest=json.loads((HERE/'build-manifest.json').read_text())
 for name,expected in manifest['tools'].items():
  if sha(ROOT/name)!=expected:raise ValueError('tool hash mismatch')
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 with tempfile.TemporaryDirectory(prefix='ep7-bridge-compile-') as tmp:
  obj=Path(tmp)/'bridge.o';caller=Path(tmp)/'caller.s'
  subprocess.run([str(gas),'-o',str(obj),str(HERE/'get_tid_bridge.s')],check=True)
  dis=subprocess.check_output([str(od),'-dr','--insn-width=16',str(obj)],text=True)
  expected=[('movm','[a2],(sp)'),('add','-12,sp'),('mov','d0,a0'),('call',None),('ret','[a2],16')]
  instructions=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
  if len(instructions)!=5:raise ValueError('wrong bridge instruction count')
  for (op,args),(want,arg) in zip(instructions,expected):
   if op!=want or (arg is not None and args.strip()!=arg):raise ValueError('wrong bridge operation')
  if ',[a2],4' not in instructions[3][1] or dis.count('R_MN10300_PCREL32')!=1 or 'ep7_stock_get_tid_unresolved+0x1' not in dis:raise ValueError('native call contract mismatch')
  sections=subprocess.check_output([str(od),'-h',str(obj)],text=True)
  if not re.search(r'\.text\s+00000011\s',sections):raise ValueError('wrong bridge size')
  subprocess.run([str(gcc),'-B'+str(gcc.parent)+'/','-std=c11','-O2','-ffreestanding','-fno-builtin','-S',str(HERE/'bridge_caller.c'),'-o',str(caller)],check=True)
  text=caller.read_text()
  if 'call _ep7_gcc_get_tid,[],0' not in text or 'ret [a2],16' not in text:raise ValueError('GCC caller contract mismatch')
  return dict(bridge_source_sha256=sha(HERE/'get_tid_bridge.s'),bridge_object_sha256=sha(obj),caller_source_sha256=sha(HERE/'bridge_caller.c'),caller_assembly_sha256=sha(caller),text_bytes=17,instructions=5,native_relocations_unresolved=1,stack_arithmetic_contract_passed=stack_contract(),stack_model_is_not_instruction_emulation=True,tool_hashes=manifest['tools'],target_linked=False,target_executed=False,native_api_executed=False,firmware_input_used=False,task_epoch_supplied=False,flash_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
