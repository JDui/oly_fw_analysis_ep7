"""Read-only common state-commit/frame and finite literal-reference witnesses."""
from pathlib import Path
import hashlib,json,struct,subprocess,tempfile,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from ep7_request_ownership import require_instruction
BASE=0x60020020
SHA='5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190'
W={1613415383: ('mov', 'a2,d0'), 1613415385: ('call', '0x602ac8d0,[],0'), 1613415390: ('call', '0x602ac748,[d2,a2,a3],32'), 1613415919: ('mov', 'd0,d2'), 1613415944: ('mov', 'd2,d0'), 1613415945: ('call', '0x602ac8d0,[],0'), 1613415950: ('call', '0x602ac748,[d2,a2,a3],32'), 1613416264: ('mov', 'd0,d2'), 1613416265: ('mov', '148,d0'), 1613416268: ('call', '0x60022700,[],4'), 1613416275: ('mov', 'a0,a3'), 1613416276: ('mov', 'd2,(8,a3)'), 1613416305: ('mov', '84,a2'), 1613416307: ('add', 'a0,a2'), 1613416344: ('mov', '84,a2'), 1613416346: ('add', 'a0,a2'), 1613416365: ('mov', '84,a2'), 1613416367: ('add', 'a0,a2'), 1613416395: ('call', '0x602acf12,[],0'), 1613416402: ('mov', '84,a2'), 1613416404: ('add', 'a0,a2'), 1613416518: ('mov', '1613416563,d0'), 1613416524: ('mov', 'd0,(4,a3)'), 1613416527: ('mov', '19,d0'), 1613416529: ('mov', 'd0,(12,sp)'), 1613416531: ('mov', '68,d0'), 1613416533: ('mov', 'd0,(8,sp)'), 1613416544: ('mov', 'a3,(16,sp)'), 1613416553: ('call', '0x6020beb4,[d2,d3],48'), 1613416560: ('ret', '[d2,a2,a3],32'), 1613416656: ('movhu', '(0x6223e79a),d1'), 1613416662: ('mov', 'd0,a0'), 1613416668: ('mov', '(a0),d0'), 1613416669: ('retf', '[],0')}
WINDOWS=[(0x602ac3d7,0x602ac3e3),(0x602ac5ef,0x602ac613),(0x602ac748,0x602ac873),(0x602ac8d0,0x602ac8e0),(0x602acf12,0x602acf50)]
SIM_SHA='355754c61879dc24bf6128bbba5a7931355731000e8cb213082b9b9cd4df0129'
def inspect(data,objdump):
 if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('wrong exact main')
 candidates=[]
 for i,b in enumerate(data):
  size=2 if b==0xcd else 4 if b==0xdd else 0
  if size and i+size+3<=len(data):
   if BASE+i+int.from_bytes(data[i+1:i+1+size],'little',signed=True)==0x602ac748:candidates.append(BASE+i)
 if candidates!=[0x602ac3de,0x602ac60e]:raise ValueError('direct relative CALL candidate inventory changed')
 sim=ROOT/'generated/ep7/gcc_abi/mn10300.igen'
 if hashlib.sha256(sim.read_bytes()).hexdigest()!=SIM_SHA:raise ValueError('semantics source mismatch')
 objdump=Path(objdump).resolve();n=0
 with tempfile.TemporaryDirectory(prefix='ep7-metadata-adapter-') as temp:
  image=Path(temp)/'verified-main.bin';image.write_bytes(data)
  for start,stop in WINDOWS:
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   for pc,pair in W.items():
    if start<=pc<stop:require_instruction(asm,pc,*pair);n+=1
 if n!=len(W):raise ValueError('witness coverage')
 return dict(sha256=SHA,objdump_sha256=hashlib.sha256(objdump.read_bytes()).hexdigest(),semantics_sha256=SIM_SHA,checked_instructions=n,direct_relative_call_candidates=[hex(x) for x in candidates],wrapper_entry_stack_offsets={'allocator_return':4,'producer_return':36},allocator_continuation='0x602ac753',supported_producer_return='0x602ac3e3',alternate_producer_return='0x602ac613',capture_id_register='d2',supported_associated_register='a2',native_bytes=148,proposed_explicit_request_bytes=192,firmware_execution=False,all_indirect_callers_proven=False,allocation_success_proven=False,native_lifetime_proven=False,windows=[{'start':hex(a),'stop':hex(b),'sha256':hashlib.sha256(data[a-BASE:b-BASE]).hexdigest()} for a,b in WINDOWS])
if __name__ == '__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--decoded',type=Path,required=True)
 p.add_argument('--objdump',type=Path,required=True,help='Explicit trusted objdump executable')
 a=p.parse_args()
 print(json.dumps(inspect(a.decoded.read_bytes(),a.objdump.resolve()),indent=2))
