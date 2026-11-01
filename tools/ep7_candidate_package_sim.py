#!/usr/bin/env python3
"""Execute E-P7 local container checks on the actual offline research package.

Only the decoder and local integrity checker run. No updater write dispatcher,
file discovery, version admission, flash controller or recovery code is invoked.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_package import check_components
from ep7_candidate_startup_sim import BASE, CALLER, STACK, STACK_BYTES, SP, require
from ep7_sim_probe import brief
from oly_container import parse
from penf_emulator import Region, execute


BUFFER, CONTROL = 0x20000000, 0x19020000
CHECKER, DECODER, LOGGER = 0x60c95a43, 0x60c95b0c, 0x6002266d


def invoke(code, engine, buffer, target, mask, frame, registers, *, writable=False,
           limit=1000, breakpoints=(), timeout=45):
    call = b'\xdd' + struct.pack('<i', target-CALLER) + bytes([mask, frame])
    control = bytearray(b'\xa5'*20)
    struct.pack_into('<I', control, 4, BUFFER)
    struct.pack_into('<I', control, 16, 1)  # Explicit ordinary packaged-input mode.
    regions = [Region('native_code', BASE, code, 'rx'),
        Region('caller', CALLER, call, 'rx'),
        Region('stack', STACK, b'\xcc'*STACK_BYTES, 'rw', True),
        Region('control', CONTROL, bytes(control)),
        Region('component', BUFFER, buffer, 'rw' if writable else 'r', writable)]
    initial = dict(pc=CALLER, sp=SP, d2=0x22334455, d3=0x33445566,
        a2=0x44556677, a3=0x55667788, psw=0x800, **registers)
    result = execute(regions, initial, CALLER+7, limit=limit, trace_limit=256,
        trace_tail=True, timeout=timeout, engine=engine, record_hashes=False,
        breakpoints=breakpoints)
    return result, initial


def returned(result, initial, expected):
    require(result['status'] == 'returned' and result['fault'] is None and
            result['registers']['pc'] == CALLER+7 and result['registers']['d0'] == expected,
            'native updater check did not return as expected: '+str(brief(result)))
    require(all(result['registers'][key] == initial[key] for key in ('sp','d2','d3','a2','a3')),
            'native updater ABI did not preserve the caller frame')


def inspect(path, engine):
    raw = path.read_bytes()
    blocks = parse(raw)
    check_components(blocks)
    code = blocks[0].payload
    # CALL tuples in the original wrapper, and key local-checker operations.
    require(code[0x60c971a5-BASE:0x60c971a5-BASE+5] ==
            b'\xcd'+struct.pack('<h', DECODER-0x60c971a5)+bytes([0xf0,28]) and
            code[0x60c971b9-BASE:0x60c971b9-BASE+5] ==
            b'\xcd'+struct.pack('<h', CHECKER-0x60c971b9)+bytes([0xf0,20]) and
            code[0x60c95a7c-BASE:0x60c95a83-BASE] == bytes.fromhex('f80f0c80202b40') and
            code[0x600fa454-BASE:0x600fa465-BASE] == bytes.fromhex('08f8c402db7450e68501f104d988de8004'),
            'native decoder/checker ABI or checksum-loop witnesses changed')
    # The smallest real component exercises the entire native permutation and
    # inversion loop without repeating unchanged large-component work.
    small = blocks[3]
    encoded = raw[small.offset:small.offset+len(small.payload)+64]
    decoded, initial = invoke(code, engine, encoded, DECODER, 0xf0, 28,
        dict(a0=BUFFER, d0=len(encoded)), writable=True, limit=3000000)
    returned(decoded, initial, 0)
    captured = bytes.fromhex(next(row['hex'] for row in decoded['memory'] if row['name']=='component'))
    require(captured == small.header+small.payload+small.trailer,
            'native decoder differs from the inherited fishcu container implementation')
    rows = [dict(name='native_decode_actual_component_010e', result=brief(decoded),
        component_bytes=len(encoded), complete_component=True,
        decoded_payload_equal_to_host=True, header_and_trailer_unchanged=True)]
    # Validate the complete modified main component, not a shortened fixture.
    main = blocks[0]
    plain = main.header+main.payload+main.trailer
    checked, initial = invoke(code, engine, plain, CHECKER, 0xf0, 20,
        dict(a0=CONTROL, d0=0), limit=6*(len(plain)//4)+500, breakpoints=[LOGGER], timeout=180)
    returned(checked, initial, 0)
    require(checked['registers']['a0'] == BUFFER+len(plain),
            'native checksum did not consume the complete main component')
    rows.append(dict(name='native_check_complete_modified_main', result=brief(checked),
        component_bytes=len(plain), returned_d0=0, complete_component=True,
        checksum_read_end=hex(checked['registers']['a0'])))
    # Header/trailer disagreement must fail before the checksum path.
    bad_metadata = bytearray(plain)
    bad_metadata[-32] ^= 1
    rejected, initial = invoke(code, engine, bytes(bad_metadata), CHECKER, 0xf0, 20,
        dict(a0=CONTROL, d0=0), limit=500, breakpoints=[LOGGER])
    returned(rejected, initial, 0x3202)
    rows.append(dict(name='native_reject_header_trailer_mismatch', result=brief(rejected),
        returned_d0='0x3202', in_memory_mutation_only=True))
    # The error branch is common to every ordinary component. Use the small
    # actual component for this negative control rather than replaying another
    # 26MB checksum. Stop before unrelated console/kernel dependencies.
    bad_sum = bytearray(captured)
    bad_sum[32] ^= 1
    failed, initial = invoke(code, engine, bytes(bad_sum), CHECKER, 0xf0, 20,
        dict(a0=CONTROL, d0=0), limit=6*(len(bad_sum)//4)+500, breakpoints=[LOGGER])
    require(failed['status'] == 'breakpoint' and failed['fault'] is None and
            failed['registers']['pc'] == LOGGER and failed['registers']['mdr'] == 0x60c95ad4 and
            failed['registers']['d0'] != 0 and
            any(row['pc'] == 0x60c95ac3 for row in failed['trace']),
            'corrupt component did not take the actual checksum-error logging branch: '+str(brief(failed)))
    rows.append(dict(name='native_corrupt_010e_checksum_error_branch', result=brief(failed),
        mutated_payload_offset=0, checksum_result=hex(failed['registers']['d0']),
        stopped_before_error_logger=True, error_return_suffix_executed=False,
        in_memory_mutation_only=True))
    return dict(scope=__doc__, status='passed', package=path.name, package_bytes=len(raw),
        engine=str(engine), cases=rows, completed_instructions=sum(row['result']['completed'] for row in rows),
        native_decoder_matches_host=True, native_local_main_integrity_check_passed=True,
        full_updater_acceptance_proven=False, flash_write_path_executed=False,
        native_API_success_stubs=False, hash_checks_performed=False,
        firmware_files_modified=False, hardware_executed=False, installable=False,
        limits=[
            'Native code and buffers are explicitly resident in the strict instruction model; no camera boot is claimed.',
            'Control+4 holds the buffer and Control+16 is explicit mode1; discovery, allocation and version/model admission before this local checker are not executed.',
            'The actual 010e component is decoded completely. The complete modified main is supplied in decoded form and checked natively; its full decoder loop is not replayed.',
            'Corrupt010e reaches the actual logging CALL. The logger and following0x3211 return suffix are not stubbed or claimed to have executed.',
            'Only local integrity semantics are established. Complete updater policy, write dispatch, recovery, S3/S4 and hardware qualification remain open.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.package, args.engine), indent=2))
