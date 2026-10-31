#!/usr/bin/env python3
"""Controller mailbox ordering and engine dispatch: bounded static checks, no SHA."""
import argparse
import json
import struct
from pathlib import Path

from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE


WINDOWS = [
    (0x6020c03c, 0x6020c15c), (0x60030c1b, 0x60030c32),
    (0x60032b6c, 0x60032bc8), (0x60035db7, 0x60035ec7),
    (0x60031f1e, 0x6003202e), (0x60033732, 0x6003380c),
    (0x600314e6, 0x60031503), (0x6003769a, 0x600377d8),
    (0x6003032f, 0x6003041a), (0x6003521f, 0x6003531d),
    (0x607796e2, 0x6077971a), (0x6077973a, 0x60779788),
    (0x6029d351, 0x6029d36e), (0x601e77d8, 0x601e7865),
    (0x6011f863, 0x6011f871), (0x6006a922, 0x6006a9aa),
    (0x60054d9f, 0x60054dc7),
    (0x60289852, 0x60289933),
]
W = {
    # Wrapper copies three words into a pool block before either send API.
    0x6020c03d: ('call', '0x60038521,[],0'),
    0x6020c047: ('bne', '0x6020c04b'), 0x6020c049: ('mov', '1,d2'),
    0x6020c04f: ('movhu', '(0x60040eb6),d0'),
    0x6020c059: ('call', '0x6003364a,[d2,d3,a2,a3],24'),
    0x6020c06c: ('call', '0x60031bb7,[d2,d3,a2,a3],20'),
    0x6020c075: ('beq', '0x6020c080'),
    0x6020c080: ('mov', 'a2,a1'), 0x6020c081: ('mov', '(24,sp),d0'),
    0x6020c083: ('mov', '8,a0'), 0x6020c085: ('add', 'd0,a0'),
    0x6020c087: ('mov', '-3,d1'), 0x6020c08a: ('mov', '(a1),d0'),
    0x6020c08b: ('inc4', 'a1'), 0x6020c08c: ('mov', 'd0,(a0)'),
    0x6020c08d: ('inc4', 'a0'), 0x6020c08e: ('inc', 'd1'),
    0x6020c08f: ('lne', ''), 0x6020c092: ('beq', '0x6020c0a6'),
    0x6020c094: ('movhu', '(0x60040cdc),d0'),
    0x6020c0a6: ('movhu', '(0x60040cdc),d0'),
    0x6020c0b6: ('cmp', '0,d0'), 0x6020c0b8: ('beq', '0x6020c0df'),
    0x6020c0db: ('mov', '-1,d0'),
    0x6020c0df: ('movhu', '(0x60040b8e),d0'),
    0x6020c0e5: ('mov', '1,d1'),
    0x6020c0e8: ('call', '0x6020c15c,[d2,d3],12'),
    0x6020c0f0: ('movhu', 'd0,(4,sp)'), 0x6020c0f3: ('mov', 'd1,(8,sp)'),
    0x6020c0f5: ('mov', 'a0,(12,sp)'),
    0x6020c0f9: ('call', '0x6020c03c,[d2,a2],36'),
    0x6020c101: ('movhu', '(0x60040cdc),d0'),
    0x6020c13d: ('mov', '8,a1'), 0x6020c141: ('mov', '-3,d1'),
    0x6020c144: ('mov', '(a1),d0'), 0x6020c146: ('mov', 'd0,(a2)'),
    0x6020c149: ('lne', ''),
    0x6020c14a: ('movhu', '(0x60040eb6),d0'),
    0x6020c151: ('call', '0x60034d18,[d2,d3,a2,a3],28'),
    # Boot row -> actual object; two separate sentinel lists.
    0x60032b78: ('mov', '(144,a0),a2'), 0x60032b82: ('mov', '(220,a0),d2'),
    0x60032b86: ('movhu', '(a2),d0'), 0x60032b8a: ('beq', '0x60032bc5'),
    0x60032b9e: ('mov', '12,a1'), 0x60032ba0: ('movhu', 'd0,(a0)'),
    0x60032ba5: ('mov', '(4,a0),d1'), 0x60032baa: ('mov', '(a0),d0'),
    0x60032bab: ('mov', 'd0,(a1)'), 0x60032bac: ('mov', 'd1,(4,a1)'),
    0x60032bb1: ('call', '0x60030c1b,[],0'), 0x60032bc1: ('add', '12,a2'),
    0x60030c1b: ('mov', '64,d0'), 0x60030c1d: ('movhu', 'd0,(2,a0)'),
    0x60030c21: ('inc4', 'a1'), 0x60030c22: ('mov', 'a1,(a1)'),
    0x60030c24: ('mov', 'a1,(4,a1)'), 0x60030c27: ('add', '20,a0'),
    0x60030c29: ('mov', 'a0,(a0)'), 0x60030c2b: ('mov', 'a0,(4,a0)'),
    # Non-task send is domain-checked, not unrestricted cross-core posting.
    0x60031f83: ('call', '0x600314e6,[d2],4'),
    0x600314e7: ('mov', '(0x8050),d2'), 0x600314ea: ('mov', '28672,d1'),
    0x600314ef: ('asr', '12,d1'), 0x600314f2: ('cmp', 'd2,d1'),
    0x600314f3: ('beq', '0x600314ff'), 0x600314f5: ('btst', '32768,d0'),
    0x600314f9: ('bne', '0x600314ff'), 0x600314fb: ('mov', '-25,d0'),
    0x60031f99: ('call', '0x60038594,[],0'),
    0x60031fa1: ('mov', '(220,a0),a0'),
    0x60031fcb: ('btst', '2,d0'), 0x60031fce: ('beq', '0x60031feb'),
    0x60031ff5: ('mov', 'a3,(96,a0)'),
    0x60031ffb: ('call', '0x600344b2,[a2,a3],12'),
    0x60032004: ('btst', '2,d0'), 0x60032007: ('beq', '0x60032013'),
    0x60032013: ('mov', '20,d1'), 0x60032015: ('add', 'a0,d1'),
    0x60032017: ('mov', 'd1,(a3)'), 0x60032018: ('mov', 'd1,a1'),
    0x6003201a: ('inc4', 'a1'), 0x6003201b: ('mov', '(a1),a0'),
    0x6003201d: ('mov', 'a0,(4,a3)'), 0x60032020: ('mov', 'a3,(a0)'),
    0x60032022: ('mov', 'a3,(a1)'), 0x60032024: ('call', '0x6003860b,[],0'),
    # Task send has the same FIFO tail insertion under the kernel envelope.
    0x60035e32: ('call', '0x60038594,[],0'),
    0x60035e3a: ('mov', '(220,a0),a0'),
    0x60035e64: ('btst', '2,d0'), 0x60035e67: ('beq', '0x60035e84'),
    0x60035e89: ('beq', '0x60035e9b'),
    0x60035e8e: ('mov', 'a3,(96,a0)'),
    0x60035e94: ('call', '0x6003442c,[a2,a3],12'),
    0x60035e9d: ('btst', '2,d0'), 0x60035ea0: ('beq', '0x60035eac'),
    0x60035eae: ('add', 'a0,d1'),
    0x60035eac: ('mov', '20,d1'), 0x60035eb0: ('mov', 'd1,(a3)'),
    0x60035eb4: ('mov', '(a0),a1'), 0x60035eb6: ('mov', 'a1,(4,a3)'),
    0x60035eb9: ('mov', 'a3,(a1)'), 0x60035ebb: ('mov', 'a3,(a0)'),
    0x60035ebd: ('call', '0x6003860b,[],0'),
    # Poll receive removes the head, with -50 for empty.
    0x6003379c: ('call', '0x60031503,[d2],4'),
    0x600337af: ('call', '0x60038594,[],0'),
    0x600337b7: ('mov', '(220,a0),a0'),
    0x600337e2: ('mov', '20,a1'), 0x600337e4: ('add', 'd0,a1'),
    0x600337e6: ('mov', '(a1),d0'), 0x600337e9: ('beq', '0x600337fc'),
    0x600337ed: ('mov', 'd0,(a0)'), 0x600337ee: ('mov', '(a1),a0'),
    0x600337f0: ('mov', '(a0),a2'), 0x600337f2: ('mov', '(4,a0),a0'),
    0x600337f5: ('mov', 'a0,(4,a2)'), 0x600337f8: ('mov', 'a2,(a0)'),
    0x600337fc: ('mov', '-50,a3'), 0x60033802: ('call', '0x6003860b,[],0'),
    # The same address can become another mailbox after deletion.
    0x60037723: ('call', '0x60038594,[],0'),
    0x60037743: ('mov', '(220,a0),a0'),
    0x60037774: ('mov', '-51,d0'), 0x60037776: ('call', '0x600344b2,[a2,a3],12'),
    0x600377bb: ('mov', '(220,a0),a0'), 0x600377c6: ('clr', 'd0'),
    0x600377c7: ('movhu', 'd0,(a0)'), 0x600377cf: ('call', '0x6003860b,[],0'),
    0x600303a2: ('call', '0x60038594,[],0'),
    0x600303ac: ('call', '0x6003521f,[d2,d3,a2,a3],24'),
    0x600303c4: ('mov', 'd1,(a1)'), 0x600303c5: ('mov', 'a0,(4,a1)'),
    0x600303ca: ('call', '0x60030c1b,[],0'),
    0x60035238: ('mov', '(220,a1),d0'), 0x60035252: ('mov', '16,a3'),
    0x60035296: ('movhu', '(a1),d1'), 0x60035298: ('cmp', '0,d1'),
    0x6003529a: ('bne', '0x600352a0'),
    0x607796e3: ('movbu', 'd0,(44,sp)'),
    0x607796e6: ('movhu', 'd0,(46,sp)'), 0x607796e9: ('mov', 'd0,(48,sp)'),
    0x60779708: ('mov', 'd0,(4,a0)'), 0x60779770: ('mov', '(4,a2),d0'),
    # Engine type 7 chooses 6011f863, not generic queued callback 601e795c.
    0x6029d351: ('mov', '7,d2'), 0x6029d353: ('movhu', 'd2,(0x6223d8a0)'),
    0x601e7829: ('add', '-4,d1'), 0x601e782b: ('mov', '1612631164,a1'),
    0x601e7831: ('mov', '31,d0'), 0x601e7835: ('asl', '3,d0'),
    0x601e783d: ('cmp', 'd1,d0'), 0x601e783e: ('beq', '0x601e7855'),
    0x601e7855: ('mov', '(4,a0),a0'), 0x601e7858: ('jmp', '(a0)'),
    0x601e785b: ('call', '0x6011f863,[d2,d3,a2,a3],32'),
    0x6011f868: ('mov', '2,d0'), 0x6011f86a: ('call', '0x6006a922,[d2],8'),
    # Existing wrapper changes PSW priority bits; it is not a proven global lock.
    0x6006a949: ('call', '0x6003138f,[a2],12'),
    0x6006a951: ('call', '0x60054d9f,[],0'),
    0x6006a958: ('or', '-2147483648,d0'),
    0x6006a961: ('call', '0x60054d9f,[],0'),
    0x6006a977: ('call', '0x60054dc0,[],0'),
    0x6006a998: ('btst', '-2147483648,d2'),
    0x6006a9a0: ('call', '0x60031477,[a2],12'),
    0x60054d9f: ('mov', 'psw,d1'), 0x60054da3: ('and', '1792,d1'),
    0x60054da7: ('asl', '8,d0'), 0x60054dab: ('bls', '0x60054dbb'),
    0x60054daf: ('and', '-1793,d1'), 0x60054db7: ('mov', 'd1,psw'),
    0x60054dc0: ('mov', 'd0,psw'),
    0x6028985d: ('add', '44,a0'), 0x6028985f: ('mov', 'a0,(28,sp)'),
    0x60289875: ('movhu', '(0x60040b8e),d0'),
    0x60289886: ('call', '0x60051143,[d2,d3,a2,a3],52'),
    0x6028988f: ('btst', '1,d0'), 0x602898ab: ('mov', '(28,sp),a0'),
    0x602898ad: ('call', '0x6020c101,[a2],28'),
    0x602898b4: ('cmp', '0,d0'), 0x602898b6: ('beq', '0x602898bb'),
    0x60289915: ('mov', '(16,a0),a0'), 0x60289921: ('mov', '(48,sp),d1'),
    0x60289926: ('mov', '(4,a0),a1'), 0x60289929: ('mov', '(28,sp),a0'),
    0x6028992b: ('calls', '(a1)'),
}
CALLS = {
    0x6003032f: ([0x607796ee], '[d2,a2,a3],20'),
    0x6003769a: ([0x60779774], '[d2,d3,a2,a3],24'),
    0x60033732: ([0x6020c10c], '[d2,d3,a2,a3],28'),
    0x60035db7: ([0x6020c09d, 0x6077994b], '[d2,d3,a2,a3],24'),
    0x60031f1e: ([0x6020c0af, 0x60779962], '[d2,d3,a2,a3],24'),
}
for target, (sites, frame) in CALLS.items():
    for site in sites:
        W[site] = ('call', f'{target:#x},{frame}')
        if not any(start <= site < stop for start, stop in WINDOWS):
            WINDOWS.append((site, site + 7))
