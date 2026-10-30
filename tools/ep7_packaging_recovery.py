"""Read-only E-P7 unchanged-container and local updater checksum audit. JSON only."""
from pathlib import Path
import hashlib,json,struct,subprocess,tempfile,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from oly_container import parse,encode,sum32
from ep7_request_ownership import require_instruction
SHA='9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb'
BASE=0x60020020
W={0x600fa454:('clr','d2'),0x600fa455:('lsr','2,d0'),0x600fa459:('mov','(a0),d1'),0x600fa45a:('inc4','a0'),0x600fa45b:('add','d1,d2'),0x600fa45e:('sub','d1,d0'),0x600fa460:('lne',''),0x600fa461:('mov','d2,d0'),0x600fa462:('retf','[d2],4'),0x60c95a7c:('mov','(12,a3),d3'),0x60c95a81:('add','64,d3'),0x60c95a8d:('mov','(d0,a3),d2'),0x60c95a8f:('mov','(d0,a0),d0'),0x60c95a91:('cmp','d0,d2'),0x60c95a94:('mov','12802,d0'),0x60c95a9d:('cmp','5,d1'),0x60c95abc:('call','0x600fa454,[d2],4'),0x60c95ac3:('cmp','0,d0'),0x60c95ac5:('beq','0x60c95b08'),0x60c95ad5:('call','0x600fa465,[],0'),0x60c95ae1:('cmp','69,d0'),0x60c95ae3:('beq','0x60c95af4'),0x60c95af4:('mov','12817,d0'),0x60c95b08:('clr','d0'),0x60c971a5:('call','0x60c95b0c,[d2,d3,a2,a3],28'),0x60c971b9:('call','0x60c95a43,[d2,d3,a2,a3],20'),0x60c95b9d:('mov','(a0),d1'),0x60c95b9e:('not','d1'),0x60c95ba0:('mov','d1,(a0)')}
WINDOWS=[(0x600fa454,0x600fa46b),(0x60c95a43,0x60c95bab),(0x60c9718c,0x60c971e5)]
STRINGS={0x60f2cb24:b'S142????BIN',0x60f2cb30:b'E142????BIN',0x60f2d81c:b'E142????BIN',0x60f2cd07:b'DCOLYMP'}
def inspect(raw,objdump):
 if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('wrong exact E-P7 stock')
 blocks=parse(raw);rows=[];roundtrip=hashlib.sha256()
 for b in blocks:
  if b.header[2:4].hex()!='1420':raise ValueError('model')
  rebuilt=b.header+encode(b.payload)+b.trailer
  if rebuilt!=raw[b.offset:b.offset+len(rebuilt)]:raise ValueError('no-op byte mismatch')
  roundtrip.update(rebuilt)
  computed=(-(sum32(b.header)+sum32(b.payload)+sum32(b.trailer[:28])))&0xffffffff
  stored=struct.unpack_from('<I',b.trailer,28)[0]
  if computed!=stored:raise ValueError('recomputed checksum mismatch')
  rows.append(dict(index=b.index,offset=b.offset,container_address=hex(b.address),kind=hex(b.kind),payload_bytes=len(b.payload),model_bytes='1420',header_build=hex(struct.unpack_from('<H',b.header,16)[0]),decoded_sha256=hashlib.sha256(b.payload).hexdigest(),component_sum32=0,trailer_checksum_recomputed_equals_stored=True,unchanged_encode_byte_identical=True))
 if roundtrip.hexdigest()!=SHA:raise ValueError('whole source hash mismatch')
 data=blocks[0].payload
 for a,s in STRINGS.items():
  if data[a-BASE:a-BASE+len(s)]!=s:raise ValueError('string witness')
 objdump=Path(objdump).resolve();n=0
 with tempfile.TemporaryDirectory(prefix='ep7-package-audit-') as td:
  image=Path(td)/'verified-main.bin';image.write_bytes(data)
  for a,b in WINDOWS:
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={a:#x}',f'--stop-address={b:#x}',str(image)],text=True)
   for pc,args in W.items():
    if a<=pc<b:require_instruction(asm,pc,*args);n+=1
 if n!=len(W):raise ValueError('witness coverage')
 return dict(scope='Unchanged container integrity and local static checksum path, NOT device acceptance, cryptographic-authentication exclusion, bootability or recovery',source_sha256=SHA,source_bytes=len(raw),exact_unchanged_byte_roundtrip=True,components=rows,checked_instructions=n,objdump_sha256=hashlib.sha256(objdump.read_bytes()).hexdigest(),filename_string_leads=[{'address':hex(a),'text':s.decode()} for a,s in STRINGS.items()],native_checksum_helper='0x600fa454',local_main_checksum_error='0x3211',cryptographic_checks_absent_proven=False,ep7_modified_image_acceptance_proven=False,ep7_same_version_install_proven=False,ep7_partial_update_proven=False,ep7_physical_recovery_entry_proven=False,independent_rescue_loader_proven=False,firmware_image_output_created=False,firmware_executed=False)
if __name__ == '__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--stock',type=Path,required=True)
 p.add_argument('--objdump',type=Path,required=True,help='Explicit trusted objdump executable')
 a=p.parse_args()
 print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
