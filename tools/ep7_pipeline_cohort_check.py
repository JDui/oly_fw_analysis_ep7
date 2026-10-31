#!/usr/bin/env python3
"""Qualify the pipeline's complete declared CALL/frame/queue cohort, without installing it."""
import argparse
import json
import re
import struct
import subprocess
import tempfile
from pathlib import Path

from ep7_far_call_check import ROOT, validate_object, inspect as inspect_semantics
from ep7_descriptor_frames import FRAMES
from ep7_producer_scope import W as PRODUCER_W
from ep7_worker_scope import W as WORKER_W
from ep7_ack_frames import W as ACK_W
from ep7_descriptor_send_frames import W as SEND_W
from ep7_descriptor_receive_frames import W as RECEIVE_W
from ep7_descriptor_frames import W as FRAME_W

CORE = ROOT/'prototypes/ep7_volatile_hl'
NATIVE = CORE/'snapshot_transport/native'
BASE = 0x60020020


def declared_rows():
    source = (NATIVE/'cohort.c').read_text()
    symbols = dict(re.findall(r'extern const unsigned char (\w+)\[\] __asm__\("(\w+)"\);', source))
    calls = re.findall(r'\{(0x[0-9a-f]+),(\w+),(2|4),(0x[0-9a-f]+|0),(\d+)\}', source)
    calls = [(int(pc, 16), symbols[symbol], int(width), int(mask, 0), int(frame))
             for pc, symbol, width, mask, frame in calls]
    short = [(pc, symbol, mask, frame) for pc, symbol, width, mask, frame in calls if width == 2]
    asm = (NATIVE/'far_calls.s').read_text()
    rows = re.findall(r'^EP7_FAR_CALL ep7_pipeline_far_([0-9a-f]+),(\w+),(0x[0-9a-f]+),(0x[0-9a-f]+),(\d+)$', asm, re.M)
    actual = []
    for pc, target, resume, mask, frame in rows:
        if int(resume, 16) != int(pc, 16)+5:
            raise ValueError('pipeline veneer does not preserve original return PC')
        actual.append((int(pc, 16), target, int(mask, 0), int(frame)))
    if len(calls) != 16 or len(short) != 8 or actual != short:
        raise ValueError('pipeline CALL/veneer count or order differs')
    frames = [(int(pc, 16), int(value)) for pc, value in re.findall(
        r'\{(0x[0-9a-f]+),(-?\d+)\}', source.split('frames[]={', 1)[1].split('};', 1)[0])]
    words = [(int(pc, 16), int(value)) for pc, value in re.findall(
        r'\{(0x[0-9a-f]+),(\d+)\}', source.split('words[]={', 1)[1].split('};', 1)[0])]
    return calls, short, frames, words


def validate_pipeline_object(obj, prefix):
    return validate_object(obj, prefix, declared_rows()[1], '.text.ep7_pipeline_far_calls')


