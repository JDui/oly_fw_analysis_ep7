"""Bounded state33/34 event tables and concrete node-disposal escape witnesses."""
from pathlib import Path
import hashlib,json,struct,subprocess,tempfile,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ep7_request_ownership import require_instruction
BASE=0x60020020
SHA='5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190'
TABLE33=[(0x18,0x602a41b2),(0x21,0x602a42f9),(0x2d,0x602a4320),(0x37,0x602a42bc),(0x42,0x602a2937),(0x43,0x602a41df),(0x44,0x602a3b87),(0x47,0x602a3765),(0x49,0x602af2fc),(0x4a,0x602af333),(0x4b,0x602a281a),(0x4c,0x602a2a66),(0x4d,0x602a2a1a),(0x4e,0x602a433c),(0x55,0x602a2b56),(0x56,0x602a3781),(0x57,0x602a380c),(0x58,0x602a383b),(0xffff,0)]
TABLE34=[(0x18,0x602a41b2),(0x21,0x602a42f9),(0x23,0x602a450a),(0x26,0x602a38c6),(0x27,0x602a44e2),(0x28,0x602a39da),(0x2d,0x602a4320),(0x2e,0x602a45a0),(0x37,0x602a42bc),(0x3d,0x602a370f),(0x42,0x602a2c8c),(0x43,0x602a41df),(0x44,0x602a3b87),(0x47,0x602a3765),(0x49,0x602af2fc),(0x4a,0x602af333),(0x4b,0x602a281a),(0x4c,0x602a2cd2),(0x55,0x602a2b56),(0x56,0x602a3781),(0x57,0x602a380c),(0x58,0x602a383b),(0xffff,0)]

