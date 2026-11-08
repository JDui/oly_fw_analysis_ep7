#!/usr/bin/env python3
"""Replay the 1100 Rec HDR seams with the strict MN10300 runner."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
from struct import pack, unpack
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from ep7_candidate_startup_sim import CALLER, SP, STACK, require
from ep7_candidate_ui_input_sim import UiMachine
from ep7_rec_hdr_patch import EVENT_METHODS, REC_OPTIONS
from penf_boot_emulator import BootState, HOOK_RETURN
from penf_emulator import Region


EVENT = 0x19310000
COMPOSER = 0x19311000
SHOOTER = 0x19313000
CONTROLLER = 0x19314000
KEY_PACKET = 0x19315000
PROPERTIES = 0x19316000
DESCRIPTORS = 0x19318000
PROPERTY_MAP = 0x604D6C14
PROPERTY_CACHE = 0xA2699CB4
BRACKET_INDEX_CACHE = 0xA269BB20
BRACKET_LIMIT = 0x61FACCE8
SEQUENCE = 0x61FACD64
TRIGGER = 0x61FACD84
READ_SETTING = 0x602AFA81
NATIVE_VALIDATE = 0x62248528
KEY_PRESS = 0x01000006
KEY_RELEASE = 0x01000007
HDR_ACTION = 0x60CE3B96
CAPTURE_ENTRY, CAPTURE_STARTED, CAPTURE_REPLY = 0x609018FC, 0x60953B92, 0x60953C1A


class Replay(UiMachine):
    def __init__(self, image, engine):
        super().__init__(image, engine)
        self.regions['stack'] = replace(self.regions['stack'], data=bytes(16384))
        self.regions['stack_after'] = replace(self.regions['stack_after'], address=STACK+16384)
        self.shots = []
        self.drive = 0
        self.interval = 0
        self.state = 1
        self.typed_keys = {}
        self.shells = {
            READ_SETTING: self.setting,
            0x60CFBC8A: lambda: self.ret(0),   # UI logger.
            0x60CCBFF5: lambda: self.ret(0),   # Current app state.
            0x60CD20E9: lambda: self.ret(1),   # Still-view admission.
            0x60CCAC3E: lambda: self.ret(0),   # Key-state notification.
            0x6005D924: self.resolve_typed_key,
            0x6005E65A: lambda: self.ret(0),   # Typed write protection service.
            0x60768516: self.lock_handle,
            0x607684F9: lambda: self.ret(0),   # SDK service lock.
            0x60768509: lambda: self.ret(0),
            0x60767EE5: lambda: self.ret(0),   # Debug logger.
            0x60A4EC2B: self.allocate_event,
            0x607AABEA: self.virtual_no_reply_pointer,
            0x607AABFC: self.enqueue,
            0x6076AA69: lambda: self.ret(0),   # Camera status flag services.
            0x6076B2A3: lambda: self.ret(0),
            0x6076998B: lambda: self.ret(0),
            0x607697E9: lambda: self.ret(0),
            0x60954C42: lambda: self.ret(0),   # Capture debug logger.
            0x6076AAD2: lambda: self.ret(self.state),
            0x6076A167: lambda: self.ret(0),   # Sequence observer service.
            0x609557A2: lambda: self.ret(0),
        }
        self.add('return', HOOK_RETURN, bytes(8), 'rx')
        self.add('event', EVENT, bytes(32))
        self.add('composer', COMPOSER, bytes(2836))
        self.add('shooter', SHOOTER, bytes(800))
        self.add('controller', CONTROLLER, bytes(2400))
        self.add('key_packet', KEY_PACKET, bytes(24))
        self.add('bracket_limit', BRACKET_LIMIT, bytes(2))
        self.add('native_sequence', SEQUENCE, bytes(0x24))
        self.add('inhibit', 0x62257B04, bytes(1))
        self.add('property_cache_init', 0xA269BF68, bytes(1))
        self.add('property_cache', PROPERTY_CACHE, bytes(1769 * 4))
        self.add('bracket_index_cache', BRACKET_INDEX_CACHE, bytes(4))
        self.add('property_values', PROPERTIES, bytes(1769 * 4))
        self.add('property_descriptors', DESCRIPTORS, bytes(1769 * 8))
        self.add('ae_bracket_kind_ptr', 0x622A0A8C, bytes(4))
        self.add('ae_hdr_type_ptr', 0x622A0B30, bytes(4))
        self.add('validator_buckets', NATIVE_VALIDATE, bytes(512 + 16))
        for index, sid in enumerate((47, 48)):
            node = NATIVE_VALIDATE + 512 + 8 * index
            self.word_set(NATIVE_VALIDATE + 4 * sid, node)
            self.word_set(node, (0x604CDA08, 0x604CDA30)[index])
        self.word_set(COMPOSER + 104, EVENT)
        self.word_set(COMPOSER + 2832, SHOOTER)
        self.word_set(SHOOTER + 728, 2)  # Native release permission.
        for sid, value in ((5, 0), (24, 3), (600, 0), (1487, 1), (1494, 0)):
            self.set_property(sid, value)
        self.word_set(0x622A0A8C, PROPERTIES + 4 * 1494)
        self.word_set(0x622A0B30, PROPERTIES + 4 * 600)

    def add(self, name, address, data, permissions='rw'):
        self.regions[name] = Region(name, address, data, permissions, 'w' in permissions)

    def word_set(self, address, value):
        self.write(address, pack('<I', value))

    def hdr_settings(self):
        return tuple(self.word(PROPERTIES + 4 * sid) for sid in (600, 1494, 5))

    def rec_key(self, key):
        self.word_set(KEY_PACKET, key)
        self.replay(HDR_ACTION, mask=0xA0, frame=44, registers=dict(d0=14, a1=KEY_PACKET))
        require(self.regs['sp'] == SP, 'Rec action changed the UI stack')

    def set_property(self, sid, value):
        key, index = unpack('<HH', self.read(PROPERTY_MAP + 4 * sid, 4))
        require(index == 0, f'unmodeled property array {sid}')
        self.typed_keys[key] = sid
        address = PROPERTIES + 4 * sid
        self.word_set(address, value)
        self.word_set(PROPERTY_CACHE + 4 * sid, address)
        self.word_set(DESCRIPTORS + 8 * sid + 4, address)

    def ret(self, value):
        BootState.return_from_model(self, value)

    def setting(self):
        sid = self.regs['d0']
        require(sid in (478, 3008, 3281, 15206), f'unexpected setting {sid}')
        self.ret({478: self.interval, 3008: 0, 3281: self.drive, 15206: 0}[sid])

    def resolve_typed_key(self):
        sid = self.typed_keys.get(self.regs['d0'])
        self.regs['a0'] = DESCRIPTORS + 8 * sid if sid is not None else 0
        self.ret(0)

    def lock_handle(self):
        self.regs['a0'] = 0
        self.ret(0)

    def allocate_event(self):
        require(self.regs['d0'] == 32, 'native one-shot allocation size changed')
        self.regs['a0'] = EVENT
        self.ret(0)

    def virtual_no_reply_pointer(self):
        self.regs.update(a0=0, pc=self.regs['mdr'])

    def enqueue(self):
        require(self.regs['a1'] == EVENT, 'native constructor did not return its event')
        self.shots.append(self.read(EVENT, 32))
        self.ret(0)

    def replay(self, target, *, mask=0, frame=0, stop=None, registers=None, mid=False):
        if mid:
            entry = target
        else:
            self.add('caller', CALLER, b'\xdd' + pack('<i', target-CALLER) + bytes([mask, frame]), 'rx')
            entry = CALLER
        self.regs = dict(self.initial, pc=entry)
        self.regs.update(registers or {})
        stops = stop or (CALLER + 7,)
        for _ in range(80):
            result = self.advance(stops[0], set(self.shells).union(stops))
            pc = self.regs['pc']
            if pc in stops:
                require(result.get('hash_checks_performed') is False, 'unexpected SHA calculation')
                return pc
            self.shells[pc]()
        raise RuntimeError('probe exceeded its service-boundary limit')

    def native_value(self, target, sid, *, index=0, frame=8, mask=0x80):
        self.replay(target, mask=mask, frame=frame, registers=dict(d0=sid, d1=index))
        require(self.regs['sp'] == SP, f'{target:#x} changed the caller stack')
        return self.regs['d0']


def inspect(directory, engine):
    report = json.loads((directory / 'report.json').read_text(encoding='utf-8'))
    image = (directory / report['image']).read_bytes()
    m = Replay(image, engine)
    require(m.native_value(0x602B9F70, 48) == len(REC_OPTIONS) + 1, 'Rec picker count differs')
    require(m.native_value(0x602B9FDB, 48, index=11) == 473 and
            m.native_value(0x602B9FDB, 48, index=12) == 3200, 'Rec HDR option is missing')
    require(m.native_value(0x602B9F70, 47) == len(REC_OPTIONS), 'AEL picker was widened')
    require(m.native_value(0x60CC885C, 473, mask=0xC0) == 14, 'native HDR action differs')

    for key in (KEY_PRESS, 0x01000008, KEY_RELEASE):
        m.rec_key(key)
    require(len(m.shots) == 1, 'Rec press did not produce exactly one request')
    event = m.shots[0]
    vtable, number = unpack('<IH', event[:6])
    require(vtable != 0x60A7DD24 and number == 1007 and
            m.read(vtable, 72) == pack('<18I', *EVENT_METHODS),
            'marked request changed the stock event ABI')

    drive_results = []
    replay_capture = dict(frame=4, stop=(CAPTURE_STARTED, CAPTURE_REPLY), registers=dict(a0=COMPOSER))
    for drive, first_curtain, electronic, shutter in ((0, 0, 0, 0), (12, 1, 0, 1), (24, 0, 1, 2)):
        m.drive = drive
        m.set_property(24, 6 if electronic else 3)
        m.set_property(166, first_curtain)
        m.set_property(764, electronic)
        reached = m.replay(CAPTURE_ENTRY, **replay_capture)
        require(reached == CAPTURE_STARTED and m.hdr_settings() == (1, 4, 4) and m.word(TRIGGER) & 1,
                f'marked drive {drive} stopped at {reached:#x} with '
                f'capture settings={m.hdr_settings()} and trigger={m.word(TRIGGER):#x}')
        require((m.word(SEQUENCE) & 0x10208) == 0x208 | (electronic << 16),
                'native sequence did not combine HDR with the selected shutter')

        if electronic:
            m.replay(0x6095057D, mask=0xE0, frame=24, registers=dict(a0=SHOOTER))
            require(m.read(BRACKET_LIMIT, 2) == pack('<H', 4), 'native bracket limit is not four')
            require(m.native_value(0x6042888C, 0) == 1, 'native exposure logic did not select HDR')
            require(m.replay(CAPTURE_ENTRY, **replay_capture) == CAPTURE_REPLY and
                    m.hdr_settings() == (1, 4, 4), 'second Rec request replaced the active sequence')

        m.word_set(SP+4, CONTROLLER)
        m.replay(0x602A47A7, mid=True, stop=(0x602A47FF,), registers=dict(a0=CONTROLLER))
        require(m.read(CONTROLLER+1998, 1) == bytes([shutter]),
                'controller selected a different shutter')

        clear = 0x609452BB if drive != 24 else 0x6093434E
        m.replay(clear, mid=True, stop=(clear+7,), registers=dict(a0=SHOOTER, d0=1 if drive != 24 else 15))
        require(m.hdr_settings() == (0, 0, 0) and m.word(TRIGGER) == 0 and
                (m.word(SEQUENCE) & 0x10208) == (electronic << 16) and m.drive == drive,
                'HDR state leaked after cleanup')
        if electronic:
            m.replay(0x6095057D, mask=0xE0, frame=24, registers=dict(a0=SHOOTER))
            require(m.read(BRACKET_LIMIT, 2) == pack('<H', 1), 'ordinary capture is still bracketed')
            require(m.native_value(0x6042888C, 0) == 0, 'ordinary exposure still selects HDR')
        drive_results.append(dict(drive=drive, controller_shutter=shutter))

    m.state = 5  # An ordinary physical half-press already owns READY_TRIG2.
    reached = m.replay(CAPTURE_ENTRY, **replay_capture)
    require(reached == CAPTURE_REPLY and m.hdr_settings() == (0, 0, 0) and m.word(TRIGGER) == 0,
            'Rec took over a half-pressed physical shutter')

    m.state = 1
    m.word_set(0x8050, 1)
    require(m.replay(CAPTURE_ENTRY, **replay_capture) == CAPTURE_REPLY and
            m.hdr_settings() == (0, 0, 0) and m.word(TRIGGER) == 0,
            'Rec armed a shot outside the synchronous settings core')
    m.word_set(0x8050, 0)

    m.interval = 1
    m.rec_key(KEY_PRESS)
    require(len(m.shots) == 1, 'Rec queued a request during interval shooting')
    m.word_set(EVENT, 0x60A7DD24)  # Original one-shot event class.
    sequence = m.word(SEQUENCE)
    require(m.replay(CAPTURE_ENTRY, **replay_capture) == CAPTURE_STARTED and
            m.hdr_settings() == (0, 0, 0) and m.word(SEQUENCE) == sequence,
            'stock interval request acquired the HDR settings')
    m.replay(0x609452BB, mid=True, stop=(0x609452C2,), registers=dict(a0=SHOOTER, d0=1))
    require(m.word(TRIGGER) == 0 and m.word(SEQUENCE) == sequence,
            'stock trigger clear acquired the HDR settings')
    return dict(status='passed', rec_menu_option=True, single_request=True,
                drive_results=drive_results, native_electronic_bracket_limit=4, native_hdr_ae=True,
                trigger_clear_restore=True, ordinary_electronic_bracket_limit=1,
                overlapping_requests_rejected=True, non_owner_core_rejected=True,
                stock_one_shot_unchanged=True,
                hash_checks_performed=False, hardware_executed=False,
                boundary='Native instruction replay covers release admission, sequence, bracket limit, '
                         'HDR AE eligibility and shutter selection. UI services, RTOS, heap, '
                         'typed-property resolution and transport are modeled.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = json.dumps(inspect(args.candidate, args.engine), indent=2) + '\n'
    args.out.write_text(result, encoding='utf-8')
    print(result, end='')
