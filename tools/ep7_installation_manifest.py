#!/usr/bin/env python3
"""Enumerate the declared build1100 installation and object dependencies; never patch or link."""
import argparse
from collections import Counter
from contextlib import nullcontext
import importlib
import json
import re
import struct
import subprocess
import tempfile
from pathlib import Path

from ep7_native_bindings import bindings
from ep7_far_call_check import capture_rows
from ep7_pipeline_cohort_check import declared_rows
from ep7_remaining_far_calls import GROUPS, group_rows
from ep7_load_regions import BASE, SECTIONS, EARLY, CHECKS as LOAD_CHECKS

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT/'prototypes/ep7_volatile_hl'
SOURCE_LIST = CORE/'target/sources.txt'


def aliases(source):
    return dict(re.findall(r'extern const unsigned char (\w+)\[\] __asm__\("(\w+)"\);', source))


def witness_modules(names):
    # These modules define observations at import. Do not execute their inspect,
    # CLI, historical identity checks, host suites or any firmware-writing path.
    return [importlib.import_module('ep7_'+name) for name in names]


def instruction_witnesses():
    result = {}
    for module in witness_modules([
            'capture_native_binding', 'capture_envelope', 'capture_transaction',
            'associated_pool', 'deferred_producer', 'engine_epoch',
            'producer_scope', 'worker_scope', 'ack_frames',
            'descriptor_send_frames', 'descriptor_receive_frames', 'descriptor_frames',
            'ui_input_binding', 'bootstrap_entry']):
        rows = module.W if hasattr(module, 'W') else {
            pc:value for _,_,group in module.GROUPS.values() for pc,value in group.items()}
        for pc, instruction in rows.items():
            if pc in result and result[pc][0] != instruction:
                raise ValueError('conflicting instruction witness at '+hex(pc))
            result[pc] = (instruction, 'tools/'+module.__name__+'.py')
    return result


def load_region(pc, length):
    if 0x60030000 <= pc and pc+length <= 0x600d0800:
        return dict(stage='early-kernel-copy', decoded_address=hex(pc),
                    flash_address=hex(pc-0x1f980000), copy_destination=hex(pc+0x40000000),
                    execution_address=hex(pc), loader_path_identified=True)
    for ident, start, end, _ in SECTIONS:
        if start <= pc and pc+length <= end:
            return dict(stage='section'+str(ident), decoded_address=hex(pc),
                        flash_address=hex(pc-0x1f980000), copy_destination=hex(pc),
                        execution_address=hex(pc), loader_path_identified=True)
    if BASE <= pc and pc+length <= 0x60030000:
        return dict(stage='boot-prefix-unqualified', decoded_address=hex(pc),
                    flash_address=None, copy_destination=None, execution_address=hex(pc),
                    loader_path_identified=False)
    raise ValueError('patch outside enumerated load regions: '+hex(pc))


