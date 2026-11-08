#!/usr/bin/env python3
"""Build HDR200/400 from 015, optionally with the Rec HDR laboratory overlay."""
import argparse
import json
from pathlib import Path
import struct
import ep7_single_dr_candidate as builder
from ep7_highlight_gamma import target_table_source


def build(prefix, baseline, out, release=None, *, rec_hdr=False):
    if release is None:
        release = '030' if rec_hdr else '023'
    if len(release) != 3 or not release.isascii() or not release.isdigit():
        raise ValueError('release must be three ASCII digits')
    image = (baseline / builder.IMAGE_NAME).read_bytes()
    symbols = {k: int(v['address'], 16) for k, v in
               json.loads((baseline / 'symbols.json').read_text()).items()}
    recipe = builder.overlay_recipe()
    recipe.modules = ('settings', 'ui', 'highlight', 'highlight_gamma', 'version')
    recipe.defines = ['-DEP7DR_HIGHLIGHT_MAPPING', f'-DEP7HL_RELEASE_TEXT=u"1.1v{release}"']
    recipe.entry = 'ep7dr_gamma_bridge'
    recipe.strategy = 'highlight_mapping_only'
    recipe.stem = 'EP7HL-NONINSTALLABLE'
    recipe.native['ep7dr_stock_version_set_text_unresolved'] = 0x60d4c9df
    recipe.native['_ep7h_refresh'] = symbols['_ep7h_refresh']
    recipe.table_source = target_table_source
    recipe.calls = [row for row in recipe.calls if row[2] == 'ui_factory']
    recipe.calls += [
        (0x60d7f271, 'dd6ed7fcfff018', 'version_body', 0xf0, 24),
        (0x60d7f2cd, 'dd12d7fcfff018', 'version_body', 0xf0, 24),
    ]
    # Preserve each BODY value's right edge while giving seven characters
    # room in both 640- and 720-wide layouts. Accessory rectangles stay stock.
    for address, old_x, new_x, width in ((0x61041f5c,422,352,116),
                                        (0x61041f9c,373,311,108)):
        old=struct.pack('<8H',old_x,145,46,40,old_x+40,145,46,40)
        new=struct.pack('<8H',new_x,145,width,40,new_x+40,145,width,40)
        recipe.literals += [(address,old.hex(),new.hex())]
    recipe.jumps = [row for row in recipe.jumps
                    if row[2].startswith(('bank_', 'ui_')) or row[2] == 'gamma']
    # 622484fa is a persistent session latch, not a busy flag. Observe both
    # complete native routines, including callbacks outside the inner copy.
    recipe.jumps += [
        (0x602b35a4, '87fca9fa842462', 'bank_session_enter'),
        (0x602b36d7, '00fc82fa842462', 'bank_session_leave'),
    ]
    if rec_hdr:
        import ep7_rec_hdr_patch
        recipe.defines.append(f'-DEP7HL_REC_RELEASE_SUFFIX=u"{release}"')
        ep7_rec_hdr_patch.configure(recipe, image)
    # Reuse exact already-installed owner seams, including both converters.
    for bridge, helper in (
            ('capture_sample', 'capture_sample'), ('capture_clone', 'capture_clone'),
            ('capture_to_job', 'capture_to_job'), ('alternate_to_job', 'capture_to_job'),
            ('live_sample', 'live_sample'), ('live_to_job', 'live_to_job')):
        start = symbols[f'ep7h_{bridge}_bridge']
        end = min(address for address in symbols.values() if address > start)
        target = symbols[f'_ep7h_{helper}']
        matches = []
        for site in range(start, end - 6):
            expected = b'\xdd' + struct.pack('<i', target - site) + bytes(2)
            if image[site-builder.BASE:site-builder.BASE+7] == expected:
                matches.append((site, expected.hex(), helper, 0, 0))
        if len(matches) != 1:
            raise ValueError(f'expected one exact 015 {bridge} helper CALL')
        recipe.calls += matches
        recipe.native[f'ep7dr_015_{helper}'] = target
    output = builder.build(prefix, baseline, out, recipe=recipe)
    # No legacy exposure, capture-property or forced-error hooks may survive.
    report = json.loads((out / 'report.json').read_text())
    forbidden = {row[0] for row in LEGACY_CAPTURE_PATCHES}
    if any(int(row['site'], 16) in forbidden for row in report['patches']):
        raise ValueError('an exposure or gain-compensation hook leaked into rendering-only build')
    result = output.read_bytes()
    for site, before, *_ in LEGACY_CAPTURE_PATCHES:
        offset, size = site-builder.BASE, len(bytes.fromhex(before))
        if result[offset:offset+size] != image[offset:offset+size]:
            raise ValueError(f'legacy capture/gain path was altered at {site:#x}')
    report.update(exposure_iso_gain_unchanged=not rec_hdr, legacy_capture_hooks_installed=False,
                  hdr_unavailable_reason_codes=True,
                  persistent_session_latch_is_not_busy=True,
                  native_session_execution_observed=True,
                  supported_picture_modes='COLOR1-4', borrowed_rgb_tuple_supported=True,
                  hdr_pipeline_observation=True,
                  color_request_types=[0,16], split_request_rejection_codes=True,
                  highlight_shoulder_revision=3, rgb_variant_in_observations=True,
                  color_source_qualifies_operation=True,
                  color_refresh_after_hdr_edit=True, selector_bypass_observed=True,
                  release=release, displayed_body_version=f'1.1v{release}')
    if rec_hdr:
        report.update(rec_hdr=dict(button_sid=48, function=473, native_recipe='HDR1', frames=4,
                                   request='native single capture', shutter='selected single drive',
                                   scope='P/A/S/M', body_status_symbol='_ep7rec_status',
                                   installable=False))
    builder.save(out / 'report.json', report)
    return output


LEGACY_CAPTURE_PATCHES = [row for row in builder.CALLS + builder.JUMPS
                          if not row[2].startswith(('ui_', 'bank_')) and row[2] != 'gamma']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--release', help='BODY version suffix (023, or 030 with --rec-hdr)')
    parser.add_argument('--rec-hdr', action='store_true',
                        help='include the non-installable Rec HDR capture experiment')
    args = parser.parse_args()
    print(build(args.prefix, args.baseline.resolve(), args.out.resolve(), args.release,
                rec_hdr=args.rec_hdr))
