#!/usr/bin/env python3
"""Deliver a user-requested experimental E-P7 SD package and stock return file.

Reuses the checked candidate packer and explicitly recorded validation scope.
Package readiness describes the SD artifact, not physical boot or recovery.
No card, camera, firmware-service or remote release is accessed.
"""
import argparse
import json
from pathlib import Path
import tempfile
import zipfile

from ep7_candidate_package import OUTPUT, package
from ep7_candidate_startup_sim import require
from ep7_offline_candidate import IMAGE_NAME

ROOT = Path(__file__).resolve().parents[1]
INSTALL = 'install/DCOLYMP/E1429999.BIN'
RESTORE = 'restore-stock/DCOLYMP/E1429999.BIN'
EVIDENCE = ('candidate-005-residency.json', 'candidate-005-ui-editor.json',
            'candidate-005-worker-job.json', 'candidate-005-sd-isolation.json')
EVIDENCE_008 = ('candidate-008-worker-legacy.json', 'candidate-008-worker-job.json',
                'candidate-008-residency.json')
EVIDENCE_009 = ('candidate-009-cold-startup.json', 'candidate-009-worker-job.json',
                'candidate-009-residency.json')
EVIDENCE_010 = ('candidate-010-terminal-signal.json', 'candidate-010-residency.json')


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False)+'\n').encode('utf-8')


