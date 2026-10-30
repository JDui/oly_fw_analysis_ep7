#!/usr/bin/env python3
"""Find raw alias reference candidates, NOT instruction or lifetime proofs."""
import argparse
import json
from pathlib import Path
import struct

from penf_disasm import refs

BASE = 0x60020020
TARGETS = dict(global_node=0x6223dd54, async_descriptor=0x6223df64,
               async_callback=0x6029e8f1, wrapper_queue=0x6223e2f0)


def inspect(data):
    if (len(data) != 26214336 or data[0xb6:0xb8] != b'\xfc\xdc'
            or struct.unpack_from('<I', data, 0xb8)[0] - 0xd9 != BASE):
        raise ValueError('main size/mapping witness mismatch')
    rows = []
    for name, address in TARGETS.items():
        pointers, calls = refs(data, address, base=BASE)
        rows.append(dict(name=name, address=hex(address),
                         literal_candidates=[hex(p) for p in pointers],
                         relative_call_candidates=[hex(p) for p in calls]))
    return dict(scope=__doc__.strip(), main_bytes=len(data), runtime_base=hex(BASE),
                references=rows, hash_checks_performed=False, firmware_execution=False,
                historical_exact_byte_identity_proven=False, lifecycle_closure=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', required=True, type=Path,
                        help='private main.decoded.bin from ep7_prepare_input.py')
    args = parser.parse_args()
    print(json.dumps(inspect(args.main.read_bytes()), indent=2))
