#!/usr/bin/env python3
"""Legacy gain-route linker, reused by ep7_highlight_candidate.py.

The user superseded the gain strategy on 2026-11-08. The current entry point is
ep7_highlight_candidate.py; direct execution here only reproduces archived work.
"""

import argparse
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from ep7_offline_candidate import BASE, IMAGE_NAME, RAM_IMAGE_START, RAM_START
from ep7_offline_candidate import replacement, save, sections, symbols
from ep7_single_dr_gamma import target_table_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'prototypes/ep7_volatile_hl/native_single_dr'
INCLUDE = ROOT / 'prototypes/ep7_volatile_hl/target/include'
CODE_START, CODE_END = 0x60049000, 0x6004dc00
STATE_START, STATE_END = 0xa004e000, 0xa004fc00
STEM = 'EP7DR-NONINSTALLABLE'
MODULES = ('exposure', 'gamma', 'settings', 'transport', 'ui')
DEFINES = []
ENTRY = 'ep7dr_exposure_freeze_bridge'
STRATEGY = 'legacy_gain_compensation'

NATIVE = {
    'ep7dr_stock_engine_dispatch': 0x601e77d8,
    'ep7dr_stock_exposure_calculate': 0x6012e2fc,
    'ep7dr_stock_gain_table': 0x6012f788,
    'ep7dr_stock_gain_resume': 0x6012e6f5,
    'ep7dr_stock_exp2': 0x6011c5e9,
    'ep7dr_stock_key_get_unresolved': 0x6005e971,
    'ep7dr_stock_bank_mode_resume': 0x602b3368,
    'ep7dr_stock_bank_session_enter_resume': 0x602b35ab,
    'ep7dr_stock_bank_session_leave_resume': 0x602b36de,
    'ep7dr_stock_bank_recall_resume': 0x602b37ed,
    'ep7dr_stock_bank_reset_resume': 0x602b3a97,
    'ep7dr_stock_bank_property': 0x602cbc0a,
    'ep7dr_stock_bank_partial_reset_resume': 0x602b3a6b,
    'ep7dr_stock_bank_inhibit': 0x602cc6c6,
    'ep7dr_stock_bank_clear_resume': 0x602b3936,
    'ep7dr_stock_bank_clear_mode8': 0x602b3954,
    'ep7dr_stock_bank_clear_recall_resume': 0x602b39bd,
    'ep7dr_stock_bank_defaults_resume': 0x602b9636,
    'ep7dr_stock_bank_default': 0x602b9bad,
    'ep7dr_stock_bank_save_resume': 0x602cc041,
    'ep7dr_stock_gamma_resume_unresolved': 0x603ae835,
    'ep7dr_stock_gamma_config': 0x603396dd,
    'ep7dr_stock_gamma_config_resume': 0x60334df2,
    'ep7dr_stock_gamma_config_cleanup': 0x60334e57,
    'ep7dr_stock_gamma_bypass': 0x60334de2,
    'ep7dr_stock_gamma_config_enter': 0x60334dec,
    'ep7dr_stock_gamma_stage_resume': 0x60354295,
    'ep7dr_stock_gamma_output_resume': 0x603f28b5,
    'ep7dr_stock_capture_pointer': 0x603dba87,
    'ep7dr_stock_capture_release': 0x603db89e,
    'ep7dr_stock_selected_metadata': 0x602a91ee,
    'ep7dr_stock_selected_resume': 0x602a2841,
    'ep7dr_stock_clone_release': 0x603ed6c4,
    'ep7dr_stock_clone_resume': 0x603edbe3,
    'ep7dr_stock_still_convert': 0x603e62d1,
}
UI_NATIVE = {
    'child_redraw': 0x60defe80, 'info': 0x60defcd8, 'dial_9031': 0x60def91e,
    'dial_9032': 0x60def75a, 'reset': 0x60defc4b, 'child_return': 0x60defe91,
    'touch': 0x60defe88, 'viewer_publish': 0x60e26bb8, 'curve_draw': 0x60e27639,
    'factory': 0x60dd518e, 'ctor_restore': 0x60df01e1, 'ctor_first_page': 0x60df01c6,
    'rebuild_resume': 0x60e266ae, 'destroy': 0x60e26130,
}

