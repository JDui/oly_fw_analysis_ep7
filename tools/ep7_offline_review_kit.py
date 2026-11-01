#!/usr/bin/env python3
"""Assemble existing E-P7 research package, stock reference and bounded evidence.

Reuses fishcu serialization; never compiles, runs the updater or creates an
updater-discovery layout. This tool cannot promote a candidate to installable.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_package import OUTPUT, check_candidate, check_components
from ep7_candidate_startup_sim import require
from oly_container import parse, reconstruct


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = 'EP7-STOCK-1100-REFERENCE.research.oly'
EVIDENCE = (
    'candidate-package-004.json',
    'candidate-updater-validation-observation.json',
    'candidate-updater-commit-sim.json',
    'candidate-sd-entry-sim.json',
    'candidate-static-kernel-sim.json',
    'candidate-selected-handoff-sim.json',
    'candidate-ui-editor-sim.json',
    'candidate-worker-job-sim.json',
    'candidate-residency-sim.json',
    'offline-candidate-004.json',
)

README = """# E-P7 基础H/L离线审查材料

状态：**NONINSTALLABLE，尚不可刷机。** 保留色轮编辑与照片处理；H/L易失，重启归零。

- `candidate/EP7HSL-NONINSTALLABLE.research.oly`：既有fishcu流程候选004，原样复制。
- `stock-reference/EP7-STOCK-1100-REFERENCE.research.oly`：fishcu无改动重建的五组件原厂参考。
- `evidence/`：10份已有报告；本工具没有重跑原生模拟或编译。
- `review.json`：当前材料核对及资格边界。
- `FLASH_BENCH_REVIEW.md`：有限台架验收计划，非当前安装操作说明。

两个容器均为111,017,984字节、E-P7型号1420、五组件及各自版本原样保留。
原厂参考不是本机备份，也不是已验证的独立救援镜像。当前没有验证过的备份/恢复条件。
三处启动前缀加载、代码/私有RAM归属、完整栈及硬件可见性尚未取得完整资格。
文件名只作操作隔离，不能阻止相机读取有效容器；不要改名复制到更新器。

