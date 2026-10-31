#!/usr/bin/env python3
"""Build a NON-INSTALLABLE E-P7 build1100 decoded candidate; no updater container or hashes."""
import argparse
import json
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from ep7_installation_manifest import BASE, ROOT, implementation_sources, inspect_objects, inspect_stock
from ep7_native_bindings import bindings

CODE = ((0x60048040, 0x6004ffc0), (0x600c8040, 0x600cffc0))
RAM_START, RAM_BYTES = 0xa1dd4d00, 0x4000
ELF_NAME = 'EP7HSL-NONINSTALLABLE.elf'
IMAGE_NAME = 'EP7HSL-NONINSTALLABLE.decoded-main.bin'
LIMITS = [
    'Both executable regions are unqualified placement assumptions, not proven free space.',
    'Private RAM uses the proposed pool payload; ownership and cold reservation timing remain unqualified.',
    'Three boot-prefix edits have no qualified upstream load path.',
    'Early copy failure, secondary CPU ordering and cache visibility remain unresolved.',
    'Full capture/alias retirement, queue/task lifetime, cancellation and GUI exclusion remain unresolved.',
    'Complete task/IRQ stack bounds remain unknown; .su data are local function measurements only.',
    'H/L persistence is excluded; this is the existing volatile implementation.',
    'No updater acceptance, recovery, camera execution, image-quality or display acceptance is established.',
]


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def sections(prefix, path):
    # Use the existing GNU reader instead of adding an ELF parser.
    text = subprocess.check_output([prefix+'objdump', '-h', str(path)], text=True)
    lines = text.splitlines()
    result = []
    for i, line in enumerate(lines):
        match = re.match(r'\s*\d+\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+'
                         r'([0-9a-f]+)\s+([0-9a-f]+)\s+2\*\*(\d+)\s*$', line)
        if match:
            name, size, vma, lma, offset, alignment = match.groups()
            result.append(dict(name=name, size=int(size,16), address=int(vma,16),
                load_address=int(lma,16), file_offset=int(offset,16), alignment=1 << int(alignment),
                flags={v.strip() for v in lines[i+1].split(',')}))
    if not result:
        raise ValueError('GNU section table not recognized: '+str(path))
    return result


def align(address, boundary):
    return (address+boundary-1) & -boundary


def layout(prefix, objects):
    ends = [start for start, _ in CODE]
    groups = [[], []]
    placements = []
    for source, path in objects:
        readonly = []
        for section in sections(prefix, path):
            if 'ALLOC' not in section['flags'] or not section['size']:
                continue
            name = section['name']
            if name == '.bss' or name.startswith('.bss.'):
                if 'CONTENTS' in section['flags']:
                    raise ValueError('BSS unexpectedly has contents: '+source)
            elif (name == '.text' or name.startswith('.text.') or
                  name == '.rodata' or name.startswith('.rodata.')):
                if not {'READONLY','CONTENTS'} <= section['flags']:
                    raise ValueError('code/constant section is not read-only: '+source+' '+name)
                readonly.append(section)
            else:
                raise ValueError('unsupported nonempty allocated input section: '+source+' '+name)
        if not readonly:
            continue
        candidates = []
        for bank, (start, limit) in enumerate(CODE):
            end = ends[bank]
            for section in readonly:
                end = align(end, section['alignment'])+section['size']
            if end <= limit:
                candidates.append((end-start, bank, end))
        if not candidates:
            raise ValueError('code placement exceeds both assumed regions: '+source)
        _, bank, end = min(candidates)
        for section in readonly:
            address = align(ends[bank], section['alignment'])
            groups[bank].append(f'    objects/{path.name}({section["name"]})')
            placements.append(dict(source=source, section=section['name'], bank=bank,
                address_upper_bound_before_constant_merging=hex(address),
                bytes=section['size'], alignment=section['alignment']))
            ends[bank] = address+section['size']
        if ends[bank] != end:
            raise ValueError('inconsistent section placement')
    return groups, ends, placements


