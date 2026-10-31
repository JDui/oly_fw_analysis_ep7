#!/usr/bin/env python3
"""Trace managed mailbox handles and execute the early-active slot window.

Reuses the existing strict GNU engine. Starts after the registry lock call and
after lookup; no lock implementation, scheduling, allocator or raw delete runs.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_native_stack import BASE, NativeGraph
from ep7_irq_stack import span
from ep7_sim_probe import run, brief, capture

GLOBAL = 0x61fa8f98
REGISTRY = 0x19020000
SLOTS = 0x19021000
STACK = 0x19010000
SP = STACK + 128
REFS = [0x60779584, 0x607795af, 0x607795f9, 0x60779610,
        0x6077967a, 0x607796c7, 0x6077971c, 0x60779757,
        0x607797b6, 0x607797e7, 0x607798a0]
W = {
    # The private cell names a generic 32-slot registry, not the kernel table.
    0x60779582: ('mov', '(0x61fa8f98),a1'),
    0x607795a2: ('mov', '32,d0'),
    0x607795a4: ('call', '0x6076dd09,[a2],8'),
    0x607795ad: ('mov', 'd0,(0x61fa8f98)'),
    0x6076dd9f: ('udfu01', '28,d0'),
    0x6076dd98: ('mov', '(4,a0),a0'),
    0x6076dda2: ('add', 'd0,a0'),
    0x6076de5a: ('udfu01', '28,d2'),
    0x6076de6d: ('mov', 'a0,(a2)'),
    0x6076de6f: ('clr', 'd0'),
    0x6076de70: ('mov', 'd2,d1'),
    0x6076de71: ('call', '0x4700115e,[d2,a2],8'),
    0x6076de78: ('mov', 'd3,(8,a3)'),
    # Reserve marks active before dropping its internal lock. It neither clears
    # nor fills the raw mailbox word. Optional name copy starts at slot+8.
    0x6076ddab: ('mov', 'a1,(8,sp)'),
    0x6076ddad: ('mov', 'a0,(4,sp)'),
    0x6076ddaf: ('mov', 'd0,d3'),
    0x6076ddb0: ('mov', '0,a3'),
    0x6076ddb9: ('call', '0x607684f9,[],4'),
    0x6076ddde: ('movbu', 'd0,(d1,a0)'),
    0x6076de0b: ('movbu', 'd0,(d1,a0)'),
    0x6076de28: ('mov', '8,a0'),
    0x6076de2c: ('mov', '15,d0'),
    0x6076de2e: ('call', '0x47001052,[d2,d3,a2,a3],28'),
    0x6076de3c: ('call', '0x60768509,[],4'),
    0x6076de43: ('mov', 'a3,d0'),
    # Release invalidates, but preserves the old raw mailbox word at +4.
    0x6076dd6e: ('clr', 'd0'),
    0x6076dd6f: ('movbu', 'd0,(8,a0)'),
    0x6076dd76: ('mov', 'd0,(24,a0)'),
    0x6076dd7b: ('movbu', 'd0,(d2,a0)'),
    # Requested public ID selects a registry slot, not a raw mailbox handle.
    0x607795ef: ('clr', 'd0'),
    0x607795f0: ('cmp', '1,a0'),
    0x607795f2: ('bne', '0x607795f7'),
    0x607795f4: ('mov', '(20,sp),a0'),
    0x607795f6: ('mov', '(a0),d0'),
    0x607795fd: ('call', '0x6076ddab,[d2,d3,a2,a3],28'),
    0x60779604: ('mov', 'd0,(8,sp)'),
    0x60779614: ('call', '0x6076dd8e,[],0'),
    0x6077961b: ('mov', 'a0,(16,sp)'),
    0x607796e2: ('clr', 'd0'),
    0x607796e3: ('movbu', 'd0,(44,sp)'),
    0x607796e6: ('movhu', 'd0,(46,sp)'),
    0x607796e9: ('mov', 'd0,(48,sp)'),
    0x607796ee: ('call', '0x6003032f,[d2,a2,a3],20'),
    0x607796fb: ('call', '0x6005379c,[d2],8'),
    0x60779702: ('cmp', '0,d0'),
    0x60779704: ('ble', '0x6077971a'),
    0x60779706: ('mov', '(16,sp),a0'),
    0x60779708: ('mov', 'd0,(4,a0)'),
    0x6077970d: ('mov', 'a3,(24,a0)'),
    0x60779710: ('mov', '(8,sp),d0'),
    0x60779712: ('mov', '(20,sp),a0'),
    0x60779714: ('mov', 'd0,(a0)'),
    # Error reporter preserves the original D0; it does not invent an ID.
    0x6005379c: ('mov', 'd0,d2'),
    0x6005379d: ('cmp', '0,d2'),
    0x6005379f: ('bge', '0x600537ae'),
    0x600537ae: ('mov', 'd2,d0'),
    0x600537af: ('ret', '[d2],8'),
    # Delete checks only lookup/null/active before reading +4.
    0x6077975b: ('call', '0x6076dd8e,[],0'),
    0x60779762: ('mov', 'a0,a2'),
    0x60779767: ('movbu', '(a2),d0'),
    0x60779769: ('cmp', '0,d0'),
    0x6077976b: ('bne', '0x60779770'),
    0x60779770: ('mov', '(4,a2),d0'),
    0x60779773: ('exth', 'd0'),
    0x60779774: ('call', '0x6003769a,[d2,d3,a2,a3],24'),
    0x607797bc: ('call', '0x6076dd48,[d2,a2],12'),
    # General receive/send use the same record and never return its pointer.
    0x607797eb: ('call', '0x6076dd8e,[],0'),
    0x60779828: ('mov', '(4,a2),d0'),
    0x607798a4: ('call', '0x6076dd8e,[],0'),
    0x60779945: ('mov', '(4,a0),d0'),
    0x6077995c: ('mov', '(4,a0),d0'),
}


def inspect(decoded, objdump, engine):
    graph = NativeGraph(decoded, objdump)
    try:
        for pc, expected in W.items():
            if graph.instruction(pc)[2:] != expected:
                raise ValueError(('registry witness changed', hex(pc), expected))
        data = graph.data
        refs = []
        pos = 0
        while (pos := data.find(struct.pack('<I', GLOBAL), pos)) >= 0:
            refs.append(BASE + pos)
            pos += 1
        if refs != REFS:
            raise ValueError('private registry literal inventory changed')
        vtable = struct.unpack_from('<4I', data, 0x60a7ff68 - BASE)
        if vtable != (0x607795b7, 0x6077973a, 0x607797c8, 0x6077988a):
            raise ValueError('managed mailbox vtable changed')
        # Keep a complete inventory of the two short mutation bodies. All their
        # writes are byte +0, optional name +8, and release +24; never raw +4.
        bodies = {}
        for name, lo, hi in [('reserve', 0x6076ddab, 0x6076de48),
                             ('release', 0x6076dd48, 0x6076dd8e)]:
            rows = span(graph, lo, hi)
            bodies[name] = [dict(pc=hex(pc), mnemonic=mn, operands=ops)
                            for pc, _, mn, ops in rows]
        checked = len(graph.decoded_instructions)
    finally:
        graph.close()

    from penf_emulator import Region
    cases = []
    # A zero-filled never-used slot and a released slot with an old handle are
    # sufficient to distinguish reservation from completed object publication.
    for old_handle in (0, 2):
        slots = bytearray(32 * 28)
        slots[0] = 1
        struct.pack_into('<I', slots, 4, 3)
        struct.pack_into('<I', slots, 28 + 4, old_handle)
        stack = bytearray(256)
        struct.pack_into('<II', stack, SP - STACK + 4, REGISTRY, 0)
        regions = [
            Region('reserve_body', 0x6076ddc0,
                   data[0x6076ddc0 - BASE:0x6076de35 - BASE], 'rx'),
            Region('registry_fixture', REGISTRY, struct.pack('<3I', 0, SLOTS, 32)),
            Region('slots_fixture', SLOTS, bytes(slots), 'rw', True),
            Region('stack_fixture', STACK, bytes(stack), 'rw', True),
        ]
        reserved = run(engine, regions, dict(pc=0x6076ddc0, sp=SP, d3=0, a3=0),
                       stop=0x6076de35, limit=100)
        updated = capture(reserved, 'slots_fixture')
        expected = bytearray(slots)
        expected[28] = 1
        if (reserved['status'] != 'returned' or reserved['registers']['a3'] != 2
                or updated != expected):
            raise ValueError(('reservation state differs', brief(reserved)))
        # Supply the selected lookup result and execute the real delete prefix.
        # Stop BEFORE the raw kernel delete CALL: no destruction is performed.
        deletion = run(engine, [
            Region('delete_prefix', 0x60779762,
                   data[0x60779762 - BASE:0x60779774 - BASE], 'rx'),
            replace(regions[2], data=updated),
        ], dict(pc=0x60779762, sp=SP, a0=SLOTS + 28),
            stop=0x60779774, limit=20)
        if (deletion['status'] != 'returned'
                or deletion['registers']['d0'] != old_handle
                or capture(deletion, 'slots_fixture') != updated):
            raise ValueError(('delete did not observe the retained handle', brief(deletion)))
        cases.append(dict(previous_raw_handle=old_handle, selected_registry_id=2,
            reserve=brief(reserved), active_before_raw_handle_publication=True,
            only_changed_byte='slot[1]+0', delete_prefix=brief(deletion),
            raw_delete_argument=deletion['registers']['d0'], raw_delete_executed=False))

    return dict(scope=__doc__, checked_witnesses=len(W),
        exact_decoded_instruction_addresses=checked,
        registry_cell=hex(GLOBAL), registry_capacity=32, slot_bytes=28,
        literal_references=[hex(p) for p in refs],
        vtable=[hex(p) for p in vtable], mutation_bodies=bodies, cases=cases,
        normal_raw_handle_source='positive unchanged return of native mailbox creation',
        output_public_id_is_registry_id=True,
        active_is_completed_publication=False, release_clears_raw_handle=False,
        observed_concurrent_race=False, full_handle_alias_closure=False,
        mailbox1_delete_unreachable_proven=False, callback_serialization_proven=False,
        all_assertions_passed=True, hash_checks_performed=False,
        firmware_modified=False, firmware_built=False, hardware_executed=False,
        limits=[
            'The literal scan covers decoded main only; derived/escaped aliases and other components are not excluded.',
            'Native reserve execution starts after lock acquisition and stops before unlock; lock calls, name copy, allocation and initialization are not simulated.',
            'Native delete execution starts after lookup with the selected slot address and stops before raw kernel deletion.',
            'Early active plus stale handle is a demonstrated local publication gap, not a demonstrated live scheduling race.',
            'Mailbox1 exclusion is only conditional on initialization, all +4 writers following the reviewed creation path, occupied kernel slot1, and no other deleting/alias-writing route.'
        ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.decoded, args.objdump, args.engine), indent=2))