CHECKS = [
    (0x60040cdc, '<H', (1,)), (0x60040eb6, '<H', (1,)),
    (0x600411a4 + 144, '<I', (0x6003ad58,)),
    (0x600411a4 + 220, '<I', (0x6003e89c,)),
    (0x6003ad58, '<6I', (1, 0, 0, 0, 0, 0)),
    (0x6003e89c, '<I', (0x6219fb74,)),
    (0x600410d8 + 16, '<2H', (0, 31)),
    (0x601ecc94, '<2I', (3, 0x601e785a)),
]


def inspect(stock, objdump):
    def scan(data):
        actual = {target: [] for target in CALLS}
        for opcode, width in [(0xcd, 2), (0xdd, 4)]:
            pos = 0
            while (offset := data.find(bytes([opcode]), pos)) >= 0:
                pos = offset + 1
                if offset + width + 3 <= len(data):
                    target = BASE + offset + int.from_bytes(
                        data[offset + 1:offset + width + 1], 'little', signed=True)
                    if target in actual:
                        actual[target].append(BASE + offset)
        for target, (sites, _) in CALLS.items():
            if sorted(actual[target]) != sites:
                raise ValueError(f'mailbox CALL inventory changed at {target:#x}')
            if data.find(struct.pack('<I', target)) >= 0:
                raise ValueError(f'new absolute mailbox entry reference at {target:#x}')

    evidence = inspect_windows(stock, objdump, WINDOWS, W, CHECKS, observe_data=scan)
    return dict(
        scope=__doc__, input_structure=evidence['input_structure'],
        objdump_version=evidence['objdump_version'],
        checked_instructions=evidence['checked_instructions'], checked_data_rows=len(CHECKS),
        mailbox_id=1, pool_id=1, boot_mailbox_object='0x6219fb74',
        boot_mailbox_attributes=0, copied_payload_bytes=12, payload_offset_in_block=8,
        fifo_tail_enqueue_head_poll_receive=True,
        ordering_preconditions=['same live mailbox instance', 'successful enqueues',
                                'reviewed kernel exclusion semantics'],
        send_success_is_not_callback_uniqueness=True,
        dynamic_mailbox_id_range=[1, 31],
        delete_clears_id_and_recreation_can_reuse_object=True,
        references={hex(t): [hex(a) for a in sites] for t, (sites, _) in CALLS.items()},
        raw_scan_is_control_flow_proof=False,
        engine_type=7, engine_dispatch_key=3, engine_submit='0x6011f863',
        generic_601e795c_dispatch_applies_to_type7=False,
        priority_wrapper_psw_mask='0x0700', priority_wrapper_is_proven_global_lock=False,
        mailbox1_delete_unreachable_proven=False, callback_serialization_proven=False,
        complete_lifetime_closure=False, firmware_executed=False, firmware_modified=False,
        firmware_built=False, hash_checks_performed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.stock, args.objdump), indent=2))
