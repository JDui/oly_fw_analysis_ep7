#!/usr/bin/env python3
"""Exact-stock UI evidence; read-only analysis, no firmware execution."""
import argparse
import json
import struct
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from ep7_stock_audit import audit, BASE
from ep7_request_ownership import require_instruction
from oly_container import parse, sha256

WINDOWS = {'color_type_and_mode': (1625453193, 1625453265),
 'cursor_value_icons': (1625453675, 1625453750),
 'descriptor_consumer': (1624747443, 1624747481),
 'descriptor_copy': (1625967644, 1625967678),
 'display_buffer_reset': (1625451201, 1625451236),
 'lookup': (1625236721, 1625236747),
 'profile1_cursor': (1625453265, 1625453348),
 'publish_display': (1625451469, 1625451523),
 'selected_property_read': (1625453573, 1625453605)}
WITNESSES = {1624747443: ('mov', 'a3,a0'),
 1624747444: ('call', '0x60d7ae23,[a2],8'),
 1624747449: ('mov', 'd2,a0'),
 1624747451: ('call', '0x60ea4c2e,[],0'),
 1624747458: ('mov', '2,d0'),
 1624747460: ('mov', 'd0,(4,sp)'),
 1624747462: ('mov', 'd2,(8,sp)'),
 1624747464: ('mov', '65508,d0'),
 1624747470: ('clr', 'd1'),
 1624747471: ('mov', '0,a0'),
 1624747473: ('mov', 'a0,a1'),
 1624747474: ('call', '0x60ea250b,[d2,d3,a2,a3],36'),
 1625236721: ('clr', 'd3'),
 1625236722: ('cmp', 'd3,d1'),
 1625236723: ('bls', '0x60df2508'),
 1625236725: ('setlb', ''),
 1625236726: ('mov', '(a1),d2'),
 1625236727: ('cmp', 'd2,d0'),
 1625236728: ('bne', '0x60df2503'),
 1625236730: ('mov', '(12,sp),a0'),
 1625236732: ('mov', '(4,a1),d0'),
 1625236735: ('movbu', 'd0,(a0)'),
 1625236737: ('bra', '0x60df2508'),
 1625236739: ('inc', 'd3'),
 1625236740: ('add', '8,a1'),
 1625236742: ('cmp', 'd1,d3'),
 1625236743: ('lcs', ''),
 1625236744: ('retf', '[d2,d3],8'),
 1625451201: ('inc4', 'a0'),
 1625451202: ('mov', '1,d0'),
 1625451204: ('mov', 'd0,(8,sp)'),
 1625451206: ('mov', 'a0,(16,sp)'),
 1625451208: ('clr', 'd0'),
 1625451209: ('mov', '334,d1'),
 1625451212: ('call', '0x4700115e,[d2,a2],8'),
 1625451219: ('mov', '340,a0'),
 1625451222: ('add', 'a3,a0'),
 1625451224: ('mov', 'a0,(12,sp)'),
 1625451226: ('clr', 'd0'),
 1625451227: ('mov', '44,d1'),
 1625451229: ('call', '0x4700115e,[d2,a2],8'),
 1625451469: ('mov', '(12,sp),a0'),
 1625451471: ('call', '0x60ea4c1c,[],0'),
 1625451478: ('mov', '(8,sp),d2'),
 1625451480: ('mov', '(16,sp),a0'),
 1625451482: ('exth', 'd2'),
 1625451483: ('mov', 'd2,a1'),
 1625451485: ('mov', '229,d0'),
 1625451488: ('mov', '334,d1'),
 1625451491: ('call', '0x60cfeca9,[d2,a2],16'),
 1625451498: ('mov', '(8,sp),d0'),
 1625451500: ('cmp', '0,d0'),
 1625451502: ('bne', '0x60e26c00'),
 1625451504: ('mov', '(0x61fc28c8),d0'),
 1625451510: ('mov', '1,d1'),
 1625451512: ('exthu', 'd0'),
 1625451513: ('call', '0x60ea12ca,[d2,d3,a2,a3],100'),
 1625451520: ('ret', '[d2,d3,a2,a3],36'),
 1625453193: ('mov', 'a0,(8,sp)'),
 1625453195: ('mov', '(384,a1),d0'),
 1625453199: ('mov', 'a1,d2'),
 1625453201: ('mov', 'd0,(12,sp)'),
 1625453203: ('clr', 'd0'),
 1625453204: ('mov', 'd0,(16,sp)'),
 1625453206: ('mov', 'd0,(20,sp)'),
 1625453208: ('mov', 'd0,(24,sp)'),
 1625453210: ('mov', '6,d0'),
 1625453212: ('mov', 'd0,(340,a1)'),
 1625453216: ('clr', 'd0'),
 1625453217: ('mov', 'd0,(0x61fc3804)'),
 1625453223: ('mov', '(0x61fc3800),d0'),
 1625453229: ('cmp', '0,d0'),
 1625453231: ('beq', '0x60e272b4'),
 1625453233: ('jmp', '0x60e27425'),
 1625453236: ('mov', '(400,a1),d0'),
 1625453240: ('cmp', '54,d0'),
 1625453242: ('beq', '0x60e272d1'),
 1625453244: ('cmp', '55,d0'),
 1625453246: ('beq', '0x60e27324'),
 1625453248: ('cmp', '56,d0'),
 1625453250: ('bne', '0x60e272c7'),
 1625453252: ('jmp', '0x60e27377'),
 1625453255: ('cmp', '64,d0'),
 1625453257: ('bne', '0x60e272ce'),
 1625453259: ('jmp', '0x60e273c5'),
 1625453262: ('jmp', '0x60e27425'),
 1625453265: ('call', '0x607f9062,[],4'),
 1625453272: ('mov', '(a0),a2'),
 1625453274: ('mov', 'sp,a1'),
 1625453275: ('mov', '(8,a2),a2'),
 1625453278: ('add', '16,a1'),
 1625453280: ('mov', '1091,d0'),
 1625453283: ('calls', '(a2)'),
 1625453285: ('mov', '(16,sp),d0'),
 1625453287: ('cmp', '255,d0'),
 1625453291: ('bne', '0x60e2730d'),
 1625453293: ('call', '0x607f9062,[],4'),
 1625453300: ('mov', '(a0),a2'),
 1625453302: ('mov', 'sp,a1'),
 1625453303: ('mov', '(8,a2),a2'),
 1625453306: ('add', '20,a1'),
 1625453308: ('mov', '1098,d0'),
 1625453311: ('calls', '(a2)'),
 1625453313: ('mov', '(20,sp),d0'),
 1625453315: ('cmp', '0,d0'),
 1625453317: ('beq', '0x60e2730a'),
 1625453319: ('jmp', '0x60e27425'),
 1625453322: ('jmp', '0x60e273fb'),
 1625453325: ('call', '0x607f9062,[],4'),
 1625453332: ('mov', '(16,sp),d0'),
 1625453334: ('mov', '1,d1'),
 1625453336: ('sub', 'd1,d0'),
 1625453338: ('add', 'd0,d0'),
 1625453339: ('mov', '1629002168,a1'),
 1625453345: ('jmp', '0x60e27419'),
 1625453573: ('call', '0x607f9062,[],4'),
 1625453580: ('mov', '(16,sp),d0'),
 1625453582: ('mov', '1,d1'),
 1625453584: ('sub', 'd1,d0'),
 1625453586: ('add', 'd0,d0'),
 1625453587: ('mov', '1629002240,a1'),
 1625453593: ('mov', '(a0),a2'),
 1625453595: ('movhu', '(d0,a1),d0'),
 1625453597: ('mov', '(8,a2),a2'),
 1625453600: ('mov', 'sp,a1'),
 1625453601: ('add', '24,a1'),
 1625453603: ('calls', '(a2)'),
 1625453675: ('mov', '162,a0'),
 1625453677: ('add', 'a3,a0'),
 1625453679: ('mov', 'a0,(4,sp)'),
 1625453681: ('mov', 'd2,a0'),
 1625453683: ('mov', '(16,sp),d0'),
 1625453685: ('mov', '1629002264,a1'),
 1625453691: ('mov', '13,d1'),
 1625453693: ('call', '0x60df24f1,[d2,d3],8'),
 1625453700: ('mov', '165,a0'),
 1625453702: ('add', 'a3,a0'),
 1625453704: ('mov', 'a0,(4,sp)'),
 1625453706: ('mov', 'd2,a0'),
 1625453708: ('mov', '(24,sp),d0'),
 1625453710: ('mov', '1629002368,a1'),
 1625453716: ('mov', '11,d1'),
 1625453718: ('call', '0x60df24f1,[d2,d3],8'),
 1625453725: ('mov', '166,a0'),
 1625453727: ('add', 'a3,a0'),
 1625453729: ('mov', 'a0,(4,sp)'),
 1625453731: ('mov', 'd2,a0'),
 1625453733: ('mov', '(24,sp),d0'),
 1625453735: ('mov', '1629002456,a1'),
 1625453741: ('mov', '11,d1'),
 1625453743: ('call', '0x60df24f1,[d2,d3],8'),
 1625967644: ('mov', '1648836584,a1'),
 1625967650: ('mov', '-11,d1'),
 1625967652: ('setlb', ''),
 1625967653: ('mov', '(a0),d0'),
 1625967654: ('inc4', 'a0'),
 1625967655: ('mov', 'd0,(a1)'),
 1625967656: ('inc4', 'a1'),
 1625967657: ('inc', 'd1'),
 1625967658: ('lne', ''),
 1625967659: ('retf', '[],0'),
 1625967662: ('mov', '1648836584,a1'),
 1625967668: ('mov', '-11,d1'),
 1625967670: ('setlb', ''),
 1625967671: ('mov', '(a1),d0'),
 1625967672: ('inc4', 'a1'),
 1625967673: ('mov', 'd0,(a0)'),
 1625967674: ('inc4', 'a0'),
 1625967675: ('inc', 'd1'),
 1625967676: ('lne', ''),
 1625967677: ('retf', '[],0')}

