#!/usr/bin/env python3
"""Check the H/L handoff contract for the native-allocated COLOR4 capture.

Selected-handler exposure/format processing is an explicit completion boundary.
Only its real backlink store and the candidate source/FIFO/retirement paths run;
no unknown metadata is supplied and no complete selected handler is claimed.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import STACK, require
from ep7_candidate_state_sim import CALL_SP, SNAPSHOT, gcc_call, objects, ready_lock
from ep7_candidate_capture_sim import (ASSOCIATED, NODE, CAPTURE, WAIT, WAIT_BACKING,
                                      native_block, summarize_capture)
from ep7_candidate_capture_allocation_sim import NEW_CAPTURE
from ep7_candidate_node_factory_sim import NEW_NODE, sparse_read
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_selected_mailbox_sim import OUTPUT
from ep7_candidate_selected_parameters_sim import selected_parameters_context


def selected_handoff_context(directory, prefix, engine):
    upstream, contexts = selected_parameters_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    syms = base['syms']
    machine = contexts['cases'][0]['selected_parameters_machine'].clone()
    sidecar = syms['_ep7_controller_sidecar_unresolved']
    sealed = machine.read(sidecar,664)
    captures = [(address,machine.read(address,SIZE)) for address in (CAPTURE,NEW_CAPTURE)]
    require(sparse_read(machine,ASSOCIATED+8,4)==struct.pack('<I',NODE) and
            machine.read(OUTPUT+8,4)==struct.pack('<I',NEW_NODE) and
            machine.read(NEW_NODE+8,4)==struct.pack('<I',ASSOCIATED) and
            machine.read(0x602a2901,5)==bytes.fromhex('f003f81808') and
            sparse_read(machine,WAIT+12,6)==struct.pack('<HHH',0,1,1),
            'selected node, backlink publication or existing FIFO state changed')
    machine.mutate('snapshot',0,b'\xcc'*25)
    stale = gcc_call(machine,syms,'_ep7q_capture_snapshot_unresolved',
                     [2,ASSOCIATED,SNAPSHOT],wanted=0)
    require(machine.read(SNAPSHOT,25)==b'\xcc'*25 and machine.read(sidecar,664)==sealed,
            'stale backlink copied values or changed the new sealed generation')
    # Replace only this previously read-only four-byte store destination.
    # Preserve its existing bytes and the adjacent one-byte padding protection.
    name,row = next((n,r) for n,r in machine.regions.items()
                    if r.address<=ASSOCIATED+8 and ASSOCIATED+12<=r.address+len(r.data))
    require(row.address==ASSOCIATED+7 and len(row.data)==5 and row.permissions=='r',
            'backlink fixture extent changed')
    del machine.regions[name]
    machine.regions['selected_associated_padding7'] = replace(row,
        name='selected_associated_padding7',data=row.data[:1])
    machine.regions['selected_associated_backlink'] = replace(row,
        name='selected_associated_backlink',address=ASSOCIATED+8,data=row.data[1:],permissions='rw',capture=True)
    # D2 is the actual mailbox-selected node. A3 is node+8, as computed by the
    # surrounding original handler. Earlier native exposure calls are not run.
    publication = native_block(machine,syms,0x602a2901,0x602a2906,
                                dict(d2=NEW_NODE,a3=NEW_NODE+8),limit=20)
    require(sparse_read(machine,ASSOCIATED+8,4)==struct.pack('<I',NEW_NODE),
            'original backlink store did not publish the selected native node')
    copied = gcc_call(machine,syms,'_ep7q_capture_snapshot_unresolved',
                      [2,ASSOCIATED,SNAPSHOT],wanted=1)
    frozen = bytes([3,5]+[0]*11+[0xfd]+[0]*11)
    require(machine.read(SNAPSHOT,25)==frozen and machine.read(sidecar,664)==sealed,
            'selected source copy lost the original COLOR4 H/L snapshot')
    queued = native_block(machine,syms,0x602ac3f6,0x602ac3fd,
                           dict(a0=WAIT,d0=ASSOCIATED))
    require(queued['registers']['d0']==4 and
            sparse_read(machine,WAIT+12,6)==struct.pack('<HHH',1,2,1) and
            sparse_read(machine,WAIT_BACKING+4,4)==struct.pack('<I',ASSOCIATED),
            'actual delayed enqueue lost the second FIFO position')
    canceled = machine.clone()
    revoked = gcc_call(canceled,syms,'_ep7cn_prewrite',[NEW_CAPTURE,0])

    def pop(case):
        # Same reviewed ancestor-frame contract used by the earlier FIFO probe.
        case.mutate('stack',CALL_SP+8-STACK,struct.pack('<I',syms['_ep7_wait_scope_native_return']))
        case.mutate('stack',CALL_SP+80-STACK,struct.pack('<I',0x602ac502))
        case.mutate('stack',CALL_SP+32-STACK,b'\xcc'*32)
        result = native_block(case,syms,0x602ac5e8,0x602ac5ef,dict(a0=WAIT))
        require(result['registers']['d0']==ASSOCIATED and
                sparse_read(case,WAIT+12,6)==struct.pack('<HHH',0,2,2),
                'native pop changed FIFO identity/order')
        return result,case.read(CALL_SP+32,32)

    consumed,scope = pop(machine)
    canceled_pop,canceled_scope = pop(canceled)
    require(scope==struct.pack('<I',2)+frozen+b'\x01\0\0' and canceled_scope==bytes(32),
            'valid/revoked handoff scope differs')
    for case in (machine,canceled):
        require(all(case.read(address,SIZE)==data for address,data in captures),
                'H/L handoff changed original capture fields')
        _,_,_,provider = objects(case,syms)
        ready_lock(case,provider)
    rows = [summarize_capture(name,result) for name,result in (
        ('old_backlink_refused',stale),('original_selected_backlink_store',publication),
        ('new_generation_source_copy',copied),('actual_delayed_enqueue',queued),
        ('capture_prewrite_revokes_delayed_value',revoked),('actual_delayed_pop',consumed),
        ('actual_delayed_pop_after_revocation',canceled_pop))]
    report = dict(scope=__doc__,status='passed',candidate_build_revision=upstream['candidate_build_revision'],
        cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        native_store_permissions_opened=4,new_input_bytes=0,unknown_metadata_fields_supplied=False,
        original_selected_handler_completed=False,mailbox_node=hex(NEW_NODE),capture=hex(NEW_CAPTURE),
        associated=hex(ASSOCIATED),capture_id=2,frozen_snapshot=list(struct.unpack('<B24b',frozen)),
        original_capture_bytes_unchanged=True,stale_backlink_rejected=True,
        delayed_snapshot_preserved=True,revocation_preserves_native_FIFO_order=True,
        hash_checks_performed=False,native_api_success_stubs=False,hardware_executed=False,installable=False,
        limits=['The actual native allocation, new COLOR4 population/freeze and mailbox results are inherited. Their documented input and scheduling assumptions remain.',
                'The real handler backlink store is entered at its reviewed two-instruction seam. Its earlier exposure/format/notification calls and later finalizer are not executed or assumed verified.',
                'Native source/FIFO hooks execute with the live selected node/capture and explicit sequential ownership; no producer result is inserted into unknown metadata.',
                'Ancestor stack words at the delayed-pop seam are explicit caller fixtures. Full controller task, concurrent lifetime closure and downstream worker/photo pixels remain outside this check.',
                'This closes a basic H/L data-handoff contract, not code/RAM ownership, physical boot or independent recovery.'])
    return report,dict(upstream=contexts,cases=[dict(handoff_machine=machine,canceled_machine=canceled)])


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(selected_handoff_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
