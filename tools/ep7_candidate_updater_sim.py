#!/usr/bin/env python3
"""E-P7 shared updater: native package validation, trapped commit requests.

Reuses fishcu's container implementation and the existing strict GNU engine.
Only console output, firmware-service delivery and flash-backend calls are
modeled. No device, filesystem discovery, physical write or recovery is tested.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct
import sys

from ep7_candidate_package import check_components
from ep7_candidate_startup_sim import BASE, CALLER, STACK, STACK_BYTES, SP, Machine, require
from ep7_sim_probe import brief
from oly_container import parse
from penf_boot_emulator import BootState, HOOK_RETURN
from penf_emulator import Region, execute
from penf_update_probe import synthetic_block


UPDATER = 0x60c964c1
BUFFER, RESULT = 0x20000000, 0x19020000
LOGS = {0x6002247c, 0x6002266d}
FLASH, SERVICE = 0x600c4f35, 0x60054cfb
NOTIFY = {0x601e7094, 0x601e71b6}


class Updater(Machine):
    def __init__(self, code, engine, components):
        self.engine = engine
        caller = b'\xdd' + struct.pack('<i', UPDATER-CALLER) + bytes([0xf0, 16])
        rows = [Region('native_code', BASE, code, 'rx'),
                Region('caller', CALLER, caller, 'rx'),
                Region('stack', STACK, b'\xcc'*STACK_BYTES, 'rw', True),
                Region('result', RESULT, b'\xa5'*16, 'rw', True),
                Region('return_trampoline', HOOK_RETURN, b'\xcb'*8, 'rx')]
        offset = 0
        for index, blob in enumerate(components):
            rows.append(Region(f'component_{index}', BUFFER+offset, blob, 'rw', True))
            offset += len(blob)
        self.length = offset
        self.regions = {row.name: row for row in rows}
        self.initial = dict(sp=SP, psw=0x800, d2=0x22334455, d3=0x33445566,
                            a2=0x44556677, a3=0x55667788)

    def write(self, address, data):
        for name, region in self.regions.items():
            if region.address <= address and address+len(data) <= region.address+len(region.data):
                self.mutate(name, address-region.address, data)
                return
        raise ValueError('model write outside explicit mapping '+hex(address))

    def string(self, address):
        result = bytearray()
        for offset in range(240):
            value = self.read(address+offset, 1)
            if value == b'\0':
                break
            result.extend(value)
        return result.decode('ascii', errors='replace')

    def call_updater(self, mode, *, backend_result=0, service_result=0):
        require(mode in (0, 1, 2), 'unreviewed updater mode')
        self.regs = dict(self.initial, pc=CALLER, a0=BUFFER, a1=RESULT,
                         d0=self.length, d1=mode)
        self.regions['stack'] = replace(self.regions['stack'], data=b'\xcc'*STACK_BYTES)
        rows, requests, diagnostics = [], [], []
        hooks = LOGS | NOTIFY | {FLASH, SERVICE}
        completed = 0
        for _ in range(160):
            result = execute(list(self.regions.values()), self.regs, CALLER+7,
                limit=100000000, trace_limit=32, trace_tail=True, timeout=180,
                changed_captures=True, breakpoints=hooks, engine=self.engine, record_hashes=False)
            for item in result['memory']:
                name = item['name']
                self.regions[name] = replace(self.regions[name], data=bytes.fromhex(item['hex']))
            self.regs = result['registers']
            completed += result['completed']
            rows.append(brief(result))
            if result['status'] == 'instruction_limit' and completed < 1200000000:
                continue
            if result['status'] != 'breakpoint':
                break
            pc = self.regs['pc']
            if pc in LOGS:
                diagnostics.append(dict(entry=hex(pc), text=self.string(self.regs['a0']),
                                        value=hex(self.regs['d0'])))
                modeled_result = 0
            elif pc == FLASH:
                source, size = self.regs['a1'], self.regs['d0']
                header = self.read(source, 32)
                requests.append(dict(kind='flash_backend', entry=hex(pc),
                    source=hex(source), destination=hex(self.regs['a0']), bytes=size,
                    backend_mode=self.regs['d1'], component_kind=hex(struct.unpack_from('<H', header, 20)[0]),
                    model_result=hex(backend_result)))
                modeled_result = backend_result
            elif pc == SERVICE:
                packet = self.read(self.regs['a0'], 16)
                source, size, destination = struct.unpack_from('<3I', packet)
                # The original 010e dispatcher creates this packet from its
                # nested header. Preserve both the source and task route.
                self.read(source, size)
                requests.append(dict(kind='firmware_service', entry=hex(pc),
                    source=hex(source), destination=hex(destination), bytes=size,
                    command=self.regs['d1'], task=self.regs['d0'], reply=self.regs['a1'],
                    submode=packet[12], model_result=hex(service_result)))
                modeled_result = service_result
            else:
                diagnostics.append(dict(entry=hex(pc), notification=True,
                                        d0=self.regs['d0'], d1=self.regs['d1']))
                modeled_result = 0
            # Reuse the original fishcu probe's CALL-frame-aware model return.
            # This executes a synthetic RET with the actual caller mask/frame.
            BootState.return_from_model(self, modeled_result)
        return dict(mode=mode, returned=result['status']=='returned',
            result=hex(self.regs['d0']), completed_instructions=completed,
            final=brief(result), calls=rows, write_requests=requests, diagnostics=diagnostics,
            callee_saved_restored=all(self.regs[name]==self.initial[name]
                                     for name in ('sp', 'd2', 'd3', 'a2', 'a3')))


def expect_return(row, expected):
    require(row['returned'] and row['callee_saved_restored'] and row['result']==hex(expected),
            'shared updater did not return as expected: '+json.dumps(row))


def inspect(package, stock_decoded, engine, *, controls_only=False, commit_only=False):
    code = stock_decoded.read_bytes()
    require(len(code)==26214336, 'unexpected E-P7 code size')
    for address, expected in (
        (0x60c96114, b'\xcd'+struct.pack('<h', UPDATER-0x60c96114)+bytes([0xf0,16])),
        (0x60c97189, bytes.fromhex('dff010')),
        (0x60c965c7, bytes.fromhex('fac82014')),
        (0x60c9722b, b'\xdd'+struct.pack('<i', FLASH-0x60c9722b)+bytes([0xf0,36])),
        (0x60c972e7, b'\xdd'+struct.pack('<i', SERVICE-0x60c972e7)+bytes([0xf0,44]))):
        require(code[address-BASE:address-BASE+len(expected)]==expected,
                'E-P7 updater witness changed at '+hex(address))
    # Small fixtures test only policy and rejection, never executable firmware.
    controls = []
    for name, blobs, mode, expected, count in (
        ('valid_main_sd_mode', [synthetic_block(0x100, 0x1420, 0x406a0000)], 0, 0, 1),
        ('wrong_model_rejected', [synthetic_block(0x100, 0x1220, 0x406a0000)], 2, 0x3202, 0),
        ('late_checksum_error_before_any_write', [synthetic_block(0x100, 0x1420, 0x406a0000),
            synthetic_block(0x101, 0x1420, 0x421a0000)], 0, 0x3211, 0)):
        if name.startswith('late_'):
            bad = bytearray(blobs[-1]); bad[40] ^= 1; blobs[-1] = bytes(bad)
        state = Updater(code, engine, blobs)
        row = state.call_updater(mode)
        expect_return(row, expected)
        require(len(row['write_requests'])==count, 'unexpected writes in '+name)
        controls.append(dict(name=name, **row))
    report = dict(scope=__doc__, controls=controls, hash_checks_performed=False,
        hardware_executed=False, physical_writes_executed=False, installable=False)
    if controls_only:
        return dict(report, status='controls_passed')

    raw = package.read_bytes()
    blocks = parse(raw)
    check_components(blocks)
    # The updater instructions must be original, including inside the candidate.
    require(all(blocks[0].payload[lo-BASE:hi-BASE]==code[lo-BASE:hi-BASE] for lo,hi in
                ((0x60c95a43,0x60c972f2),(0x60067102,0x60067146))), 'candidate changes the updater')
    if commit_only:
        state = Updater(code,engine,[b.header+b.payload+b.trailer for b in blocks])
        validated = dict(executed=False,source='fishcu host-decoded actual package',
                         native_validation_claim=False)
    else:
        encoded = [raw[b.offset:b.offset+len(b.payload)+64] for b in blocks]
        state = Updater(code, engine, encoded)
        print('E-P7: checking the actual five-component package natively', file=sys.stderr, flush=True)
        validated = state.call_updater(2)
        expect_return(validated, 0)
        require(not validated['write_requests'], 'validation mode attempted a write')
        require(all(state.regions[f'component_{i}'].data==b.header+b.payload+b.trailer
                    for i,b in enumerate(blocks)), 'native decoded package differs from fishcu parser')
        print('E-P7: validation returned; tracing commit requests without writing', file=sys.stderr, flush=True)
    decoded_regions = dict(state.regions)
    committed = state.call_updater(1)
    expect_return(committed, 0)
    flash = [row for row in committed['write_requests'] if row['kind']=='flash_backend']
    service = [row for row in committed['write_requests'] if row['kind']=='firmware_service']
    require(len(flash)==4 and len(service)==1, 'five-component routing differs')
    for row in flash:
        block = next(b for b in blocks if hex(b.kind)==row['component_kind'])
        require(row['source']==hex(BUFFER+block.offset) and row['bytes']==len(block.payload)+64 and
                row['destination']==hex(block.address+0x40000000 if block.kind==0x100 else block.address) and
                row['backend_mode']==1, 'component flash route differs')
    auxiliary = blocks[3]
    auxiliary_plain = auxiliary.header+auxiliary.payload+auxiliary.trailer
    nested = struct.unpack_from('<I',auxiliary.payload)[0]
    destination,size = struct.unpack_from('<II',auxiliary_plain,nested+8)
    require(nested+32+size<=len(auxiliary_plain) and service[0]['source']==hex(BUFFER+auxiliary.offset+nested+32) and
            service[0]['destination']==hex(destination) and service[0]['bytes']==size and
            service[0]['command']==128 and service[0]['task']==9 and service[0]['reply']==36 and
            service[0]['submode']==2, 'nested auxiliary component service route differs')
    state.regions = dict(decoded_regions)
    failed = state.call_updater(1, backend_result=0x3102)
    expect_return(failed, 0x3102)
    failed_flash = [row for row in failed['write_requests'] if row['kind']=='flash_backend']
    require(len(failed_flash)==1, 'backend failure did not stop later flash requests')
    require(all(state.regions[f'component_{i}'].data==b.header+b.payload+b.trailer
                for i,b in enumerate(blocks)), 'commit modified the validated source buffers')
    return dict(report, status='passed', package_bytes=len(raw), component_count=len(blocks),
        native_validation=validated, trapped_commit=committed, backend_failure=failed,
        commit_only=commit_only,full_native_decode_and_checksum=not commit_only,
        native_decoded_bytes_equal_to_fishcu=None if commit_only else True,
        original_component_versions_preserved=True, updater_entry=hex(UPDATER),
        model_boundaries=[hex(x) for x in sorted(LOGS|NOTIFY|{FLASH,SERVICE})],
        limits=['Shared updater is entered by a synthetic CALL with explicit resident code/buffers; physical SD/USB entry is not tested.',
                'Console calls and notifications return modeled zero. Backend and service requests are recorded then return the specified model result.',
                'No erase, program, readback, firmware-service receiver, device boot, recovery or H/L runtime behavior is established here.',
                ('Commit-only run: real buffers are host-decoded by fishcu. No native validation is claimed for this invocation.' if commit_only else
                 'Mode 2 validates and decodes the full real package; mode 1 uses exactly those validated buffers. Small mode 0 fixtures cover policy only.'),
                'Shared updater acceptance does not establish all checks in the earlier SD/USB clients or installable status.'])


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--stock-decoded', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--controls-only', action='store_true')
    parser.add_argument('--commit-only', action='store_true',
                        help='Recheck commit routing on host-decoded real input; does not claim native validation')
    args = parser.parse_args()
    print(json.dumps(inspect(args.package, args.stock_decoded, args.engine,
                             controls_only=args.controls_only,commit_only=args.commit_only), indent=2))