CALLS = [
    (0x6029d68e, 'dd4aa1f4ffe020', 'exposure_freeze', 0xe0, 32),
    (0x601429cc, 'dd30b9fefff038', 'exposure_scope', 0xf0, 56),
    (0x6029be17, 'dd70fc1300f02c', 'capture_claim', 0xf0, 44),
    (0x6029be5d, 'dd41fa13000004', 'capture_release', 0, 4),
    (0x6029e966, 'dd88a80000f040', 'still_result', 0xf0, 64),
    (0x603edbce, 'dd39aac5fff01c', 'clone', 0xf0, 28),
    (0x603f2850, 'dd813afffff048', 'convert', 0xf0, 72),
    (0x602a7eb9, 'ddb86adbffc00c', 'capture_key', 0xc0, 12),
    (0x602a7ef0, 'dd816adbffc00c', 'capture_key', 0xc0, 12),
    (0x602a7f57, 'dd1a6adbffc00c', 'capture_key', 0xc0, 12),
    (0x602a7f79, 'ddf869dbffc00c', 'capture_key', 0xc0, 12),
    (0x602a803b, 'dd3669dbffc00c', 'capture_key', 0xc0, 12),
    (0x602a8051, 'dd2069dbffc00c', 'capture_key', 0xc0, 12),
    (0x602a8360, 'dd1166dbffc00c', 'capture_key', 0xc0, 12),
    (0x602a8560, 'dd1164dbffc00c', 'capture_key', 0xc0, 12),
    (0x602a8577, 'ddfa63dbffc00c', 'capture_key', 0xc0, 12),
    (0x602a85b7, 'ddba63dbffc00c', 'capture_key', 0xc0, 12),
    (0x602a8811, 'dd6061dbffc00c', 'capture_key', 0xc0, 12),
    (0x6061f118, 'dd59f8a3ffc00c', 'capture_format_key', 0xc0, 12),
    (0x60e2677d, 'dd11eafaffe010', 'ui_factory', 0xe0, 16),
]
JUMPS = [
    (0x6012e6ef, '9ccd9810300c', 'exposure_gain'),
    (0x602a75ba, 'fc82d0e52362', 'metadata_claim'),
    (0x602a283c, 'cdb269f040', 'selected'),
    (0x603edbde, 'cde6fa8010', 'clone_release'),
    (0x603ae830, 'f8923c5c24', 'gamma'),
    (0x60334ded, 'cdf048a048', 'gamma_config'),
    (0x60334dda, '58c0faec0080', 'gamma_bypass'),
    (0x60354290, '5c08f0701c', 'gamma_stage'),
    (0x603f28b0, 'f8bc0ca000', 'gamma_output'),
    (0x602b3363, 'f1d2f89a05', 'bank_mode'),
    (0x602b37e8, 'f1d2f89a05', 'bank_recall'),
    (0x602b3a8c, '87828029dd7a8101000004', 'bank_reset'),
    (0x602b3a60, '87828001dd628c01000000', 'bank_partial_reset'),
    (0x602b3930, '8216aa08c820', 'bank_clear'),
    (0x602b39b4, '8683178ccd78ff8008', 'bank_clear_recall'),
    (0x602b962f, '0c8ccd7c05f014', 'bank_defaults'),
    (0x602cc03a, '830817fb03d20d', 'bank_save'),
    (0x60e26bb1, '9c91cd860af034', 'ui_draw'),
    (0x60df01be, '5818fac8800c', 'ui_restore'),
    (0x60e266a9, 'f1d3004204', 'ui_rebuild'),
]
POINTERS = [
    (0x61159e74, 'd8fcde60', 'ui_info'),
    (0x61159e44, '4bfcde60', 'ui_reset'),
    (0x61159e7c, '88fede60', 'ui_touch'),
    (0x61159ee4, '5af7de60', 'ui_dial_9032'),
    (0x61159ee8, '1ef9de60', 'ui_dial_9031'),
    (0x611895a4, '3061e260', 'ui_destroy'),
]
LITERALS = [
    (0x603537f0, '2c983c', '2c9c3c'),  # 15512 -> 15516 byte allocation
    (0x6035390c, '8528', '852c'),      # preserve 015's start, clear 44 bytes
]


def overlay_recipe():
    return SimpleNamespace(stem=STEM, modules=MODULES, defines=list(DEFINES), entry=ENTRY,
                           strategy=STRATEGY, native=dict(NATIVE), calls=list(CALLS),
                           jumps=list(JUMPS), pointers=list(POINTERS), literals=list(LITERALS),
                           table_source=target_table_source)