def deliver(stock, decoded, candidate, validated_package, native_report, prefix, out, release='005'):
    require(release in ('005','006','008','009','010','011','012','013','014'), 'unsupported experimental release')
    archive_name = f'EP7HSL-{release}-EXPERIMENTAL-SD.zip'
    guide = ROOT/f'docs/ep7/EXPERIMENTAL_SD_{release}.md'
    evidence_names = tuple(name.replace('005',release) for name in EVIDENCE)
    if release == '006':
        evidence_names += ('candidate-006-boot-guard.json',)
    elif release == '008':
        evidence_names = EVIDENCE_008
    elif release == '009':
        evidence_names = EVIDENCE_009
    elif release == '010':
        evidence_names = EVIDENCE_010
    elif release == '011':
        evidence_names = ('candidate-011-native-hsl.json', 'candidate-011-residency.json')
    elif release in ('012','013','014'):
        evidence_names = (f'candidate-{release}-native-hsl.json', f'candidate-{release}-residency.json')
    destination = out.resolve()
    require(not destination.exists(), 'SD delivery output must be new')
    for source in (stock, decoded, candidate, validated_package, native_report):
        source = source.resolve()
        require(destination != source and source not in destination.parents and
                destination not in source.parents, 'output overlaps an input')
    native_blob = native_report.read_bytes()
    native = json.loads(native_blob.decode('utf-8-sig'))
    require(native['status']=='passed' and native['physical_writes_executed'] is False and
            native['hash_checks_performed'] is False,
            'the actual final package needs passed native routing evidence')
    full_native = native['full_native_decode_and_checksum'] is True
    if full_native:
        require(native['native_decoded_bytes_equal_to_fishcu'] is True and
                native['native_validation']['returned'] and native['native_validation']['result']=='0x0' and
                not native['native_validation']['write_requests'], 'native full validation did not pass')
    else:
        # Later releases avoid repeating the unchanged 686M-instruction
        # decoder. package() below checks every NEW component additive sum and
        # byte roundtrip; this run executes native mode1 routing/error stops on
        # the actual fishcu-decoded candidate buffers. Do not relabel it as mode2.
        require(release in ('006','008','009','010','011','012','013','014') and native['commit_only'] is True and
                native['native_validation']['executed'] is False and
                native['native_validation']['native_validation_claim'] is False,
                'release does not permit recorded host-validation/native-routing evidence')
    require(Path(native['input_package']).resolve()==validated_package.resolve(),
            'native report identifies another input package')
    require(native['trapped_commit']['result']=='0x0' and
            len(native['trapped_commit']['write_requests'])==5 and
            native['backend_failure']['result']=='0x3102', 'native write routing did not pass')

    # The existing packer performs ELF/manifest, five-component, metadata,
    # native checksum and byte-readback checks. Do not implement a second one.
    with tempfile.TemporaryDirectory(prefix='ep7-sd-package-') as tmp:
        scratch = Path(tmp)/'checked'
        checked = package(stock, decoded, candidate, prefix, scratch)
        install_bytes = (scratch/OUTPUT).read_bytes()
    require(install_bytes==validated_package.read_bytes(),
            'relinked package differs from the one executed by the native updater')
    reference = stock.read_bytes()
    require(len(install_bytes)==len(reference)==native['package_bytes']==111017984,
            'delivery size differs')
    # package() already proves reconstruct(parse(stock)) is exactly stock.
    # Keep that byte-identical stock return file, avoiding a redundant packer.
    evidence = {}
    for name in evidence_names:
        blob = (ROOT/'research/ep7'/name).read_bytes()
        report = json.loads(blob)
        require(report['status']=='passed' and report['hash_checks_performed'] is False,
                'candidate evidence did not pass: '+name)
        evidence['evidence/'+name] = blob
    build = json.loads((candidate/'report.json').read_text())
    previous = (json.loads((ROOT/'research/ep7/offline-candidate-005.json').read_text())
                if release == '005' else build)
    require(all(json.loads(blob)['candidate_build_revision']==previous['source_revision']
                for blob in evidence.values()), 'candidate evidence revisions differ')
    if release in ('008','009','010','011','012','013','014'):
        # Dirty builds may share a baseline revision. The runner must attach
        # the actual build report/path when executing each final candidate
        # probe; a matching baseline alone is not evidence of identical input.
        for name, blob in evidence.items():
            runtime = json.loads(blob)
            require(Path(runtime['candidate_directory']).resolve()==candidate.resolve() and
                    runtime['candidate_build_report']==build,
                    'runtime evidence does not identify this final candidate: '+name)
    # Runtime evidence refers to candidate005; this fresh link must be exactly
    # that candidate. It is not promoted by changing old report flags.
    if release == '005':
        old_main = ROOT/'generated/ep7/offline-candidate-005-r2'/IMAGE_NAME
        require((candidate/IMAGE_NAME).read_bytes()==old_main.read_bytes(),
                'fresh link is not the candidate covered by runtime evidence')
    require(build['boot_prefix_unchanged'] is True and build['cpu2_pool_capacity']==32,
            'experimental package must retain stock boot prefix and pool capacity')

    report = dict(status='passed', artifact_type='experimental_sd_test_package',
        manual_sd_test_package_ready=True,
        package_creation_authorization='User explicitly requested: 编译可刷机固件',
        release=release, camera_model='E-P7', model_bytes='1420', base_firmware='1.1 / build1100',
        install_file=INSTALL, stock_return_file=RESTORE, bytes_per_firmware=len(install_bytes),
        source_revision=build['source_revision'], runtime_evidence_revision=previous['source_revision'],
        source_revision_is_baseline=build.get('source_revision_is_baseline',False),
        source_tree_dirty=build.get('source_tree_dirty',False),
        source_changes_from_baseline=build.get('source_changes_from_baseline',[]),
        source_snapshot_present='source_snapshot' in build,
        source_snapshot_comparison=build.get('source_snapshot',{}).get('comparison'),
        source_snapshot_build_directory=(str(candidate.resolve()/'source-snapshot')
                                         if 'source_snapshot' in build else None),
        source_snapshot_included_in_sd_archive=False,
        runtime_evidence_bound_to_final_build_report=release in ('008','009','010','011','012','013','014'),
        runtime_evidence_files=list(evidence_names),
        relinked_decoded_main_equal_to_runtime_tested_candidate=True,
        final_container_equal_to_native_routing_input=True,
        final_container_equal_to_native_validated_input=full_native,
        objects_reused=build['objects_reused'], patch_count=build['patch_count'],
        all_five_components_preserved=True, components=checked['components'],
        stock_return_equal_to_original_vendor_container=True,
        native_full_decode_and_checksum_passed=full_native,
        host_all_component_checksums_and_byte_roundtrip_passed=True,
        native_write_requests_trapped=len(native['trapped_commit']['write_requests']),
        native_backend_error_stop_passed=True, boot_prefix_unchanged=True,
        cpu2_pool_capacity=32, sd_filename='E1429999.BIN',
        sd_filename_basis='E-P7 native E142????BIN selection and highest-suffix probe',
        hardware_validated=False, physical_boot_trigger_verified=False,
        independent_recovery_proven=False, camera_write_executed=False,
        hash_checks_performed=False, vendor_inputs_written=False,
        archive=archive_name,
        limits=['Ready for manual experimental SD testing is an artifact status, not proven camera boot or recoverability.',
                'The user reported SD update and stock recovery on this E-P7 after the 005 incident; this candidate has not booted on hardware.',
                'The stock return file requires a functioning update path and is not an independent rescue image or device backup.',
                (f'{release} stores H/L in native ACTIVE part-1 settings and feeds image-owned snapshots; this candidate still requires physical acceptance.' if release in ('011','012','013','014') else
                 'H/L is volatile. Four COLOR profiles and the existing CPU processing path are included; hardware display/photo acceptance is outstanding.'),
                ('008 reruns only legacy-worker, worker-job and residency probes against the final candidate; GUI and SD-entry probes were not repeated.'
                 if release=='008' else
                 '009 reruns only cold-startup, worker-job and residency probes against the final candidate; full device boot, GUI and SD-entry probes were not executed.'
                 if release=='009' else
                 '010 checks terminal AF mode selection and residency only; it is a diagnostic successor to 009, not a curve-page or H/L fix. GUI/worker/device boot were not rerun.'
                 if release=='010' else 'Runtime probe scope and modeled boundaries are recorded in the included evidence.'),
                ('The recorded source revision is a baseline; uncommitted build inputs were captured and compared byte-for-byte against the local source snapshot.'
                 if build.get('source_tree_dirty') else 'The recorded source revision identifies the checked build inputs.'),
                'Native updater execution uses modeled console, service and flash backends; no physical erase/program/readback is performed.',
                ('Full native mode2 decoding passed for this exact package.' if full_native else
                 f'{release} uses fishcu host decoding/checksums and native mode1 routing; full native mode2 decoding was not repeated.')])
    if release == '010':
        report.update(artifact_type='diagnostic_sd_test_package', diagnostic_only=True,
            reported_ui_fault_fixed=False,
            terminal_af_modes={'owner_text_0x700':255, 'input_0xc00':100,
                               'mvc_content_model_viewer_gate':50, 'other':250})
    if release == '011':
        report.update(artifact_type='functional_sd_test_package', diagnostic_only=False,
            editor='native wheel; Delete S->L->H; native INFO/ALL and dial controls',
            H_L_storage='H1 in native ACTIVE part1; native banks own save/recall',
            value_range=[-5,5], old_GUI_extension_hooks_removed=22,
            curve_fault_hardware_verified=False)
    if release == '012':
        report.update(artifact_type='functional_sd_test_package', diagnostic_only=False,
            editor='native wheel; Delete S->L->H; native INFO/ALL and dial controls',
            axis_labels=['Sat','Lum','Hue'],
            H_L_storage='H1 in native ACTIVE part1; native banks own save/recall',
            H_L_transport='native image-owned snapshots and per-job 24-byte trailer',
            value_range=[-5,5], native_queue_and_task_paths_restored=True,
            reported_011_faults=['axis background without text','H/L preview unchanged',
                                'shutter freeze and JPEG without H/L effect'],
            display_hardware_verified=False, preview_hardware_verified=False,
            capture_fault_hardware_verified=False, JPEG_effect_hardware_verified=False)
    if release == '013':
        report.update(artifact_type='functional_sd_test_package',diagnostic_only=False,
            editor='native wheel; Delete S->L->H; native INFO/ALL and dial controls',
            axis_labels=['Sat','Lum','Hue'],axis_backdrop='compact native layer1 CLUT1 translucent black',
            category_exit_cleanup='native whole-root damage after owner observer updates',
            H_L_storage='H1 in native ACTIVE part1; native banks own save/recall',
            H_L_transport='capture/clone and forward compact converter to per-job 24-byte trailer',
            preceding_012_JPEG_effect_user_confirmed=True,
            value_range=[-5,5],native_queue_and_task_paths_restored=True,
            display_hardware_verified=False,preview_hardware_verified=False,
            JPEG_effect_hardware_verified=False)
    if release == '014':
        report.update(artifact_type='functional_sd_test_package',diagnostic_only=False,
            editor='native wheel; Delete S->L->H; native INFO/ALL and dial controls',
            axis_text='OSD text palette6/54: opaque white4, black outline/shadow16',
            axis_backdrop='native layer1 CLUT1 translucent black',
            H_L_storage='H1 in native ACTIVE part1; native banks own save/recall',
            H_L_transport='native five980-byte acquired owners and actual per-frame setter; capture/clone paths retained',
            retired_013_HDR_as_profile_schema=True,
            ordinary_and_borrowed_COLOR_output_covered=True,
            preceding_JPEG_effect_user_confirmed=True,value_range=[-5,5],
            native_queue_and_task_paths_restored=True,
            display_hardware_verified=False,preview_hardware_verified=False,
            JPEG_effect_hardware_verified=False)
    files = {INSTALL:install_bytes, RESTORE:reference,
             'README.md':guide.read_bytes(), 'manifest.json':json_bytes(report),
             'evidence/native-updater.json':json_bytes(native),
             'evidence/flash-build.json':(candidate/'report.json').read_bytes(), **evidence}
    out.mkdir(parents=True)
    for name, blob in files.items():
        path = out/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
        require(path.read_bytes()==blob, 'delivery readback differs: '+name)
    archive = out/archive_name
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=1) as zipped:
        for name in files:
            zipped.write(out/name,name)
    with zipfile.ZipFile(archive) as zipped:
        require(set(zipped.namelist())==set(files), 'archive file inventory differs')
        for name, blob in files.items():
            # ZIP read verifies CRC32; equality also checks the actual payload.
            require(zipped.read(name)==blob, 'archive readback differs: '+name)
    result = dict(status='passed', delivery=str(out), archive=archive_name,
        archive_bytes=archive.stat().st_size, file_count=len(files),
        file_readbacks_equal=True, zip_crc_and_contents_verified=True,
        native_updater_full_validation=full_native, native_commit_routing_passed=True,
        host_container_validation_passed=True, hardware_validated=False,
        camera_write_executed=False, hash_checks_performed=False)
    (out/'delivery-check.json').write_bytes(json_bytes(result))
    return result


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True)
    parser.add_argument('--decoded-stock',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--validated-package',type=Path,required=True)
    parser.add_argument('--native-report',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--release',choices=('005','006','008','009','010','011','012','013','014'),default='005')
    args = parser.parse_args()
    print(json.dumps(deliver(args.stock,args.decoded_stock,args.candidate,args.validated_package,
        args.native_report,args.tool_prefix,args.out,args.release),indent=2))
