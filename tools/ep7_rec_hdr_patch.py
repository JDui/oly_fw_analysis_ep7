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
        'ep7rec_native_latch_release': 0x60955F49,
        'ep7rec_native_set_release_event': 0x60955F7A,
        'ep7rec_native_sync_release_keys': 0x6095AF39,
        'ep7rec_native_read_key': 0x602FCA52,
        'ep7rec_native_release_from_ready': 0x609630AC,
        'ep7rec_native_af_exec': 0x60557126,
        'ep7rec_native_caf_exec': 0x6055710D,
        'ep7rec_native_stop_burst': 0x6094F064,
        'ep7rec_native_normalize_key': 0x60CC9A05,
        'ep7rec_native_subapp_active': 0x60CE0AA2,
        'ep7rec_native_key_continue': 0x60CE3B9B,
        'ep7rec_native_key_return': 0x60CE3C0A,
        'ep7rec_native_submit': 0x607913AB,
        'ep7rec_native_create_event': 0x60775507,
        'ep7rec_native_interval_guard': 0x60769BEE,
        'ep7rec_native_busy_guard': 0x60769C04,
        'ep7rec_native_one_shot': 0x60953AB0,
        'ep7rec_native_interval_admission': 0x60954C33,
        'ep7rec_native_interval_admission_resume': 0x60953B5D,
        'ep7rec_native_capture_state': 0x6076AAD2,
        'ep7rec_native_set_capture_state': 0x6076B6BA,
        'ep7rec_native_capture_standby': 0x60953B6F,
        'ep7rec_native_standby_guard': 0x60962715,
        'ep7rec_native_capture_reply': 0x60953C1A,
    })
    recipe.pointers += [(0x604CDA34, '6cae4c60', 'rec_hdr_options')]
    recipe.literals += [(0x604CDA3C, '1800', '1a00')]
    recipe.calls = [(site, before, 'rec_hdr_version_body' if target == 'version_body' else target,
                     mask, frame) for site, before, target, mask, frame in recipe.calls]
    recipe.calls += [
        (0x607913CB, 'dd2388fdff0008', 'rec_hdr_sdk_guard', 0, 8),
        (0x6079142B, 'dddc40feff0004', 'rec_hdr_create', 0, 4),
        (0x60953AB2, 'dd3c61e1ff0008', 'rec_hdr_capture_guard', 0, 8),
        (0x60953B9D, 'dd78eb00002008', 'rec_hdr_standby', 0x20, 8),
        (0x6093434E, 'ddb1c402000000', 'rec_hdr_clear', 0, 0),
        (0x6093251D, 'dd9d91e3ff000c', 'rec_hdr_idle', 0, 12),
        (0x60932CE2, 'dd82c301002008', 'rec_hdr_burst_limit', 0x20, 8),
        (0x60425391, 'dd951d13000004', 'rec_hdr_af_exec', 0, 4),
        (0x604255C0, 'dd661b13000004', 'rec_hdr_af_exec', 0, 4),
        (0x60429C62, 'ddc4d412000004', 'rec_hdr_af_exec', 0, 4),
        (0x60429B9E, 'dd6fd512000004', 'rec_hdr_caf_exec', 0, 4),
    ]
    recipe.jumps += [
        (0x60CE3B96, '96823c201c', 'rec_hdr_press'),
        (0x609018FC, 'fa20100bddb0210500b020', 'rec_hdr_event'),
        (0x60953B54, '5c108002cddb108004', 'rec_hdr_admission'),
    ]
