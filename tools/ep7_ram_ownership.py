#!/usr/bin/env python3
"""Map E-P7 startup RAM owners and a bounded reservation proposal; no SHA or patches."""
import argparse
import json
import struct
from pathlib import Path

from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE

# Domain, size class, backing, slots, alloc base/count/bitmap operands,
# free base/count operands. Native payload sizes omit a 64-byte guard per slot.
CACHED = [
    (0, 0, 0x61b21fc0, 3040, 0x60022901, 0x60022907, 0x6002290a, 0x62039cf0, 0x60022b6a, 0x60022b70),
    (0, 1, 0x61e85800, 448, 0x60022913, 0x60022919, 0x6002291c, 0x62039e6c, 0x60022b7c, 0x60022b82),
    (0, 2, 0x61bd6d40, 64, 0x60022925, 0x6002292b, 0x6002292d, 0x62039ea4, 0x60022b8e, 0x60022b94),
    (1, 0, 0x61bb07c0, 320, 0x6002294c, 0x60022952, 0x60022955, 0x62640f18, 0x60022bb8, 0x60022bbe),
    (1, 1, 0x61f6c800, 32, 0x6002295d, 0x60022963, 0x60022965, 0x62640f40, 0x60022bc9, 0x60022bcf),
    (1, 2, 0x61cd7d40, 32, 0x6002296d, 0x60022973, 0x60022975, 0x62640f44, 0x60022bd9, 0x60022bdf),
    (2, 0, 0x61bbf7c0, 320, 0x60022992, 0x60022998, 0x6002299b, 0x62668f18, 0x60022c01, 0x60022c07),
    (2, 1, 0x61f7d000, 32, 0x600229a3, 0x600229a9, 0x600229ab, 0x62668f40, 0x60022c12, 0x60022c18),
    (2, 2, 0x61d58540, 32, 0x600229b3, 0x600229b9, 0x600229bb, 0x62668f44, 0x60022c22, 0x60022c28),
]
STRIDES = (192, 2112, 16448, 192)
UNCACHED = [(0xa1bce7c0, 178), (0xa1f8d800, 21), (0xa1dd8d40, 43), (0xa27f3500, 100)]
FENCES = [
    (0x61b21fc0, 128, 3680, 0xdeb10000),
    (0xa1bce7c0, 128, 178, 0xdeb20000),
    (0xa27f3500, 128, 100, 0xdeb70000),
    (0x61bd6d40, 16384, 128, 0xdeb30000),
    (0xa1dd8d40, 16384, 43, 0xdeb40000),
    (0x61e85800, 2048, 512, 0xdeb50000),
    (0xa1f8d800, 2048, 21, 0xdeb60000),
]
KERNEL = [(0x600411a4, 0x6203c940, 0xb1000),
          (0x60041330, 0x620ed940, 0x70000), (0x600414bc, 0x6215d940, 0x30000)]
WINDOWS = [(0x60020049, 0x6002007f), (0x60020117, 0x60020139),
           (0x6002046d, 0x600204ad), (0x60020653, 0x60020671),
           (0x60022700, 0x60022732), (0x600228b6, 0x60022a61),
           (0x60022a61, 0x60022b23), (0x60022b23, 0x60022cc5),
           (0x600fad97, 0x600fae13), (0x600360b5, 0x600360f5)]