def inspect_stock(decoded):
    data = decoded.read_bytes()
    if len(data) != 26214336:
        raise ValueError('unsupported decoded main length')
    native = bindings()
    for row in native.values():
        if not (ROOT/row['evidence']).is_file():
            raise ValueError('missing native binding evidence '+row['evidence'])
    for pc, fmt, values in LOAD_CHECKS:
        if struct.unpack_from(fmt, data, pc-BASE) != values:
            raise ValueError('ordinary load table changed at '+hex(pc))
    if EARLY[0][5:] != (0x60030000, 0x600d0800, 0x406b0000, 0xa0030000):
        raise ValueError('early copy recipe changed; review stage mapping')
    patches = []

    def add(pc, old, kind, group, replacement, evidence):
        if data[pc-BASE:pc-BASE+len(old)] != old:
            raise ValueError('stock bytes differ at '+hex(pc))
        patches.append(dict(site=hex(pc), bytes=len(old), original_hex=old.hex(), kind=kind,
                            group=group, replacement=replacement, evidence=evidence,
                            load=load_region(pc, len(old))))

    witnesses = instruction_witnesses()

    def add_call(pc, target, width, mask, frame, group, original=None, evidence=None):
        if original is None:
            (mn, operands), evidence = witnesses[pc]
            if mn != 'call':
                raise ValueError('expected CALL witness at '+hex(pc))
            original_text, rest = operands.split(',', 1)
            saves, frame_text = rest.rsplit(',', 1)
            native_mask = sum(dict(d2=128, d3=64, a2=32, a3=16)[s]
                              for s in saves.strip('[]').split(',') if s)
            if (native_mask, int(frame_text)) != (mask, frame):
                raise ValueError('cohort and original CALL frame differ at '+hex(pc))
            original = int(original_text, 16)
        old = bytes([0xcd if width == 2 else 0xdd]) + (original-pc).to_bytes(
            width, 'little', signed=True)+bytes([mask, frame])
        recipe = dict(encoding='JMP32' if width == 2 else 'CALL32',
                      target_symbol=f'ep7_{group}_far_{pc:x}' if width == 2 else target,
                      adapter_symbol=target, mask=mask, frame=frame,
                      original_target=hex(original), original_resume=hex(pc+width+3))
        add(pc, old, 'short_call_via_veneer' if width == 2 else 'wide_call', group, recipe, evidence)

    source = (CORE/'controller_sidecar/cohort.c').read_text()
    names = aliases(source)
    capture = [(int(pc, 16), names[name], int(width), int(mask, 0), int(frame))
               for pc, name, width, mask, frame in re.findall(
                   r'\{(0x[0-9a-f]+),(\w+),([24]),(0x[0-9a-f]+|0),(\d+)\}', source)]
    if len(capture) != 39 or [(p,t,m,f) for p,t,w,m,f in capture if w == 2] != capture_rows():
        raise ValueError('capture cohort and veneers differ')
    for row in capture:
        add_call(*row, 'capture')
    pipeline, _, frames, words = declared_rows()
    for row in pipeline:
        add_call(*row, 'pipeline')
    for group, spec in GROUPS.items():
        for pc, target, mask, frame in group_rows(group):
            add_call(pc, target, 2, mask, frame, group, spec['original'], 'tools/ep7_remaining_far_calls.py')
    source = (CORE/'ui_native/cohort.c').read_text()
    names = aliases(source)
    wide_ui = re.findall(r'\bcall\((ep7_stock_\w+),([a-z]+),(0x[0-9a-f]+),(\d+)\)', source)
    if len(wide_ui) != 2:
        raise ValueError('unexpected UI wide CALL count')
    for name, target, mask, frame in wide_ui:
        add_call(native['_'+name]['address'], names[target], 4, int(mask,16), int(frame), 'input')
    add_call(0x60191371, 'ep7_native_cold_bootstrap_bridge', 4, 0, 4, 'bootstrap')

    table_witnesses = {}
    for module in witness_modules(['ui_owner_binding', 'ui_mvc_lifetime',
                                   'ui_viewer_join', 'ui_input_binding', 'ui_selector_storage']):
        for pc, fmt, values in module.CHECKS:
            packed = struct.pack(fmt, *values)
            for offset in range(0, len(packed)-3, 4):
                table_witnesses[pc+offset] = (packed[offset:offset+4], 'tools/'+module.__name__+'.py')
    word_pattern = re.compile(r'(ep7_stock_\w+)(?:\[(\d+)(?:/(\d+))?\])?'
                             r'(?:==|!=)\(uint32_t\)\(uintptr_t\)(\w+)')
    for relative, group, count in [('ui_owner/cohort.c','owner',4), ('ui_mvc/cohort.c','mvc',5),
                                   ('ui_native/cohort.c','input',1), ('ui_selector/selector.c','selector',1)]:
        source = (CORE/relative).read_text(); names = aliases(source)
        rows = [r for r in word_pattern.findall(source) if r[3] in names]
        if len(rows) != count:
            raise ValueError('unexpected pointer-word cohort '+relative)
        for name, numerator, divisor, target in rows:
            index = int(numerator or '0')//int(divisor or '1')
            pc = native['_'+name]['address']+4*index
            old, evidence = table_witnesses[pc]
            add(pc, old, 'function_pointer_word', group,
                dict(encoding='absolute_le32', target_symbol=names[target]), evidence)
    for pc, value in frames:
        old = value+12 if value < 0 else value-12
        add(pc, b'\xfa\xfe'+old.to_bytes(2,'little',signed=True), 'stack_frame', 'pipeline',
            dict(encoding='literal', hex=(b'\xfa\xfe'+value.to_bytes(2,'little',signed=True)).hex()),
            'tools/ep7_descriptor_frames.py')
    for pc, value in words:
        old = 300 if value == 312 else 9728
        add(pc, struct.pack('<I',old), 'queue_capacity', 'pipeline',
            dict(encoding='literal', hex=struct.pack('<I',value).hex()), 'tools/ep7_pipeline_cohort_check.py')

    prior = json.loads((ROOT/'research/ep7/cold-bootstrap.json').read_text(encoding='utf-8-sig'))
    inline = {int(r['address'],16):r for r in prior['inline_spans']}
    source = (CORE/'runtime/cold_cohort.c').read_text(); names = aliases(source)
    spans = [(int(p,16), names[n], int(size)) for p,n,size in re.findall(
        r'\{(0x[0-9a-f]+),(\w+),(\d+)\}', source)]
    # The old cold-clear JMP and two pool-bound edits were removed when state
    # moved into the existing loaded image. Retain the other reviewed spans.
    if {pc for pc,_,_ in spans} != set(inline)-{0x600201fe} or len(spans) != 4:
        raise ValueError('inline spans differ from reviewed cold cohort')
    for pc, target, size in spans:
        old = bytes.fromhex(inline[pc]['original'])
        if len(old) != size:
            raise ValueError('inline span length changed')
        add(pc, old, 'inline_jump', 'cold', dict(encoding='JMP32_NOP_suffix',
            target_symbol=target, nop_count=size-5), 'research/ep7/cold-bootstrap.json')
    for pc, old in [(0x600201fe,inline[0x600201fe]['original']),
                    (0x600229b9,'8020'),(0x60022c28,'8f20')]:
        value = bytes.fromhex(old)
        if data[pc-BASE:pc-BASE+len(value)] != value:
            raise ValueError('original prefix differs at '+hex(pc))
    patches.sort(key=lambda row:int(row['site'],16))
    for left, right in zip(patches, patches[1:]):
        if int(left['site'],16)+left['bytes'] > int(right['site'],16):
            raise ValueError('overlapping installation entries '+left['site']+' '+right['site'])
    expected = dict(short_call_via_veneer=36, wide_call=32, function_pointer_word=11,
                    stack_frame=9, queue_capacity=6, inline_jump=4)
    if dict(Counter(r['kind'] for r in patches)) != expected:
        raise ValueError('installation inventory changed; review declared cohort coverage')
    return dict(patches=patches, count_by_kind=expected,
        count_by_stage=dict(Counter(r['load']['stage'] for r in patches)),
        total_patch_entries=len(patches), total_original_span_bytes=sum(r['bytes'] for r in patches),
        ordinary_load_table_rows_checked=len(LOAD_CHECKS), patch_ranges_nonoverlapping=True,
        unknown_boot_prefix_loader_sites=[r['site'] for r in patches if not r['load']['loader_path_identified']],
        native_bindings={name:{**row,'address':hex(row['address']) if row['address'] is not None else None,
            **({'proposed_address':hex(row['proposed_address'])} if 'proposed_address' in row else {})}
            for name,row in sorted(native.items())})


