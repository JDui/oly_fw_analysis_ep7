"""Read-only common state-commit/frame and finite literal-reference witnesses."""
from pathlib import Path
import hashlib,json,struct,subprocess,tempfile,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from ep7_request_ownership import require_instruction
BASE=0x60020020
SHA='5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190'
HITS=[0x602897d7,0x602898c8,0x60289908,0x6028994b,0x60289989,0x602899fb,0x60289a3b,0x60289a7f,0x60289abb,0x60289b33,0x60289b73,0x60289bb7,0x60289bf3,0x60289c2b,0x60289c55,0x60289c79,0x60289c8b,0x60289cb1,0x60289cd6,0x60289ce3,0x60289fae]
W={0x6028996f:('call','0x60289c5e,[d2,d3,a2],16'),0x60289aa4:('call','0x60289c5e,[d2,d3,a2],16'),0x60289bdc:('call','0x60289c5e,[d2,d3,a2],16'),0x60289c5e:('call','0x6028a882,[d2,d3,a2,a3],32'),0x60289c73:('mov','1614992752,a2'),0x60289c79:('movhu','(0x62234fc0),d2'),0x60289c7f:('movhu','(0x62234fc2),d0'),0x60289c85:('movhu','d2,(0x62234fc8)'),0x60289c8b:('movhu','d0,(0x62234fc0)'),0x60289c97:('movhu','d3,(0x62234fc2)'),0x60289cfa:('calls','(a0)'),0x60289d15:('ret','[d2,d3,a2],16'),0x602897d7:('movhu','d0,(0x62234fc0)')}
W.update({0x60289c63:('movhu','(0x62234fc2),d0'),0x60289c69:('clr','d2'),0x60289c6a:('mov','255,d3'),0x60289c6d:('cmp','d3,d0'),0x60289c6e:('bne','0x60289c73'),0x60289c70:('jmp','0x60289d13'),0x60289c9d:('and','1,d0'),0x60289ca0:('cmp','1,d0'),0x60289ca2:('bne','0x60289cd4'),0x60289d02:('call','0x6028a882,[d2,d3,a2,a3],32'),0x60289d07:('movhu','(0x62234fc2),d0'),0x60289d0d:('cmp','d3,d0'),0x60289d0e:('beq','0x60289d13'),0x60289d10:('jmp','0x60289c79')})
W.update({0x6028a883:('mov','d0,(4,sp)'),0x6028a899:('mov','a2,(8,sp)'),0x6028a89b:('mov','d2,(12,sp)'),0x6028a8c5:('mov','(8,sp),d1'),0x6028a8ce:('mov','(12,sp),d1'),0x6028a8e8:('mov','(4,sp),d0'),0x6028a906:('mov','(8,sp),d1'),0x6028a914:('mov','(12,sp),d1'),0x6028a929:('ret','[d2,d3,a2,a3],32')})
WINDOWS=[(0x6028a882,0x6028a92c),(0x6028996f,0x60289974),(0x60289aa4,0x60289aa9),(0x60289bdc,0x60289be1),(0x60289c5e,0x60289d18),(0x602897d6,0x602897dd)]
def inspect(data,objdump):
 if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('wrong exact main')
 pattern=struct.pack('<I',0x62234fc0);hits=[];offset=0
 while (offset:=data.find(pattern,offset))>=0:hits.append(BASE+offset-2);offset+=1
 if hits!=HITS:raise ValueError('literal inventory mismatch')
 stores=[]
 for pc in hits:
  op=data[pc-BASE:pc-BASE+2]
  if op==bytes.fromhex('fc83'):stores.append(pc)
  elif op not in [bytes.fromhex(x) for x in ['fcac','fcad','fcae']]:raise ValueError('unclassified literal use')
 if stores!=[0x602897d7,0x60289c8b]:raise ValueError('directstore inventory mismatch')
 objdump=Path(objdump).resolve(); n=0
 with tempfile.TemporaryDirectory(prefix='ep7-state-guard-') as temp:
  image=Path(temp)/'verified-main.bin';image.write_bytes(data)
  for start,stop in WINDOWS:
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   for pc,pair in W.items():
    if start<=pc<stop:require_instruction(asm,pc,*pair);n+=1
 if n!=len(W):raise ValueError('witness coverage')
 return dict(scope='Direct literal references and local sequential state-commit ABI; NOT all alias writes, task exclusivity, or live registry proof',sha256=SHA,objdump_sha256=hashlib.sha256(objdump.read_bytes()).hexdigest(),checked_instructions=n,literal_hits=[hex(x) for x in hits],direct_absolute_stores=[hex(x) for x in stores],enclosing_entry='0x60289c5e',native_call_saved_registers=['d2','d3','a2'],native_frame_bytes=16,deferred_service_frame_bytes=32,deferred_service_local_stack_offsets=[4,8,12],deferred_service_window_sha256=hashlib.sha256(data[0x6028a882-BASE:0x6028a92c-BASE]).hexdigest(),direct_service_caller_stack_arguments_found=False,candidate_precommit_boundary='0x60289c85',old_state_register='d2',new_state_register='d0',revoke_condition='actual pending commit !=255 and old==33, including same-state reentry',service_wrapper_callsites=['0x60289c5e','0x60289d02'],incoming_flags_needed_at_precommit=False,incoming_mdr_explicit_consumer_found=False,initialization_must_clear=True,global_mutex_proven=False,no_indirect_alias_proven=False,firmware_execution=False)
if __name__ == '__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--decoded',type=Path,required=True,help='Local exact-stock decoded main; never executed')
 p.add_argument('--objdump',type=Path,required=True,help='Explicit trusted GNU objdump executable')
 a=p.parse_args()
 print(json.dumps(inspect(a.decoded.read_bytes(),a.objdump.resolve()),indent=2))