封装复用 `patches/hsl/pen-f/build.py` 的思路与 `tools/oly_container.py`。
候选已经使用parse → replace_payload → reconstruct；原厂参考使用reconstruct(parse(stock))。
E-P7保留五组件，不采用PEN-F两组件输出、E122文件名或按键步骤。
仅原生加和及字节比较，无SHA。没有相机写入、tag或Release。
"""


def assemble(stock, decoded, candidate, package_path, prefix, out):
    # Verify the existing candidate against its actual ELF/declared edits. This
    # is input selection for the kit, not another build or native CPU test.
    data, build, span_count = check_candidate(decoded, candidate, prefix)
    raw = stock.read_bytes()
    original = parse(raw)
    check_components(original)
    require(original[0].payload == decoded.read_bytes(), 'stock/decoded input differs')
    reference = reconstruct(original)
    require(reference == raw, 'fishcu stock reconstruction differs')
    packed = package_path.read_bytes()
    changed = parse(packed)
    check_components(changed)
    require(len(packed) == len(reference) == 111017984 and changed[0].payload == data,
            'existing package does not contain the reviewed final candidate')
    component_rows = []
    for before, after in zip(original, changed):
        end = before.offset+len(before.payload)+64
        unchanged = raw[before.offset:end] == packed[before.offset:end]
        require(before.header == after.header and before.trailer[:28] == after.trailer[:28],
                'component metadata changed')
        require((before.index == 0) != unchanged, 'candidate component change scope differs')
        component_rows.append(dict(kind=hex(before.kind), address=hex(before.address),
            header_build=hex(struct.unpack_from('<H', before.header, 16)[0]),
            payload_bytes=len(before.payload), model_bytes=before.header[2:4].hex(),
            unchanged_between_candidate_and_stock=unchanged, native_additive_checksums_valid=True))

    snapshots = {}
    for name in EVIDENCE:
        blob = (ROOT/'research/ep7'/name).read_bytes()
        report = json.loads(blob)
        if 'candidate_build_revision' in report:
            require(report['candidate_build_revision'] == build['source_revision'],
                    'evidence belongs to a different candidate: '+name)
        require(report.get('installable') is not True and report.get('hardware_executed') is not True,
                'unexpected qualification claim in evidence: '+name)
        snapshots[name] = blob
    destination = out.resolve()
    require(not destination.exists(), 'review-kit output must be new')
    require(not any(p.upper() == 'DCOLYMP' for p in destination.parts), 'updater discovery output forbidden')
    for source in (stock, decoded, candidate, package_path):
        path = source.resolve()
        require(destination != path and path not in destination.parents and destination not in path.parents,
                'output overlaps an input')
    out.mkdir(parents=True)
    bench = (ROOT/'docs/ep7/FLASH_BENCH_REVIEW.md').read_text(encoding='utf-8')
    bench = bench.replace('(CANDIDATE_UPDATER_SIM.md)',
                          '(evidence/candidate-updater-validation-observation.json)')
    bench = bench.replace('[离线材料工具](../../tools/ep7_offline_review_kit.py)',
                          '`tools/ep7_offline_review_kit.py`（源码仓库）')
    bench = bench.replace('(../../research/ep7/offline-review-kit-004.json)', '(review.json)')
    files = {f'candidate/{OUTPUT}': packed, f'stock-reference/{REFERENCE}': reference,
             'README.md': README.encode('utf-8'),
             'FLASH_BENCH_REVIEW.md': bench.encode('utf-8')}
    files.update({f'evidence/{name}': blob for name, blob in snapshots.items()})
    written = []
    for relative, content in files.items():
        target = out/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        require(target.read_bytes() == content, 'disk byte readback differs: '+relative)
        written.append(dict(path=relative, bytes=len(content), byte_readback_equal=True))
    result = dict(scope=__doc__, status='passed', candidate_build_revision=build['source_revision'],
        candidate_file=f'candidate/{OUTPUT}', stock_reference_file=f'stock-reference/{REFERENCE}',
        candidate_bytes=len(packed), stock_reference_bytes=len(reference),
        firmware_bytes=len(packed)+len(reference), candidate_write_spans=span_count,
        components=component_rows, files=written,
        stock_reconstructed_with_fishcu=True, stock_reference_equal_to_original_input=True,
        candidate_copied_without_repacking=True, candidate_matches_actual_ELF_and_patch_recipes=True,
        evidence_snapshots=len(snapshots), existing_native_tests_reexecuted=False,
        native_updater_mode2_evidence_has_missing_detailed_report=True,
        filename_is_not_a_device_enforced_block=True, updater_discovery_layout_created=False,
        hash_checks_performed=False, firmware_recompiled=False, source_firmware_written=False,
        hardware_executed=False, installation_authorized=False, installable=False,
        verified_device_backup_available=False, independent_recovery_proven=False,
        qualification=dict(container='passed_offline',
            updater='conditional_native_validation_and_trapped_routes',
            hl_function='conditional_native_seams_with_explicit_models',
            startup_residency='unqualified_prefix_and_ownership_dependencies',
            physical_update_entry='unverified', full_task_irq_stack_bounds='unknown',
            physical_display_and_photo='not_executed', recovery='not_verified'),
        outstanding_inputs=[
            'E-P7 prefix-loader, cold pool/guard ownership and cache/secondary startup evidence.',
            'Complete task/IRQ resource qualification and CPU2 reduced-pool capacity.',
            'Verified device-specific backup and an independent recovery route covering main-startup failure.',
            'Physical update-entry and subsequent device acceptance under separate camera-operation authorization.'])
    output = json.dumps(result, indent=2)+'\n'
    (out/'review.json').write_text(output, encoding='utf-8')
    require((out/'review.json').read_text(encoding='utf-8') == output, 'review report readback differs')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--decoded-stock', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(assemble(args.stock, args.decoded_stock, args.candidate,
                              args.package, args.tool_prefix, args.out), indent=2))
