#!/usr/bin/env python3
"""Exact-stock E-P7 output lane evidence; no native memory writes."""
import argparse,json,subprocess,sys,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE
from ep7_request_ownership import require_instruction
from oly_container import parse
W={
0x603b02c5:('mov','(12,a2),d1'),0x603b02d9:('call','0x603b0068,[d2,d3,a2,a3],96'),
0x603b006e:('add','688,d0'),0x603b007a:('add','168,d0'),
0x603b0090:('add','12,d0'),0x603b0096:('add','16,d0'),0x603b009c:('add','20,d0'),
0x603b00d4:('udf00','28,d1'),0x603b00e4:('mov','a1,d1'),0x603b00e6:('add','d1,d1'),0x603b00e7:('add','a0,d1'),0x603b00e9:('movbu','(d1,a2),d2'),
0x603b015b:('movhu','(12,a2),d2'),0x603b015e:('mov','(16,sp),a0'),0x603b0160:('asl','16,d2'),0x603b016a:('mov','d2,(a0)'),
0x603b016b:('movhu','(16,a2),d1'),0x603b016e:('mov','(4,sp),a2'),0x603b0175:('asl','16,d1'),0x603b0178:('or','d1,d3'),0x603b017a:('mov','d3,(a2)'),
0x603b019f:('mov','(4,sp),d0'),0x603b01a1:('add','24,d0'),0x603b01a3:('mov','d0,(4,sp)'),0x603b01a5:('mov','(16,sp),d0'),0x603b01a7:('add','24,d0'),0x603b01a9:('mov','d0,(16,sp)'),
0x603b017d:('add','24,d0'),0x603b01c3:('cmp','6,d0'),0x603b01cc:('cmp','2,a0'),0x603b01d8:('mov','d0,(976,a0)')}
def inspect(raw,od):
 identity=audit(raw);main=parse(raw)[0].payload
 with tempfile.TemporaryDirectory(prefix='ep7-output-map-') as d:
  path=Path(d)/'main.bin';path.write_bytes(main)
  asm=subprocess.check_output([str(od),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}','--start-address=0x603b0068','--stop-address=0x603b02de',str(path)],text=True)
  for addr,(op,args) in W.items():require_instruction(asm,addr,op,args)
 return dict(source_sha256=identity['source_sha256'],objdump_sha256=hashlib.sha256(od.read_bytes()).hexdigest(),objdump_version=subprocess.check_output([str(od),'--version'],text=True).splitlines()[0],window_start='0x603b0068',window_end_exclusive='0x603b02de',camera_accessed=False,firmware_executed=False,flash_ready=False,window_sha256=hashlib.sha256(main[0x603b0068-BASE:0x603b02de-BASE]).hexdigest(),witness_count=len(W),output_base='*(setup+12)',records=[dict(output_record=6*p+k,input_bin=2*k+p,source12_lane_offset=706+24*(6*p+k),source16_lane_offset=710+24*(6*p+k),saturation_offset=708+24*(6*p+k)) for p in range(2) for k in range(6)],required_buffer_length=976,hue_lightness_calibration_verified=False,firmware_modified=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True);a=p.parse_args();print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
