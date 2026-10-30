#!/usr/bin/env python3
"""Static E-P7 get_tid API and named caller evidence, not a TLS implementation."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE,require
from ep7_request_ownership import require_instruction
from oly_container import parse,sha256
WINDOWS={'native_get_tid': (1610815404, 1610815472),
 'named_query_caller': (1630304492, 1630304570)}
WITNESSES={1610815404: ('mov', '(0x8050),d0'),
 1610815407: ('mov', '-1880096764,a2'),
 1610815413: ('asl2', 'd0'),
 1610815414: ('mov', '(d0,a2),a1'),
 1610815416: ('mov', '(28,a1),a1'),
 1610815419: ('movbu', '(a1),d1'),
 1610815425: ('bne', '0x600317c4'),
 1610815441: ('movbu', '(1,a1),d0'),
 1610815444: ('cmp', '1,d0'),
 1610815446: ('bne', '0x600317dc'),
 1610815448: ('mov', '-25,d0'),
 1610815452: ('mov', '(0x8050),d0'),
 1610815456: ('mov', '(d0,a2),a1'),
 1610815458: ('mov', '(96,a1),a1'),
 1610815461: ('mov', '(a1),a1'),
 1610815463: ('movhu', '(16,a1),d0'),
 1610815466: ('movhu', 'd0,(a0)'),
 1610815468: ('clr', 'd0'),
 1630304492: ('mov', 'sp,a0'),
 1630304493: ('add', '8,a0'),
 1630304495: ('call', '0x600317ac,[a2],4'),
 1630304502: ('cmp', '0,d0'),
 1630304504: ('beq', '0x612c790d'),
 1630304506: ('mov', '1630978515,d0'),
 1630304516: ('call', '0x612c79cc,[],0'),
 1630304521: ('mov', '0,a0'),
 1630304525: ('movhu', '(8,sp),d2'),
 1630304528: ('movhu', '(0x60040f14),d1'),
 1630304539: ('udf00', '20,d0'),
 1630304542: ('mov', '1644004672,a1')}
def inspect(raw,objdump):
 identity=audit(raw);main=parse(raw)[0].payload
 require(main[0x6136c1d3-BASE:0x6136c1eb-BASE]==b'get_tid returned Error\n\x00','named current-task error string mismatch')
 version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0];windows={}
 with tempfile.TemporaryDirectory(prefix='ep7-task-identity-') as temp:
  image=Path(temp)/'main.bin';image.write_bytes(main)
  for name,(start,stop) in WINDOWS.items():
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   addresses=[a for a in WITNESSES if start<=a<stop]
   for a in addresses:require_instruction(asm,a,*WITNESSES[a])
   windows[name]=dict(start=hex(start),stop_exclusive=hex(stop),sha256=sha256(main[start-BASE:stop-BASE]),witness_count=len(addresses))
 return dict(source_sha256=identity['source_sha256'],objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),windows=windows,instruction_witness_count=len(WITNESSES),
  query_api=dict(address='0x600317ac',output='halfword through a0',success_return=0,context_failure_return=-25,task_id_is_not_cpu_word_8050=True,named_caller='0x612c78ec'),
  limitations=['Current-task identity is a candidate key, not an allocation or generation certificate.','Per-core context flags are checked; exact interrupt/dispatch-disabled semantics remain unqualified.','No available TLS slot, task-ID nonreuse, task destruction hook or safe nesting facility has been established.','No native scoped admission implementation or concurrency safety claim.'],camera_accessed=False,firmware_executed=False,admission_hook_implemented=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path);a=p.parse_args();print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
