#!/usr/bin/env python3
"""Read-only E-P7 1100 job allocator class evidence; not allocation permission."""
import argparse
import json
import struct
import subprocess
import tempfile
from pathlib import Path
from ep7_stock_audit import audit, BASE, require
from ep7_gui_bridge import require_instruction
from oly_container import parse, sha256

WINDOWS = {
    'size_dispatch': (0x60022700, 0x60022732),
    'free_dispatch': (0x60022732, 0x60022782),
    'pool_stride_load': (0x600228b6, 0x600228d6),
    'pool_initial_index': (0x600229d4, 0x600229e9),
    'pool_recycled_index': (0x60022a16, 0x60022a2f),
    'pool_return': (0x60022a49, 0x60022a61),
}
WITNESSES = {
    0x60022700: ('cmp', '128,d0'),
    0x60022704: ('bhi', '0x60022709'),
    0x60022709: ('cmp', '2048,d0'),
    0x6002270d: ('bhi', '0x60022713'),
    0x60022713: ('cmp', '16384,d0'),
    0x60022717: ('bhi', '0x60022722'),
    0x60022719: ('mov', '2,d0'),
    0x6002271b: ('call', '0x600228b6,[d2,d3,a2,a3],36'),
    0x6002272d: ('mov', '0,a0'),
    0x6002275b: ('cmp', '1639804224,d0'),
    0x60022763: ('cmp', '1641909568,d0'),
    0x6002276b: ('mov', '2,d0'),
    0x6002276d: ('call', '0x60022b23,[d2,d3,a2,a3],40'),
    0x600228c7: ('asl2', 'd1'),
    0x600228c8: ('mov', '1610772020,a1'),
    0x600228d0: ('mov', '(d1,a1),d1'),
    0x600228d4: ('mov', 'd1,(12,sp)'),
    0x600229d9: ('mov', '(12,sp),d1'),
    0x600229db: ('udf00', 'd1,d0'),
    0x600229dd: ('add', 'a3,d0'),
    0x60022a26: ('mov', '(12,sp),d0'),
    0x60022a29: ('udf00', 'd0,d3'),
    0x60022a2b: ('add', 'a3,d3'),
    0x60022a49: ('mov', '(4,sp),a2'),
    0x60022a56: ('call', '0x6006a96b,[d2],8'),
    0x60022a5d: ('mov', 'a2,a0'),
}


def proposed_size_class(size):
    """Host model of positive-size branch thresholds, not a real allocator."""
    if type(size) is not int or size <= 0:
        raise ValueError('positive integer size required')
    return 0 if size <= 128 else 1 if size <= 2048 else 2 if size <= 16384 else None


def inspect(raw, objdump):
    identity = audit(raw)  # Identity gate precedes any tool invocation.
    main = parse(raw)[0].payload
    offset = 0x60026e34 - BASE
    strides = struct.unpack_from('<3I', main, offset)
    require(strides == (192, 2112, 16448), 'pool stride table mismatch')
    windows = {}
    version = subprocess.check_output([str(objdump), '--version'], text=True).splitlines()[0]
    with tempfile.TemporaryDirectory(prefix='ep7-pool-') as tmp:
        image = Path(tmp) / 'main.bin'
        image.write_bytes(main)
        for name, (start, end) in WINDOWS.items():
            assembly = subprocess.check_output([
                str(objdump), '-b', 'binary', '-m', 'mn10300', '-D', '-z',
                '--insn-width=16', f'--adjust-vma={BASE:#x}',
                f'--start-address={start:#x}', f'--stop-address={end:#x}', str(image)
            ], text=True)
            witnesses = [address for address in WITNESSES if start <= address < end]
            for address in witnesses:
                require_instruction(assembly, address, *WITNESSES[address])
            windows[name] = dict(start=hex(start), end_exclusive=hex(end),
                sha256=sha256(main[start-BASE:end-BASE]), witness_count=len(witnesses))
    return dict(
        source_sha256=identity['source_sha256'],
        scope='Static allocator branch/stride evidence, not trailer ownership or allocation provenance',
        requested_sizes={'stock': 15488, 'hypothetical_plus_24': 15512},
        branch_class={'stock': proposed_size_class(15488), 'hypothetical_plus_24': proposed_size_class(15512)},
        pool_stride_table=dict(address='0x60026e34', values=list(strides), sha256=sha256(main[offset:offset+12])),
        windows=windows, instruction_witness_count=len(WITNESSES),
        objdump_version=version, objdump_sha256=sha256(objdump.read_bytes()),
        limitations=[
            'Same class does not authorize writing any stock tail or establish expanded initialization.',
            'Pool occupancy, concurrent users, guard regions and all allocator/free error paths are not qualified.',
            'udf00 is the disassembler rendering; exact ISA multiply semantics are not independently established here.',
            'No constructor admission, whole-job copy exclusion or safe H/L hook is established.'
        ], camera_accessed=False, firmware_executed=False, flash_ready=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.stock.read_bytes(), args.objdump.resolve()), indent=2))