def inspect(raw, objdump):
    identity = audit(raw) # Reject wrong build before any parsing/disassembler execution.
    main = parse(raw)[0].payload
    version = subprocess.check_output([str(objdump), '--version'], text=True).splitlines()[0]
    windows = {}
    with tempfile.TemporaryDirectory(prefix='ep7-source-clone-') as temp:
        image = Path(temp)/'main.bin'
        image.write_bytes(main)
        for name,(start,stop) in WINDOWS.items():
            asm = subprocess.check_output([str(objdump), '-b','binary','-m','mn10300','-D','-z',
                '--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',
                f'--stop-address={stop:#x}',str(image)],text=True)
            addresses = [a for a in WITNESSES if start <= a < stop]
            for address in addresses: require_instruction(asm,address,*WITNESSES[address])
            windows[name] = dict(start=hex(start), stop_exclusive=hex(stop),
                sha256=sha256(main[start-BASE:stop-BASE]), witness_count=len(addresses))
    tables={}
    for address,first in [(0x611899b8,927),(0x611899d0,939),(0x611899e8,951),(0x61189a00,1655)]:
        row=list(struct.unpack_from('<12H',main,address-BASE))
        if row!=list(range(first,first+12)):raise ValueError('viewer S property table mismatch')
        tables[hex(address)]=row
    rows={}
    for address,count,expected in [(0x61189a18,13,[(0,7)]+[(i,(i+1)//2) for i in range(1,13)]),
      (0x61189a80,11,[(i,3 if i<0 else 1 if i==0 else 2) for i in range(-5,6)]),
      (0x61189ad8,11,[(i,abs(i)+1) for i in range(-5,6)])]:
        row=[struct.unpack_from('<iI',main,address-BASE+8*i) for i in range(count)]
        if row!=expected:raise ValueError('viewer lookup map mismatch')
        rows[hex(address)]=row
    return dict(scope='One COLOR selected-value viewer/data route; not a general rendering library audit',
      source_sha256=identity['source_sha256'],objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),
      windows=windows,instruction_witness_count=len(WITNESSES),S_property_tables=tables,icon_lookup_tables=rows,
      interface=dict(native_lookup='0x60df24f1',lookup_row_bytes=8,lookup_output_bytes=1,
        no_match='output unchanged',S_icon_key_range=[-5,5],display_flags_bytes=334,descriptor_bytes=44,
        descriptor_copy_destination='0x62473fe8',COLOR_descriptor_type=6),
      limitations=['Lookup helper is not a drawing helper and does not accept 12 axis values.',
        'Native selected-value producer reads S property IDs; it cannot render H/L unchanged.',
        'No icon entries for -7,-6,+6,+7 were found in these two exact 11-entry tables.',
        'Category4/5 require a new qualified viewer branch and independent H/L state/value source.',
        'Descriptor/global display transport is not a caller-owned immutable 12-value array API.',
        'No S setter, native drawing call, firmware write, or hardware validation performed.'],
      camera_accessed=False,firmware_executed=False,flash_ready=False)
if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True)
    parser.add_argument('--objdump',type=Path,required=True,help='Explicit trusted objdump executable')
    args=parser.parse_args()
    print(json.dumps(inspect(args.stock.read_bytes(),args.objdump.resolve()),indent=2))
