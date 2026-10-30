#!/usr/bin/env python3
"""Exact-stock E-P7 editor/key table checks; NOT physical input qualification."""
import argparse
import json
from pathlib import Path
import struct

from ep7_stock_audit import BASE, SAT_IDS, TABLE, audit, require
from oly_container import parse, sha256

EDITOR_KEYS = (0x13b3, 0x13b4, 0x13b5, 0x140c)
CURSOR_IDS = (1091, 1096, 1097, 1686)
# Table addresses, logical producer values, and application-level IDs.
# These are NOT GPIO numbers or COLOR GUI-local events.
KEY_ROWS = (
    ('ok_press', 0x60adc290, 0x02000004, 0x43, 0x60a6eef0, 'EV_PRESS_OK_KEY'),
    ('ok_release', 0x60adc298, 0x02010004, 0x44, 0x60a6eef8, 'EV_RELEASE_OK_KEY'),
    ('delete_press', 0x60adc2c0, 0x02000084, 0x53, 0x60a6ef70, 'EV_PRESS_DEL_KEY'),
    ('delete_release', 0x60adc2c8, 0x02010084, 0x54, 0x60a6ef78, 'EV_RELEASE_DEL_KEY'),
    ('info_press', 0x60adc2d0, 0x02001205, 0x57, 0x60a6ef90, 'EV_PRESS_INFO_KEY'),
    ('info_release', 0x60adc2d8, 0x02011205, 0x58, 0x60a6ef98, 'EV_RELEASE_INFO_KEY'),
)


def inspect(raw):
    identity = audit(raw)
    main = parse(raw)[0].payload
    editors = []
    for i, expected_key in enumerate(EDITOR_KEYS):
        address = 0x61186c7c+i*8
        key, count, pointer = struct.unpack_from('<HHI', main, address-BASE)
        require((key, count) == (expected_key, 13), 'COLOR descriptor mismatch')
        require(BASE <= pointer <= BASE+len(main)-count*8, 'child array bounds')
        children = [struct.unpack_from('<II', main, pointer-BASE+j*8) for j in range(count)]
        require(children == [(0, value) for value in [CURSOR_IDS[i], *range(SAT_IDS[i], SAT_IDS[i]+12)]],
                'COLOR cursor/value children mismatch')
        handlers = 0x61185bdc+i*0x38
        words = struct.unpack_from('<5I', main, handlers-BASE)
        require(words == (key, 0x60e20a54, 0x60e20bc7, 0x60e20e0a, 0x60e2107a),
                'COLOR actuator handlers mismatch')
        editors.append(dict(profile=i+1, editor_key=hex(key), descriptor=hex(address),
                            child_array=hex(pointer), child_count=count, cursor_property=children[0][1],
                            saturation_properties=[x[1] for x in children[1:]],
                            handler_row=hex(handlers), increment_candidate='0x60e20e0a',
                            decrement_candidate='0x60e2107a'))
    key, count, pointer = struct.unpack_from('<HHI', main, 0x61186c74-BASE)
    require((key, count) == (0x13a9, 2), 'CRT descriptor mismatch')
    require([struct.unpack_from('<II', main, pointer-BASE+j*8) for j in range(2)] == [(0,617),(0,618)],
            'CRT child properties mismatch')
    keys = []
    for label, address, logical, application, name_row, expected_name in KEY_ROWS:
        require(struct.unpack_from('<II', main, address-BASE) == (logical, application), 'key translation mismatch')
        key, pointer = struct.unpack_from('<II', main, name_row-BASE)
        require(key == application and BASE <= pointer < BASE+len(main)-64, 'key name pointer mismatch')
        require(main[pointer-BASE:pointer-BASE+64].split(b'\0')[0].decode('ascii') == expected_name,
                'key name mismatch')
        keys.append(dict(label=label, logical_event=hex(logical), application_event=hex(application),
                         translation_row=hex(address), naming_row=hex(name_row)))
    mode_keys = [struct.unpack_from('<II', main, 0x61189298-BASE+i*8) for i in range(4)]
    require(mode_keys == list(zip((54,55,56,64), EDITOR_KEYS)), 'mode/editor selection mismatch')
    callbacks = (0x60e20a54,0x60e20bc7,0x60e20e0a,0x60e2107a,
                 0x60e213bb,0x60e21852,0x60e21cae,0x60e21efb,
                 0x60e22191,0x60e223ae,0x60e22579,0,0)
    for i, key in enumerate(EDITOR_KEYS):
        require(struct.unpack_from('<14I', main, 0x61185bdc+i*56-BASE) == (key,*callbacks),
                'complete COLOR callback row mismatch')
    require(struct.unpack_from('<I', main, 0x61187534-BASE)[0] == 0x60dd5250,
            'parent dispatcher vtable mismatch')
    require(struct.unpack_from('<I', main, 0x61187534+68-BASE)[0] == 0x60e20cdc,
            'parent event wrapper vtable mismatch')
    dispatch = dict(struct.unpack_from('<II', main, 0x6114040c-BASE+i*8) for i in range(16))
    for event, target in ((0x900c,0x60dd5489),(0x9014,0x60dd55bb),
                          (0x9016,0x60dd54e2),(0xf802,0x60dd5623)):
        require(dispatch.get(event-0x9003) == target, 'local event dispatcher mismatch')
    windows = {'mode_to_editor_factory': (0x60e266a9,0x60e26789),
               'callback_installation': (0x60e20760,0x60e2086b),
               'parent_local_dispatch': (0x60dd5250,0x60dd5695),
               'parent_callback_wrapper': (0x60e20cdc,0x60e20d22),
               'color_default_and_hold': (0x60e22191,0x60e2229f),
               'color_ok_callback': (0x60e223ae,0x60e22404),
               'color_info_all_callback': (0x60e22579,0x60e228e9),
               'logical_key_mapper': (0x60825002,0x608251e0),
               'editor_child_constructor': (0x60e20aca,0x60e20b2d),
               'color_increment_candidate': (0x60e20e0a,0x60e20f6d),
               'color_decrement_candidate': (0x60e2107a,0x60e211cd),
               'color_processing_caller': (0x603b1466,0x603b1517),
               'generic_table_packer': (0x603afb94,0x603afd26)}
    for i in range(12):
        require(struct.unpack_from('<h', main, TABLE-BASE+i*28+12)[0] == 0 and
                struct.unpack_from('<h', main, TABLE-BASE+i*28+16)[0] == 0,
                'stock COLOR H/L source fields are not neutral')
    return dict(scope='Static data tables and inspected-window identity only; no complete physical key-to-editor chain',
                source_sha256=identity['source_sha256'], editors=editors,
                crt=dict(editor_key='0x13a9', child_count=2, properties=[617,618]),
                logical_key_translation=keys,
                color_source_hl_fields_zero=True, color_source_records=12,
                inspected_windows={name: dict(start=hex(start), stop_exclusive=hex(stop),
                    sha256=sha256(main[start-BASE:stop-BASE])) for name,(start,stop) in windows.items()},
                mode_to_editor=[dict(mode=mode, editor_key=hex(key)) for mode,key in mode_keys],
                local_callbacks=dict(default='0x60e22191', event_900c='0x60e223ae',
                                     event_9014='0x60e22579', timer_event='0xf802',
                                     pending_hold_event='0x903e'),
                physical_gpio_verified=False, selected_color_application_state_verified=False,
                delete_axis_switch_implemented=False, camera_accessed=False, flash_ready=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.stock.read_bytes()), indent=2))


if __name__ == '__main__':
    main()
