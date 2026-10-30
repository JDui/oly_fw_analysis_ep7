#!/usr/bin/env python3
"""Exact-stock wait/cancel operands; not hardware quiescence proof."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE
from ep7_request_ownership import require_instruction
from oly_container import parse,sha256
WINDOWS={
 'wait_branching':(0x60350c1a,0x60350ce4),
 'postwait_gate':(0x60350da1,0x60350dbf),
 'predicate':(0x60354ac9,0x60354aee),
 'conditional_abort':(0x60334d84,0x60334daa),
 'abort_register_paths':(0x60345a59,0x60345af8),
 'bitmap_cleanup':(0x60350b6f,0x60350ba8),
}
WITNESSES={
 0x60350c25:('btst','-2147483648,d1'),
 0x60350c2b:('beq','0x60350c93'),
 0x60350c40:('mov','20,d1'),
 0x60350c49:('call','0x6003883c,[d2,d3,a2,a3],40'),
 0x60350c54:('cmp','-50,d0'),
 0x60350c61:('call','0x60354ac9,[a2],8'),
 0x60350c69:('beq','0x60350c8b'),
 0x60350c6d:('call','0x60334d84,[d2],8'),
 0x60350c76:('mov','(52,sp),d1'),
 0x60350c7a:('mov','d1,(4,sp)'),
 0x60350c82:('call','0x6003883c,[d2,d3,a2,a3],40'),
 0x60350c89:('bra','0x60350cd8'),
 0x60350c8b:('inc','d3'),
 0x60350c8d:('cmp','50,d3'),
 0x60350c8f:('blt','0x60350c3b'),
 0x60350c91:('bra','0x60350cba'),
 0x60350cab:('call','0x6003883c,[d2,d3,a2,a3],40'),
 0x60350cb6:('cmp','-50,d0'),
 0x60350cba:('mov','40651,d0'),
 0x60350cc2:('mov','40648,d0'),
 0x60350cd8:('mov','40449,d0'),
 0x60350da9:('cmp','0,d2'),
 0x60350dab:('beq','0x60350db5'),
 0x60350dad:('cmp','40449,d2'),
 0x60350db3:('bne','0x60350dbb'),
 0x60350db6:('call','0x60350d71,[],4'),
 0x60354ace:('mov','13,d0'),
 0x60354ad2:('call','0x6034442b,[a2,a3],12'),
 0x60354ada:('cmp','0,d0'),
 0x60354ae7:('movhu','d0,(a2)'),
 0x60334d86:('call','0x603459a8,[],0'),
 0x60334d8e:('cmp','d2,d0'),
 0x60334d8f:('bne','0x60334da6'),
 0x60334d91:('btst','-2147483648,d0'),
 0x60334d97:('beq','0x60334da6'),
 0x60334d99:('mov','40449,d0'),
 0x60334d9f:('call','0x60345a59,[d2],8'),
 0x60345a96:('bra','0x60345af5'),
 0x60345aeb:('mov','(0x9f000070),d0'),
 0x60345af1:('and','d1,d0'),
 0x60345af3:('cmp','d1,d0'),
 0x60350b89:('mov','(a0),d1'),
 0x60350b96:('not','d0'),
 0x60350b98:('and','d0,d1'),
 0x60350b9a:('mov','d1,(a0)'),
}
def inspect(raw,objdump):
 identity=audit(raw);main=parse(raw)[0].payload
 version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0];windows={}
 with tempfile.TemporaryDirectory(prefix='ep7-timeout-') as temp:
  image=Path(temp)/'main.bin';image.write_bytes(main)
  for name,(start,stop) in WINDOWS.items():
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   addresses=[a for a in WITNESSES if start<=a<stop]
   for a in addresses:require_instruction(asm,a,*WITNESSES[a])
   windows[name]=dict(start=hex(start),stop_exclusive=hex(stop),sha256=sha256(main[start-BASE:stop-BASE]),witness_count=len(addresses))
 return dict(source_sha256=identity['source_sha256'],objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),windows=windows,instruction_witness_count=len(WITNESSES),
  waits=dict(poll_timeout_operand=20,poll_limit=50,lower_timeout_result=-50,timeout_return='0x9ecb',generic_error_return='0x9ec8',cancel_return='0x9e01',second_wait_result_tested=False),
  qualification=dict(cancel_return_does_not_prove_second_wait_success=True,abort_requires_matching_id_and_bit31=True,bitmap_clear_is_not_quiescence_proof=True,all_transitive_cleanup_not_mapped=True,permits_extension_reuse=False),
  limitations=['MMIO status meanings and all cleanup targets are not qualified.','Some abort paths poll hardware state; absence of all synchronization is NOT asserted.','Do not treat cancellation/timeout return or bitmap cleanup as extension lifetime proof.'],camera_accessed=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path);a=p.parse_args();print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