def linker_script(groups, native):
    if native['__ep7_private_uncached_start']['address'] is not None or \
       native['__ep7_private_uncached_start']['proposed_address'] != RAM_START:
        raise ValueError('private RAM assumption changed; review the offline layout')
    result = ['/* NON-INSTALLABLE: region ownership and startup remain unqualified. */',
              'OUTPUT_FORMAT("elf32-mn10300")', 'OUTPUT_ARCH(mn10300)',
              'ENTRY(ep7_native_cold_clear)', 'MEMORY {']
    for i, (start, end) in enumerate(CODE):
        result.append(f'  CODE{i} (rx) : ORIGIN = {start:#x}, LENGTH = {end-start:#x}')
    result += [f'  PRIVATE (rw) : ORIGIN = {RAM_START:#x}, LENGTH = {RAM_BYTES:#x}', '}',
               '__ep7_private_uncached_start = ORIGIN(PRIVATE);',
               '__ep7_private_uncached_end = ORIGIN(PRIVATE) + LENGTH(PRIVATE);']
    for name, row in sorted(native.items()):
        if row['address'] is not None:
            result.append(f'{name} = {row["address"]:#x};')
    result.append('SECTIONS {')
    for i, rows in enumerate(groups):
        result += [f'  .ep7_code{i} : {{', *rows, f'  }} > CODE{i}']
    result += ['  .ep7_empty_readonly : { *(.text .text.* .rodata .rodata.*) } > CODE0',
               '  .data : { *(.data .data.*) } > PRIVATE',
               '  .bss (NOLOAD) : {', '    __ep7_bss_start = .;',
               '    *(.bss .bss.* COMMON)', '    . = ALIGN(4);', '    __ep7_bss_end = .;',
               '  } > PRIVATE', '  /DISCARD/ : { *(.comment .note.GNU-stack) }', '}',
               'ASSERT(SIZEOF(.ep7_empty_readonly) == 0, "unassigned readonly input bytes")',
               'ASSERT(SIZEOF(.data) == 0, "initialized writable data has no startup copy")',
               'ASSERT(__ep7_bss_start == ORIGIN(PRIVATE), "BSS origin drift")',
               'ASSERT(__ep7_bss_end <= __ep7_private_uncached_end, "private RAM overflow")']
    return '\n'.join(result)+'\n'


def symbols(prefix, elf):
    result = {}
    for line in subprocess.check_output([prefix+'nm','-g','--defined-only',str(elf)],text=True).splitlines():
        address, kind, name = line.split()
        if name in result:
            raise ValueError('duplicate linked global: '+name)
        result[name] = dict(address=int(address,16), kind=kind)
    if subprocess.check_output([prefix+'nm','-u',str(elf)],text=True).strip():
        raise ValueError('linked output still contains undefined symbols')
    return result


def replacement(row, syms):
    site = int(row['site'],16)
    recipe = row['replacement']
    kind = recipe['encoding']
    target = syms[recipe['target_symbol']]['address'] if 'target_symbol' in recipe else None
    if kind == 'literal':
        data = bytes.fromhex(recipe['hex'])
    elif kind == 'absolute_le32':
        data = struct.pack('<I',target)
    elif kind in ('JMP32','JMP32_NOP_suffix','CALL32'):
        displacement = struct.pack('<i',target-site)
        if kind == 'CALL32':
            data = b'\xdd'+displacement+bytes([recipe['mask'],recipe['frame']])
        else:
            data = b'\xdc'+displacement+b'\xcb'*recipe.get('nop_count',0)
    else:
        raise ValueError('unsupported patch encoding: '+kind)
    if len(data) != row['bytes']:
        raise ValueError('replacement changes original instruction span: '+row['site'])
    return data, target