def build(prefix, baseline, out, *, recipe=None):
    if recipe is None:
        recipe = overlay_recipe()
    image = bytearray((baseline / IMAGE_NAME).read_bytes())
    old_symbols = json.loads((baseline / 'symbols.json').read_text(encoding='utf-8'))
    old_addresses = {name: int(row['address'], 16) for name, row in old_symbols.items()}
    bindings = dict(recipe.native, **{name: old_addresses[name] for name in
                              ('_ep7h_stock_value', '_ep7h_active_get', '_ep7h_active_set')},
                    ep7dr_015_clone_bridge=old_addresses['ep7h_capture_clone_bridge'])
    bindings.update({f'ep7dr_stock_ui_{name}_unresolved': address
                     for name, address in UI_NATIVE.items()})
    if (len(image) != 26214336 or bindings['ep7dr_015_clone_bridge'] != 0x60048607
            or old_addresses['__ep7_bss_end'] > STATE_START):
        raise ValueError('expected the existing build 015 decoded candidate and symbol map')

    out.mkdir(parents=True, exist_ok=True)
    (out / 'single_dr_gamma_tables.inc').write_text(recipe.table_source(image), encoding='ascii')
    gcc_include = subprocess.check_output([prefix + 'gcc', '-print-file-name=include'],
                                          text=True).strip()
    common = ['-mno-setlb', '-mno-liw']
    c_flags = ['-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-ffreestanding',
               '-fno-builtin', '-fstack-usage', '-nostdinc', '-I' + str(INCLUDE),
               '-I' + gcc_include, '-I' + str(out), *recipe.defines]
    objects = []
    for source in sorted(SOURCE.iterdir()):
        if source.stem not in recipe.modules or source.suffix not in ('.c', '.s'):
            continue
        obj = out / (source.name + '.o')
        flags = c_flags if source.suffix == '.c' else []
        subprocess.run([prefix + 'gcc', *common, *flags, '-c', str(source), '-o', str(obj)],
                       check=True)
        objects.append(str(obj))

    script = out / 'single-dr.ld'
    script.write_text(f'OUTPUT_ARCH(mn10300)\nENTRY({recipe.entry})\n' +
                      ''.join(f'{name} = {address:#x};\n' for name, address in bindings.items()) +
                      f'''SECTIONS {{
    .ep7dr_code {CODE_START:#x} : {{ *(.text .text.* .rodata .rodata.*) }}
    .ep7dr_state {STATE_START:#x} (NOLOAD) : {{ *(.bss .bss.* COMMON) }}
    .data : {{ *(.data .data.*) }}
    /DISCARD/ : {{ *(.comment .note.GNU-stack) }}
}}
ASSERT(SIZEOF(.data) == 0, "unexpected initialized mutable state")
ASSERT(ADDR(.ep7dr_code) + SIZEOF(.ep7dr_code) <= {CODE_END:#x}, "code overflow")
ASSERT(ADDR(.ep7dr_state) + SIZEOF(.ep7dr_state) <= {STATE_END:#x}, "state overflow")
''', encoding='ascii')
    elf = out / (recipe.stem + '.elf')
    subprocess.run([prefix + 'ld', '-T', str(script), '-Map', str(out / (recipe.stem + '.map')),
                    '-o', str(elf), *objects], check=True)
    syms = symbols(prefix, elf)
    save(out / 'symbols.json', {name: dict(row, address=hex(row['address']))
                                for name, row in syms.items()})
    linked = {row['name']: row for row in sections(prefix, elf)
              if 'ALLOC' in row['flags'] and row['size']}
    if set(linked) != {'.ep7dr_code', '.ep7dr_state'}:
        raise ValueError('unexpected allocated ELF section')
    code = out / 'single-dr.code.bin'
    subprocess.run([prefix + 'objcopy', '-O', 'binary', '-j', '.ep7dr_code',
                    str(elf), str(code)], check=True)
    code_bytes = code.read_bytes()
    state = linked['.ep7dr_state']
    state_image = RAM_IMAGE_START + state['address'] - RAM_START
    if ('CONTENTS' in state['flags'] or any(image[state_image - BASE:
                                                  state_image - BASE + state['size']])):
        raise ValueError('DR state requires the existing image-initialized zero tail')

    def overlay(address, expected, data):
        index = address - BASE
        if len(data) != len(expected) or image[index:index + len(expected)] != expected:
            raise ValueError(f'015 preimage mismatch at {address:#010x}')
        image[index:index + len(data)] = data

    overlay(CODE_START, b'\xff' * len(code_bytes), code_bytes)
    patches = []
    for site, before, target, *args in recipe.calls + recipe.jumps + recipe.pointers:
        instruction = {'target_symbol': f'ep7dr_{target}_bridge'}
        size = len(bytes.fromhex(before))
        if args:
            instruction.update(encoding='CALL32', mask=args[0], frame=args[1])
        elif size == 4:
            instruction.update(encoding='absolute_le32')
        else:
            instruction.update(encoding='JMP32_NOP_suffix', nop_count=size - 5)
        row = dict(site=hex(site), bytes=size, replacement=instruction)
        after, _ = replacement(row, syms)
        overlay(site, bytes.fromhex(before), after)
        patches.append(dict(site=hex(site), before=before, after=after.hex(),
                            target=instruction['target_symbol']))
    for site, before, after in recipe.literals:
        overlay(site, bytes.fromhex(before), bytes.fromhex(after))
        patches.append(dict(site=hex(site), before=before, after=after))

    output = out / (recipe.stem + '.decoded-main.bin')
    output.write_bytes(image)
    save(out / 'report.json', dict(
        status='NON-INSTALLABLE laboratory decoded image', baseline='015', strategy=recipe.strategy,
        image=output.name, code=dict(address=hex(CODE_START), bytes=len(code_bytes)),
        state=dict(address=hex(state['address']), bytes=state['size']), patches=patches,
        limits=['Loaded code padding and uncached RAM ownership are unqualified on-camera.',
                'Legacy/invalid HDR tags decode as OFF. INFO uses the original ACTIVE/bank records.',
                'No updater container, flashing, or camera acceptance.']))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', required=True, help='GNU MN10300 toolchain prefix')
    parser.add_argument('--baseline', type=Path, required=True, help='existing 015 output directory')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(build(args.prefix, args.baseline.resolve(), args.out.resolve()))


if __name__ == '__main__':
    main()
