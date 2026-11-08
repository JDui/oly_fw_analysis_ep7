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
NOTIFY_EVENT, NOTIFY_QUEUE, NOTIFY_METHODS, NOTIFY_SEND = (
    0x19320000, 0x19320100, 0x19320200, 0x19320300)
AE_SERVICE = 0x19320400
CAPTURE_BUFFER = 0x19320600
CAPTURE_JOB = 0x19320700
TAKE_SERVICE = 0x19320800
COMBINE_CONTROLLER = 0x19321000
RECORD_SERVICE = 0x19321200
COMBINE_EVENT = 0x19321300
OUTPUT_METADATA = 0x19321400
FOCUS_ENGINE = 0x19321500
READY_SEQUENCE, READY_REQUEST = 0x19321700, 0x19321800
FRAME_JOBS = tuple(CAPTURE_JOB + 32 * index for index in range(4))
OUTPUT_JOB = CAPTURE_JOB + 128
RELEASE_ENABLED = 0x6233B844
ACTIVE_RELEASE = 0x61FACCE0
TAKE_PICTURE_REQUEST = 0x61FACD00
SET_RELEASE_STATUS = 0x60950AEA
CAPTURE_STATE = 0x61FA748C
PROPERTY_MAP = 0x604D6C14
PROPERTY_CACHE = 0xA2699CB4
BRACKET_INDEX_CACHE = 0xA269BB20
BRACKET_LIMIT = 0x61FACCE8
SEQUENCE = 0x61FACD64
TRIGGER = 0x61FACD84
RELEASE_HISTORY = 0x61FACD88
RELEASE_EVENT = 0x61FACD8C
FULL_RELEASE_FLAGS = SHOOTER + 464
HDR_FRAMES_DONE = SHOOTER + 498
READ_SETTING = 0x602AFA81
NATIVE_VALIDATE = 0x62248528
KEY_PRESS = 0x01000006
KEY_RELEASE = 0x01000007
WRAPPED_KEY = 0x0100002E
HDR_ACTION_CALL, HDR_ACTION_RETURN = 0x60CE03BB, 0x60CE03C0
STOCK_HDR_RESUME = 0x60CE3B9B
CAPTURE_ENTRY, CAPTURE_REPLY = 0x60904471, 0x60953C1A
STANDBY_ADVANCE, STANDBY_REFUSED = 0x60962780, 0x60962752
STANDBY_GUARD_RETURN = 0x60953BA4
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
        self.burst_stops = 0
        self.half_held = False
        self.capture_job = CAPTURE_JOB
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
            0x602CDDA2: lambda: self.ret(0),   # No storage-slot error flags.
            0x602FCA52: self.physical_shutter,
            0x602CBC5D: self.reset_release_setting,
            MEDIA_READY: self.ready_media,
            NOTIFY_SEND: self.capture_notify,
            0x6094D3C9: self.ready_media,     # Native media capacity check.
            0x6076A167: lambda: self.ret(0),   # Sequence observer service.
            0x609557A2: lambda: self.ret(0),
            0x60A326B3: self.acknowledge_capture,
            0x60877995: lambda: self.ret(0),   # Retire the lens ready timer.
            0x6087793E: lambda: self.ret(1),   # Lens ready service accepted the request.
            0x6087AC7B: lambda: self.ret(0),   # No pending lens timer.
            0x6087DDB9: lambda: self.ret(0),   # Stop the lens ready timer.
            0x6087E402: lambda: self.ret(0),   # Change the lens service timer phase.
            0x60875637: lambda: self.ret(0),   # End the lens ready wait.
            0x6087AC82: lambda: self.ret(0),   # Idle lens command slot.
            0x608779C9: lambda: self.ret(0),   # No conflicting lens request.
            0x60874603: lambda: self.ret(1),   # AF is ready for exposure.
            0x6087BB59: lambda: self.ret(1),   # Lens service permits TakeReady.
            0x60874BC8: lambda: self.ret(0),   # Send the lens readiness request.
            0x60874B0D: lambda: self.ret(0),   # Send the lens capture-preparation request.
            0x608752F3: self.stop_exposures,
            0x6087543F: self.accept_exposure_job,
            0x60875491: self.accept_exposure_job,
            0x602F7DA3: lambda: self.ret(0),   # Publish the ready indication.
            0x602EA74C: lambda: self.ret(0),   # No auxiliary ready notification.
            0x60889900: lambda: self.ret(0),   # Successful AE result read.
            0x6088A5BB: lambda: self.ret(0),   # AE service accepts next phase.
            0x6088A17E: lambda: self.ret(0),   # No pending review abort.
            0x6088A721: lambda: self.ret(0),   # Apply a native AE service command.
            0x6088A752: lambda: self.ret(0),   # Reset a native AE service flag.
            0x6091170E: lambda: self.ret(0),   # AE service mode notification.
            0x6091153F: lambda: self.ret(OUTPUT_METADATA),  # Final AE metadata buffer.
            0x60886492: lambda: self.ret(0),   # Lens has no pending request.
            0x6082EF00: lambda: self.ret(1),   # One capture buffer is available.
            0x6082F6B2: self.allocate_capture_job,
            0x6082F49B: self.allocate_output_job,
            0x608FE29A: lambda: self.ret(0),   # Capture observer registration.
            0x6083A1B4: lambda: self.ret(0),   # Reset the capture service counters.
            0x60557498: lambda: self.ret(0),   # Focus-engine debug output.
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
        self.add('notify_event', NOTIFY_EVENT, bytes(40))
        self.add('notify_queue', NOTIFY_QUEUE, pack('<I', NOTIFY_METHODS))
        self.add('notify_methods', NOTIFY_METHODS, bytes(4) + pack('<I', NOTIFY_SEND))
        self.add('ae_service', AE_SERVICE, bytes(512))
        self.add('capture_buffer', CAPTURE_BUFFER, bytes(4))
        self.add('capture_jobs', CAPTURE_JOB, bytes(160))
        self.add('combine_controller', COMBINE_CONTROLLER, bytes(276))
        self.add('combine_event', COMBINE_EVENT, bytes(44))
        self.add('combine_debug_flags', 0x61FACBD4, bytes(2))
        self.add('focus_engine', FOCUS_ENGINE, bytes(320))
        self.add('focus_engine_enabled', 0xA2788CA8, pack('<II', 1, FOCUS_ENGINE))
        self.add('ready_sequence', READY_SEQUENCE, bytes(16))
        self.add('ready_request', READY_REQUEST, bytes(64))
        self.add('exposure_focus_mode', 0x622A063C, bytes(0x50))
        self.add('exposure_ready_state', 0x622A076C, bytes(0x240))
        self.add('exposure_ready_gate', 0x622A0A68, bytes(4))
        self.add('exposure_focus_gate', 0x622A0B34, bytes(4))
        self.add('ui_release_flags', RELEASE_ENABLED, pack('<II', 1, 0))
        self.add('interval_ui_flags', 0x61FB0AC0, bytes(4))
        self.add('active_release', ACTIVE_RELEASE, bytes(4))
        self.add('release_settings', 0x61FACCF8, bytes(24))
        self.add('capture_debug_state', 0x61FACD10, bytes(12))
        self.add('capture_notifications', 0x61FACD38, bytes(4))
        self.add('release_movie_mode', 0x61FA73AC, bytes(4))
        self.add('capture_state', CAPTURE_STATE, pack('<I', 1) + bytes(0x7C))
        self.add('still_mode', 0x61FA73A0, pack('<I', 1))
        self.add('touch_movie', 0x61FA7360, bytes(4))
        self.add('capture_continue_state', 0x61FA7358, bytes(4))
        self.add('media_block', 0x61FA727C, bytes(4))
        self.add('release_cancel', 0x61FA7428, bytes(4))
        self.add('capture_busy', 0x61FA7480, bytes(12))
        self.add('camera_error', 0x61FA71E8, bytes(4))
        self.add('release_mode', 0x61FACCDC, bytes(1))
        self.add('release_conflicts', 0x61FACD3C, bytes(8))
        self.add('bracket_limit', BRACKET_LIMIT, bytes(2))
        self.add('native_sequence', SEQUENCE, bytes(0x24))
        self.add('release_history', RELEASE_HISTORY, bytes(8))
        self.add('capture_log_flags', 0x61FACCEC, bytes(4))
        self.add('ready_service_state', 0x622CB16C, bytes(0x130))
        self.add('ready_service_result', 0x61FA7418, bytes(4))
        self.add('capture_mode_state', 0x61FA72E4, bytes(4))
        self.add('capture_ready_state', 0x61FA7260, bytes(12))
        self.add('capture_af_mode', 0x61FA73BC, bytes(4))
        self.add('lens_drive_state', 0x61FA8FD4, bytes(4))
        self.add('capture_finish_flags', 0x61FA7420, bytes(8))
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
        self.word_set(SHOOTER + 336, NOTIFY_QUEUE)
        self.word_set(SHOOTER + 672, AE_SERVICE)
        self.word_set(SHOOTER + 584, CAPTURE_BUFFER)
        self.word_set(SHOOTER + 592, CAPTURE_JOB)
        self.word_set(SHOOTER + 700, TAKE_SERVICE)
        self.word_set(AE_SERVICE+184, AE_SERVICE)
        self.word_set(AE_SERVICE+204, AE_SERVICE)
        self.word_set(SHOOTER + 240, 1)  # Stock standby enables release flags.
        self.write(SHOOTER + 788, pack('<II', 17, 17))  # Stock standby selectors.
        self.word_set(SHOOTER + 808, 1)  # Stock constructor and release cleanup set this flag.
        for sid, value in ((5, 0), (24, 3), (600, 0), (1494, 0)):
            self.set_property(sid, value)
        self.select_drive(0)
        self.word_set(0x622A0A8C, PROPERTIES + 4 * 1494)
        self.word_set(0x622A0B30, PROPERTIES + 4 * 600)

    def set_release(self, enabled, *, take_picture=0):
        # AUTO_RELEASE_ENABLE registers the shutter keys with no immediate
        # take-picture request (60cd1e77, 60cd209c, 60789a82..60789abd).
        keys = (0x02000100, 0x02000101) if enabled else (0, 0)
        self.write(SP+4, pack('<4I', *keys, 0, 0))
        self.replay(SET_RELEASE_STATUS, mask=0xA0, frame=44,
                    registers=dict(a0=SHOOTER, d0=int(enabled), d1=take_picture, a1=0))
        require(self.regs['sp'] == SP and self.word(ACTIVE_RELEASE) == int(enabled) and
                self.word(TAKE_PICTURE_REQUEST) == take_picture, 'native ctrlRelease state differs')

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

    def reset_release_setting(self):
        require(self.regs['d0'] == 4510 and self.regs['d1'] == 0xFFFFFFFF,
                'unexpected release service setting write')
        self.ret(0)

    def allocate_capture_job(self):
        require(self.regs['a0'] == CAPTURE_BUFFER, 'unexpected capture buffer service')
        self.regs['a0'] = self.capture_job
        self.ret(0)

    def accept_exposure_job(self):
        require(self.regs['a0'] == TAKE_SERVICE and self.regs['a1'] == self.capture_job,
                'unexpected HDR exposure service arguments')
        self.ret(0)

    def allocate_output_job(self):
        require(self.regs['a0'] == CAPTURE_BUFFER, 'unexpected HDR output pool')
        self.regs['a0'] = OUTPUT_JOB
        self.ret(0)

    def physical_shutter(self):
        require(self.regs['d0'] in (0x02000100, 0x02000101), 'unexpected key query')
        self.ret(int(self.regs['d0'] == 0x02000101 or not self.half_held))

    def stop_exposures(self):
        require(self.regs['a0'] == TAKE_SERVICE, 'unexpected burst stop receiver')
        self.burst_stops += 1
        self.ret(0)

    def capture(self, *, complete_guard=False):
        stops = ((STANDBY_GUARD_RETURN, CAPTURE_REPLY) if complete_guard else
                 (STANDBY_ADVANCE, CAPTURE_REPLY, STANDBY_REFUSED))
        return self.replay(CAPTURE_ENTRY, mask=0xF0, frame=40,
                           stop=stops,
                           registers=dict(a0=COMPOSER))

    def exit_standby(self):
        self.replay(0x60934334, mask=0x20, frame=8, registers=dict(a0=SHOOTER))

    def finish_focus(self):
        # Execute the stock READY entry and the actual TakeReadyFinish callback.
        # The lens service fixture accepts the native metering and focus request.
        self.replay(0x6093137E, registers=dict(a0=SHOOTER))
        require(self.word(0x61FA7418) == 1, 'native TakeReady request did not start')
        self.replay(0x60963EB9, registers=dict(a0=SHOOTER))
        return self.word(SHOOTER+792)

    def hold_half_press(self):
        # Use the stock release sample and ready handlers for a completed S-AF half-press.
        self.half_held = True
        self.replay(0x6095AF39, mask=0xA0, frame=12, registers=dict(a0=SHOOTER))
        self.exit_standby()
        require(self.finish_focus() == 21, 'physical half-press did not complete readiness')
        self.replay(0x6093179A, registers=dict(a0=SHOOTER))
        require(self.word(CAPTURE_STATE) == 4 and self.word(SHOOTER+788) == 21 and
                self.word(SHOOTER+792) == 21 and self.word(RELEASE_EVENT) == 1,
                'stock READY_FINISH did not retain the half-press')

    def ready_requests_af(self):
        # The native exposure-side judge combines FCS need_afae and chk_af_exec.
        self.write(FOCUS_ENGINE + 49, b'\x01')
        self.shells[0x60556F30] = lambda: self.ret(1)
        self.replay(0x60429C56, mask=0xF0, frame=16)
        return self.regs['d0'] == 1

    def check_metering_without_focus(self):
        # Follow native TakeReady past the AF decision to its AE-only command.
        capture_shells = self.shells
        self.shells = {**capture_shells, **{
            0x6040E7A4: lambda: self.ret(0),  # Exposure service clock.
            0x603F3AFB: lambda: self.ret(0),  # Clear a pending phase-detect plan.
            0x60555C80: lambda: self.ret(0),  # Sensor available for ordinary readiness.
            0x6005E971: lambda: self.ret(0),  # Native exposure readiness parameters.
        }}
        self.write(FOCUS_ENGINE+5, b'\x01\x02')
        self.write(FOCUS_ENGINE+51, b'\x01')
        self.write(FOCUS_ENGINE+168, b'\x01')
        self.write(0x622A063E, b'\x05')  # Exercise the native continuous AF classifier.
        self.write(READY_SEQUENCE+2, b'\x01\x01')
        self.replay(0x604226E2, mask=0xB0, frame=28, stop=(0x6042295A, 0x60422979, 0x60422966),
                    registers=dict(a0=READY_SEQUENCE, a1=READY_REQUEST))
        require(self.regs['pc'] == 0x6042295A and self.regs['d0'] == 0x050F,
                'Rec readiness did not choose the native AE-only command')
        self.write(READY_SEQUENCE+2, b'\x04')
        self.write(READY_SEQUENCE+6, b'\x01')
        self.replay(0x604255B2, mask=0xF0, frame=16, stop=(CALLER+7, 0x60425690),
                    registers=dict(a0=READY_SEQUENCE))
        require(self.regs['pc'] == CALLER+7, 'Rec issued a follow-up lens focus command')
        self.shells = capture_shells

    def start_exposure(self):
        # All shutters use the stock HDR capture job, including silent single.
        self.replay(0x609319A8, registers=dict(a0=SHOOTER))
        require(self.word(SHOOTER+792) == 14, 'HDR did not select TAKE_PICTURE_CONT')
        self.replay(0x609336C7, stop=(0x60962E3A,), registers=dict(a0=SHOOTER))
        require(self.regs['a1'] == CAPTURE_JOB, 'continuous HDR did not receive a capture buffer')
        require(self.word(self.regs['sp']+8) == 1 and self.read(BRACKET_LIMIT, 2) == pack('<H', 4),
                f'drive {self.drive} exposure handoff had HDR={self.word(self.regs["sp"]+8)} '
                f'and limit={int.from_bytes(self.read(BRACKET_LIMIT, 2), "little")}')

    def finish_exposure(self, completed):
        # Drive the real TKPC_TakePictureDone handler after the sensor's
        # third or fourth exposure callback, using its accumulated count.
        self.write(HDR_FRAMES_DONE, pack('<H', completed - 1))
        self.write(SEQUENCE + 20, pack('<H', 1))  # One outstanding exposure.
        # The sub-limit branch leads to the next frame's AE and buffers.
        stop = (0x60932CEC,) if completed < 4 else None
        self.replay(0x60965C9B, stop=stop, registers=dict(a0=SHOOTER))
        require(self.read(HDR_FRAMES_DONE, 2) == pack('<H', completed), 'native frame count differs')

    def collect_hdr_frames(self):
        # Resume the first HDR exposure request, then run the native request
        # for each additional frame. Only the take service and job pool are modeled.
        self.word_set(SHOOTER+716, COMBINE_CONTROLLER)
        self.replay(0x60962E3A, mid=True, registers=self.regs, stop=(0x60962F03,))
        for job in FRAME_JOBS[1:]:
            self.capture_job = job
            self.replay(0x6094F0B8, mask=0xF0, frame=24, registers=dict(a0=SHOOTER))
        self.capture_job = CAPTURE_JOB
        require(self.read(COMBINE_CONTROLLER+184, 2) == pack('<H', 4) and
                self.read(COMBINE_CONTROLLER+192, 16) == pack('<4I', *FRAME_JOBS),
                'native HDR controller did not collect four distinct exposure jobs')

    def rebuild_release_history(self):
        self.replay(0x6095AF0C, mask=0xA0, frame=12, registers=dict(a0=SHOOTER))

    def selects_end_wait(self):
        self.replay(0x6094A4BA, mask=0xB0, frame=20, stop=(CALLER+7, 0x6094A85D, 0x6094A985),
                    registers=dict(a0=SHOOTER))
        return self.word(SHOOTER+792) == 29

    def request_hdr_compose(self):
        # After the modeled sensor-end notification, run the native HDR
        # end handler up to its StartCombine event submission.
        self.word_set(SHOOTER+680, RECORD_SERVICE)
        self.word_set(COMBINE_CONTROLLER+268, COMPOSER)
        self.word_set(AE_SERVICE+424, 5)  # AE result consumed by the native end handler.
        self.replay(0x60932D7E, stop=(0x60916BFA,), registers=dict(a0=SHOOTER))
        require(self.regs['a0'] == COMBINE_CONTROLLER and self.regs['a1'] == COMBINE_EVENT and
                self.read(COMBINE_EVENT+4, 2) == pack('<H', 883) and
                self.read(COMBINE_EVENT+36, 1) == b'\x04' and
                self.read(COMBINE_CONTROLLER+192, 16) == pack('<4I', *FRAME_JOBS),
                'native electronic HDR did not submit four frames for composition')
        self.word_set(SHOOTER+680, 0)
        self.word_set(AE_SERVICE+424, 0)

    def restore_standby(self):
        self.replay(0x609324F7, stop=(0x6093253F,), registers=dict(a0=SHOOTER))

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
        require(sid in (16, 478, 3008, 3281, 15206), f'unexpected setting {sid}')
        self.ret({16: 3, 478: self.interval, 3008: 0, 3281: self.drive, 15206: 0}[sid])

    def resolve_typed_key(self):
        sid = self.typed_keys.get(self.regs['d0'])
        self.regs['a0'] = DESCRIPTORS + 8 * sid if sid is not None else 0
        self.ret(0)

    def lock_handle(self):
        self.regs['a0'] = 0
        self.ret(0)

    def allocate_event(self):
        size = self.regs['d0']
        if self.regs['mdr'] == 0x6079141B:
            require(size == 32, 'native one-shot allocation size changed')
            self.regs['a0'] = EVENT
        elif self.regs['mdr'] == 0x60916BD1:
            require(size == 44, 'native StartCombine allocation size changed')
            self.regs['a0'] = COMBINE_EVENT
        else:
            require(28 <= size <= 40, 'unexpected capture notification allocation')
            self.regs['a0'] = NOTIFY_EVENT
        self.ret(0)

    def virtual_no_reply_pointer(self):
        self.regs.update(a0=0, pc=self.regs['mdr'])

    def enqueue(self):
        require(self.regs['a1'] == EVENT, 'native constructor did not return its event')
        self.shots.append(self.read(EVENT, 32))
        self.release_enabled_on_submit.append(self.word(RELEASE_ENABLED))
        self.ret(0)

    def capture_notify(self):
        require(self.regs['a0'] == NOTIFY_QUEUE and self.regs['a1'] == NOTIFY_EVENT,
                'unexpected native capture notification')
        self.regs.update(d0=0, pc=self.regs['mdr'])

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