W={
0x60289861:('mov','1614992752,a3'),0x60289897:('mov','65535,d3'),0x60289908:('movhu','(0x62234fc0),d0'),0x6028990e:('udfu01','20,d0'),0x60289911:('add','a3,d0'),0x60289915:('mov','(16,a0),a0'),0x60289919:('movhu','(a0),d0'),0x6028991b:('cmp','d3,d0'),0x6028991c:('bne','0x60289921'),0x6028991e:('mov','d3,d2'),0x6028991f:('bra','0x60289933'),0x60289926:('mov','(4,a0),a1'),0x6028992b:('calls','(a1)'),0x60289930:('add','8,a0'),
0x602897d7:('movhu','d0,(0x62234fc0)'),0x60289c79:('movhu','(0x62234fc0),d2'),0x60289c85:('movhu','d2,(0x62234fc8)'),0x60289c5e:('call','0x6028a882,[d2,d3,a2,a3],32'),0x60289c46:('movhu','d0,(0x62234fc2)'),0x60289c73:('mov','1614992752,a2'),0x60289c7f:('movhu','(0x62234fc2),d0'),0x60289c8b:('movhu','d0,(0x62234fc0)'),0x60289cea:('udfu01','20,d1'),0x60289cf1:('mov','(8,a0),a0'),0x60289cfa:('calls','(a0)'),
0x602a4251:('call','0x6020b9ff,[],24'),0x602a4258:('mov','d0,d2'),0x602a4259:('mov','d2,a0'),0x602a425b:('mov','(a0),a3'),0x602a427c:('mov','a3,a0'),0x602a427d:('call','0x60022732,[],4'),0x602a4284:('mov','d2,a0'),0x602a4286:('call','0x60022732,[],4'),
0x602a2afa:('mov','4,d0'),0x602a2afc:('call','0x60022700,[],4'),0x602a2b03:('mov','a0,a1'),0x602a2b04:('mov','d2,(a1)'),0x602a2b05:('mov','(0x6223e2f0),a0'),0x602a2b0b:('mov','a1,d0'),0x602a2b0d:('call','0x6020b98b,[],8'),0x602a2b32:('mov','d2,a0'),0x602a2b34:('call','0x602a446d,[a2,a3],12'),
0x602a446d:('mov','a0,a3'),0x602a44ba:('mov','a3,a1'),0x602a44bb:('inc4','a1'),0x602a44bd:('or','8,d0'),0x602a44c1:('and','24,d0'),0x602a44c4:('cmp','24,d0'),0x602a44c6:('bne','0x602a44df'),0x602a44d7:('mov','a3,a0'),0x602a44d8:('call','0x60022732,[],4'),
0x602a43cf:('mov','34,d0'),0x602a43d2:('call','0x60289c18,[d2],24'),0x602a4585:('mov','34,d0'),0x602a4588:('call','0x60289c18,[d2],24'),
0x602a2c91:('mov','(8,a0),a3'),0x602a2c94:('mov','(8,a3),a2'),0x602a2c9d:('mov','a2,a1'),0x602a2c9e:('inc4','a1'),0x602a2ca0:('or','16,d0'),0x602a2ca4:('and','24,d0'),0x602a2ca7:('cmp','24,d0'),0x602a2ca9:('bne','0x602a2cc0'),0x602a2cb8:('mov','a2,a0'),0x602a2cb9:('call','0x60022732,[],4'),
0x602a2cd9:('mov','(8,a0),d2'),0x602a2cde:('mov','d2,a3'),0x602a2ce0:('inc4','a3'),0x602a2ce4:('or','8,d0'),0x602a2cfc:('and','24,d0'),0x602a2cff:('cmp','24,d0'),0x602a2d01:('bne','0x602a2d14'),0x602a2d0b:('mov','d2,a0'),0x602a2d0d:('call','0x60022732,[],4')}
W.update({
0x602a2be6:('mov','1613376819,a0'),0x602a2bec:('mov','49280,d0'),0x602a2bf5:('call','0x6028a74c,[d2,d3,a2,a3],56'),0x602a2d36:('mov','19,d0'),0x602a2d39:('call','0x60289c18,[d2],24'),
0x6028a74d:('mov','a0,(36,sp)'),0x6028a7ff:('mov','(36,sp),d0'),0x6028a801:('udf00','20,d2'),0x6028a806:('add','1646481400,a0'),0x6028a80c:('mov','d0,(a0)'),0x6028a8aa:('mov','1646481400,a2'),0x6028a8d7:('mov','(a2),a0'),0x6028a8d9:('calls','(a0)'),0x6028a8dc:('mov','d0,(a2)'),0x6028a8e2:('add','20,a2'),0x6028a8e4:('cmp','12,d2'),0x6028a8e6:('blt','0x6028a8b0')})
WINDOWS=[(0x602897d6,0x602897e6),(0x602a2be3,0x602a2c00),(0x602a2d33,0x602a2d43),(0x6028a74c,0x6028a834),(0x6028a882,0x6028a8e8),(0x60289852,0x60289933),(0x60289c18,0x60289d18),(0x602a424b,0x602a428d),(0x602a2afa,0x602a2b39),(0x602a446d,0x602a44e2),(0x602a43cf,0x602a43db),(0x602a4585,0x602a4594),(0x602a2c8c,0x602a2d1b)]
def inspect(data,objdump):
 if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('wrong exact decoded E-P7 main')
 for i,row in enumerate(TABLE33):
  if struct.unpack_from('<II',data,0x6042d28c-BASE+i*8)!=row:raise ValueError('state33 table mismatch')
 for i,row in enumerate(TABLE34):
  if struct.unpack_from('<II',data,0x6042d344-BASE+i*8)!=row:raise ValueError('state34 table mismatch')
 for a,values in {0x6042d804:(33,0x6042d555,0x602a26aa,0x6042d26c,0x6042d28c),0x6042d818:(34,0x6042d561,0x602a2b82,0x6042d324,0x6042d344),0x6042d394:(0x42,0x602a2c8c),0x6042d3cc:(0x4c,0x602a2cd2)}.items():
  if struct.unpack_from('<'+'I'*len(values),data,a-BASE)!=values:raise ValueError('state/row mismatch')
 objdump=Path(objdump).resolve(); objsha=hashlib.sha256(objdump.read_bytes()).hexdigest(); version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0]
 n=0
 with tempfile.TemporaryDirectory(prefix='ep7-node-table-') as temp:
  image=Path(temp)/'verified-main.bin';image.write_bytes(data)
  for start,stop in WINDOWS:
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   for a,pair in W.items():
    if start<=a<stop:require_instruction(asm,a,*pair);n+=1
 if n!=len(W):raise ValueError('witness coverage')
 return dict(scope='Finite state33 table and explicit free/state escape witnesses; not transitive lifecycle closure',decoded_sha256=SHA,objdump_sha256=objsha,objdump_version=version,checked_instructions=n,state33_table_start='0x6042d28c',state33_table_stop_exclusive='0x6042d324',state33_handlers=[dict(event=hex(e),handler=hex(h)) for e,h in TABLE33[:-1]],state34_handlers=[dict(event=hex(e),handler=hex(h)) for e,h in TABLE34[:-1]],state34_stop_exclusive='0x6042d3fc',sentinel='0xffff,0',new_node_frees=['0x602a427d','0x602a44d8','0x602a2cb9','0x602a2d0d'],not_node_free_wrapper_site='0x602a4286',explicit_state_transition='33 to34; event42/4c handlers differ; registered state34 completion callback requests19',lifecycle_closure=False,firmware_execution=False)
if __name__ == '__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--decoded',type=Path,required=True,help='Local exact-stock decoded main; never executed')
 p.add_argument('--objdump',type=Path,required=True,help='Explicit trusted GNU objdump executable')
 a=p.parse_args()
 print(json.dumps(inspect(a.decoded.read_bytes(),a.objdump.resolve()),indent=2))