def check_veneer(row, syms, read):
    recipe = row['replacement']
    address = syms[recipe['target_symbol']]['address']
    target = syms[recipe['adapter_symbol']]['address']
    site, mask, frame = int(row['site'],16), recipe['mask'], recipe['frame']
    prefix = bytes([0xcd,5,0,mask,frame,0xf8,0xfe,0xfc,0x42,0,0xfc,0xcc])+\
        struct.pack('<I',site+5)+bytes([0x42,frame+4,0xf2,0xf2,0x58,0,0xf8,0xfe,4,0xdc])
    if read(address,30) != prefix+struct.pack('<i',target-(address+25)):
        raise ValueError('linked veneer shape/return/frame/adapter mismatch: '+row['site'])


def check_branch(prefix, candidate, row, target):
    site = int(row['site'],16)
    text = subprocess.check_output([prefix+'objdump','-D','-z','-b','binary','-m','mn10300',
        '--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={site:#x}',
        f'--stop-address={site+row["bytes"]:#x}',str(candidate)],text=True)
    instruction = next((line for line in text.splitlines() if line.startswith(f'{site:x}:')), '')
    recipe = row['replacement']
    if recipe['encoding'] == 'CALL32':
        names = ','.join(name for name,mask in [('d2',128),('d3',64),('a2',32),('a3',16)]
                         if recipe['mask'] & mask)
        expected = f'call 0x{target:x},[{names}],{recipe["frame"]}'
    else:
        expected = f'jmp 0x{target:x}'
    match = re.match(r'^[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z0-9]+)\s+(.*)$', instruction)
    if not match or ' '.join(match.groups()) != expected:
        raise ValueError('GNU does not decode candidate branch as intended: '+row['site']+' '+instruction)


def changed_build_inputs(revision):
    # Reuse is based on the recorded Git revision and unchanged tracked sources,
    # never hashes of firmware or generated binaries. Include assembly macros,
    # headers and the existing compiler command implementation in this check.
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('expected a full recorded Git revision')
    command = ['git','--no-optional-locks','-c',f'safe.directory={ROOT}',
               '-c','core.autocrlf=true','-c','core.safecrlf=false','-C',str(ROOT)]
    paths = ['prototypes/ep7_volatile_hl','tools/ep7_installation_manifest.py']
    if subprocess.check_output([*command,'ls-files','--others','--exclude-standard','--',*paths],text=True):
        raise ValueError('untracked build inputs prevent object reuse/provenance verification')
    return subprocess.check_output([*command,'diff','--name-only',revision,'--',*paths],text=True).splitlines()


def check_sources_at_revision(revision):
    changed = changed_build_inputs(revision)
    if changed:
        raise ValueError('build inputs differ from recorded revision: '+', '.join(changed))