def inspect(directory, engine, prior_024=None, prior_025=None, prior_026=None, prior_027=None,
            prior_028=None, prior_029=None):
    report = json.loads((directory / 'report.json').read_text(encoding='utf-8'))
    image = (directory / report['image']).read_bytes()
    m = Replay(image, engine)
    m.set_release(True)
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

    require(m.ready_requests_af(), 'ordinary capture did not allow the native AF request')
    drive_results = []
    for drive, electronic, shutter in ((0, 0, 0), (12, 0, 1), (30, 1, 2)):
        m.select_drive(drive)
        require(m.hdr_settings() == NO_HDR, 'native single drive did not start unbracketed')
        if electronic:
            m.hold_half_press()
            m.rec_key(KEY_PRESS)
            require(len(m.shots) == 2 and m.word(status) == 2,
                    'held half-press prevented the Rec request from being posted')
        reached = m.capture(complete_guard=True)
        expected = (CAPTURE_REPLY, 20, 0) if electronic else (STANDBY_GUARD_RETURN, 22, 1)
        require((reached, m.word(SHOOTER+792), m.word(TRIGGER)) == expected and
                m.hdr_settings() == HDR1 and m.word(status) == 12,
                f'marked drive {drive} stopped at {reached:#x} with '
                f'capture settings={m.hdr_settings()}, next={m.word(SHOOTER+792)}, '
                f'trigger={m.word(TRIGGER):#x}, status={m.word(status)}')
        require(m.word(SHOOTER+728) == 0, 'Rec armed the interval session')
        require((m.word(SEQUENCE) & 0x10208) == 0x208,
                'Rec HDR took the native Silent H/L burst route')

        if electronic:
            require(m.native_value(0x6042888C, 0) == 1, 'native exposure logic did not select HDR')
            require(m.capture() == CAPTURE_REPLY and
                    m.hdr_settings() == HDR1 and m.word(status) == 11,
                    'second Rec request replaced the active sequence')

        m.word_set(SP+4, CONTROLLER)
        m.replay(0x602A47A7, mid=True, stop=(0x602A47FF,), registers=dict(a0=CONTROLLER))
        require(m.read(CONTROLLER+1998, 1) == bytes([shutter]),
                'controller selected a different shutter')

        if not electronic:
            m.exit_standby()
        require(m.hdr_settings() == HDR1 and m.word(TRIGGER) == 0 and
                m.word(RELEASE_HISTORY) & 5 == 5 and m.word(RELEASE_EVENT) == 4 and
                m.word(FULL_RELEASE_FLAGS) & 0x100,
                'native readiness discarded the Rec release')
        require(not m.ready_requests_af(), 'Rec allowed a new autofocus request')
        if not electronic:
            if drive == 0:
                m.check_metering_without_focus()
            require(m.finish_focus() == 20 and m.hdr_settings() == HDR1,
                    'native TakeReady completion did not select READY_TRIG2 with HDR')
        m.start_exposure()
        require(m.hdr_settings() == HDR1, 'the exposure request lost its HDR recipe')
        if electronic:
            m.collect_hdr_frames()
        previous_stops = m.burst_stops
        m.finish_exposure(3)
        require(m.burst_stops == previous_stops and m.word(RELEASE_EVENT) == 4,
                'Rec released the simulated shutter before the fourth frame')
        m.finish_exposure(4)
        m.rebuild_release_history()
        physical_event = 1 if electronic else 2
        require(m.burst_stops == previous_stops + 1 and m.word(RELEASE_EVENT) == physical_event and
                m.word(RELEASE_HISTORY) & 5 == int(m.half_held) and m.word(FULL_RELEASE_FLAGS) & 0x100 == 0 and
                m.hdr_settings() == HDR1 and m.word(status) == 13,
                'native burst completion did not release the shutter and retain the HDR recipe')
        require(m.selects_end_wait(), 'native end handler is still waiting for another shutter event')
        if electronic:
            m.request_hdr_compose()
        m.restore_standby()
        require(m.hdr_settings() == NO_HDR and m.word(TRIGGER) == 0 and
                m.word(RELEASE_HISTORY) & 5 == int(m.half_held) and m.word(RELEASE_EVENT) == physical_event and
                m.word(FULL_RELEASE_FLAGS) & 0x100 == 0 and
                (m.word(SEQUENCE) & 0x10209) == 0 and m.drive == drive and m.word(status) == 8,
                'HDR state leaked after cleanup')
        if electronic:
            require(m.ready_requests_af(), 'Rec left ordinary shutter autofocus disabled')
            require(m.native_value(0x60429CDB, 0, mask=0, frame=4) == 1,
                    'Rec left the native continuous AF classifier disabled')
            m.half_held = False
            m.replay(0x6095AF39, mask=0xA0, frame=12, registers=dict(a0=SHOOTER))
            m.replay(0x6095057D, mask=0xE0, frame=24, registers=dict(a0=SHOOTER))
            require(m.read(BRACKET_LIMIT, 2) == pack('<H', 1), 'ordinary capture is still bracketed')
            require(m.native_value(0x6042888C, 0) == 0, 'ordinary exposure still selects HDR')
        drive_results.append(dict(drive=drive, controller_shutter=shutter, native_hdr_frames=4,
                                  half_press_held=bool(electronic)))

    m.word_set(CAPTURE_STATE, 5)  # An ordinary full press already owns READY_TRIG2.
    reached = m.capture()
    require(reached == CAPTURE_REPLY and m.hdr_settings() == NO_HDR and m.word(TRIGGER) == 0 and
            m.word(status) == 9,
            'Rec took over an ordinary full press')

    m.word_set(CAPTURE_STATE, 1)
    m.set_release(False)
    require(m.capture() == CAPTURE_REPLY and m.hdr_settings() == NO_HDR and
            m.word(TRIGGER) == 0 and m.word(status) == 10,
            'Rec armed a shot while still release was disabled')
    m.set_release(True)

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
    require(len(m.shots) == 2, 'Rec queued a request during interval shooting')
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
                native_release_enable_with_no_take_picture_request=True,
                interval_bit_left_clear=True,
                still_release_disable_respected=True,
                drive_results=drive_results, native_electronic_bracket_limit=4, native_hdr_ae=True,
                native_ae_only_ready_from_standby=True, native_hdr_exposure_handoff=True,
                native_ready_finish_hdr_with_half_press_held=True,
                ordinary_autofocus_allowed_after_rec=True,
                native_fourth_frame_released_rec_keys=True,
                native_end_wait_selected_without_extra_shutter_input=True,
                native_electronic_hdr_jobs_collected=4,
                native_electronic_hdr_composition_submitted=True,
                standby_restores_single_capture=True, ordinary_electronic_bracket_limit=1,
                overlapping_requests_rejected=True, non_owner_core_rejected=True,
                stock_one_shot_unchanged=True,
                hash_checks_performed=False, hardware_executed=False,
                boundary='Native replay covers event dispatch, AE-only readiness, held half-press, shutter selection, '
                          'HDR capture routing, the fourth-frame release and the native electronic HDR '
                          'StartCombine event at its transport boundary. Sensor callbacks and the '
                          'return to standby are modeled. Lens, buffer, media, RTOS, UI, heap, '
                          'typed-property resolution and transport services are modeled.')
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
        legacy.set_release(True, take_picture=1)
        legacy.rec_key(KEY_PRESS)
        require(len(legacy.shots) == 1 and legacy.word(RELEASE_ENABLED) == 1 and
                legacy.capture() == CAPTURE_REPLY and legacy.hdr_settings() == NO_HDR and
                legacy.word(TRIGGER) == 0, 'original 025 interval-gate rejection did not reproduce')
        result['original_025_interval_gate_rejection_reproduced'] = True
    if prior_026 is not None:
        previous = json.loads((prior_026 / 'report.json').read_text(encoding='utf-8'))
        require(previous['release'] == '026', 'expected the original 026 firmware')
        legacy = Replay((prior_026 / previous['image']).read_bytes(), engine)
        legacy.set_release(True, take_picture=1)
        legacy.rec_key(KEY_PRESS)
        for drive in (0, 12, 30):
            legacy.select_drive(drive)
            require(legacy.capture() == CAPTURE_REPLY and legacy.hdr_settings() == NO_HDR and
                    legacy.word(TRIGGER) == 0, f'026 did not reject native single drive {drive}')
        result['original_026_stock_single_rejection_reproduced'] = True
    if prior_027 is not None:
        previous = json.loads((prior_027 / 'report.json').read_text(encoding='utf-8'))
        require(previous['release'] == '027', 'expected the original 027 firmware')
        prior_symbols = json.loads((prior_027 / 'symbols.json').read_text(encoding='utf-8'))
        prior_status = int(prior_symbols[previous['rec_hdr']['body_status_symbol']]['address'], 16)
        legacy = Replay((prior_027 / previous['image']).read_bytes(), engine)
        legacy.set_release(True)
        legacy.rec_key(KEY_PRESS)
        require(len(legacy.shots) == 1 and legacy.capture() == CAPTURE_REPLY and
                legacy.word(prior_status) == 3 and legacy.hdr_settings() == NO_HDR and
                legacy.word(TRIGGER) == 0, '027 did not reproduce the reported D rejection')
        legacy.set_release(True, take_picture=1)
        require(legacy.capture() == STANDBY_ADVANCE and legacy.hdr_settings() == HDR1,
                '027 did not distinguish the take-picture request field')
        result['original_027_d_reproduced_with_native_release_enable'] = True
    if prior_028 is not None:
        previous = json.loads((prior_028 / 'report.json').read_text(encoding='utf-8'))
        require(previous['release'] == '028', 'expected the original 028 firmware')
        legacy = Replay((prior_028 / previous['image']).read_bytes(), engine)
        legacy.set_release(True)
        legacy.rec_key(KEY_PRESS)
        require(legacy.capture(complete_guard=True) == STANDBY_GUARD_RETURN and
                legacy.word(SHOOTER+792) == 22 and legacy.hdr_settings() == HDR1,
                '028 did not start the standby to READY transition')
        legacy.exit_standby()
        require(legacy.hdr_settings() == NO_HDR and legacy.word(RELEASE_HISTORY) & 4 == 0 and
                legacy.finish_focus() == 21, '028 did not reproduce the wait for full release')
        result['original_028_cleared_hdr_before_focus_and_waited_for_full_release'] = True
    if prior_029 is not None:
        previous = json.loads((prior_029 / 'report.json').read_text(encoding='utf-8'))
        require(previous['release'] == '029', 'expected the original 029 firmware')
        original = (prior_029 / previous['image']).read_bytes()
        for drive in (0, 30):
            legacy = Replay(original, engine)
            legacy.set_release(True)
            legacy.select_drive(drive)
            legacy.rec_key(KEY_PRESS)
            require(legacy.capture(complete_guard=True) == STANDBY_GUARD_RETURN,
                    '029 did not start the Rec sequence')
            legacy.exit_standby()
            require(legacy.finish_focus() == 20, '029 did not finish focusing')
            if drive == 30:
                legacy.replay(0x609319A8, registers=dict(a0=SHOOTER))
                require(legacy.word(SHOOTER+792) == 15,
                        '029 did not reproduce the Silent H/L auto burst')
            else:
                legacy.start_exposure()
                legacy.finish_exposure(4)
                legacy.rebuild_release_history()
                require(legacy.burst_stops == 1 and legacy.word(RELEASE_HISTORY) & 5 == 5 and
                        not legacy.selects_end_wait(),
                        '029 did not reproduce the synthetic full press after the fourth frame')
        result['original_029_silent_burst_and_stale_release_reproduced'] = True
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--prior-024', type=Path, help='reproduce the original 024 release-lock regression')
    parser.add_argument('--prior-025', type=Path, help='reproduce the original 025 interval-gate rejection')
    parser.add_argument('--prior-026', type=Path, help='reproduce 026 on native single-drive properties')
    parser.add_argument('--prior-027', type=Path, help='reproduce 027 with stock shutter enabled and no shot requested')
    parser.add_argument('--prior-028', type=Path, help='reproduce the original 028 stall after focusing')
    parser.add_argument('--prior-029', type=Path, help='reproduce 029 burst routing and release state')
    args = parser.parse_args()
    result = json.dumps(inspect(args.candidate, args.engine, args.prior_024, args.prior_025,
                                args.prior_026, args.prior_027, args.prior_028, args.prior_029), indent=2) + '\n'
    args.out.write_text(result, encoding='utf-8')
    print(result, end='')
