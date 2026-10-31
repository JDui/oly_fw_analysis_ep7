#!/usr/bin/env python3
"""Exercise actual named-send CALL frames through the linked native critical gate.

Stops before accepted queue I/O. Rejections execute the original error epilogue;
the named wrapper's ancestor return slot is explicit fixture input.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import STACK,require
from ep7_candidate_publish_sim import bootstrap_context,publish_runtime,u32,released,signed
from ep7_candidate_state_sim import CALL_SP,INPUT,gcc_call,guarded
from ep7_sim_probe import brief

SITES = (0x600514ec,0x60051550)
RAW_SEND,GATE,ACCEPT,REJECT = 0x60036ede,0x60036f93,0x60036f99,0x600370a3


def inspect(directory,prefix,engine,expect_legacy_bypass=False):
    base,front,syms,build,_ = bootstrap_context(directory,prefix,engine)
    machine,_,_,_ = publish_runtime(base,front,syms)
    runtime = u32(machine,syms['_ep7_native_runtime_slot'])
    obj = machine.regions['queue_4b'].address
    guarded(machine,'queue_gate_input',INPUT,b'\x5a'*28,'r')
    cases = []
    for site in SITES:
        instruction = machine.read(site,7)
        require(instruction==b'\xdd'+struct.pack('<i',RAW_SEND-site)+b'\xf0\x28',
                'named raw send is no longer the reviewed seven-byte CALL')
        for condition in ('valid','maximum_changed','io_closed'):
            m = machine.clone()
            if condition=='maximum_changed':
                m.mutate('queue_4b',24,struct.pack('<I',144))
            if condition=='io_closed':
                gcc_call(m,syms,'_ep7r_note_queue_delete',[runtime,obj])
            m.mutate('stack',CALL_SP+48-STACK,struct.pack('<I',syms['_ep7_queue_named_send_native_return']))
            front = m.run(site,GATE,overrides=dict(sp=CALL_SP,d0=0x4b,d1=28,a0=INPUT,
                a1=0 if site==SITES[0] else 0xffffffff),full_trace=True,limit=3000)
            require(front['status']=='returned' and front['registers']['sp']==CALL_SP-40,
                    'raw send did not reach its gate: '+str(brief(front)))
            w = front['registers']['sp']
            require(u32(m,w+40)==site+7 and u32(m,w+88)==syms['_ep7_queue_named_send_native_return'],
                    'actual native CALL frame did not contain the expected return chain')
            gated = m.resume(front['registers'],ACCEPT,breakpoints=[REJECT],full_trace=True,limit=3000)
            accepted = gated['status']=='returned' and gated['registers']['pc']==ACCEPT
            rejected = gated['status']=='breakpoint' and gated['registers']['pc']==REJECT
            require(accepted or rejected,'unexpected gate frontier: '+str(brief(gated)))
            expected = condition=='valid' or expect_legacy_bypass
            require(accepted==expected,'named-send ownership gate did not enforce the expected decision')
            row = dict(call_site=hex(site),actual_return=hex(site+7),condition=condition,
                front=brief(front),gate=brief(gated),accepted=accepted,queue_backing_unmapped=True,
                native_critical_entry_executed=True,
                gate_native_api_calls=sum(r['pc'] in (0x600317ac,0x600370af,0x60035b62)
                                          for r in gated['trace']))
            require(row['gate_native_api_calls']==0,'gate called a native API while inside kernel critical section')
            if rejected:
                end = m.resume(gated['registers'],site+7,full_trace=True,limit=3000)
                require(end['status']=='returned' and end['registers']['sp']==CALL_SP and
                        signed(end['registers']['d0'])==-42,'rejected send did not exit natively with -42')
                released(m)
                row.update(native_error_epilogue=brief(end),returned_status=-42,locks_released=True)
            cases.append(row)
    return dict(scope=__doc__,candidate_build_revision=build['source_revision'],
        actual_elf_code_equals_decoded_candidate=True,all_assertions_passed=True,
        expectation='known_legacy_bypass' if expect_legacy_bypass else 'ownership_checks_enforced',
        ownership_checks_passed=not expect_legacy_bypass,
        actual_named_return_sites=[hex(site+7) for site in SITES],cases=cases,
        hash_checks_performed=False,native_api_success_stubs=False,firmware_files_modified=False,
        hardware_executed=False,installable=False,
        limits=['Runtime and kernel context are created by the S2 probe with its explicit fixtures.',
                'Both actual seven-byte CALLs construct their native frames and execute original lookup/critical entry plus the linked gate. The outer named-wrapper return label is a fixture.',
                'Accepted calls stop before native queue I/O. Rejected calls execute the original critical-exit/return epilogue. Post-send notification and full queue send remain later tests.'])


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--expect-legacy-bypass',action='store_true',
                        help='record the already identified old-candidate defect, never a readiness pass')
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine,args.expect_legacy_bypass),indent=2))