def build(decoded, prefix, out, report, reuse=None):
    print('Checking stock input and declared installation manifest...',flush=True)
    manifest = inspect_stock(decoded)
    stock = decoded.read_bytes()
    for start, end in CODE:
        # Keep the existing 64-byte front/back guard outside the emitted region.
        if stock[start-BASE:end-BASE] != b'\xff'*(end-start):
            raise ValueError('assumed code region no longer contains the expected FF bytes')
    sources = implementation_sources()
    if reuse is None:
        print(f'Compiling {len(sources)} implementation sources for the whole candidate...',flush=True)
        inventory = inspect_objects(prefix,manifest['patches'],object_directory=out/'objects')
        report['objects_reused'] = 0
    else:
        previous = json.loads((reuse/'report.json').read_text(encoding='utf-8'))
        if not previous['whole_candidate_compiled']:
            raise ValueError('cached build did not finish compiling all implementation objects')
        changed = changed_build_inputs(previous['source_revision'])
        inventory = json.loads((reuse/'object-inventory.json').read_text(encoding='utf-8'))
        if list(inventory['objects']) != sources or inventory['compiler'] != \
                subprocess.check_output([prefix+'gcc','--version'],text=True).splitlines()[0]:
            raise ValueError('cached source order or compiler differs')
        source_paths = {'prototypes/ep7_volatile_hl/'+source:source for source in sources}
        if not set(changed)<=set(source_paths):
            raise ValueError('cached headers/macros/compiler recipe changed; whole compile required')
        selected = [source for source in sources if 'prototypes/ep7_volatile_hl/'+source in changed]
        (out/'objects').mkdir()
        for i in range(len(sources)):
            shutil.copyfile(reuse/'objects'/f'{i}.o',out/'objects'/f'{i}.o')
            usage = reuse/'objects'/f'{i}.su'
            if usage.exists():
                shutil.copyfile(usage,out/'objects'/usage.name)
        if selected:
            # Reuse the existing partial-inventory compiler. It numbers selected
            # objects locally, so remap them to the stable whole-candidate order.
            with tempfile.TemporaryDirectory(prefix='ep7-object-refresh-') as temp:
                inventory = inspect_objects(prefix,manifest['patches'],source_selection=selected,
                    prior_objects=inventory['objects'],object_directory=Path(temp))
                for index,source in enumerate(selected):
                    destination = sources.index(source)
                    shutil.copyfile(Path(temp)/f'{index}.o',out/'objects'/f'{destination}.o')
                    usage = Path(temp)/f'{index}.su'
                    if usage.exists():
                        shutil.copyfile(usage,out/'objects'/f'{destination}.su')
            report.update(objects_reused=len(sources)-len(selected),objects_recompiled=selected,
                reused_from_source_revision=previous['source_revision'],
                object_source_revision=report['source_revision'],
                reused_headers_macros_and_compiler_recipe_unchanged=True,
                changed_build_inputs=changed)
            print(f'Recompiled {len(selected)} changed sources; reused {len(sources)-len(selected)} unchanged objects.',flush=True)
        else:
            report.update(objects_reused=len(sources),object_source_revision=previous['source_revision'],
                reused_source_and_header_diff_empty=True)
            print(f'Reusing {len(sources)} objects: implementation/header/compiler recipe diff is empty.',flush=True)
    save(out/'object-inventory.json',inventory)
    report.update(whole_candidate_compiled=True,source_count=len(sources))
    save(out/'report.json',report)
    objects = [(source,out/'objects'/f'{i}.o') for i,source in enumerate(sources)]
    groups, expected_ends, placements = layout(prefix,objects)
    (out/'offline-layout.ld').write_text(linker_script(groups,bindings()),encoding='utf-8')
    (out/'objects.rsp').write_text(''.join(f'objects/{obj.name}\n' for _,obj in objects),encoding='utf-8')
    print('Linking all implementation objects at the explicit offline assumption addresses...',flush=True)
    command = [prefix+'ld','--no-relax','--build-id=none','--no-undefined','--fatal-warnings',
        '--orphan-handling=error','-T','offline-layout.ld','-Map=EP7HSL-NONINSTALLABLE.map',
        '@objects.rsp','-o',ELF_NAME]
    linked = subprocess.run(command,cwd=out,capture_output=True,text=True,timeout=120)
    (out/'link.log').write_text(' '.join(command)+'\n'+linked.stdout+linked.stderr,encoding='utf-8')
    linked.check_returncode()
    report['whole_candidate_linked'] = True
    save(out/'report.json',report)
    elf = out/ELF_NAME
    syms = symbols(prefix,elf)
    for name, row in bindings().items():
        expected = row['address'] if row['address'] is not None else RAM_START
        if syms[name]['address'] != expected:
            raise ValueError('linked native binding drift: '+name)
    allocated = [s for s in sections(prefix,elf) if 'ALLOC' in s['flags'] and s['size']]
    if {s['name'] for s in allocated} != {'.ep7_code0','.ep7_code1','.bss'}:
        raise ValueError('unexpected allocated output sections')
    memory = []
    blocks = []
    for i, (start, end) in enumerate(CODE):
        section = next(s for s in allocated if s['name'] == f'.ep7_code{i}')
        # GNU may merge identical readonly constants. The input-section packing
        # is an upper bound; use the actual final section size and symbol table.
        if (section['address'],section['load_address']) != (start,start) or \
                not 0 < section['size'] <= expected_ends[i]-start or 'READONLY' not in section['flags']:
            raise ValueError('linked code layout differs from the input-section allocation')
        binary = out/f'code{i}.bin'
        subprocess.run([prefix+'objcopy','-O','binary','-j',section['name'],str(elf),str(binary)],check=True)
        data = binary.read_bytes()
        if len(data) != section['size']:
            raise ValueError('extracted code length differs from ELF')
        blocks.append((start,data))
        memory.append(dict(section=section['name'],start=hex(start),end=hex(start+len(data)),
            bytes=len(data),capacity=end-start,remaining=end-start-len(data),ownership_proven=False))
    bss = next(s for s in allocated if s['name'] == '.bss')
    if bss['address'] != RAM_START or bss['size'] > RAM_BYTES or 'CONTENTS' in bss['flags']:
        raise ValueError('private BSS must be bounded NOLOAD at the assumed RAM origin')
    memory.append(dict(section='.bss',start=hex(RAM_START),end=hex(RAM_START+bss['size']),
        bytes=bss['size'],capacity=RAM_BYTES,remaining=RAM_BYTES-bss['size'],noload=True,ownership_proven=False))

    def read(address,length):
        for start,data in blocks:
            if start <= address and address+length <= start+len(data):
                return data[address-start:address-start+length]
        raise ValueError('target is outside emitted executable sections: '+hex(address))

    targets = {row['replacement'][key] for row in manifest['patches']
               for key in ('target_symbol','adapter_symbol') if key in row['replacement']}
    for name in targets:
        read(syms[name]['address'],1)
    for row in manifest['patches']:
        if row['kind'] == 'short_call_via_veneer':
            check_veneer(row,syms,read)
    print('Synthesizing the non-installable decoded image and checking final branch encodings...',flush=True)
    spans = [(start,data,'code') for start,data in blocks]
    patch_rows = []
    branches = []
    for row in manifest['patches']:
        data,target = replacement(row,syms)
        spans.append((int(row['site'],16),data,'patch'))
        patch_rows.append(dict(site=row['site'],bytes=row['bytes'],kind=row['kind'],
            target=hex(target) if target is not None else None,
            load_stage=row['load']['stage'],upstream_load_path_qualified=row['load']['loader_path_identified']))
        if row['replacement']['encoding'] in ('CALL32','JMP32','JMP32_NOP_suffix'):
            branches.append((row,target))
    spans.sort()
    candidate = bytearray(stock)
    previous_end = BASE
    changed = 0
    for address,data,_ in spans:
        if address < previous_end or not BASE <= address < address+len(data) <= BASE+len(stock):
            raise ValueError('candidate output writes overlap or exceed decoded extent')
        offset = address-BASE
        changed += sum(a != b for a,b in zip(stock[offset:offset+len(data)],data))
        candidate[offset:offset+len(data)] = data
        previous_end = address+len(data)
    previous_end = BASE
    for address,data,_ in spans:
        if candidate[previous_end-BASE:address-BASE] != stock[previous_end-BASE:address-BASE]:
            raise ValueError('bytes outside declared candidate spans changed')
        previous_end = address+len(data)
    if candidate[previous_end-BASE:] != stock[previous_end-BASE:]:
        raise ValueError('bytes after final candidate span changed')
    image = out/IMAGE_NAME
    image.write_bytes(candidate)
    if image.read_bytes() != candidate:
        raise ValueError('candidate readback differs from the synthesized bytes')
    report['decoded_candidate_synthesized'] = True
    for row,target in branches:
        check_branch(prefix,image,row,target)
    if decoded.read_bytes() != stock:
        raise ValueError('stock input changed during the offline build')
    save(out/'symbols.json',{name:{**row,'address':hex(row['address'])} for name,row in sorted(syms.items())})
    save(out/'section-placement.json',placements)
    report.update(status='passed',whole_candidate_compiled=True,whole_candidate_linked=True,
        decoded_candidate_synthesized=True,source_count=len(sources),
        global_implementation_definitions=inventory['global_definition_count'],
        native_binding_count=len(bindings()), unresolved_symbols=[],
        unlinked_text_data_bss=inventory['unlinked_text_data_bss'],layout=memory,
        entry_symbol='ep7_native_cold_clear',entry_address=hex(syms['ep7_native_cold_clear']['address']),
        entry_is_not_a_boot_proof=True,patch_count=len(patch_rows),patches=patch_rows,
        original_patch_span_bytes=manifest['total_original_span_bytes'],
        patch_count_by_kind=manifest['count_by_kind'],patch_count_by_stage=manifest['count_by_stage'],
        patch_targets_checked=len(targets),linked_veneers_checked=36,gnu_decoded_branches_checked=len(branches),
        candidate_length=len(candidate),changed_bytes=changed,write_span_count=len(spans),
        undeclared_bytes_unchanged=True,candidate_readback_equal=True,stock_input_unchanged=True,
        toolchain=dict(compiler=inventory['compiler'],
            linker=subprocess.check_output([prefix+'ld','--version'],text=True).splitlines()[0]),
        artifacts=dict(elf=ELF_NAME,map='EP7HSL-NONINSTALLABLE.map',image=IMAGE_NAME,
            linker_script='offline-layout.ld',symbols='symbols.json',objects='objects/',
            input_sections='section-placement.json',object_inventory='object-inventory.json'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--source-revision',required=True,help='Git revision recorded by the invoking build job')
    parser.add_argument('--output',type=Path,required=True,help='new or empty dedicated output directory')
    parser.add_argument('--reuse-objects-from',type=Path,
                        help='reuse checked unchanged objects; refresh changed C/ASM with the existing compiler')
    args = parser.parse_args()
    out, decoded = args.output.resolve(), args.decoded.resolve()
    if out == decoded.parent or decoded.is_relative_to(out):
        parser.error('output must be separate from stock input')
    if out.exists() and any(out.iterdir()):
        parser.error('output must be empty; existing artifacts are never overwritten')
    check_sources_at_revision(args.source_revision)
    out.mkdir(parents=True,exist_ok=True)
    (out/'NONINSTALLABLE.txt').write_text(
        'NON-INSTALLABLE RESEARCH CANDIDATE. DO NOT FLASH.\n'
        'Decoded main only: no vendor updater container, no recovery or hardware acceptance.\n'
        'ELF and image may be incomplete unless report.json status is passed.\n\n'+
        '\n'.join(LIMITS)+'\n',encoding='utf-8')
    report = dict(scope=__doc__,status='building',installable=False,installation_authorized=False,
        whole_candidate_compiled=False,whole_candidate_linked=False,decoded_candidate_synthesized=False,
        hardware_executed=False,updater_container_generated=False,hash_checks_performed=False,
        source_revision=args.source_revision,
        stock_length_expected=26214336,limits=LIMITS,
        ram_binding_override=dict(symbol='__ep7_private_uncached_start',official_address=None,
            offline_assumption=hex(RAM_START),production_binding_table_unchanged=True),
        evidence='docs/ep7/OFFLINE_CANDIDATE.md')
    save(out/'report.json',report)
    try:
        build(decoded,args.tool_prefix,out,report,
              args.reuse_objects_from.resolve() if args.reuse_objects_from else None)
    except Exception as error:
        report.update(status='failed',error=str(error))
        save(out/'report.json',report)
        raise
    save(out/'report.json',report)
    print(json.dumps({key:report[key] for key in ('status','source_count','patch_count','layout',
        'candidate_length','changed_bytes','installable')},indent=2))


if __name__ == '__main__':
    main()
