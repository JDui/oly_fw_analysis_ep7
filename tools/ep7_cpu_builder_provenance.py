#!/usr/bin/env python3
"""Static E-P7 constructor/pointer transfer and conditional synchronous CPU builder witnesses."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE,require
from ep7_request_ownership import require_instruction
from oly_container import parse,sha256
WINDOWS={'fresh_job': (1614703876, 1614704024),
 'native_constructor': (1614100459, 1614100498),
 'request_wrapper': (1614107657, 1614107673),
 'operation_bind': (1614105484, 1614105598),
 'submit_request': (1614109801, 1614109870),
 'submit_stack_root': (1614108878, 1614108898),
 'driver_config_order': (1613974964, 1613975086),
 'config_dispatch': (1613993693, 1613993732),
 'conditional_color_builder': (1613994074, 1613994111),
 'input_format_dispatch': (1614458093, 1614458151),
 'color_cpu_calls': (1614485478, 1614485547),
 'color_selector_caller': (1614484582, 1614484759),
 'color_selector': (1614479954, 1614480094),
 'header_stage_override': (1614140251, 1614140274)}
WITNESSES={1614703934: ('call', '0x603537eb,[d2,d3,a2,a3],44'),
 1614703941: ('mov', 'd0,(36,a3)'),
 1614703952: ('call', '0x603e62d1,[d2,d3,a2,a3],72'),
 1614704004: ('call', '0x603e61b8,[d2,a2,a3],24'),
 1614704013: ('call', '0x603e6c8d,[a2,a3],24'),
 1614100464: ('mov', '15488,d0'),
 1614100467: ('call', '0x60022700,[],4'),
 1614107657: ('mov', '11364,a2'),
 1614107660: ('add', 'a0,a2'),
 1614107663: ('mov', 'a2,a1'),
 1614107664: ('call', '0x60354ce4,[d2,d3,a2,a3],32'),
 1614107669: ('mov', 'a2,a0'),
 1614105505: ('mov', 'a2,(a0)'),
 1614105572: ('mov', 'a0,(4,a3)'),
 1614105587: ('add', '11364,a0'),
 1614105591: ('mov', 'd3,(4,a0)'),
 1614105596: ('mov', 'a0,(a2)'),
 1614109820: ('mov', '(56,sp),a0'),
 1614109823: ('mov', '(a0),a0'),
 1614109825: ('call', '0x60334ba8,[],4'),
 1614108878: ('mov', 'a0,(16,sp)'),
 1614108882: ('add', '8,d0'),
 1614108884: ('mov', 'd0,(56,sp)'),
 1613974987: ('call', '0x60344975,[d2,d3,a2,a3],40'),
 1613975021: ('call', '0x603396dd,[d2,a2],72'),
 1613975067: ('call', '0x603450dd,[d2,d3,a2,a3],28'),
 1613993707: ('mov', '(4,a2),a1'),
 1613993710: ('mov', '1615744896,a0'),
 1613993716: ('movbu', '(16,a1),d0'),
 1613993720: ('mov', '(d0,a0),a1'),
 1613993724: ('calls', '(a1)'),
 1613994076: ('call', '0x60339c27,[a2],4'),
 1613994083: ('beq', '0x6033987f'),
 1613994096: ('call', '0x603aaced,[a2],8'),
 1614458094: ('inc4', 'a2'),
 1614458095: ('mov', '(a2),a1'),
 1614458097: ('movbu', '(16,a1),d0'),
 1614458100: ('cmp', '0,d0'),
 1614458121: ('movhu', '(28,a1),d0'),
 1614458124: ('asr', '8,d0'),
 1614458127: ('cmp', '1,d0'),
 1614458131: ('cmp', '2,d0'),
 1614458137: ('call', '0x603b17e6,[a2],8'),
 1614458144: ('call', '0x603b1819,[a2],8'),
 1614485503: ('call', '0x603b1466,[d2,d3,a2,a3],40'),
 1614485530: ('call', '0x603b1466,[d2,d3,a2,a3],40'),
 1614484723: ('call', '0x603b0252,[d2,d3,a2,a3],20'),
 1614480065: ('cmp', '11,d1'),
 1614480072: ('add', '1816,a3'),
 1614480089: ('call', '0x603b0068,[d2,d3,a2,a3],96'),
 1614140252: ('call', '0x60355409,[a2],8'),
 1614140264: ('movhu', 'd0,(12,a3)')}
def inspect(raw,objdump):
 identity=audit(raw);main=parse(raw)[0].payload
 require(main[0x604e4f80-BASE:0x604e4f84-BASE]==(0x603397db).to_bytes(4,'little'),'type0 configuration dispatcher mismatch')
 version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0];windows={}
 with tempfile.TemporaryDirectory(prefix='ep7-cpu-builder-') as temp:
  image=Path(temp)/'main.bin';image.write_bytes(main)
  for name,(start,stop) in WINDOWS.items():
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   addresses=[a for a in WITNESSES if start<=a<stop]
   for a in addresses:require_instruction(asm,a,*WITNESSES[a])
   windows[name]=dict(start=hex(start),stop_exclusive=hex(stop),sha256=sha256(main[start-BASE:stop-BASE]),witness_count=len(addresses))
 return dict(source_sha256=identity['source_sha256'],objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),windows=windows,instruction_witness_count=len(WITNESSES),
  conditional_cpu_chain=['0x603558ce','0x60355c81','0x60334ba8','0x60334db4','0x603396dd','0x603397db','0x60339870','0x603aaced','0x603b17e6 or 0x603b1819','0x603b1466','0x603b0252','0x603b0068'],
  limitations=['Conditional direct-call chain, not proof that every capture or stage reaches COLOR builder.','Constructor return is stored as a pointer; supported embedded shape is not allocation provenance.','Header fields may be changed after request wrapper; example stage sets request+12=0xf005.','New trailer may not be read to discover whether the allocation was enlarged. Admission needs independently established provenance and liveness.','No trailer allocation, firmware patch, camera memory read or hardware quiescence claim.'],camera_accessed=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path);a=p.parse_args();print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