W = {
    0x6002004d: ('mov', f'{0x6203c934},d1'),
    0x60020053: ('mov', f'{0x62038100},d0'),
    0x60020059: ('call', '0x6002046d,[d2,d3,a2],76'),
    0x60020068: ('mov', f'{0xa2796888-0x100000000},d1'),
    0x6002006e: ('mov', f'{0x621caf00},d0'),
    0x60020074: ('call', '0x6002046d,[d2,d3,a2],76'),
    0x6002046e: ('mov', '1073741823,d1'),
    0x60020474: ('and', 'd1,d0'), 0x6002047c: ('or', 'd2,d0'),
    0x6002047e: ('and', 'd1,d3'), 0x60020481: ('or', 'd2,d1'),
    0x600204a5: ('sub', 'd0,d1'), 0x600204ad: ('mov', 'd0,(8,sp)'),
    0x60020660: ('clr', 'd0'), 0x60020661: ('mov', 'd0,(a0)'),
    0x60020662: ('inc4', 'a0'), 0x6002066e: ('ret', '[d2,d3,a2],76'),
    0x60020117: ('mov', f'{0x6002e8e8},a0'),
    0x6002011d: ('mov', f'{0x6002e020},a1'),
    0x60020123: ('mov', f'{0x61b20fe0},a2'),
    0x6002012b: ('sub', 'a1,d0'), 0x60020131: ('mov', '(a1),d2'),
    0x60020133: ('mov', 'd2,(a2)'), 0x60020137: ('bgt', '0x60020131'),
    0x60022700: ('cmp', '128,d0'), 0x60022709: ('cmp', '2048,d0'),
    0x60022713: ('cmp', '16384,d0'),
    0x6002271b: ('call', '0x600228b6,[d2,d3,a2,a3],36'),
    0x60022728: ('call', '0x60022694,[d2,a2],24'),
    0x6002272d: ('mov', '0,a0'),
    0x600228c8: ('mov', f'{0x60026e34},a1'),
    0x600228d0: ('mov', '(d1,a1),d1'),
    0x600228d6: ('mov', '(0x8050),d1'),
    0x600228ed: ('add', f'{0x62038118},a1'),
    0x60022939: ('add', f'{0x62640c00},a1'),
    0x60022980: ('add', f'{0x62668c00},a1'),
    0x600229d4: ('mov', '(a1),d1'), 0x600229d5: ('cmp', 'd0,d1'),
    0x600229d6: ('bge', '0x600229e9'), 0x600229db: ('udf00', 'd1,d0'),
    0x600229dd: ('add', 'a3,d0'), 0x600229e6: ('mov', 'd1,(a1)'),
    0x60022a21: ('add', 'd0,d0'), 0x60022a22: ('movhu', '(d0,a1),d1'),
    0x60022a29: ('udf00', 'd0,d3'),
    0x60022a44: ('call', '0x60022d9f,[d2],4'),
    0x60022a4f: ('call', '0x60022dcd,[],16'),
    0x60022a5d: ('mov', 'a2,a0'),
    0x60022a85: ('mov', f'{0x60026e34},a0'),
    0x60022a95: ('mov', f'{0x60026e04},a1'),
    0x60022aa5: ('mov', f'{0x60026df4},a1'),
    0x60022ab5: ('mov', 'd1,(a0)'),
    0x60022b30: ('mov', '(0x8050),d0'),
    0x60022c44: ('sub', 'a0,d0'), 0x60022c4b: ('div', 'd2,d1'),
    0x60022c55: ('div', 'd1,d0'), 0x60022c57: ('mov', 'mdr,d0'),
    0x60022c5b: ('bne', '0x60022c65'), 0x60022c5f: ('blt', '0x60022c65'),
    0x60022c61: ('cmp', 'd3,a3'), 0x60022c63: ('blt', '0x60022c6d'),
    0x60022c70: ('call', '0x60022d8b,[d2],4'),
    0x60022c8c: ('call', '0x60022db5,[d2],4'),
    0x60022ca7: ('movhu', 'd1,(d0,a0)'),
    0x600fad97: ('mov', f'{0x60026f38},a3'),
    0x600fada1: ('mov', '(8,a3),d0'), 0x600fada4: ('mov', '(4,a3),d2'),
    0x600fada9: ('mov', '(12,a3),d0'),
    0x600fadb0: ('call', '0x60067102,[d2],4'),
    0x600fadc0: ('mov', '64,a1'), 0x600fadc2: ('add', 'd2,a1'),
    0x600fadc4: ('add', 'd0,d2'), 0x600fadc9: ('or', 'd3,d0'),
    0x600fadcf: ('mov', '(a2),d0'), 0x600fadd0: ('cmp', 'a0,d0'),
    0x600fadf2: ('inc4', 'a2'), 0x600fadf4: ('cmp', '16,d1'),
    0x600fae07: ('add', '16,a3'), 0x600fae0c: ('cmp', '7,d0'),
    0x600360b5: ('mov', '(0x8050),d0'),
    0x600360b8: ('mov', f'{0x8ff00004-0x100000000},a3'),
    0x600360bf: ('mov', '(d0,a3),a0'),
    0x600360c1: ('mov', '(40,a0),a2'),
    0x600360ca: ('mov', '(44,a0),a1'),
    0x600360d3: ('mov', '(48,a0),d0'),
    0x600360d6: ('mov', 'a2,(a1)'),
    0x600360e1: ('mov', 'd0,(16,a1)'),
    0x600360e4: ('mov', 'a1,(a2)'),
    0x600360ef: ('mov', 'd0,(16,a2)'),
}
# Cover the final address operand above without overlapping witness windows.
WINDOWS[2] = (0x6002046d, 0x600204af)
for domain, cls, start, count, ab, ac, bm, bitmap, fb, fc in CACHED:
    W[ab] = ('mov', f'{start},a3')
    W[ac] = ('mov', f'{count},d0')
    W[bm] = ('mov', f'{bitmap},a0')
    W[fb] = ('mov', f'{start},a0')
    W[fc] = ('mov', f'{count},d3')
CHECKS = [(0x60026e34, '<4I', STRIDES),
          (0x60026df4, '<4I', tuple(x[0] for x in UNCACHED)),
          (0x60026e04, '<4I', tuple(x[1] for x in UNCACHED))]
