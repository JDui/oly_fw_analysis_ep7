#!/usr/bin/env python3
"""Exact-stock source/clone operands; static read-only candidate, no firmware execution."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from ep7_stock_audit import audit, BASE
from ep7_request_ownership import require_instruction
from oly_container import parse, sha256

WINDOWS = {
 'descriptor_processing_loop': (0x603e5d57, 0x603e5fa0),
 'source_clone_and_release': (0x603edb9a, 0x603edc10),
 'descriptor_transport_entry': (0x603df9f1, 0x603dfa41),
 'allocator_class_selector': (0x603ed63d, 0x603ed6c4),
}
WITNESSES = {
 0x603e5d59: ('add', '-396,sp'),
 0x603e5d61: ('mov', 'sp,a3'),
 0x603e5d62: ('add', '16,a3'),
 0x603e5d6e: ('movhu', '(0x60040d70),d0'),
 0x603e5d76: ('call', '0x603df9f1,[a2],16'),
 0x603e5d91: ('mov', '(44,sp),a0'),
 0x603e5d93: ('movhu', '(23924,a0),d0'),
 0x603e5d97: ('cmp', '5,d0'),
 0x603e5d99: ('bne', '0x603e5de9'),
 0x603e5de4: ('call', '0x603edb9a,[a2,a3],12'),
 0x603e5e16: ('call', '0x603edc07,[],0'),
 0x603e5e1b: ('mov', 'd0,(44,sp)'),
 0x603e5ee5: ('call', '0x603e5fce,[d2,a2,a3],20'),
 0x603e5f78: ('call', '0x603e16f1,[d2,d3,a2,a3],24'),
 0x603e5f7d: ('cmp', '0,d0'),
 0x603e5f7f: ('bne', '0x603e5f84'),
 0x603e5f81: ('jmp', '0x603e5df7'),
 0x603e5f84: ('call', '0x603edbed,[],0'),
 0x603e5f8a: ('cmp', '1,d0'),
 0x603e5f8c: ('bne', '0x603e5f94'),
 0x603e5f8f: ('call', '0x603edbd8,[],4'),
 0x603edb9b: ('movhu', '(260,a2),d0'),
 0x603edb9f: ('cmp', '0,d0'),
 0x603edba1: ('beq', '0x603edbb0'),
 0x603edba3: ('mov', '(116,a2),d0'),
 0x603edba6: ('call', '0x6029b9d1,[],24'),
 0x603edbad: ('mov', 'a0,a3'),
 0x603edbb0: ('mov', '(28,a2),a3'),
 0x603edbb3: ('mov', 'a2,a0'),
 0x603edbb4: ('mov', '41984,d0'),
 0x603edbba: ('call', '0x603ed63d,[d2,a2],20'),
 0x603edbbf: ('mov', 'd0,(0x622933dc)'),
 0x603edbc5: ('mov', 'd0,(28,a2)'),
 0x603edbc8: ('mov', 'd0,a0'),
 0x603edbca: ('mov', '27332,d0'),
 0x603edbcd: ('mov', 'a3,a1'),
 0x603edbce: ('call', '0x47001052,[d2,d3,a2,a3],28'),
 0x603edbd8: ('mov', '(0x622933dc),d0'),
 0x603edbde: ('call', '0x603ed6c4,[d2],16'),
 0x603edbe3: ('clr', 'd0'),
 0x603edbe4: ('mov', 'd0,(0x622933dc)'),
 0x603edc07: ('mov', '(0x622933dc),d0'),
 0x603df9fb: ('mov', '300,d1'),
 0x603dfa04: ('call', '0x603eeb57,[d2,d3,a2,a3],44'),
 0x603ed63d: ('mov', '(28,a0),a2'),
 0x603ed644: ('movhu', '(a1),d1'),
 0x603ed64c: ('movbu', '(24776,a2),d1'),
 0x603ed6bc: ('call', '0x603ecb42,[d2,d3,a2,a3],52'),
}

def inspect(raw, objdump):
    identity = audit(raw) # Reject wrong build before any parsing/disassembler execution.
    main = parse(raw)[0].payload
    version = subprocess.check_output([str(objdump), '--version'], text=True).splitlines()[0]
    windows = {}
    with tempfile.TemporaryDirectory(prefix='ep7-source-clone-') as temp:
        image = Path(temp)/'main.bin'
        image.write_bytes(main)
        for name,(start,stop) in WINDOWS.items():
            asm = subprocess.check_output([str(objdump), '-b','binary','-m','mn10300','-D','-z',
                '--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',
                f'--stop-address={stop:#x}',str(image)],text=True)
            addresses = [a for a in WITNESSES if start <= a < stop]
            for address in addresses: require_instruction(asm,address,*WITNESSES[address])
            windows[name] = dict(start=hex(start), stop_exclusive=hex(stop),
                sha256=sha256(main[start-BASE:stop-BASE]), witness_count=len(addresses))
    return dict(scope='Exact E-P7 stock static source/clone operands, not runtime ownership proof',
        source_sha256=identity['source_sha256'], objdump_version=version,
        objdump_sha256=sha256(objdump.read_bytes()), windows=windows,
        instruction_witness_count=len(WITNESSES),
        source_selection=dict(nonzero_flag_offset=260, registry_id_offset=116,
            registry_getter='0x6029b9d1', alternate_pointer_offset=28),
        clone=dict(requested_bytes=41984, copy_length_operand=27332,
            copy_source='selected registry pointer or entry descriptor+28',
            allocator_class_input='entry descriptor+28, NOT necessarily selected registry pointer',
            descriptor_pointer_offset=28, global_pointer='0x622933dc',
            stock_S_halfword_range=[24058,24082], stock_S_range_inside_copy=True),
        descriptor=dict(stack_offset=16, transport_size_operand=300,
            producer_and_ownership_not_established=True),
        limitations=['Local conditional release is not proof of asynchronous job completion.',
            'Allocator failure semantics and all clone consumers remain unqualified.',
            '41984 allocation request does not prove extension bytes are spare or copied.',
            'No H/L storage, patch hook, or working image processing established.'],
        camera_accessed=False, firmware_executed=False, flash_ready=False)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True)
    parser.add_argument('--objdump',type=Path,required=True,help='Explicit trusted objdump executable')
    args=parser.parse_args()
    print(json.dumps(inspect(args.stock.read_bytes(),args.objdump.resolve()),indent=2))
