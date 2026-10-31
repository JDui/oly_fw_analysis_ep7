#!/usr/bin/env python3
"""Check local cold-start copy, ready flags and secondary-entry ordering; no hardware execution."""
import argparse
import json
import subprocess
from pathlib import Path

from ep7_request_ownership import require_instruction
from ep7_load_regions import W as LOAD_W

BASE = 0x60020020
GROUPS = {
    'primary_start_and_copy': (0x600200ce, 0x6002020a, {
        0x600200ce: ('mov', '1191184380,a0'),
        0x600200d4: ('mov', 'a0,sp'),
        0x600200d6: ('mov', '1610744057,a0'),
        0x600200dc: ('jmp', '(a0)'),
        0x60020160: ('mov', '1,d2'),
        0x6002017b: ('clr', 'd0'),
        0x60020188: ('movbu', 'd0,(0x8ff00058)'),
        0x6002018e: ('movbu', 'd0,(0x8ff00059)'),
        0x60020194: ('movbu', 'd0,(0x8ff0005a)'),
        **{pc: LOAD_W[pc] for pc in [0x600201db, 0x600201e7, 0x600201ed, 0x600201f3, 0x600201f9]},
        0x600201fe: ('mov', '(0x6218d984),d0'),
        0x60020204: ('mov', '1082853376,a0'),
    }),
    'primary_secondary_setup_and_release': (0x6002030d, 0x60020399, {
        0x6002030d: ('clr', 'd0'),
        0x6002030e: ('mov', 'd0,(0xa26c3388)'),
        0x60020314: ('mov', '1610772759,a0'),
        0x6002031a: ('mov', '-1731198656,a1'),
        0x60020320: ('mov', 'a0,(a1)'),
        0x60020337: ('mov', 'd2,(0x98800240)'),
        0x6002033d: ('mov', '1610773877,a0'),
        0x60020343: ('mov', '-1731198652,a1'),
        0x60020349: ('mov', 'a0,(a1)'),
        0x6002035e: ('mov', 'd2,(0x98800244)'),
        0x60020364: ('mov', 'd2,d0'),
        0x60020365: ('mov', 'd0,(0xa26c3388)'),
        0x60020392: ('call', '0x6003009c,[],0'),
    }),
    'ready_predicate': (0x6002067a, 0x600206a0, {
        0x6002067a: ('movbu', '(0x8ff00058),d0'),
        0x60020680: ('cmp', '1,d0'),
        0x60020682: ('bne', '0x60020698'),
        0x60020684: ('movbu', '(0x8ff00059),d0'),
        0x6002068a: ('cmp', '1,d0'),
        0x6002068c: ('bne', '0x60020698'),
        0x6002068e: ('movbu', '(0x8ff0005a),d0'),
        0x60020694: ('cmp', '1,d0'),
        0x60020696: ('beq', '0x6002069b'),
        0x60020698: ('clr', 'd0'),
        0x60020699: ('bra', '0x6002069d'),
        0x6002069b: ('mov', '1,d0'),
        0x6002069d: ('retf', '[],0'),
    }),
    'copy_entry': (0x6002144e, 0x6002145c, {
        0x60021452: ('call', '0x6002195b,[],4'),
    }),
    'copy_exit': (0x60021618, 0x60021621, {
        0x60021618: ('call', '0x60021984,[],4'),
        0x6002161d: ('clr', 'd0'),
        0x6002161e: ('ret', '[d2,d3,a2,a3],32'),
    }),
    'copy_lock_ready_gates': (0x6002195b, 0x600219ab, {
        0x6002195b: ('call', '0x6002067a,[],0'),
        0x60021960: ('cmp', '1,d0'),
        0x60021962: ('bne', '0x60021981'),
        0x6002196d: ('call', '0x6005168d,[d2,d3,a2],40'),
        0x60021981: ('ret', '[],4'),
        0x60021984: ('call', '0x6002067a,[],0'),
        0x60021989: ('cmp', '1,d0'),
        0x6002198b: ('bne', '0x600219a8'),
        0x60021994: ('call', '0x60051762,[d2,d3],36'),
        0x600219a8: ('ret', '[],4'),
    }),
    'secondary_one_transfer': (0x600271ae, 0x600271b6, {
        0x600271ae: ('mov', '1610773001,a0'),
        0x600271b4: ('jmp', '(a0)'),
    }),
    'secondary_one_barrier': (0x60027209, 0x60027255, {
        0x60027212: ('call', '0x60054a7a,[a2],8'),
        0x60027219: ('mov', '(0xa26c3388),d0'),
        0x6002721f: ('cmp', '0,d0'),
        0x60027221: ('beq', '0x60027219'),
        0x60027223: ('mov', '-1589392896,a1'),
        0x60027229: ('mov', '1191184384,a0'),
        0x60027236: ('cmp', '1536,d1'),
        0x6002724e: ('call', '0x60027570,[],0'),
    }),
    'secondary_one_kernel': (0x60027570, 0x60027579, {
        0x60027570: ('jmp', '0x600325db'),
    }),
    'secondary_two_transfer': (0x6002760c, 0x60027614, {
        0x6002760c: ('mov', '1610774036,a0'),
        0x60027612: ('jmp', '(a0)'),
    }),
    'secondary_two_barrier': (0x60027614, 0x60027660, {
        0x6002761d: ('call', '0x60054a7a,[a2],8'),
        0x60027624: ('mov', '(0xa26c3388),d0'),
        0x6002762a: ('cmp', '0,d0'),
        0x6002762c: ('beq', '0x60027624'),
        0x6002762e: ('mov', '-1589392896,a1'),
        0x60027634: ('mov', '1191184384,a0'),
        0x60027641: ('cmp', '1536,d1'),
        0x60027659: ('call', '0x60027990,[],0'),
    }),
    'secondary_two_kernel': (0x60027990, 0x60027995, {
        0x60027990: ('jmp', '0x600325e9'),
    }),
    'primary_kernel': (0x6003009c, 0x600300a1, {
        0x6003009c: ('jmp', '0x600325ce'),
    }),
}