CHECKS += [(0x60026f38+16*i, '<4I', row) for i, row in enumerate(FENCES)]
CHECKS += [(table+44, '<2I', (start, size)) for table, start, size in KERNEL]


def inspect_data(data):
    cached = []
    for domain, cls, start, count, ab, ac, _, bitmap, fb, fc in CACHED:
        stride = STRIDES[cls]
        cached.append(dict(domain=domain, size_class=cls, start=hex(start),
                           end_exclusive=hex(start+count*stride), slots=count,
                           payload_bytes=stride-64, guard_bytes=64, stride=stride,
                           bitmap=hex(bitmap), allocation_limit_instruction=hex(ac),
                           free_limit_instruction=hex(fc)))
    for cls in range(3):
        pools = sorted((int(x['start'], 16), int(x['end_exclusive'], 16))
                       for x in cached if x['size_class']==cls)
        if any(a[1]!=b[0] for a,b in zip(pools,pools[1:])):
            raise ValueError('cached domain pools are not adjacent as reviewed')
        fence = next(row for row in FENCES if row[0]==pools[0][0])
        if pools[-1][1] != fence[0]+fence[2]*(fence[1]+64):
            raise ValueError('fence extent disagrees with allocator pools')
    # This is a concrete proposal, not an installed reservation. Never modify data.
    alloc, free = 0x600229b9, 0x60022c28
    expected = [(alloc, b'\x80\x20', b'\x80\x1f'), (free, b'\x8f\x20', b'\x8f\x1f')]
    for address, before, _ in expected:
        if data[address-BASE:address-BASE+2] != before:
            raise ValueError('reservation operand encoding changed')
    start = 0x61d58540+31*0x4040
    calls = []
    for opcode, width in ((b'\xcd', 2), (b'\xdd', 4)):
        pos = data.find(opcode)
        while 0 <= pos < len(data)-width:
            if BASE+pos+int.from_bytes(data[pos+1:pos+1+width], 'little', signed=True)==0x6002046d:
                calls.append(BASE+pos)
            pos=data.find(opcode,pos+1)
    if sorted(calls) != [0x60020059,0x60020074]:
        raise ValueError('startup clear finite CALL inventory changed')
    return dict(
        startup_clear_ranges=[dict(start='0x62038100',end_exclusive='0x6203c934',bytes=0x4834),
                              dict(start='0x621caf00',end_exclusive='0x62796888',bytes=0x5cb988)],
        clear_entry='0x6002046d', clear_direct_call_candidates=[hex(x) for x in sorted(calls)],
        clear_hardware_dma_executed=False,
        early_initialized_globals=dict(source='0x6002e020',end_exclusive='0x6002e8e8',
                                       destination='0x61b20fe0',destination_end='0x61b218a8',bytes=2248),
        kernel_arena_initializer='0x600360b5',
        kernel_arenas=[dict(domain=i,config=hex(table),start=hex(start),
                           end_exclusive=hex(start+size),bytes=size)
                       for i,(table,start,size) in enumerate(KERNEL)],
        cached_pools=cached,
        uncached_pools=[dict(size_class=i,start=hex(start),end_exclusive=hex(start+count*STRIDES[i]),
                            cached_alias=hex(start-0x40000000),slots=count,
                            payload_bytes=STRIDES[i]-64,guard_bytes=64)
                        for i,(start,count) in enumerate(UNCACHED)],
        fence_scanner=dict(entry_window='0x600fad97',table='0x60026f38',rows=7,
                           guard_words=16,reads_guard_only_in_reviewed_loop=True),
        reservation_proposal=dict(domain=2,size_class=2,retained_native_slots=31,
            start=hex(start),end_exclusive=hex(start+0x4000),bytes=0x4000,
            preserved_guard_start=hex(start+0x4000),preserved_guard_end='0x61dd8d40',
            operand_edits=[dict(address=hex(a),expected=old.hex(),proposed=new.hex()) for a,old,new in expected],
            stock_bytes_written=False,explicit_candidate_zeroing_required=True,
            fence_table_change_needed_for_payload_only=False,
            native_capacity_reduction_tested=False,cold_install_order_qualified=False,
            other_computed_accesses_excluded=False,approved_for_placement=False),
        udf_multiply_semantics_executed=False,
        allocator_success_or_nonreturn_on_exhaustion_proven=False)


def inspect(stock, objdump):
    ownership = {}
    evidence = inspect_windows(stock,objdump,WINDOWS,W,CHECKS,
                               observe_data=lambda data: ownership.update(inspect_data(data)))
    return dict(scope=__doc__,input_structure=evidence['input_structure'],
                objdump_version=evidence['objdump_version'],
                checked_instructions=evidence['checked_instructions'],checked_data_rows=len(CHECKS),
                **ownership,hash_checks_performed=False,firmware_modified=False,
                firmware_built=False,camera_accessed=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True)
    parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.stock,args.objdump),indent=2))
