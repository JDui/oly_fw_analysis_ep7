#!/usr/bin/env python3
"""Locate the real capture-template initializer's unresolved property dependency.

Run original6030002c/60301170 in a cloned published-runtime fixture. A poisoned,
bounded template is writable; missing property state stays unmapped. This report
records a native execution frontier, not a successful template initialization.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER,require
from ep7_candidate_state_sim import CALL_SP,guarded
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_descriptor_sim import descriptor_context
from ep7_candidate_message_sim import summarize_message
from penf_emulator import Region

TEMPLATE,SIZE = 0x6225882c,27332


def inspect(directory,prefix,engine):
    upstream,context = descriptor_context(directory,prefix,engine)
    machine = context['machine'].clone()
    source = machine.read(CAPTURE,24084)
    # This independent initializer call must not reuse the materializer's live
    # enclosing stack as though it belonged to the same continuation.
    stack = machine.regions['stack']
    machine.regions['stack'] = replace(stack,data=b'\xcc'*len(stack.data))
    guarded(machine,'native_capture_template',TEMPLATE,b'\xa5'*SIZE)
    # 60300055 loads this template and copies 6833 words to the original capture.
    # Validate the observed bound without running the unsafe partial copy.
    require(machine.read(0x60300055,10)==bytes.fromhex('fcdd2c8825622d4fe5db'),
            'native capture template pointer/copy word count changed')
    machine.regions['caller'] = Region('caller',CALLER,
        b'\xdd'+struct.pack('<i',0x6030002c-CALLER)+bytes([0,4]),'rx')
    result = machine.run(CALLER,CALLER+7,overrides=dict(sp=CALL_SP),full_trace=True,limit=20000,
        breakpoints=[context['syms']['_ep7_gcc_quarantine']])
    expected_fault = dict(kind=1,pc=0x6005d924,map=0,address=0xa26ffa84,size=2,access='read')
    require(result['status']=='memory_fault' and result['fault']==expected_fault,
            'capture template frontier changed: '+str(result['fault']))
    trace = result['trace']
    dispatch = result['registers']
    require(sum(r['pc']==0x60301170 for r in trace)==1 and
            machine.read(CAPTURE,24084)==source,
            'native initializer entry or unchanged source boundary changed')
    data = machine.read(TEMPLATE,SIZE)
    changed = [i for i,b in enumerate(data) if b!=0xa5]
    row = summarize_message('native_capture_template_initializer_frontier',result,CALL_SP)
    row['d0_at_stop'] = row.pop('returned_d0')
    return dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),frontier_identified=True,template_initialization_passed=False,
        case=row,
        template=dict(address=hex(TEMPLATE),bytes=SIZE,initial_fill='a5',
                      bytes_different_from_initial_fill=len(changed),
                      first_difference=changed[0] if changed else None,
                      last_difference=changed[-1] if changed else None),
        native_property_dispatch=dict(entry='0x6005d924',property_key=hex(dispatch['d0'] & 0xffff),
                                      native_return_pc=hex(dispatch['mdr'])),
        missing_property_state=hex(expected_fault['address']),
        source_capture_unchanged=True,partial_template_copied_to_capture=False,
        hash_checks_performed=False,native_api_success_stubs=False,firmware_files_modified=False,
        hardware_executed=False,installable=False,
        limits=['Upstream conditional runtime/capture/message fixtures remain. The template call runs on a cloned machine with a fresh stack, not a proven boot-order continuation.',
                'The 27332-byte template bound follows the actual 6833-word copy at60300055, not a claim that the entire41984-byte capture allocation is initialized.',
                'The original initializer executes until the native property dispatcher reads unmappeda26ffa84. No zero or successful getter value is supplied to advance it.',
                'Partially initialized template is never copied to the capture. Later capture population, relay preprocessing and worker job construction remain unresolved.'])


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine),indent=2))
