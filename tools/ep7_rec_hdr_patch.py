"""Build-1100 Rec HDR overlay recipe for the decoded-image linker."""

from struct import pack

from ep7_offline_candidate import BASE


REC_OPTIONS = (3453, 44, 106, 84, 85, 88, 3461, 34, 3474, 568, 426, 3200)
EVENT_METHODS = (
    0x607765F4, 0x60A4D3D7, 0x6077551E, 0x60768470, 0x60768477, 0x60A4D428,
    0x60A4D42E, 0x60A4D434, 0x60A4D43A, 0x60A4D440, 0x60A4D446, 0x60A4D3D4,
    0x60A4D40C, 0x60A4D404, 0x60A4D410, 0x60A4D408, 0x60A4D413, 0x60A4D3C7,
)


def configure(recipe, image):
    for address, expected in ((0x604CAE6C, pack('<12H', *REC_OPTIONS)),
                              (0x60A7DD24, pack('<18I', *EVENT_METHODS))):
        offset = address - BASE
        if image[offset:offset + len(expected)] != expected:
            raise ValueError(f'Rec HDR data preimage mismatch at {address:#x}')

    recipe.modules += ('rec_hdr',)
    recipe.strategy = 'rec_hdr_lab'
    recipe.native.update({
        'ep7rec_native_get': 0x602CBC0A,
        'ep7rec_native_get_setting': 0x602AFA81,
        'ep7rec_native_write_effective': 0x602CBC74,
        'ep7rec_native_settings_inhibit': 0x602CC6CF,
        'ep7rec_native_judge_sequence': 0x609351B0,
        'ep7rec_native_publish_sequence': 0x609466B2,
        'ep7rec_native_get_trigger': 0x609607F6,
        'ep7rec_native_clear_trigger': 0x609607FF,
        'ep7rec_native_normalize_key': 0x60CC9A05,
        'ep7rec_native_subapp_active': 0x60CE0AA2,
        'ep7rec_native_key_continue': 0x60CE3B9B,
        'ep7rec_native_key_return': 0x60CE3C0A,
        'ep7rec_native_submit': 0x607913AB,
        'ep7rec_native_create_event': 0x60775507,
        'ep7rec_native_interval_guard': 0x60769BEE,
        'ep7rec_native_busy_guard': 0x60769C04,
        'ep7rec_native_one_shot': 0x60953AB0,
        'ep7rec_native_capture_state': 0x6076AAD2,
        'ep7rec_native_capture_standby': 0x60953B6F,
        'ep7rec_native_capture_other_state': 0x60953BA6,
        'ep7rec_native_capture_reply': 0x60953C1A,
        'ep7rec_native_silent_continue': 0x60968A4B,
        'ep7rec_native_silent_block': 0x60968ADB,
    })
    recipe.pointers += [(0x604CDA34, '6cae4c60', 'rec_hdr_options')]
    recipe.literals += [(0x604CDA3C, '1800', '1a00')]
    recipe.calls += [
        (0x607913CB, 'dd2388fdff0008', 'rec_hdr_sdk_guard', 0, 8),
        (0x6079142B, 'dddc40feff0004', 'rec_hdr_create', 0, 4),
        (0x60953AB2, 'dd3c61e1ff0008', 'rec_hdr_capture_guard', 0, 8),
        (0x6093434E, 'ddb1c402000000', 'rec_hdr_clear', 0, 0),
        (0x609452BB, 'dd44b501000000', 'rec_hdr_clear', 0, 0),
    ]
    recipe.jumps += [
        (0x60CE3B96, '96823c201c', 'rec_hdr_press'),
        (0x609018FC, 'fa20100bddb0210500b020', 'rec_hdr_event'),
        (0x60953B64, 'dd6e6fe1ff0000a001c939', 'rec_hdr_admission'),
        (0x60968A44, 'a000c805cc9300', 'rec_hdr_silent_guard'),
    ]
