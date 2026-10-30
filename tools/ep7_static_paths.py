#!/usr/bin/env python3
"""Static E-P7 profile/cursor evidence, not executable firmware or a patch.

Requires a trusted, locally built GNU MN103 objdump supplied explicitly.
Temporary decoded input is deleted on exit; stdout contains no disassembly.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

from ep7_stock_audit import BASE, PROFILE_CASES, PUBLIC_MODES, SAT_IDS, audit, require
from oly_container import parse, sha256


def property_reads(assembly):
    return [int(v) for v in re.findall(r'\bmov\s+(\d+),a0\b', assembly)]


def direct_calls(assembly):
    return [int(v, 16) for v in re.findall(r'\bcall\s+0x([0-9a-f]+),', assembly)]


def inspect(raw, objdump):
    identity = audit(raw)  # Fail closed before executing the external tool.
    main = parse(raw)[0].payload
    version = subprocess.check_output([str(objdump), '--version'], text=True).splitlines()[0]
    rows = []
    with tempfile.TemporaryDirectory(prefix='ep7-static-') as tmp:
        path = Path(tmp)/'main.bin'
        path.write_bytes(main)

        def disassemble(start, stop):
            return subprocess.check_output([str(objdump), '-b', 'binary', '-m', 'mn10300',
                '-D', '-z', '--insn-width=16', f'--adjust-vma={BASE:#x}',
                f'--start-address={start:#x}', f'--stop-address={stop:#x}', str(path)], text=True)

        for i, start in enumerate(PROFILE_CASES):
            stop = (PROFILE_CASES+(0x602b850d,))[i+1]
            assembly = disassemble(start, stop)
            keys = property_reads(assembly)
            expected = [[912,909,963,964,965,1667], [913,910,966,967,968,1668],
                        [914,911,969,970,971,1669], [1653,1651,1672,1673,1674,1670]][i]
            expected += list(range(SAT_IDS[i], SAT_IDS[i]+12))
            require(keys == expected, f'COLOR{i+1}: native property read sequence differs')
            calls = direct_calls(assembly)
            require(len(calls) == (18 if i == 3 else 17) and set(calls) == {0x602b2237},
                    f'COLOR{i+1}: getter call sequence differs')
            if i < 3:
                require(re.search(r'\bjmp\s+0x602b8503\s*$', assembly, re.M) is not None,
                        f'COLOR{i+1}: common final getter branch differs')
            rows.append(dict(profile=i+1, public_mode=PUBLIC_MODES[i], start=hex(start),
                             stop_exclusive=hex(stop), native_property_read_order=keys,
                             direct_getter_calls=len(calls), getter='0x602b2237',
                             sha256=sha256(main[start-BASE:stop-BASE])))
        cursor = disassemble(0x60de83b7, 0x60de857f)
        # These assertions witness operands at reviewed instruction boundaries;
        # they do not establish physical events, callers or camera reachability.
        witnesses = {
            '0x60de83d8': ('cmp', '1091,d0'), '0x60de83de': ('cmp', '1096,d0'),
            '0x60de83e4': ('cmp', '1097,d0'), '0x60de83ea': ('cmp', '1686,d0'),
            '0x60de8485': ('mov', '1098,d0'), '0x60de84c7': ('mov', '1099,d0'),
            '0x60de8505': ('mov', '1100,d0'), '0x60de853d': ('mov', '1687,d0'),
            '0x60de8427': ('cmp', '255,d0'), '0x60de8423': ('cmp', '12,d0'),
            '0x60de856e': ('movhu', 'd0,(90,a0)'),
        }
        for address, (mnemonic, operands) in witnesses.items():
            line = next((line for line in cursor.splitlines() if line.startswith(address[2:]+':')), '')
            require(re.search(r'\b'+mnemonic+r'\s+'+re.escape(operands)+r'\s*$', line) is not None,
                    f'cursor operand mismatch at {address}')
    return dict(scope='Static disassembly assertions only; no firmware execution or physical input mapping',
        source_sha256=identity['source_sha256'], objdump_version=version,
        objdump_sha256=sha256(objdump.read_bytes()), profiles=rows,
        cursor=dict(window_start='0x60de83b7', window_stop_exclusive='0x60de857f',
                    property_predicates=[1091,1096,1097,1686],
                    related_property_reads=[1098,1099,1100,1687],
                    all_sentinel_compared=255, upper_cursor_bound_compared=12,
                    child_index_write_offset=90, operand_witness_addresses=list(witnesses)),
        limitations=['Profile cases 1-3 share the final getter in case 4.',
                     'Related cursor properties are static leads, not fully traced storage semantics.',
                     'Physical key events, persistent H/L storage and capture/job ownership remain unproven.'],
        camera_accessed=False, firmware_executed=False, flash_ready=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', required=True, type=Path)
    parser.add_argument('--objdump', required=True, type=Path, help='trusted GNU MN103 objdump executable')
    args = parser.parse_args()
    print(json.dumps(inspect(args.stock.read_bytes(), args.objdump.resolve()), indent=2))


if __name__ == '__main__':
    main()