def inspect(decoded, reference, prefix):
    main = decoded.read_bytes()
    if len(main) != 26214336:
        raise ValueError('unsupported decoded main length')
    calls, short, frames, words = declared_rows()
    known = {}
    for source in [PRODUCER_W, WORKER_W, ACK_W, SEND_W, RECEIVE_W, FRAME_W]:
        for pc, value in source.items():
            if pc in known and known[pc] != value:
                raise ValueError('conflicting pre-existing instruction witness')
            known[pc] = value
    # Existing source-level witnesses supply original destination/save tuple.
    # The current input supplies the exact CALL width; no historical SHA entrypoint is run.
    call_report = []
    for pc, target, width, mask, frame in calls:
        mn, operands = known[pc]
        if mn != 'call':
            raise ValueError('pipeline CALL not covered by original witness')
        original, rest = operands.split(',', 1)
        saves, native_frame = rest.rsplit(',', 1)
        native_mask = sum({'d2':0x80, 'd3':0x40, 'a2':0x20, 'a3':0x10}[s]
                          for s in saves.strip('[]').split(',') if s)
        if (native_mask, int(native_frame)) != (mask, frame):
            raise ValueError('pipeline cohort disagrees with original frame')
        stock = bytes([0xcd if width == 2 else 0xdd]) + (int(original, 16)-pc).to_bytes(width, 'little', signed=True)+bytes([mask, frame])
        if main[pc-BASE:pc-BASE+len(stock)] != stock:
            raise ValueError('original pipeline CALL bytes differ at '+hex(pc))
        call_report.append(dict(site=hex(pc), original=original, bytes=len(stock), mask=hex(mask),
            frame=frame, adapter=target, original_resume=hex(pc+len(stock)),
            replacement='JMP32 to known veneer' if width == 2 else 'same-width CALL32'))
    expected_frames = []
    for _, _, _, local, _, alloc, free, *_ in FRAMES:
        expected_frames.append((alloc, -local-12))
        if free:
            expected_frames.append((free, local+12))
    if frames != expected_frames:
        raise ValueError('pipeline cohort differs from existing five-frame plan')
    frame_report = []
    for pc, value in frames:
        old = value+12 if value < 0 else value-12
        expected = b'\xfa\xfe'+old.to_bytes(2, 'little', signed=True)
        if main[pc-BASE:pc-BASE+4] != expected:
            raise ValueError('original stack adjustment differs at '+hex(pc))
        frame_report.append(dict(site=hex(pc), original=expected.hex(),
            proposed=(b'\xfa\xfe'+value.to_bytes(2, 'little', signed=True)).hex(), adjustment=value))
    expected_words = [(pc+offset, value) for pc in [0x6003b41c, 0x6003bb88, 0x6003b458]
                      for offset, value in [(8, 312), (12, 10112)]]
    if words != expected_words:
        raise ValueError('pipeline cohort queue fields differ from declared three-queue expansion')
    for pc, value in words:
        old = 300 if value == 312 else 9728
        if struct.unpack_from('<I', main, pc-BASE)[0] != old:
            raise ValueError('original queue configuration differs at '+hex(pc))
    ranges = sorted([(pc, pc+width+3) for pc, _, width, _, _ in calls]+
                    [(pc, pc+4) for pc, _ in frames+words])
    if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
        raise ValueError('pipeline group contains overlapping byte ranges')
    prior = json.loads((ROOT/'research/ep7/pipeline-far-call-target.json').read_text(encoding='utf-8-sig'))
    definitions = {name for row in prior['objects'].values() for name in row['definitions']}
    if not {row[1] for row in calls} <= definitions:
        raise ValueError('pipeline adapter not present in existing target-object closure')
    objects = {}
    with tempfile.TemporaryDirectory(prefix='ep7-pipeline-cohort-') as temp:
        out = Path(temp)
        include = subprocess.check_output([prefix+'gcc', '-print-file-name=include'], text=True).strip()
        flags = ['-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-ffreestanding', '-fno-builtin',
                 '-mno-setlb', '-mno-liw', '-nostdinc', '-I'+str(CORE/'target/include'),
                 '-I'+include, '-I'+str(CORE), '-fstack-usage']
        for name in ['cohort.c', 'far_calls.s']:
            src = NATIVE/name;obj = out/(src.stem+'.o')
            if src.suffix == '.c':
                subprocess.run([prefix+'gcc', *flags, '-c', str(src), '-o', str(obj)], check=True)
            else:
                subprocess.run([prefix+'as', '-I', str(CORE/'target'), str(src), '-o', str(obj)], check=True)
            sizes = subprocess.check_output([prefix+'size', str(obj)], text=True).splitlines()[-1].split()[:3]
            undefined = [line.split()[-1] for line in subprocess.check_output([prefix+'nm', '-u', str(obj)], text=True).splitlines()]
            objects[src.stem] = dict(source=str(src.relative_to(ROOT)), size_output=sizes,
                undefined=undefined, stack_usage=obj.with_suffix('.su').read_text().splitlines() if obj.with_suffix('.su').exists() else [])
        veneer_check = validate_pipeline_object(out/'far_calls.o', prefix)
        available = definitions | {'ep7_pipeline_far_calls', 'ep7_pipeline_far_calls_end'}
        unresolved = {s for row in objects.values() for s in row['undefined']} - available
        if unresolved:
            raise ValueError('new unresolved pipeline symbol: '+str(sorted(unresolved)))
        subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-pedantic',
                        '-fno-pie', '-no-pie', str(NATIVE/'test_cohort.c'), str(CORE/'target/far_call.c'),
                        '-o', str(out/'cohort')], check=True)
        host = json.loads(subprocess.check_output([str(out/'cohort')], text=True))
    semantic = inspect_semantics(reference, prefix, {(mask, frame) for _, _, mask, frame in short})
    return dict(scope=__doc__, checked_original_calls=call_report, checked_frame_edits=frame_report,
        checked_queue_fields=[dict(address=hex(pc), proposed=value) for pc, value in words],
        declared_group_items=len(calls)+len(frames)+len(words), all_ranges_nonoverlapping=True,
        objects=objects, **veneer_check, host_checks=host, veneer_semantics=semantic,
        previous_28_short_site_inventory_incomplete=True, additional_pipeline_short_sites=8,
        combined_known_short_sites=36, publication_callback_wired=False,
        existing_adapter_object_report_reused=True, all_native_hook_entries_enumerated=False,
        pipeline_lifecycle_suites_rerun=False, firmware_modified=False, firmware_built=False,
        camera_executed=False, hash_checks_performed=False,
        limits=['Cohort comparison requires resident code/tables and a separately qualified cold installer.',
                'This group does not include capture initialization, kernel gates, UI tables or all placement checks.',
                'No hardware visibility, original caller closure, total stack or live queue lifetime proof.',
                'New object references are compared with prior object definitions, not a whole firmware link.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.decoded, args.reference, args.tool_prefix), indent=2))
