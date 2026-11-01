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


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False)+'\n').encode('utf-8')


def deliver(stock, decoded, candidate, validated_package, native_report, prefix, out, release='005'):
    require(release in ('005','006'), 'unsupported experimental release')
    archive_name = f'EP7HSL-{release}-EXPERIMENTAL-SD.zip'
    guide = ROOT/f'docs/ep7/EXPERIMENTAL_SD_{release}.md'
    evidence_names = tuple(name.replace('005',release) for name in EVIDENCE)
    if release == '006':
        evidence_names += ('candidate-006-boot-guard.json',)
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
        # 006 intentionally avoids repeating the unchanged 686M-instruction
        # decoder. package() below checks every NEW component additive sum and
        # byte roundtrip; this run executes native mode1 routing/error stops on
        # the actual fishcu-decoded 006 buffers. Do not relabel it as mode2.
        require(release=='006' and native['commit_only'] is True and
                native['native_validation']['executed'] is False and
                native['native_validation']['native_validation_claim'] is False,
                'only 006 permits explicitly recorded host-validation/native-routing evidence')
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
                'H/L is volatile. Four COLOR profiles and the existing CPU processing path are included; hardware display/photo acceptance is outstanding.',
                'Native updater execution uses modeled console, service and flash backends; no physical erase/program/readback is performed.',
                ('Full native mode2 decoding passed for this exact package.' if full_native else
                 '006 uses fishcu host decoding/checksums and native mode1 routing; full native mode2 decoding was not repeated.')])
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
    parser.add_argument('--release',choices=('005','006'),default='005')
    args = parser.parse_args()
    print(json.dumps(deliver(args.stock,args.decoded_stock,args.candidate,args.validated_package,
        args.native_report,args.tool_prefix,args.out,args.release),indent=2))
