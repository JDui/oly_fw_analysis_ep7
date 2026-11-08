#!/usr/bin/env python3
"""Deliver a numbered highlight release using existing loader/updater tools.

Validates the two-ELF overlay explicitly instead of pretending it has the older
single-ELF manifest. No SHA, camera access or full native mode2 decode.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from ep7_candidate_package import check_components
from ep7_candidate_residency_sim import loaded_state, placement
from ep7_candidate_startup_sim import require
from ep7_candidate_updater_sim import inspect as updater_inspect
from ep7_highlight_candidate import build as build_highlight
from ep7_installation_manifest import BASE, load_region
from ep7_offline_candidate import RAM_START, RAM_BYTES, RAM_IMAGE_START, sections, symbols
from oly_container import parse, reconstruct, replace_payload

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False)+'\n').encode('utf-8')


def elf_bytes(prefix, elf, section):
    with tempfile.TemporaryDirectory(prefix='ep7hl-elf-') as temp:
        out = Path(temp)/'section.bin'
        subprocess.run([prefix+'objcopy', '-O', 'binary', '-j', section, str(elf), str(out)], check=True)
        return out.read_bytes()


def audit_overlay(baseline, candidate, tested, reference_package, stock, prefix, *,
                  strategy='highlight_mapping_only'):
    old = read_json(baseline/'report.json')
    report = read_json(candidate/'report.json')
    tested_report = read_json(tested/'report.json')
    require(report['strategy'] == tested_report['strategy'] == strategy,
            'candidate strategy differs from the requested package')
    data = (candidate/report['image']).read_bytes()
    require(data == (tested/tested_report['image']).read_bytes(),
            'fresh final build differs from the candidate covered by runtime probes')
    original = (baseline/'EP7HSL-NONINSTALLABLE.decoded-main.bin').read_bytes()
    reference = parse(reference_package.read_bytes())
    check_components(reference)
    require(reference[0].payload == original, '015 baseline differs from delivered reference')
    require(len(data) == len(original) == len(stock) == 26214336, 'decoded length changed')
    # Extra new source files are not retroactively part of 015. Verify each of
    # its recorded inputs without reinterpreting the old source inventory.
    for relative in old['source_snapshot']['paths']:
        saved = baseline/'source-snapshot'/relative
        require(saved.read_bytes() == (ROOT/relative).read_bytes(),
                'recorded 015 source changed: '+relative)
    old_elf = baseline/'EP7HSL-NONINSTALLABLE.elf'
    for row in old['layout']:
        address = int(row.get('load_address', row['start']), 16)
        content = elf_bytes(prefix, old_elf, row['section'])
        require(len(content) == row['bytes'] and
                original[address-BASE:address-BASE+len(content)] == content,
                '015 ELF section differs from baseline')
    elf = candidate/report['image'].replace('.decoded-main.bin', '.elf')
    actual = {row['name']: row for row in sections(prefix, elf) if row['size'] and 'ALLOC' in row['flags']}
    require(set(actual) == {'.ep7dr_code', '.ep7dr_state'}, 'unexpected overlay section')
    symbols(prefix, elf)  # Also rejects unresolved symbols; no hash calculation.
    code = elf_bytes(prefix, elf, '.ep7dr_code')
    address = int(report['code']['address'], 16)
    require(actual['.ep7dr_code']['address'] == address and len(code) == report['code']['bytes'],
            'overlay code extent differs')
    expected = bytearray(original)
    require(expected[address-BASE:address-BASE+len(code)] == b'\xff'*len(code), 'overlay code collision')
    expected[address-BASE:address-BASE+len(code)] = code
    state = actual['.ep7dr_state']
    old_symbols = read_json(baseline/'symbols.json')
    require('CONTENTS' not in state['flags'] and state['address'] == int(report['state']['address'],16) and
            state['size'] == report['state']['bytes'] and
            state['address'] >= int(old_symbols['__ep7_bss_end']['address'],16) and
            state['address']+state['size'] <= RAM_START+RAM_BYTES,
            'state overlaps 015 or exceeds the already initialized reservation')
    require(data[RAM_IMAGE_START-BASE:RAM_IMAGE_START-BASE+RAM_BYTES] == bytes(RAM_BYTES),
            'private image initialization changed')
    for row in report['patches']:
        index = int(row['site'],16)-BASE
        before, after = bytes.fromhex(row['before']), bytes.fromhex(row['after'])
        require(len(before) == len(after) and expected[index:index+len(before)] == before,
                'overlay preimage differs at '+row['site'])
        expected[index:index+len(after)] = after
    require(bytes(expected) == data, 'bytes outside the declared overlay changed')
    require(data[:0x60030000-BASE] == stock[:0x60030000-BASE], 'boot prefix changed')

    # A normalized placement view describes the composition of both ELFs.
    # The early code0 interval includes the original 015 code, FF gap and new
    # code. No original build flags or evidence reports are rewritten.
    view = copy.deepcopy(old)
    first = view['layout'][0]
    require(first['section'] == '.ep7_code0' and int(first['end'],16) <= address,
            '015 code overlaps highlight code')
    first['end'] = hex(address+len(code))
    first['bytes'] = address+len(code)-int(first['start'],16)
    require(address+len(code) <= RAM_IMAGE_START, 'code overlaps state image')
    private = next(row for row in view['layout'] if row['section'] == '.ep7_private')
    private['bss_bytes'] = state['address']+state['size']-RAM_START-4
    private['remaining'] = RAM_BYTES-4-private['bss_bytes']
    patches = {row['site']: row for row in view['patches']}
    for row in report['patches']:
        site, size = int(row['site'],16), len(bytes.fromhex(row['after']))
        patches[row['site']] = dict(site=row['site'], bytes=size, kind=strategy,
                                    load_stage=load_region(site,size)['stage'])
    view['patches'] = list(patches.values())
    view['patch_count'] = len(patches)
    layout = placement(data, stock, view)
    return data, report, dict(status='passed',
        baseline_reference_equal=True, baseline_elf_sections_equal=True,
        recorded_baseline_sources_equal=True, overlay_elf_equal=True,
        declared_overlay_equals_entire_final_image=True, final_equals_runtime_tested_image=True,
        runtime_tested_directory=str(tested), boot_prefix_unchanged=True,
        exposure_iso_gain_unchanged=report['exposure_iso_gain_unchanged'],
        layout=layout, hash_checks_performed=False, hardware_executed=False)


def runtime_evidence(args, build):
    directory = args.tested
    names = ('replay.json', 'settings-probe.json', 'ui-probe-core0.json',
             'ui-probe-core1.json', 'version-probe.json')
    if args.rec_hdr:
        directory = args.build.resolve()
        probes = (('rec-hdr-probe.py', 'rec-hdr-replay.json'),
                  ('highlight-version-probe.py', 'version-probe.json'))
        names = tuple(name for _, name in probes)
        for script, name in probes:
            print(f"{build['release']}: replaying {script} on the final build", flush=True)
            subprocess.run([sys.executable, '-B', str(ROOT/'research/ep7'/script),
                            '--candidate', str(directory), '--engine', str(args.engine.resolve()),
                            '--out', str(directory/name)], check=True, stdout=subprocess.DEVNULL)

    evidence = {}
    for name in names:
        blob = (directory/name).read_bytes()
        result = json.loads(blob)
        require(result['status'] == 'passed' and result['hash_checks_performed'] is False,
                'runtime evidence failed: '+name)
        if name == 'version-probe.json':
            require(result['displayed_body_version'] == build['displayed_body_version'],
                    'tested BODY version differs')
        evidence['evidence/'+name] = blob
    return evidence


def deliver(args):
    tested = read_json(args.tested/'report.json')
    release = tested['release']
    require(len(release)==3 and release.isascii() and release.isdigit(), 'bad release')
    require(release not in ('024', '025', '026'), '024 through 026 have known Rec HDR failures')
    require(args.rec_hdr or release != '027', 'release 027 needs --rec-hdr')
    require(not args.rec_hdr or release >= '027', 'Rec HDR SD packaging requires 027 or later')
    strategy = 'rec_hdr_lab' if args.rec_hdr else 'highlight_mapping_only'
    require(tested['strategy'] == strategy, 'candidate strategy differs from the requested package')
    out = args.out.resolve()
    require(not out.exists(), 'delivery output must be new')
    require(not args.build.exists(), 'final build output must be new')
    raw = args.stock.read_bytes()
    blocks = parse(raw)
    check_components(blocks)
    stock = args.decoded_stock.read_bytes()
    require(blocks[0].payload == stock and len(raw) == 111017984 and reconstruct(blocks) == raw,
            'stock source/decoded main/container roundtrip differs')
    print(f'{release}: building {strategy} candidate', flush=True)
    build_highlight(args.prefix, args.baseline.resolve(), args.build.resolve(), release,
                    rec_hdr=args.rec_hdr)
    data, build, audit = audit_overlay(args.baseline, args.build, args.tested,
                                      args.reference, stock, args.prefix, strategy=strategy)
    runtime = runtime_evidence(args, build)
    print(f'{release}: checking original loader with poisoned destination memory', flush=True)
    residency = dict(status='passed', original_loader=loaded_state(data,args.engine),
                     placement=audit['layout'], hash_checks_performed=False, hardware_executed=False)
    print(f'{release}: reconstructing and reading back all five components', flush=True)
    packed = reconstruct([replace_payload(blocks[0], data), *blocks[1:]])
    checked = parse(packed)
    check_components(checked)
    require(len(packed) == len(raw) and checked[0].payload == data, 'package payload differs')
    for before, after in zip(blocks,checked):
        require(before.header == after.header and before.trailer[:28] == after.trailer[:28],
                'component metadata changed')
        if before.index:
            start,end = before.offset,before.offset+len(before.payload)+64
            require(raw[start:end] == packed[start:end], 'non-main component changed')
    # Keep this intermediary outside SD discovery until routing completes.
    intermediary = args.build/f'EP7HL-{release}.research.oly'
    intermediary.write_bytes(packed)
    require(intermediary.read_bytes() == packed, 'container disk readback failed')
    print(f'{release}: executing native mode1 routing with every physical write trapped', flush=True)
    native = updater_inspect(intermediary,args.decoded_stock,args.engine,commit_only=True)
    require(native['status'] == 'passed' and native['physical_writes_executed'] is False and
            native['trapped_commit']['result'] == '0x0' and
            len(native['trapped_commit']['write_requests']) == 5 and
            native['backend_failure']['result'] == '0x3102', 'updater routing failed')
    evidence = {
        'evidence/overlay-audit.json': json_bytes(audit),
        'evidence/residency.json': json_bytes(residency),
        'evidence/native-updater.json': json_bytes(native),
        'evidence/build.json': json_bytes(build),
        **runtime,
    }
    inputs = [path for path in (ROOT/'prototypes/ep7_volatile_hl/native_single_dr').iterdir()
              if path.suffix in ('.h','.c','.s')]
    inputs += [ROOT/'tools'/name for name in ('ep7_highlight_candidate.py','ep7_highlight_gamma.py',
               'ep7_single_dr_candidate.py','ep7_single_dr_gamma.py','ep7_highlight_sd_package.py')]
    inputs += list((ROOT/'prototypes/ep7_volatile_hl/target/include').rglob('*.h'))
    inputs += [ROOT/'research/ep7'/name for name in ('highlight-candidate-probe.py',
        'highlight-version-probe.py','single-dr-curve-ui-probe.py',
        'single-dr-settings-candidate-probe.py')]
    if args.rec_hdr:
        inputs += [ROOT/'tools/ep7_rec_hdr_patch.py', ROOT/'research/ep7/rec-hdr-probe.py']
    snapshot = args.build/'highlight-source-snapshot'
    for source in inputs:
        target = snapshot/source.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source.read_bytes())
        require(target.read_bytes() == source.read_bytes(), 'source snapshot differs')
    manifest = dict(status='passed', release=release, camera='E-P7', base='1.1 / build1100',
        displayed_body_version=build['displayed_body_version'],
        strategy=strategy, manual_sd_test_package_ready=True,
        install_file='install/DCOLYMP/E1429999.BIN', stock_return_file='restore-stock/DCOLYMP/E1429999.BIN',
        bytes_per_firmware=len(packed), source_build=str(args.build),
        source_snapshot=str(snapshot), baseline='015', retained_015_HSL=True,
        exposure_iso_gain_unchanged=build['exposure_iso_gain_unchanged'],
        host_all_component_additive_checksums_passed=True, native_mode1_routing_passed=True,
        native_full_mode2_decode_repeated=False, final_equals_runtime_tested_image=True,
        camera_write_executed=False, physical_boot_verified=False, physical_save_verified=False,
        JPEG_effect_hardware_verified=False, independent_recovery_proven=False,
        hash_checks_performed=False,
        limits=['Experimental manual SD artifact; no physical camera acceptance.',
                'Native storage/backend/service successes are model boundaries; actual writes are trapped.',
                'The stock return file needs a working updater and is not independent recovery.',
                'Curve strength does not establish a measured EV or dynamic range improvement.'])
    if args.rec_hdr:
        manifest['rec_hdr'] = {key: build['rec_hdr'][key] for key in
                               ('button_sid', 'function', 'native_recipe', 'frames', 'shutter', 'scope')}
        manifest['rec_hdr']['camera_capture_verified'] = False
        manifest['limits'].append('Rec HDR replay models UI services, RTOS, heap and transport. '
                                  'Full exposure, composition and cleanup on camera await validation.')
    else:
        manifest['raw_capture_path_unchanged'] = True
    files = {manifest['install_file']:packed, manifest['stock_return_file']:raw,
             'README.md':(ROOT/f'docs/ep7/EXPERIMENTAL_SD_{release}.md').read_bytes(),
             'manifest.json':json_bytes(manifest), **evidence}
    out.mkdir(parents=True)
    for name,blob in files.items():
        target = out/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(blob)
        require(target.read_bytes() == blob, 'delivery readback failed: '+name)
    archive = out/f'EP7HSL-{release}-EXPERIMENTAL-SD.zip'
    print(f'{release}: writing ZIP with installation and original stock return files', flush=True)
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as bundle:
        for name in files:
            bundle.write(out/name,name)
    with zipfile.ZipFile(archive) as bundle:
        require(set(bundle.namelist()) == set(files), 'ZIP inventory differs')
        for name,blob in files.items():
            require(bundle.read(name) == blob, 'ZIP CRC or byte readback differs: '+name)
    result = dict(status='passed', archive=str(archive), archive_bytes=archive.stat().st_size,
                  file_count=len(files), zip_crc_and_byte_readback_passed=True,
                  firmware_bytes=len(packed), native_mode1_routing_passed=True,
                  hardware_validated=False, camera_write_executed=False, hash_checks_performed=False)
    (out/'delivery-check.json').write_bytes(json_bytes(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('stock','decoded-stock','baseline','tested','reference','build','out','engine'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--prefix',required=True)
    parser.add_argument('--rec-hdr', action='store_true', help='package a corrected Rec HDR candidate')
    args = parser.parse_args()
    print(json.dumps(deliver(args),indent=2))
