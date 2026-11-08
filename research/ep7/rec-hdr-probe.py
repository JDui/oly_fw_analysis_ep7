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
RELEASE_SERVICE = 0x1931C000
RELEASE_METHODS = 0x1931C100
RELEASE_CALL = 0x1931D000
COMPOSER_REPLY = 0x1931E000
MEDIA_SERVICE, MEDIA_METHODS, MEDIA_READY = 0x1931F000, 0x1931F100, 0x1931F200
RELEASE_ENABLED = 0x6233B844
ACTIVE_RELEASE = 0x61FACCE0
STILL_ENABLED = 0x61FACD00
CAPTURE_STATE = 0x61FA748C
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
WRAPPED_KEY = 0x0100002E
HDR_ACTION_CALL, HDR_ACTION_RETURN = 0x60CE03BB, 0x60CE03C0
STOCK_HDR_RESUME = 0x60CE3B9B
CAPTURE_ENTRY, CAPTURE_REPLY = 0x60904471, 0x60953C1A
STANDBY_ADVANCE, STANDBY_REFUSED = 0x60962780, 0x60962752
NO_HDR = (0, 0, 0, 0)
HDR1 = (1, 4, 4, 1)


class Replay(UiMachine):
    def __init__(self, image, engine):
        super().__init__(image, engine)
        self.regions['stack'] = replace(self.regions['stack'], data=bytes(16384))
        self.regions['stack_after'] = replace(self.regions['stack_after'], address=STACK+16384)
        self.shots = []
        self.release_commands = []
        self.release_enabled_on_submit = []
        self.subapp_active = False
        self.interval = 0
        self.typed_keys = {}
        self.shells = {
            READ_SETTING: self.setting,
            RELEASE_CALL: self.control_release,
            0x60CFBC8A: lambda: self.ret(0),   # UI logger.
            0x60CFBD9C: lambda: self.ret(0),
            0x60CFD297: self.resolve_release_service,
            0x60CE0AA2: self.current_subapp,
            0x60CCBFF5: lambda: self.ret(0),   # Current app state.
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
            0x6076998B: lambda: self.ret(0),
            0x607697E9: lambda: self.ret(0),
            0x60954C42: lambda: self.ret(0),   # Capture debug logger.
            0x602F94C5: lambda: self.ret(3),   # Ordinary P/A/S/M capture context.
            0x602ECF25: lambda: self.ret(0),   # Storage readiness API.
            MEDIA_READY: self.ready_media,
            0x6094D3C9: self.ready_media,     # Native media capacity check.
            0x6076A167: lambda: self.ret(0),   # Sequence observer service.
            0x609557A2: lambda: self.ret(0),
            0x60A326B3: self.acknowledge_capture,
        }
        self.add('return', HOOK_RETURN, bytes(8), 'rx')
        self.add('event', EVENT, bytes(32))
        self.add('composer', COMPOSER, bytes(2836))
        self.add('shooter', SHOOTER, bytes(816))
        self.add('controller', CONTROLLER, bytes(2400))
        self.add('key_packet', KEY_PACKET, bytes(24))
        self.add('release_service', RELEASE_SERVICE, pack('<I', RELEASE_METHODS))
        self.add('release_methods', RELEASE_METHODS, bytes(216) + pack('<I', RELEASE_CALL))
        self.add('media_service', MEDIA_SERVICE, pack('<I', MEDIA_METHODS))
        self.add('media_methods', MEDIA_METHODS, bytes(196) + pack('<I', MEDIA_READY))
        self.add('ui_release_flags', RELEASE_ENABLED, pack('<II', 1, 0))
        self.add('interval_ui_flags', 0x61FB0AC0, bytes(4))
        self.add('active_release', ACTIVE_RELEASE, pack('<I', 1))
        self.add('still_enabled', STILL_ENABLED, pack('<I', 1))
        self.add('capture_state', CAPTURE_STATE, pack('<I', 1))
        self.add('still_mode', 0x61FA73A0, pack('<I', 1))
        self.add('touch_movie', 0x61FA7360, bytes(4))
        self.add('media_block', 0x61FA727C, bytes(4))
        self.add('release_cancel', 0x61FA7428, bytes(4))
        self.add('capture_busy', 0x61FA7480, bytes(4))
        self.add('camera_error', 0x61FA71E8, bytes(4))
        self.add('release_mode', 0x61FACCDC, bytes(1))
        self.add('movie_release', 0x61FACCF8, bytes(4))
        self.add('release_conflicts', 0x61FACD3C, bytes(8))
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
        self.word_set(COMPOSER + 172, COMPOSER_REPLY)
        self.word_set(COMPOSER + 2832, SHOOTER)
        self.word_set(SHOOTER, 0x60B49240)  # Original still-shooting vtable.
        self.word_set(SHOOTER + 640, MEDIA_SERVICE)
        self.write(SHOOTER + 788, pack('<II', 17, 17))  # Stock standby selectors.
        self.word_set(SHOOTER + 808, 1)  # Stock constructor and release cleanup set this flag.
        for sid, value in ((5, 0), (24, 3), (600, 0), (1494, 0)):
            self.set_property(sid, value)
        self.select_drive(0)
        self.word_set(0x622A0A8C, PROPERTIES + 4 * 1494)
        self.word_set(0x622A0B30, PROPERTIES + 4 * 600)

    def add(self, name, address, data, permissions='rw'):
        self.regions[name] = Region(name, address, data, permissions, 'w' in permissions)

    def word_set(self, address, value):
        self.write(address, pack('<I', value))

    def hdr_settings(self):
        return tuple(self.word(PROPERTIES + 4 * sid) for sid in (600, 1494, 5, 1487))

    def select_drive(self, drive):
        # The native drive decoder loads an effective tuple from the ROM row
        # and uses the property order in 0x60430424. Seed that tuple as a unit.
        sid, _, rows, codes, size, stride = unpack('<HHIIHH', self.read(0x604CC98C, 16))
        require(sid == 3281 and stride == 64, 'unexpected native drive descriptor')
        count = size // stride
        values = unpack(f'<{count}I', self.read(codes, count * 4))
        props = unpack('<11H', self.read(0x60430426, 22))
        require(props[-1] == 3200, 'unexpected native drive property list')
        row = unpack('<10I', self.read(rows + stride * values.index(drive), 40))
        for prop, value in zip(props[:-1], row):
            self.set_property(prop, value)
        self.drive = drive

    def rec_key(self, key, *, wrapped=False):
        packet = (WRAPPED_KEY, key) if wrapped else (key, 0)
        self.write(KEY_PACKET, pack('<II', *packet))
        self.replay(HDR_ACTION_CALL, mid=True, stop=(HDR_ACTION_RETURN,),
                    registers=dict(d0=14, a1=KEY_PACKET))
        require(self.regs['sp'] == SP, 'Rec action changed the UI stack')

    def current_subapp(self):
        require(self.regs['d0'] == 40, 'unexpected stock HDR subapp selector')
        self.ret(int(self.subapp_active))

    def resolve_release_service(self):
        require(self.regs['a0'] == 0x60F41C40, 'unexpected UI service')
        self.regs['a0'] = RELEASE_SERVICE
        self.ret(0)

    def control_release(self):
        command = self.regs['d0']
        require(self.regs['a0'] == RELEASE_SERVICE and command in (0, 1), 'unexpected ctrlRelease call')
        self.release_commands.append(command)
        self.regs.update(d0=0, pc=self.regs['mdr'])

    def acknowledge_capture(self):
        require(self.regs['a0'] == COMPOSER_REPLY and self.regs['d0'] == 1007 and
                self.regs['d1'] == 0 and self.regs['a1'] == self.word(EVENT+28),
                'native dispatcher did not acknowledge the submitted event')
        self.ret(0)

    def ready_media(self):
        expected = MEDIA_SERVICE if self.regs['pc'] == MEDIA_READY else SHOOTER
        require(self.regs['a0'] == expected, 'unexpected media service receiver')
        self.regs.update(d0=1, pc=self.regs['mdr'])

    def capture(self):
        return self.replay(CAPTURE_ENTRY, mask=0xF0, frame=40,
                           stop=(STANDBY_ADVANCE, CAPTURE_REPLY, STANDBY_REFUSED),
                           registers=dict(a0=COMPOSER))

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
        self.release_enabled_on_submit.append(self.word(RELEASE_ENABLED))
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


