#!/usr/bin/env python3
"""E-P7 native load recipes and short-CALL placement constraints; no image edits or SHA."""
import argparse
import json
import re
import struct
from pathlib import Path

from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE

ROOT = Path(__file__).resolve().parents[1]
TABLE = 0x60027068
# ID, decoded source/destination, end selected by60045786, branch address.
SECTIONS = [
    (1, 0x600d7800, 0x60211000, 0x6004579c),
    (2, 0x60280800, 0x6055e800, 0x600457a4),
    (3, 0x6057b200, 0x605b7800, 0x600457d4),
    (4, 0x605baa00, 0x60748000, 0x600457ac),
    (5, 0x6075a800, 0x60b9e000, 0x600457b4),
    (6, 0x60ba7000, 0x61243000, 0x600457bc),
    (7, 0x612c7000, 0x61379000, 0x600457c4),
    (8, 0x613bd000, 0x613bd000, 0x600457cc),
    (9, 0x613c1000, 0x6143a800, 0x600457dd),
]
# End constant instruction, source instruction, destination instruction,
# subtraction instruction, call, decoded source/end, logical flash, RAM alias.
EARLY = [
    (0x600201db, 0x600201e7, 0x600201ed, 0x600201f3, 0x600201f9,
     0x60030000, 0x600d0800, 0x406b0000, 0xa0030000),
    (0x600201ab, 0x60020204, 0x6002020a, 0x60020210, 0x60020216,
     0x60230800, 0x6025eb50, 0x408b0800, 0xa1f98540),
    (0x600201b7, 0x60020221, 0x60020227, 0x6002022d, 0x60020233,
     0x60270800, 0x602750c4, 0x408f0800, 0xa1fd8540),
    (0x600201c3, 0x6002023e, 0x60020244, 0x6002024a, 0x60020250,
     0x60278800, 0x60278804, 0x408f8800, 0xa1fe0540),
    (0x600201cf, 0x6002025b, 0x60020261, 0x60020267, 0x6002026d,
     0x6027c800, 0x6027c804, 0x408fc800, 0xa1fe4540),
]
WINDOWS = [(0x600201ab, 0x600202af), (0x60045786, 0x6004595c),
           (0x6004595c, 0x600459a7), (0x600670bc, 0x60067146),
           (0x6005bc79, 0x6005bd54), (0x60058d2a, 0x60058d44),
           (0x6004507d, 0x6004509e)]
