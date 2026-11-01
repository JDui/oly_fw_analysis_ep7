#!/usr/bin/env python3
"""Wrap an E-P7 offline candidate using the inherited fishcu container workflow.

Produces a research container only. Its valid format does not establish updater
acceptance, bootability, recoverability, or permission to install it.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import candidate_inputs, require
from ep7_installation_manifest import BASE, inspect_stock
from ep7_offline_candidate import CODE, ELF_NAME, replacement, sections
from oly_container import parse, reconstruct, replace_payload


# E-P7 1100 component order, container addresses, sizes and individual builds.
# These are container coordinates, not MN103 execution addresses.
COMPONENTS = (
    (0x100, 0x406a0000, 26214336, 0x1100),
    (0x101, 0x421a0000, 26214336, 0x0100),
    (0x106, 0x43aa0000, 45219776, 0x0100),
    (0x10e, 0x00000000, 262080, 0x0001),
    (0x102, 0x467e0000, 13107136, 0x0100),
)
OUTPUT = 'EP7HSL-NONINSTALLABLE.research.oly'


def check_components(blocks):
    require(len(blocks) == len(COMPONENTS), 'E-P7 requires all five reviewed components')
    for block, expected in zip(blocks, COMPONENTS):
        require(block.header[2:4] == bytes.fromhex('1420'), 'E-P7 model bytes differ')
        actual = (block.kind, block.address, len(block.payload),
                  struct.unpack_from('<H', block.header, 16)[0])
        require(actual == expected, 'E-P7 component order/address/size/build differs')


def check_candidate(stock_decoded, directory, prefix):
    """Reuse the actual ELF checks and installation recipes; do not recompile."""
    data, addresses, build = candidate_inputs(directory, prefix)
    require(build['installable'] is False and build['installation_authorized'] is False,
            'this entry point only packages unqualified offline candidates')
    manifest = inspect_stock(stock_decoded)
    original = stock_decoded.read_bytes()
    expected = bytearray(original)
    spans = []
    linked = sections(prefix, directory/ELF_NAME)
    for index, (low, high) in enumerate(CODE):
        section = next(row for row in build['layout'] if row['section'] == f'.ep7_code{index}')
        actual = next(row for row in linked if row['name'] == f'.ep7_code{index}')
        end = low + actual['size']
        require(int(section['start'], 16) == low == actual['address'] and
                section['bytes'] == actual['size'] and int(section['end'], 16) == end and end <= high and
                original[low-BASE:high-BASE] == b'\xff' * (high-low),
                'reviewed candidate code region differs')
        expected[low-BASE:end-BASE] = data[low-BASE:end-BASE]
        spans.append((low, end))
    symbols = {name: dict(address=address) for name, address in addresses.items()}
    for row in manifest['patches']:
        value, _ = replacement(row, symbols)
        start = int(row['site'], 16)
        expected[start-BASE:start-BASE+len(value)] = value
        spans.append((start, start+len(value)))
    spans.sort()
    require(all(left[1] <= right[0] for left, right in zip(spans, spans[1:])),
            'candidate write spans overlap')
    require(bytes(expected) == data, 'candidate differs from the linked code and declared patches')
    return data, build, len(spans)


def package(stock, stock_decoded, directory, prefix, out):
    raw = stock.read_bytes()
    blocks = parse(raw)
    check_components(blocks)
    require(len(raw) == 111017984 and blocks[0].payload == stock_decoded.read_bytes(),
            'decoded stock is not the main component of this E-P7 source')
    require(reconstruct(blocks) == raw, 'unchanged fishcu container round trip differs')
    candidate, build, span_count = check_candidate(stock_decoded, directory, prefix)
    changed = [replace_payload(blocks[0], candidate), *blocks[1:]]
    packed = reconstruct(changed)
    verified = parse(packed)  # Checks the native additive checksum of every component.
    check_components(verified)
    require(len(packed) == len(raw) and verified[0].payload == candidate,
            'packed candidate size or decoded payload differs')
    rows = []
    for before, after in zip(blocks, verified):
        require(after.offset == before.offset and after.header == before.header and
                after.trailer[:28] == before.trailer[:28], 'component metadata changed')
        end = before.offset + len(before.payload) + 64
        unchanged = packed[before.offset:end] == raw[before.offset:end]
        require(before.index == 0 or unchanged, 'an unmodified component changed')
        rows.append(dict(index=before.index, kind=hex(before.kind),
            container_address=hex(before.address), offset=before.offset,
            payload_bytes=len(before.payload), model_bytes=after.header[2:4].hex(),
            header_build=hex(struct.unpack_from('<H', after.header, 16)[0]),
            metadata_preserved=True, original_encoded_component_unchanged=unchanged,
            additive_checksum_valid=True))
    require(not rows[0]['original_encoded_component_unchanged'], 'no candidate changes were packaged')
    # Keep the artifact away from both inputs, and never overwrite an older run.
    destination = out.resolve()
    for source in (stock.resolve(), stock_decoded.resolve(), directory.resolve()):
        require(destination != source and source not in destination.parents and
                destination not in source.parents, 'output overlaps a source path')
    require(not any(part.upper() == 'DCOLYMP' for part in destination.parts),
            'research output cannot use an updater discovery directory')
    out.mkdir(parents=True, exist_ok=False)
    warning = ('NON-INSTALLABLE E-P7 HSL RESEARCH CONTAINER\n\n'
        'This file uses the original Olympus container format and native checksums.\n'
        'The filename is an operational separation, not a device-enforced rejection.\n'
        'Do not rename/copy it into an updater or use it to flash a camera.\n'
        'No E-P7 updater acceptance, full boot/runtime, or independent recovery is proven.\n'
        'This entry point cannot promote an artifact to installable.\n\n' +
        '\n'.join('- ' + item for item in build['limits']) + '\n')
    (out/'NONINSTALLABLE.txt').write_text(warning, encoding='utf-8')
    artifact = out/OUTPUT
    artifact.write_bytes(packed)
    require(artifact.read_bytes() == packed, 'research container disk readback differs')
    report = dict(scope=__doc__, status='passed', package=OUTPUT,
        package_bytes=len(packed), candidate_build_revision=build['source_revision'],
        workflow_reference='patches/hsl/pen-f/build.py: parse -> replace_payload -> reconstruct',
        container_implementation='tools/oly_container.py', component_count=len(rows), components=rows,
        original_container_roundtrip_equal=True, candidate_matches_linked_ELF_and_patch_recipes=True,
        candidate_write_spans=span_count, decoded_main_equal_to_candidate=True,
        package_disk_readback_equal=True, updater_discovery_layout_created=False,
        native_checksum_algorithm_used=True, firmware_updater_executed=False,
        hash_checks_performed=False, source_firmware_written=False,
        installation_authorized=False, installable=False, hardware_executed=False,
        independent_recovery_proven=False, filename_is_not_an_enforced_installation_block=True,
        limits=build['limits'] + [
            'All five E-P7 components and their individual build fields are retained. '
            'No PEN-F E122 name, two-component assumption or restoration claim is used.',
            'Host-side container validation is not the complete E-P7 updater validation/write path.',
            'The existing official input is not a verified device backup or independent rescue image.'])
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--decoded-stock', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.stock, args.decoded_stock, args.candidate,
                             args.tool_prefix, args.out), indent=2))