def inspect(directory, engine, prior_024=None, prior_025=None, prior_026=None):
    report = json.loads((directory / 'report.json').read_text(encoding='utf-8'))
    image = (directory / report['image']).read_bytes()
    m = Replay(image, engine)
    symbols = json.loads((directory / 'symbols.json').read_text(encoding='utf-8'))
    status = int(symbols[report['rec_hdr']['body_status_symbol']]['address'], 16)
    require(m.native_value(0x602B9F70, 48) == len(REC_OPTIONS) + 1, 'Rec picker count differs')
    require(m.native_value(0x602B9FDB, 48, index=11) == 473 and
            m.native_value(0x602B9FDB, 48, index=12) == 3200, 'Rec HDR option is missing')
    require(m.native_value(0x602B9F70, 47) == len(REC_OPTIONS), 'AEL picker was widened')
    require(m.native_value(0x60CC885C, 473, mask=0xC0) == 14, 'native HDR action differs')

    m.rec_key(KEY_PRESS, wrapped=True)
    require(m.word(status) == 2, 'Rec event preparation was not visible')
    m.rec_key(0x01000008)
    m.rec_key(KEY_RELEASE)
    m.subapp_active = True
    m.rec_key(KEY_PRESS)
    m.subapp_active = False
    require(len(m.shots) == 1 and m.word(status) == 1,
            'Rec press did not produce exactly one request or subapp gate was not visible')
    require(not m.release_commands and m.release_enabled_on_submit == [1] and
            m.word(RELEASE_ENABLED) == 1, 'Rec changed the stock shutter release lock')
    m.write(KEY_PACKET, pack('<II', WRAPPED_KEY, 0x01000004))
    m.replay(HDR_ACTION_CALL, mid=True, stop=(STOCK_HDR_RESUME,),
             registers=dict(d0=14, d1=0x1357, a1=KEY_PACKET))
    require((m.regs['d2'], m.regs['d1'], m.regs['a2'], m.regs['a0']) ==
            (14, 0x1357, KEY_PACKET, m.regs['sp'] + 28),
            'non-Rec HDR action changed its original inputs')
    event = m.shots[0]
    vtable, number = unpack('<IH', event[:6])
    require(vtable != 0x60A7DD24 and number == 1007 and
            m.read(vtable, 72) == pack('<18I', *EVENT_METHODS),
            'marked request changed the stock event ABI')

    drive_results = []
    for drive, electronic, shutter in ((0, 0, 0), (12, 0, 1), (30, 1, 2)):
        m.select_drive(drive)
        require(m.hdr_settings() == NO_HDR, 'native single drive did not start unbracketed')
        reached = m.capture()
        require(reached == STANDBY_ADVANCE and m.word(SHOOTER+792) == 22 and
                m.hdr_settings() == HDR1 and m.word(TRIGGER) & 1 and m.word(status) == 7,
                f'marked drive {drive} stopped at {reached:#x} with '
                f'capture settings={m.hdr_settings()} and trigger={m.word(TRIGGER):#x}')
        require(m.word(SHOOTER+728) == 0, 'Rec armed the interval session')
        require((m.word(SEQUENCE) & 0x10208) == 0x208 | (electronic << 16),
                'native sequence did not combine HDR with the selected shutter')

        if electronic:
            m.replay(0x6095057D, mask=0xE0, frame=24, registers=dict(a0=SHOOTER))
            require(m.read(BRACKET_LIMIT, 2) == pack('<H', 4), 'native bracket limit is not four')
            require(m.native_value(0x6042888C, 0) == 1, 'native exposure logic did not select HDR')
            require(m.capture() == CAPTURE_REPLY and
                    m.hdr_settings() == HDR1, 'second Rec request replaced the active sequence')

        m.word_set(SP+4, CONTROLLER)
        m.replay(0x602A47A7, mid=True, stop=(0x602A47FF,), registers=dict(a0=CONTROLLER))
        require(m.read(CONTROLLER+1998, 1) == bytes([shutter]),
                'controller selected a different shutter')

        clear = 0x609452BB if drive != 24 else 0x6093434E
        m.replay(clear, mid=True, stop=(clear+7,), registers=dict(a0=SHOOTER, d0=1 if drive != 24 else 15))
        require(m.hdr_settings() == NO_HDR and m.word(TRIGGER) == 0 and
                (m.word(SEQUENCE) & 0x10209) == 0 and m.drive == drive and m.word(status) == 8,
                'HDR state leaked after cleanup')
        if electronic:
            m.replay(0x6095057D, mask=0xE0, frame=24, registers=dict(a0=SHOOTER))
            require(m.read(BRACKET_LIMIT, 2) == pack('<H', 1), 'ordinary capture is still bracketed')
            require(m.native_value(0x6042888C, 0) == 0, 'ordinary exposure still selects HDR')
        drive_results.append(dict(drive=drive, controller_shutter=shutter))

    m.word_set(CAPTURE_STATE, 5)  # A physical half-press already owns READY_TRIG2.
    reached = m.capture()
    require(reached == CAPTURE_REPLY and m.hdr_settings() == NO_HDR and m.word(TRIGGER) == 0 and
            m.word(status) == 3,
            'Rec took over a half-pressed physical shutter')

    m.word_set(CAPTURE_STATE, 1)
    m.word_set(STILL_ENABLED, 0)
    require(m.capture() == CAPTURE_REPLY and m.hdr_settings() == NO_HDR and m.word(TRIGGER) == 0,
            'Rec armed a shot while still release was disabled')
    m.word_set(STILL_ENABLED, 1)

    m.word_set(0x8050, 1)
    require(m.capture() == CAPTURE_REPLY and m.word(status) == 4 and
            m.hdr_settings() == NO_HDR and m.word(TRIGGER) == 0,
            'Rec armed a shot outside the synchronous settings core')
    m.word_set(0x8050, 0)

    m.select_drive(24)  # The native table identifies 24 as a self-timer mode.
    require(m.capture() == CAPTURE_REPLY and m.word(status) == 5 and
            m.hdr_settings() == NO_HDR and m.word(TRIGGER) == 0,
            'Rec treated custom self-timer as silent single drive')
    m.select_drive(0)

    m.interval = 1
    m.rec_key(KEY_PRESS)
    require(len(m.shots) == 1, 'Rec queued a request during interval shooting')
    m.word_set(EVENT, 0x60A7DD24)  # Original one-shot event class.
    sequence = m.word(SEQUENCE)
    require(m.capture() == CAPTURE_REPLY, 'stock one-shot ran without an interval session')
    m.word_set(SHOOTER+728, 2)
    require(m.capture() == STANDBY_ADVANCE and
            m.hdr_settings() == NO_HDR and m.word(SEQUENCE) == sequence,
            'stock interval request acquired the HDR settings')
    m.replay(0x609452BB, mid=True, stop=(0x609452C2,), registers=dict(a0=SHOOTER, d0=1))
    require(m.word(TRIGGER) == 0 and m.word(SEQUENCE) == sequence,
            'stock trigger clear acquired the HDR settings')
    result = dict(status='passed', rec_menu_option=True, single_request=True,
                ui_release_enabled_through_rec=True, stock_hdr_dispatch_preserved=True,
                native_standby_trigger_reached=True, native_standby_guard_passed=True,
                single_drive_properties_from_stock_table=True,
                interval_bit_left_clear=True,
                still_release_disable_respected=True,
                drive_results=drive_results, native_electronic_bracket_limit=4, native_hdr_ae=True,
                trigger_clear_restore=True, ordinary_electronic_bracket_limit=1,
                overlapping_requests_rejected=True, non_owner_core_rejected=True,
                stock_one_shot_unchanged=True,
                hash_checks_performed=False, hardware_executed=False,
                boundary='Native replay covers event dispatch through the standby state selection, HDR AE eligibility, '
                          'sequence and shutter selection. UI services, RTOS, heap, typed-property resolution, '
                          'media readiness and transport are modeled.')
    if prior_024 is not None:
        previous = json.loads((prior_024 / 'report.json').read_text(encoding='utf-8'))
        require(previous['release'] == '024', 'expected the original 024 firmware')
        legacy = Replay((prior_024 / previous['image']).read_bytes(), engine)
        legacy.rec_key(KEY_PRESS)
        require(legacy.release_commands == [1] and legacy.release_enabled_on_submit == [0] and
                legacy.word(RELEASE_ENABLED) == 0, 'original 024 release-lock regression did not reproduce')
        result['original_024_release_disable_reproduced'] = True
    if prior_025 is not None:
        previous = json.loads((prior_025 / 'report.json').read_text(encoding='utf-8'))
        require(previous['release'] == '025', 'expected the original 025 firmware')
        legacy = Replay((prior_025 / previous['image']).read_bytes(), engine)
        legacy.rec_key(KEY_PRESS)
        require(len(legacy.shots) == 1 and legacy.word(RELEASE_ENABLED) == 1 and
                legacy.capture() == CAPTURE_REPLY and legacy.hdr_settings() == NO_HDR and
                legacy.word(TRIGGER) == 0, 'original 025 interval-gate rejection did not reproduce')
        result['original_025_interval_gate_rejection_reproduced'] = True
    if prior_026 is not None:
        previous = json.loads((prior_026 / 'report.json').read_text(encoding='utf-8'))
        require(previous['release'] == '026', 'expected the original 026 firmware')
        legacy = Replay((prior_026 / previous['image']).read_bytes(), engine)
        legacy.rec_key(KEY_PRESS)
        for drive in (0, 12, 30):
            legacy.select_drive(drive)
            require(legacy.capture() == CAPTURE_REPLY and legacy.hdr_settings() == NO_HDR and
                    legacy.word(TRIGGER) == 0, f'026 did not reject native single drive {drive}')
        result['original_026_stock_single_rejection_reproduced'] = True
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--prior-024', type=Path, help='reproduce the original 024 release-lock regression')
    parser.add_argument('--prior-025', type=Path, help='reproduce the original 025 interval-gate rejection')
    parser.add_argument('--prior-026', type=Path, help='reproduce 026 on native single-drive properties')
    args = parser.parse_args()
    result = json.dumps(inspect(args.candidate, args.engine, args.prior_024, args.prior_025,
                                args.prior_026), indent=2) + '\n'
    args.out.write_text(result, encoding='utf-8')
    print(result, end='')