W = {
    0x60045787: ('cmp', '1,d0'), 0x6004578b: ('cmp', '9,d0'),
    0x6004578f: ('add', '-1,d0'), 0x60045791: ('asl2', 'd0'),
    0x60045792: ('mov', '1610901376,a0'),
    0x60045798: ('mov', '(d0,a0),a0'), 0x6004579a: ('jmp', '(a0)'),
    0x600457e9: ('mov', 'd0,d3'), 0x600457ea: ('add', '-1,d3'),
    0x600457ec: ('call', '0x60045786,[],0'), 0x600457f1: ('mov', 'd0,d2'),
    0x600457f4: ('udfu01', '12,d0'), 0x600457f9: ('add', f'{TABLE},a3'),
    0x600457ff: ('mov', '(8,a3),d0'), 0x60045802: ('call', '0x60067102,[d2],4'),
    0x60045809: ('mov', 'd0,a2'), 0x6004580b: ('mov', '(4,a3),d0'),
    0x6004580e: ('call', '0x60067102,[d2],4'),
    0x60045815: ('mov', '(a3),d1'), 0x60045818: ('sub', 'd1,d2'),
    0x6004581a: ('mov', '257,d1'), 0x6004581d: ('mov', 'd2,d0'),
    0x6004581e: ('mov', 'a2,a0'),
    0x6004581f: ('call', '0x6005bc79,[d2,d3,a2,a3],20'),
    0x6004582a: ('beq', '0x60045849'),
    0x60045833: ('call', '0x60022694,[d2,a2],24'),
    0x60045842: ('call', '0x60022694,[d2,a2],24'),
    0x6004584f: ('call', '0x6018e1f2,[d2,a2],12'),
    0x60045859: ('asl', 'd3,d0'),
    0x6004585b: ('mov', '(0xa272e420),d1'),
    0x60045863: ('mov', 'd0,(0xa272e420)'),
    # Read/attempt flag and later initializer-completed flag are different.
    0x60045874: ('mov', '(0xa272e420),d0'),
    0x6004587a: ('and', 'd2,d0'), 0x6004587c: ('bne', '0x60045889'),
    0x60045880: ('call', '0x600313ef,[d2,a2,a3],16'),
    0x60045893: ('mov', '(0xa272e424),d1'),
    0x6004589c: ('mov', 'd3,(0xa272e424)'),
    0x600458c5: ('call', '0x60045786,[],0'),
    0x600458ca: ('call', '0x600670bc,[d2],4'),
    0x600458d4: ('udf00', '12,d0'), 0x600458d7: ('add', f'{TABLE},d0'),
    0x600458df: ('mov', '(8,a0),d0'),
    0x600458f9: ('call', '0x60058c66,[d2,d3,a2,a3],56'),
    0x60045916: ('call', '0x6018e19c,[d2,a2],12'),
    0x6004591f: ('call', '0x6018e19e,[d2,a2],12'),
    0x60045928: ('call', '0x6018e1b3,[d2,a2],12'),
    0x60045931: ('call', '0x6018e1c8,[d2,a2],12'),
    0x6004593a: ('call', '0x6018e1dd,[d2,a2],12'),
    0x60045941: ('mov', '(0xa272e41c),d0'),
    0x60045949: ('mov', 'd0,(0xa272e41c)'),
    # Full tracked interval passed to native range-register configuration.
    0x60045963: ('mov', '8,d0'), 0x60045965: ('movbu', 'd0,(6,sp)'),
    0x60045970: ('mov', '9,d0'), 0x60045972: ('call', '0x60045786,[],0'),
    0x6004597e: ('mov', 'd0,(12,sp)'),
    0x60045980: ('mov', '(0x60027070),d0'),
    0x6004598d: ('mov', 'd0,(16,sp)'),
    0x6004599d: ('call', '0x60058c66,[d2,d3,a2,a3],56'),
    0x60058d2a: ('cmp', '8,d1'), 0x60058d2e: ('mov', '(12,a0),d1'),
    0x60058d31: ('mov', 'd1,(0x99700058)'),
    0x60058d37: ('mov', '(8,a0),d1'),
    0x60058d3a: ('mov', 'd1,(0x9970005c)'),
    # Early helper data beyond the final ordinary section.
    0x60020272: ('mov', str(0x41abca00)+',a0'),
    0x60020278: ('mov', str(0xa143ca00-0x100000000)+',a1'),
    0x6002027e: ('mov', '6144,d0'),
    0x60020281: ('call', '0x6002144e,[d2,d3,a2,a3],32'),
    0x60020297: ('mov', str(0xa143ca00-0x100000000)+',a1'),
    0x6002029d: ('mov', str(0x47000800)+',a0'),
    0x600202a5: ('mov', '(a1),d0'), 0x600202a7: ('mov', 'd0,(a0)'),
    0x600202aa: ('cmp', '1536,d1'),
    # The trailing32 bytes have a separate startup read, outside decoded payload.
    0x6004507d: ('mov', str(0x6191ffe0)+',d0'),
    0x6004508c: ('mov', str(0x41f9ffe0)+',a1'),
    0x60045092: ('mov', '32,d0'), 0x60045094: ('mov', '257,d1'),
    0x60045097: ('call', '0x6005bc79,[d2,d3,a2,a3],20'),
    # Selected storage operation and CPU alias conversion, no hardware model.
    0x6005bcab: ('mov', '65280,d0'), 0x6005bcb1: ('and', 'd3,d0'),
    0x6005bd0a: ('cmp', '256,d0'), 0x6005bd0e: ('bne', '0x6005bd1e'),
    0x6005bd14: ('call', '0x600c4e80,[d2,d3,a2],16'),
    0x60067132: ('and', '1073741823,d0'),
    0x60067138: ('or', '-2147483648,d0'),
    0x60067140: ('beq', '0x60067143'), 0x60067142: ('mov', 'd2,d0'),
}
for _, _, end, branch in SECTIONS:
    W[branch] = ('mov', f'{end},d0')
for load, source, dest, subtract, call, start, end, flash, ram in EARLY:
    W[load] = ('mov', f'{end},d0')
    W[source] = ('mov', f'{flash},a0')
    W[dest] = ('mov', f'{ram-0x100000000},a1')
    W[subtract] = ('add', f'{-start},d0')
    W[call] = ('call', '0x6002144e,[d2,d3,a2,a3],32')
# Only the finite nine load caller sites, not a whole-startup scheduling proof.
LOAD_CALLS = [(0x60044f2d, 1), (0x60044f66, 7), (0x60045007, 2),
              (0x600450d7, 3), (0x600450fa, 4), (0x60045143, 5),
              (0x60045166, 6), (0x600451ac, 8), (0x600451d0, 9)]
for call, section in LOAD_CALLS:
    WINDOWS.append((call-2, call+5))
    W[call-2] = ('mov', f'{section},d0')
    W[call] = ('call', '0x600457e7,[d2,d3,a2,a3],24')
CHECKS = [(0x60046780, '<9I', tuple(s[3] for s in SECTIONS))]
CHECKS += [(TABLE+(ident-1)*12, '<3I', (start, start-0x1f980000, start))
           for ident, start, _, _ in SECTIONS]


