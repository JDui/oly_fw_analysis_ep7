"""Read-only exact decoded stock witness checks. Outputs non-payload report only."""
from pathlib import Path
import hashlib, json, struct, subprocess, tempfile, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from ep7_request_ownership import require_instruction
BASE=0x60020020
IMAGE=ROOT/'generated/ep7/main.decoded.bin'
OBJDUMP=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
EXPECTED='5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190'
W={
0x602a2903:('mov','d2,(8,a0)'),
0x602a293c:('mov','(8,a0),d2'),0x602a2945:('mov','d2,a0'),0x602a2947:('movbu','(6,a0),d0'),0x602a294a:('mov','(8,a0),a3'),0x602a294d:('cmp','1,d0'),0x602a294f:('bne','0x602a29c6'),
0x602a29aa:('mov','a3,a0'),0x602a29ab:('call','0x60022732,[],4'),
0x602a29e4:('mov','a3,a1'),0x602a29e6:('mov','(a1),d0'),0x602a29e7:('or','16,d0'),0x602a29ea:('mov','d0,(a1)'),0x602a29eb:('and','24,d0'),0x602a29ee:('cmp','24,d0'),0x602a29f0:('bne','0x602a2a07'),0x602a29ff:('mov','a3,a0'),0x602a2a00:('call','0x60022732,[],4'),
0x602a2a20:('mov','(8,a3),a2'),0x602a2a26:('or','32,d0'),0x602a2a2a:('and','48,d0'),0x602a2a2d:('cmp','48,d0'),0x602a2a47:('mov','a2,a0'),0x602a2a48:('call','0x60022732,[],4'),
0x602a2a73:('mov','(8,a0),d2'),0x602a2a84:('mov','d2,a3'),0x602a2a8a:('or','8,d0'),0x602a2aa4:('and','24,d0'),0x602a2aa7:('cmp','24,d0'),0x602a2aa9:('bne','0x602a2abc'),0x602a2ab3:('mov','d2,a0'),0x602a2ab5:('call','0x60022732,[],4'),
0x602a3198:('movbu','d0,(6,a0)'),
0x602ac2e4:('mov','66,d0'),0x602ac2e6:('mov','a2,d1'),0x602ac2e8:('call','0x602ad656,[d2],20'),
0x602ad65b:('mov','d0,(8,sp)'),0x602ad65d:('mov','d1,(12,sp)'),
}
W.update({
0x602a29e5:('inc4','a1'),0x602a2a86:('inc4','a3'),0x602a2a87:('mov','(a3),d0'),0x602a2a8d:('mov','d0,(a3)'),
0x602a2755:('mov','1613376835,d0'),0x602a275b:('mov','d0,(4,sp)'),0x602a275d:('mov','1613377223,d0'),0x602a2763:('mov','d0,(8,sp)'),0x602a27a8:('mov','1613377425,d0'),0x602a27ae:('mov','d0,(24,sp)'),0x602a27bc:('mov','1613377602,d0'),0x602a27c2:('mov','d0,(a0)'),0x602a27e4:('call','0x6029ad23,[a2],8'),
0x602a2ecc:('mov','a1,a2'),0x602a2ecd:('inc4','a2'),0x602a2ece:('mov','(a2),d1'),0x602a2ed0:('or','32,d1'),0x602a2ed3:('mov','d1,(a2)'),0x602a2ed4:('mov','a1,a0'),0x602a2ed5:('call','0x602a302b,[],4'),
0x602a2fb1:('mov','a1,a2'),0x602a2fb2:('inc4','a2'),0x602a2fb3:('mov','(a2),d1'),0x602a2fb5:('or','4,d1'),0x602a2fb8:('mov','d1,(a2)'),0x602a2fb9:('mov','a1,a0'),0x602a2fba:('call','0x602a302b,[],4'),
0x602a302b:('mov','(4,a0),d1'),0x602a302e:('and','36,d1'),0x602a3031:('cmp','36,d1'),0x602a3033:('bne','0x602a303f'),0x602a3036:('mov','76,d1'),0x602a3038:('call','0x6020c0f0,[],16'),0x602a3046:('mov','75,d1'),0x602a3048:('call','0x6020c0f0,[],16'),
})
WINDOWS=[(0x602a2755,0x602a27e9),(0x602a2ec7,0x602a2edd),(0x602a2f91,0x602a3052),(0x602a281a,0x602a2b56),(0x602a3116,0x602a31a9),(0x602ac2c2,0x602ac2fe),(0x602ad656,0x602ad67a)]
ROWS={0x6042d2ac:(0x42,0x602a2937),0x6042d2dc:(0x4b,0x602a281a),0x6042d2e4:(0x4c,0x602a2a66),0x6042d2ec:(0x4d,0x602a2a1a)}
def inspect(data, objdump):
 if hashlib.sha256(data).hexdigest()!=EXPECTED:raise ValueError('wrong exact decoded E-P7 main')
 for a,pair in ROWS.items():
  if struct.unpack_from('<II',data,a-BASE)!=pair:raise ValueError('event row mismatch')
 checked=0
 objdump=Path(objdump).resolve()
 objdump_sha256=hashlib.sha256(objdump.read_bytes()).hexdigest()
 version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0]
 with tempfile.TemporaryDirectory(prefix='ep7-node-disposal-') as temp:
  image=Path(temp)/'verified-main.bin'
  image.write_bytes(data)
  for start,stop in WINDOWS:
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   for address,(mn,op) in W.items():
    if start<=address<stop:
     require_instruction(asm,address,mn,op)
     checked+=1
 if checked!=len(W):raise ValueError('uncovered or duplicate instruction witness')
 return dict(scope='Exact-stock static pointer witnesses, not execution or exhaustive disposal closure',decoded_sha256=EXPECTED,objdump_sha256=objdump_sha256,objdump_version=version,checked_instructions=checked,checked_event_rows=len(ROWS),new_node_free_sites=['0x602a29ab','0x602a2a00','0x602a2a48','0x602a2ab5'],normal_associated_flag_zero_sites=['0x602a2a00','0x602a2ab5'],associated_flag_one_branch_site='0x602a29ab',flag_one_guarded_event_emitter_site='0x602a2a48',closure_established=False,firmware_execution=False)
if __name__ == '__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--decoded',type=Path,required=True,help='Local exact-stock decoded main; never executed')
 p.add_argument('--objdump',type=Path,required=True,help='Explicit trusted GNU objdump executable')
 a=p.parse_args()
 print(json.dumps(inspect(a.decoded.read_bytes(),a.objdump.resolve()),indent=2))