def inspect(decoded, objdump):
    main = decoded.read_bytes()
    if len(main) != 26214336:
        raise ValueError('unsupported decoded main length')
    witnesses = []
    for name, (start, end, rows) in GROUPS.items():
        asm = subprocess.check_output([str(objdump), '-D', '-z', '-b', 'binary', '-m', 'mn10300',
            '--insn-width=16', f'--adjust-vma={BASE:#x}', f'--start-address={start:#x}',
            f'--stop-address={end:#x}', str(decoded)], text=True)
        for pc, (mn, operands) in rows.items():
            require_instruction(asm, pc, mn, operands)
            witnesses.append(dict(group=name, address=hex(pc), mnemonic=mn, operands=operands))
    if main[0x600201fe-BASE:0x60020204-BASE] != bytes.fromhex('fca484d91862'):
        raise ValueError('whole original seam instruction changed')
    return dict(scope=__doc__, decoded_bytes=len(main), instruction_witness_count=len(witnesses),
        instruction_witnesses=witnesses,
        candidate=dict(site='0x600201fe', overwritten_instruction_bytes=6, resume='0x60020204',
            replay_load_word='0x6218d984', follows_local_kernel_copy_return=True,
            precedes_primary_secondary_setup_and_kernel_call=True),
        ready_gate=dict(addresses=['0x8ff00058', '0x8ff00059', '0x8ff0005a'],
            cleared_before_copy_locally=True, semaphore_operations_require_all_three_equal_one=True,
            predicate='0x6002067a', copy_wrappers=['0x6002195b', '0x60021984'],
            whole_copy_transitive_calls_proven=False),
        secondary_boot=dict(entry_registers=['0x98d00140', '0x98d00144'],
            entry_values=['0x60027117', '0x60027575'], ready_word='0xa26c3388',
            primary_release_store='0x60020365', wait_reads=['0x60027219', '0x60027624'],
            pre_barrier_calls=['0x60054a7a'], post_barrier_helper_copy_words=1536,
            kernel_targets=['0x600325db', '0x600325e9'],
            mmio_release_and_cross_core_visibility_verified=False),
        pool_bound_sites=['0x600229b9', '0x60022c28'],
        pool_bounds_inside_early_kernel_copy=False, boot_prefix_original_loading_proven=False,
        firmware_modified=False, firmware_built=False, camera_executed=False, hash_checks_performed=False,
        limits=['Exact local instruction order only, not complete CFG, callee, reset-source or interrupt closure.',
                'Secondary cores execute a native helper before their wait; they are not globally quiescent by proof.',
                'MMIO semantics, D2 liveness across every callee, cache and hardware publication are unverified.',
                'The copy helper locally returns zero; return does not establish successful transfer of all bytes.',
                'The boot-prefix load and allocator guard initialization remain outside this probe.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.decoded, args.objdump), indent=2))