def implementation_sources():
    rows = [line.strip() for line in SOURCE_LIST.read_text().splitlines()
            if line.strip() and not line.startswith('#')]
    if len(rows) != len(set(rows)):
        raise ValueError('duplicate implementation source')
    for relative in rows:
        source = (CORE/relative).resolve()
        if not source.is_relative_to(CORE.resolve()) or not source.is_file():
            raise ValueError('invalid implementation source '+relative)
        if source.suffix not in ('.c','.s') or source.name.startswith(('test_', 'check')) or source.name.endswith('_caller.c'):
            raise ValueError('nonproduction source '+relative)
    return rows


def inspect_objects(prefix, patches, source_selection=None, prior_objects=None, *, object_directory=None):
    # A caller using prior metadata must separately prove the unchanged source
    # and header set. The normal CLI always rebuilds the complete inventory.
    sources = implementation_sources()
    selected = sources if source_selection is None else list(source_selection)
    if len(selected)!=len(set(selected)) or not selected or not set(selected)<=set(sources):
        raise ValueError('invalid object refresh selection')
    objects = {} if prior_objects is None else dict(prior_objects)
    if set(selected)!=set(sources) and set(objects)!=set(sources):
        raise ValueError('partial object refresh requires the complete prior inventory')
    include = subprocess.check_output([prefix+'gcc','-print-file-name=include'],text=True).strip()
    flags = ['-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin',
             '-mno-setlb','-mno-liw','-nostdinc','-I'+str(CORE/'target/include'),
             '-I'+include,'-I'+str(CORE),'-I'+str(CORE/'poll_lock_provider'),'-fstack-usage']
    definitions = {}; references = {}
    # The offline candidate reuses this exact compiler/source inventory and
    # retains its objects for the whole link. Existing probes remain temporary.
    workspace = (tempfile.TemporaryDirectory(prefix='ep7-installation-objects-')
                 if object_directory is None else nullcontext(object_directory))
    with workspace as temp:
        Path(temp).mkdir(parents=True, exist_ok=True)
        for i, relative in enumerate(selected):
            src = CORE/relative; obj = Path(temp)/(str(i)+'.o')
            if src.suffix == '.c':
                extra = ['-fno-tree-loop-distribute-patterns'] if relative == 'target/memory.c' else []
                command = [prefix+'gcc',*flags,*extra,'-c',str(src),'-o',str(obj)]
            else:
                command = [prefix+'as','-I',str(CORE/'target'),str(src),'-o',str(obj)]
            subprocess.run(command,check=True,timeout=60)
            defs = {}
            for line in subprocess.check_output([prefix+'nm','-g','--defined-only',str(obj)],text=True).splitlines():
                _, kind, name = line.split()
                defs[name] = kind
            und = [line.split()[-1] for line in subprocess.check_output([prefix+'nm','-u',str(obj)],text=True).splitlines()]
            sizes = [int(v) for v in subprocess.check_output([prefix+'size',str(obj)],text=True).splitlines()[-1].split()[:3]]
            usage = obj.with_suffix('.su')
            objects[relative] = dict(source='prototypes/ep7_volatile_hl/'+relative,
                definitions=defs, undefined=und, text_data_bss=sizes,
                stack_usage=[line.replace(str(CORE)+'/', '') for line in usage.read_text().splitlines()] if usage.exists() else [])
    for relative,row in objects.items():
        for name in row['definitions']:
            if name in definitions:raise ValueError('duplicate global '+name)
            definitions[name]=relative
        for name in row['undefined']:
            references.setdefault(name,[]).append(relative)
    external = set(references)-set(definitions)
    native = bindings()
    if external != set(native):
        raise ValueError('native binding mismatch: missing='+str(sorted(external-set(native)))+
                         ' unused='+str(sorted(set(native)-external)))
    targets = {r['replacement'][field] for r in patches for field in ('target_symbol','adapter_symbol')
               if field in r['replacement']}
    if not targets <= set(definitions):
        raise ValueError('missing installation targets '+str(sorted(targets-set(definitions))))
    totals = [sum(r['text_data_bss'][i] for r in objects.values()) for i in range(3)]
    return dict(compiler=subprocess.check_output([prefix+'gcc','--version'],text=True).splitlines()[0],
        implementation_sources=len(sources), objects=objects, global_definition_count=len(definitions),
        external_count=len(external), external_consumers={s:references[s] for s in sorted(external)},
        resolved_native_address_count=sum(r['address'] is not None for r in native.values()),
        placement_required_symbols=[s for s,r in native.items() if r['address'] is None],
        patch_target_symbols_checked=len(targets), unlinked_text_data_bss=totals,
        current_implementation_recompiled=set(selected)==set(sources),
        recompiled_sources=selected, reused_object_count=len(sources)-len(selected),
        target_linked=False, target_executed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded',type=Path,required=True)
    parser.add_argument('--tool-prefix',help='also compile the single unified object inventory, without linking')
    args = parser.parse_args()
    report = inspect_stock(args.decoded)
    if args.tool_prefix:
        report['object_inventory'] = inspect_objects(args.tool_prefix,report['patches'])
    report.update(scope=__doc__,source_list=str(SOURCE_LIST.relative_to(ROOT)),
        source_count=len(implementation_sources()), native_binding_count=len(bindings()),
        final_linker_bindings_emitted=False, installation_authorized=False,
        firmware_modified=False, firmware_built=False, hash_checks_performed=False,
        limits=['Enumerates currently declared hooks; does not prove native caller/alias/lifetime closure.',
                'Binding evidence references existing investigations; only patch preimages and load-table rows are freshly compared here.',
                'All declared edits have identified ordinary load paths; the boot prefix remains original.',
                'Executable/RAM placement, cache visibility, complete stack bounds and cold installer ordering remain unqualified.',
                'A mapped stock symbol does not approve its ABI or runtime domain beyond its existing evidence.',
                'No candidate image, linker output, packer, emulator run or device operation is produced.'])
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