def inspect_data(data):
    regions = []
    for ident, start, end, _ in SECTIONS:
        if not BASE <= start <= end <= BASE+len(data):
            raise ValueError('section extent outside payload')
        regions.append(dict(id=ident, source=hex(start-0x1f980000), decoded_source=hex(start),
                            destination=hex(start), end_exclusive=hex(end), bytes=end-start))

    def section_of(address):
        if 0x60030000 <= address < 0x600d0800:
            return 'early-kernel-copy'
        matches = [i for i, start, end, _ in SECTIONS if start <= address < end]
        if len(matches) != 1:
            raise ValueError(f'candidate site outside reviewed load ranges: {address:#x}')
        return matches[0]

    # Derive interval constraints from the current implemented capture cohort.
    # Parse data only; do not import/execute historical hash-pinned checks.
    source = (ROOT/'prototypes/ep7_volatile_hl/controller_sidecar/cohort.c').read_text()
    raw_sites = re.findall(r'\{(0x[0-9a-f]+),(\w+),([24]),(0x[0-9a-f]+|0),(\d+)\}', source)
    if len(raw_sites) != 39:
        raise ValueError('capture cohort changed; review placement inventory')
    short = {}
    sites = []
    for text, bridge, width, mask, frame in raw_sites:
        address, width, mask, frame = int(text, 16), int(width), int(mask, 0), int(frame)
        offset = address-BASE
        if (data[offset], data[offset+width+1], data[offset+width+2]) != (
                0xcd if width == 2 else 0xdd, mask, frame):
            raise ValueError(f'capture CALL shape changed: {address:#x}')
        target = address+int.from_bytes(data[offset+1:offset+1+width], 'little', signed=True)
        sites.append(dict(address=hex(address), bridge=bridge, displacement_bytes=width,
                          original_target=hex(target), load_section=section_of(address)))
        if width == 2:
            low, high = address-32768, address+32767
            if bridge in short:
                low, high = max(low, short[bridge][0]), min(high, short[bridge][1])
            if low > high:
                raise ValueError(f'no shared short-CALL reachability for {bridge}')
            short[bridge] = (low, high)
    # Minimum interval stabbing count is a lower bound only. Selected numeric
    # endpoints are NOT code-cave addresses, allocations or installer decisions.
    remaining = sorted(short.items(), key=lambda row: row[1][1])
    lower_bound = 0
    while remaining:
        point = remaining[0][1][1]
        lower_bound += 1
        remaining = [row for row in remaining if not row[1][0] <= point <= row[1][1]]
    roles = {
        'kernel_receive_gate': 0x60036d3c, 'kernel_send_gate': 0x60036f93,
        'kernel_delete_observer': 0x60031072, 'controller_initializer': 0x602897d7,
        'producer': 0x602ac748, 'command_owner': 0x603df803,
        'kind19_worker': 0x603f26a1, 'cpu_color_builder': 0x603b0068,
        'GUI_allocator': 0x60a4ec03, 'GUI_input': 0x60cfd53a,
        'GUI041d_entry': 0x60e5dae9, 'GUI_service_vtable': 0x60faaab4,
        'text_template': 0x61032ea8,
    }
    return dict(
        table=hex(TABLE), selector='0x60045786', loader='0x600457e7', sections=regions,
        early_copies=[dict(decoded_source=hex(start), decoded_end_exclusive=hex(end),
                          flash_source=hex(flash), destination=hex(ram), bytes=end-start,
                          cached_alias=hex(ram-0x40000000))
                      for _, _, _, _, _, start, end, flash, ram in EARLY],
        helper_copy=dict(decoded_source='0x6143ca00', end_exclusive='0x6143e200',
                         initial_destination='0xa143ca00', final_destination='0x47000800', bytes=6144),
        separate_tail_read=dict(source='0x41f9ffe0', destination='0x6191ffe0', bytes=32,
                                outside_decoded_payload=BASE+len(data)==0x6191ffe0),
        role_residency={name: dict(address=hex(address), load_section=section_of(address))
                        for name, address in roles.items()},
        capture_cohort_sites=sites,
        short_bridge_intersections={name: [hex(lo), hex(hi)] for name, (lo, hi) in short.items()},
        abstract_short_bridge_region_lower_bound=lower_bound,
        chosen_trampoline_addresses=[], qualified_free_code_regions=[], qualified_private_ram_regions=[],
        copy_attempt_bits='0xa272e420', initialization_bits='0xa272e41c',
        native_range_configuration_call='0x60058c66',
        range_configuration_registers=['0x99700058', '0x9970005c'],
        read_error_has_no_local_return_before_attempt_bit=True,
        diagnostic_nonreturn_behavior_proven=False,
        udf_index_opcodes_emulated=False, hardware_range_permissions_proven=False,
        load_call_sites=[dict(address=hex(a), section=i) for a, i in LOAD_CALLS])


def inspect(stock, objdump):
    mapped = {}
    evidence = inspect_windows(stock, objdump, WINDOWS, W, CHECKS,
                               observe_data=lambda data: mapped.update(inspect_data(data)))
    return dict(scope=__doc__, input_structure=evidence['input_structure'],
                objdump_version=evidence['objdump_version'],
                checked_instructions=evidence['checked_instructions'], checked_data_rows=len(CHECKS),
                **mapped, whole_startup_executed=False, all_later_overwrites_excluded=False,
                installation_order_qualified=False, firmware_modified=False, firmware_built=False,
                hash_checks_performed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.stock, args.objdump), indent=2))
