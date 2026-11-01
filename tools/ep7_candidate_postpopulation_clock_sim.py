#!/usr/bin/env python3
"""Continue postpopulation with explicit retained-controller register inputs.

The original register conversion and calendar routines run without API stubs.
Their synthetic inputs do not establish a physical controller or current time.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_message_sim import result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_device_state_sim import admit
from ep7_candidate_fresh_population_sim import fresh_population_context


def postpopulation_clock_context(directory,prefix,engine):
    upstream,contexts = fresh_population_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    context = contexts['cases'][0]
    machine = context['postpopulation_machine'].clone()
    # Match the existing bounded retained-controller modeling convention: only
    # explicitly selected register values exist. No generic MMIO zero mapping.
    register_inputs = [(0x98e00000,0,'rw'),(0x98e00098,1609459200,'r'),(0x98e0009c,0x002468a0,'r')]
    for address,value,permissions in register_inputs:
        admit(machine,f'postpopulation_register_model_{address:x}',address,struct.pack('<I',value),permissions)
    require(machine.read(0x6006d842,7) == b'\x80\x2a\xcd'+struct.pack('<h',0x60066cd0-0x6006d844)+bytes(2) and
            machine.read(0x602a8e98,6) == bytes.fromhex('fad17608f041') and
            machine.read(0x602a1fa0,6) == bytes.fromhex('fc8292dc2362'),
            'native ready-field writer or request-member consumer/source changed')
    stack = machine.regions['stack']
    machine.regions['stack'] = replace(stack,data=b'\xcc'*len(stack.data))
    # Execute the actual 42 constant and native RMW helper. This is the reviewed
    # ready-field publication slice, not the enclosing controller programming,
    # readback comparison, interrupt window or hardware handshake.
    ready = machine.run(0x6006d842,0x6006d849,overrides=dict(sp=CALL_SP),full_trace=True,limit=100)
    result_ok(machine,ready,0x6006d849,CALL_SP)
    require(machine.read(0x98e00000,4) == struct.pack('<I',42 << 2),
            'native retained-controller ready-field RMW changed')
    machine.regions['stack'] = stack
    continued = machine.resume(context['postpopulation_result']['registers'],0x602a44ba,
        full_trace=True,limit=60000,breakpoints=[base['syms']['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
    require(continued['status'] == 'memory_fault' and continued['fault'] == dict(
            kind=1,pc=0x602a8e9c,map=0,address=0x6223dc92,size=1,access='read') and
            machine.read(CAPTURE+24156,4) == struct.pack('<I',(0x002468a0 >> 5) & 0xffff) and
            machine.read(CAPTURE+23832,10) == struct.pack('<H6BH',2021,1,1,0,0,0,81,0),
            'native register conversion, calendar record or request frontier changed')
    trace = continued['trace']
    require(all(sum(t['pc'] == pc for t in trace) == 1
                for pc in (0x6006d68c,0x600fb44e,0x6006d58d,0x600fbbfd,0x600fb622)) and
            not any(t['pc'] in (0x600fb596,0x60061808,base['syms']['_ep7cn_population']) for t in trace),
            'native calendar conversion unexpectedly used fallback, logger or finish observer')
    rows = [stage('native_retained_controller_ready_field_slice',ready),
            stage('native_second_population_after_register_model',continued)]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        register_model=[dict(address=hex(a),value=hex(v),permissions=p) for a,v,p in register_inputs],
        register_model_bytes=12,conditional_BSS_bytes_added=0,
        native_ready_field=dict(start='0x6006d842',stop='0x6006d849',helper='0x60066cd0',value=42,
            original_program_and_readback_comparison_executed=False),
        capture_register_word=dict(offset=24156,value=0x2345,conversion='(register98e0009c >> 5) & 0xffff'),
        native_calendar=dict(offset=23832,bytes=10,year=2021,month=1,day=1,hour=0,minute=0,second=0,
            fractional_byte=81,status_halfword=0,data=machine.read(CAPTURE+23832,10).hex(),
            native_decoder_and_validator_returned=True,fallback_initializer_executed=False),
        frontier=dict(status=continued['status'],fault=continued['fault'],input_object='0x6223d41c',
            member_offset=2166,native_writer='0x602a1fa0',writer_enclosing_callback='0x602a1efa',
            native_reset_writer='0x602a49df',reset_enclosing_function='0x602a471d',
            input_message_bytes=76,input_type_member_offset=52,input_message_producer_executed=False),
        second_population_completed=False,finish_observer_executed=False,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Three explicitly modeled registers are synthetic stable readbacks. The seconds input denotes2021-01-01 and the subcounter input is intentionally nonzero; neither is a camera measurement or current clock.',
                'Only the original ready-field publication slice and its complete RMW helper execute. Controller programming, readback/handshake completion and real counter advancement remain unmodeled.',
                'The calendar decoder, validator and capture stores execute original code. No successful date record or return value is substituted.',
                'Execution stops before reading input-object member2166. One writer derives state from a76-byte message; another native path resets the member. Neither enclosing producer nor the rest of the object is replaced with zero-filled memory.',
                'The second population and finish observer remain incomplete; all inherited mode, geometry, task, lifetime, residency and recovery conditions still apply.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        postpopulation_machine=machine,postpopulation_result=continued)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(postpopulation_clock_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
