#!/usr/bin/env python3
"""Read-only exact E-P7 postbuilder entry/continuation evidence."""
import json,subprocess,sys,tempfile,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE
from ep7_request_ownership import require_instruction
from oly_container import parse
WINDOWS=[(0x603b00cf,0x603b00d0),(0x603b01c3,0x603b01d3),(0x603b0244,0x603b0247),(0x603b0252,0x603b0345),(0x603b14f1,0x603b1506),(0x603b0a70,0x603b0ad1)]
W={0x603b00cf:('setlb',''),0x603b01c5:('llt',''),0x603b0244:('ret','[d2,d3,a2,a3],96'),0x603b0252:('mov','a0,a2'),0x603b0253:('mov','(4,a2),a3'),0x603b02c5:('mov','(12,a2),d1'),0x603b02c8:('add','1816,a3'),0x603b02cc:('mov','a3,a1'),0x603b02d9:('call','0x603b0068,[d2,d3,a2,a3],96'),0x603b02de:('mov','(60,a2),d0'),0x603b02e1:('btst','2,d0'),0x603b02e4:('beq','0x603b0338'),0x603b02e6:('add','56,a2'),0x603b02e8:('mov','(a2),d0'),0x603b02e9:('cmp','0,d0'),0x603b02eb:('bne','0x603b02f0'),0x603b02ed:('ret','[d2,d3,a2,a3],20'),0x603b02f0:('mov','(a2),a0'),0x603b02f2:('clr','d0'),0x603b02f3:('mov','d0,(5760,a0)'),0x603b02f7:('bra','0x603b0342'),0x603b0338:('add','108,a2'),0x603b033a:('mov','(a2),d0'),0x603b033b:('and','-3,d0'),0x603b0341:('mov','d0,(a2)'),0x603b0342:('ret','[d2,d3,a2,a3],20'),0x603b14f3:('call','0x603b0252,[d2,d3,a2,a3],20'),0x603b14f8:('mov','d3,a0'),0x603b14fa:('call','0x603b0a70,[d2,d3,a2,a3],176'),0x603b0a72:('mov','(4,a0),d0'),0x603b0a75:('clr','d1'),0x603b0a9f:('beq','0x603b0ad3'),0x603b0aa4:('mov','(4,sp),a1')}
def inspect(raw,od):
 identity=audit(raw);main=parse(raw)[0].payload;windows=[]
 with tempfile.TemporaryDirectory(prefix='ep7-postbuilder-stock-') as tmp:
  path=Path(tmp)/'main.bin';path.write_bytes(main)
  for lo,hi in WINDOWS:
   asm=subprocess.check_output([str(od),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={lo:#x}',f'--stop-address={hi:#x}',str(path)],text=True)
   for addr,(op,args) in W.items():
    if lo<=addr<hi:require_instruction(asm,addr,op,args)
   windows.append(dict(start=hex(lo),end_exclusive=hex(hi),sha256=hashlib.sha256(main[lo-BASE:hi-BASE]).hexdigest()))
 return dict(source_sha256=identity['source_sha256'],windows=windows,witness_count=len(W),flags_dead_at_continuation=True,full_transitive_a1_liveness_proven=False,conservative_volatile_save_design=True,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path);a=p.parse_args();print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
