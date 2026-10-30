#!/usr/bin/env python3
"""Exact-build E-P7 static owner/transport witnesses; no firmware execution.

Not a patch builder. Emits metadata, not firmware/listings.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from ep7_stock_audit import audit, BASE, require
from oly_container import parse, sha256

WINDOWS = {
    'capture_pool_initializer': (0x603daf36, 0x603daf5d),
    'capture_pool_base_constructor': (0x603dd1d8, 0x603dd223),
    'capture_pool_derived_constructor': (0x603dda0e, 0x603dda74),
    'capture_pool_resolver': (0x603ddbdb, 0x603ddc20),
    'capture_registry_getter': (0x6029b9d1, 0x6029ba1e),
    'capture_registry_allocate_release': (0x6029bdec, 0x6029be82),
    'capture_population_entry': (0x602a7ea0, 0x602a7eb0),
    'job_allocate_then_convert': (0x603e6d04, 0x603e6d98),
    'job_constructor': (0x603537eb, 0x60353915),
    'request_header': (0x60354cb9, 0x60354ce4),
    'request_producer': (0x60354ce4, 0x60355098),
    'request_wrapper': (0x60355409, 0x60355419),
    'job_parameter_getter': (0x60353cfb, 0x60353d02),
    'table_borrow_wrappers': (0x6035109b, 0x603510af),
    'table_slot_and_publish': (0x603510af, 0x60351174),
    'table_borrow_scope': (0x6036884d, 0x603688ed),
    'current_S_to_capture': (0x602a85c4, 0x602a86b7),
    'capture_to_job': (0x603e62d1, 0x603e66a0),
    'alternate_capture_to_job': (0x603e8af1, 0x603e91e4),
    'compact_to_parameters': (0x60324071, 0x60324376),
}
# Small instruction-operand assertions at reviewed boundaries; no blob matching.
WITNESSES = {
    0x603daf36: ('mov', '25,d0'),
    0x603daf38: ('mov', 'd0,(4,sp)'),
    0x603daf43: ('mov', '-1570121344,a0'),
    0x603daf49: ('mov', '-1352648768,d0'),
    0x603daf4f: ('mov', '41984,d1'),
    0x603daf55: ('mov', '5376,a1'),
    0x603daf58: ('call', '0x603dda0e,[d2,a2],32'),
    0x603dd1e4: ('mov', 'd0,(8,a2)'),
    0x603dd1e7: ('mov', 'd1,(12,a2)'),
    0x603dd1f6: ('movhu', 'd0,(20,a2)'),
    0x603dd1fb: ('movhu', 'd0,(22,a2)'),
    0x603dd203: ('movhu', 'd0,(24,a2)'),
    0x603dda2a: ('call', '0x603dd1d8,[d2,a2],12'),
    0x603dda30: ('mov', '1616095336,d0'),
    0x603dda36: ('mov', 'd0,(a2)'),
    0x603ddbe5: ('and', '255,d2'),
    0x603ddbf6: ('add', '-1,d2'),
    0x603ddc12: ('mov', '(12,a2),d0'),
    0x603ddc15: ('mov', '(8,a2),d1'),
    0x603ddc1a: ('add', 'd1,d2'),
    0x603ddc1b: ('mov', 'd2,(a3)'),
    0x6029b9d1: ('cmp', '1,d0'),
    0x6029b9d5: ('cmp', '26,d0'),
    0x6029b9df: ('add', '1646514552,a0'),
    0x6029b9e7: ('btst', '4,d1'),
    0x6029ba18: ('mov', '(12,a0),a0'),
    0x6029bdef: ('mov', '5376,d0'),
    0x6029bdf2: ('call', '0x603db792,[d2,d3,a2,a3],48'),
    0x6029be11: ('movhu', 'd0,(16,a2)'),
    0x6029be17: ('call', '0x603dba87,[d2,d3,a2,a3],44'),
    0x6029be1e: ('mov', 'd0,(12,a2)'),
    0x6029be2a: ('or', '4,d0'),
    0x6029be5a: ('movhu', '(16,a2),d0'),
    0x6029be5d: ('call', '0x603db89e,[],4'),
    0x6029be66: ('and', '65531,d0'),
    0x602a7ea0: ('call', '0x6029b9d1,[],24'),
    0x602a7ea7: ('mov', 'a0,d3'),
    0x603e6d3e: ('call', '0x603537eb,[d2,d3,a2,a3],44'),
    0x603e6d45: ('mov', 'd0,(36,a3)'),
    0x603e6d50: ('call', '0x603e62d1,[d2,d3,a2,a3],72'),
    0x603537f0: ('mov', '15488,d0'),
    0x603537f3: ('call', '0x60022700,[],4'),
    0x60353817: ('mov', '6556,d1'),
    0x60353898: ('mov', 'd0,(13252,a3)'),
    0x60354cba: ('mov', '1614110676,d0'), # callback 0x60355fd4
    0x60354cc0: ('mov', 'd0,(a1)'),
    0x60354ce7: ('mov', '1884,d1'),
    0x60354cee: ('call', '0x4700115e,[d2,a2],8'),
    0x60354d14: ('mov', '(13252,a0),a0'),
    0x60354d1a: ('mov', 'a0,(1524,a2)'),
    0x60354d03: ('add', '36,a3'),
    0x60354e8b: ('mov', '5538,a1'),
    0x60354e96: ('add', 'a3,a1'),
    0x60354f8e: ('mov', '1816,a0'),
    0x60354f99: ('add', 'a2,a0'),
    0x60354faa: ('movbu', '(d0,a1),d1'),
    0x60354fad: ('movbu', 'd1,(d0,a0)'),
    0x60354fb1: ('cmp', '12,d2'),
    0x60355409: ('mov', '11364,a2'),
    0x60355410: ('call', '0x60354ce4,[d2,d3,a2,a3],32'),
    0x60353cfd: ('add', '36,a0'),
    0x6035109d: ('call', '0x60351156,[],0'),
    0x603510a7: ('call', '0x60351167,[],0'),
    0x60351156: ('mov', '15436,a1'),
    0x6035115d: ('inc', 'd0'),
    0x60351160: ('mov', '(15416,a0),a0'),
    0x60351167: ('add', '15436,a0'),
    0x6035116d: ('add', '-1,d0'),
    0x603510be: ('mov', '2408,a1'),
    0x603510c3: ('mov', '(15416,a2),d0'),
    0x603510d2: ('mov', '(15420,a2),a0'),
    0x603510da: ('mov', '(15424,a2),a0'),
    0x603510ed: ('cmp', '3,d3'),
    0x60351113: ('movhu', '(a3),d0'),
    0x60351117: ('bne', '0x60351141'),
    0x60351121: ('mov', 'd0,(15416,a2)'),
    0x6035114a: ('call', '0x600313ef,[d2,a2,a3],16'),
    0x60351151: ('bra', '0x6035110c'),
    0x60368886: ('mov', '4752,a2'),
    0x60368890: ('call', '0x6035109b,[],4'),
    0x60368897: ('mov', 'a0,(13252,a3)'),
    0x603688bc: ('call', '0x60366f21,[d2,d3,a2,a3],16'),
    0x603688c8: ('call', '0x603510a5,[],4'),
    0x603688d0: ('mov', 'd0,(13252,a3)'),
    0x602a85d4: ('mov', '24058,a2'),
    0x602a85d9: ('movhu', 'd0,(a2)'),
    0x602a86b4: ('movhu', 'd0,(22,a2)'),
    0x603e62d3: ('mov', '(28,a0),d0'),
    0x603e6304: ('call', '0x60353cfb,[],0'),
    0x603e6683: ('cmp', '11,d0'),
    0x603e668a: ('add', '24058,a1'),
    0x603e668e: ('mov', '5538,a0'),
    0x603e6694: ('movhu', '(a1),d0'),
    0x603e6697: ('movbu', 'd0,(a0)'),
    0x603e669c: ('cmp', '12,d1'),
    0x603e8af3: ('mov', '(28,a0),d0'),
    0x603e8b26: ('call', '0x60353cfb,[],0'),
    0x603e91cf: ('add', '24058,a1'),
    0x603e91d3: ('add', '5538,a0'),
    0x603e91d9: ('movhu', '(a1),d0'),
    0x603e91dc: ('movbu', 'd0,(a0)'),
    0x60324362: ('add', '2119,a1'),
    0x60324366: ('add', '5538,a0'),
    0x6032436c: ('movbu', '(d1,a1),d0'),
    0x6032436f: ('movbu', 'd0,(d1,a0)'),
    0x60324373: ('cmp', '12,d2'),
}


def require_instruction(assembly, address, mnemonic, operands):
    lines = [line for line in assembly.splitlines() if line.startswith(f'{address:x}:')]
    require(len(lines) == 1 and re.search(r'\b'+re.escape(mnemonic)+r'\s+'+re.escape(operands)+r'\s*$', lines[0]),
            f'instruction mismatch at {address:#x}')


def inspect(raw, objdump):
    identity = audit(raw)
    main = parse(raw)[0].payload
    require(main[0x6053a300-BASE:0x6053a308-BASE] == bytes.fromhex('0015000080d969a2'), 'capture pool ROM descriptor mismatch')
    require(main[0x6053a870-BASE:0x6053a874-BASE] == bytes.fromhex('dbdb3d60'), 'capture pool resolver vtable mismatch')
    version = subprocess.check_output([str(objdump), '--version'], text=True).splitlines()[0]
    reports = {}
    with tempfile.TemporaryDirectory(prefix='ep7-ownership-') as temp:
        image = Path(temp)/'main.bin'
        image.write_bytes(main)
        for name, (start, stop) in WINDOWS.items():
            asm = subprocess.check_output([str(objdump), '-b', 'binary', '-m', 'mn10300', '-D', '-z',
                '--insn-width=16', f'--adjust-vma={BASE:#x}', f'--start-address={start:#x}',
                f'--stop-address={stop:#x}', str(image)], text=True)
            witnesses = [a for a in WITNESSES if start <= a < stop]
            for address in witnesses:
                require_instruction(asm, address, *WITNESSES[address])
            if name == 'current_S_to_capture':
                require(len(re.findall(r'\bmov\s+63210,d0\b', asm)) == 12, 'current S key count')
                require(len(re.findall(r'\bcall\s+0x6005e971,', asm)) == 12, 'current S getter count')
                indices = [int(v) for v in re.findall(r'\bmov\s+(\d+),d1\b', asm)]
                require(indices == list(range(1,12)) and re.search(r'\bclr\s+d1\b', asm), 'current S indices')
            reports[name] = dict(start=hex(start), stop_exclusive=hex(stop),
                sha256=sha256(main[start-BASE:stop-BASE]), witness_count=len(witnesses))
    return dict(scope='Exact E-P7 1100 static ownership and transport operands; no firmware execution',
        source_sha256=identity['source_sha256'], objdump_version=version,
        objdump_sha256=sha256(objdump.read_bytes()), windows=reports,
        instruction_witness_count=len(WITNESSES),
        job=dict(allocation_request_bytes=15488, parameter_offset=36,
            parameter_zeroed_bytes=6556, embedded_request_offset=11364, request_bytes=1884,
            request_callback='0x60355fd4', borrowed_table_pointer_offset=13252),
        saturation_transport=dict(current_record='0xf6ea', sector_count=12,
            capture_halfwords_offset=24058, compact_bytes_offset=2119,
            job_parameter_bytes_offset=5538, job_absolute_bytes_offset=5574,
            request_bytes_offset=1816),
        capture_registry=dict(base='0x6223d178', first_valid_id=1, last_valid_id=25,
            stride_operand=24, pointer_offset=12, handle_halfword_offset=16,
            valid_flag_mask=4, pool_type_selector='0x1500',
            pool_pointer_from_ROM='0xa269d980', configured_slot_count=25, backing_base='0xaf6037c0',
            slot_stride_operand=41984, resolver='0x603ddbdb',
            current_pool_RAM_state_not_established=True),
        table_lifetime=dict(resource_pointer_in_job=4752, resource_current_table_pointer=15416,
            resource_reader_count_halfword=15436, candidate_slots=3,
            selection_base_offset=2408, stride_operand=4184,
            publish_waits_for_zero_reader_count=True,
            borrowed_pointer_copied_to_request_offset=1524),
        limitations=['Static slot-stride multiply opcode still requires precise MN103 semantics.',
            'Acquire/release counter routines do not themselves establish atomic cross-core safety.',
            'Not all producer/capture pool/reuse paths or async completion edges are mapped.',
            'No spare extension storage, safe patch address or H/L pixel behavior is established.'],
        camera_accessed=False, firmware_executed=False, flash_ready=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', required=True, type=Path)
    parser.add_argument('--objdump', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.stock.read_bytes(), args.objdump.resolve()), indent=2))
