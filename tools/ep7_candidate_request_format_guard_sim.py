#!/usr/bin/env python3
"""Reproduce the native request-format rejection of a capture-only registry row.

Intermediate ROM-derived format fields are retained as failure evidence only.
The incomplete producer never supplies the waiting population consumer.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import native_call
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_request_constructor_sim import request_constructor_context, OBJECT, PACKET


FORMAT = OBJECT+496
FORMAT_MEMBERS = [(0,2),(4,4),(8,2),(12,26),(40,2),(44,16),(60,1),
                  (64,16),(80,2),(82,1),(84,4),(88,4),(92,4)]


def request_format_guard_context(directory,prefix,engine):
    upstream,contexts = request_constructor_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    context = contexts['cases'][0]
    machine = context['request_machine'].clone()
    capture = machine.read(CAPTURE,SIZE)
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    require(machine.read(0x6029b870,3) == bytes.fromhex('f8ed01') and
            machine.read(0x6029bef6,7) == bytes.fromhex('f060f8e401f070') and
            machine.read(0x6223d190,2) == struct.pack('<H',4),
            'native format registry guard, allocation writer or input fixture changed')
    selected = native_call(machine,base['syms'],0x602a65bd,0,0,dict(a0=OBJECT,a1=PACKET),limit=2000)
    require(selected['registers']['d0'] == 0x10000 and
            machine.read(OBJECT+1660,2) == bytes(2), 'native format class or caller state changed')
    gaps = missing_bytes(machine,[FORMAT+offset+i for offset,size in FORMAT_MEMBERS for i in range(size)],
        0xa5,'native_request_format_output')
    require(len(gaps) == 84, 'reviewed format output extent changed')
    stack = machine.regions['stack']
    data = bytearray(stack.data)
    struct.pack_into('<I',data,CALL_SP+8-stack.address,OBJECT)
    struct.pack_into('<I',data,CALL_SP+20-stack.address,PACKET)
    machine.regions['stack'] = replace(stack,data=bytes(data))
    # Two explicit enclosing-frame pointers and D2=0 from602a5482 permit the
    # actual argument suffix and CALL to run. The branch choosing this suffix
    # and the rest of the enclosing controller function are not executed.
    attempted = machine.run(0x602a549b,0x602a54bb,
        overrides=dict(sp=CALL_SP,d0=selected['registers']['d0'],d2=0),full_trace=True,limit=20000,
        breakpoints=[0x60061808,0x6040e126,base['syms']['_ep7_gcc_quarantine']])
    registers,trace = attempted['registers'],attempted['trace']
    require(attempted['status'] == 'breakpoint' and attempted['fault'] is None and
            registers['pc'] == 0x60061808 and registers['d0'] == 0x25000402 and
            registers['d1'] == 1 and registers['mdr'] == 0x6029b89b,
            'capture-only registry row no longer reaches the native format diagnostic')
    # The logger CALL has already reserved112B when the breakpoint fires.
    args = struct.unpack('<5I',machine.read(registers['sp']+116,20))
    require(args == (4,528,1,0,0x73) and
            sum(t['pc'] == 0x6029b870 and t['d1'] == 4 for t in trace) == 1 and
            not any(t['pc'] in (0x6029b89e,0x603dba87,0x605556d7) for t in trace) and
            machine.read(FORMAT+88,4) == b'\xa5'*4 and machine.read(CAPTURE,SIZE) == capture,
            'native rejection was bypassed, format pointer fabricated or capture changed')
    require(machine.read(FORMAT+12,8) == bytes.fromhex('700032005014400f') and
            machine.read(FORMAT+80,2) == struct.pack('<H',12),
            'intermediate original ROM-derived geometry changed')
    rows = [stage('native_request_format_class',selected),stage('native_format_registry_rejection',attempted)]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        native_store_capacity_added=84,conditional_BSS_bytes_added=0,
        native_format_class='0x10000',native_ROM_row='0x6055ca20',format_record=hex(FORMAT),
        intermediate_fields=dict(coordinates=[112,50],dimensions=[5200,3904],field80=12,
            missing_buffer_pointer_offset=88,unwritten_pointer_poison='a5a5a5a5',consumed_by_population=False),
        registry_guard=dict(row='0x6223d190',owned_capture_id=1,actual_flags=4,required_mask=1,
            guard_pc='0x6029b870',native_diagnostic='0x25000402',severity=1,arguments=list(args),
            allocation_flag_writer='0x6029befb',allocation_function='0x6029be82',
            allocation_dependency='0x603db792',native_allocation_executed=False),
        property_lookups=[hex(t['d0'] & 0xffff) for t in trace if t['pc'] == 0x6005d924],
        producer_completed=False,postpopulation_resumed=False,capture_unchanged=True,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['This is the original native rejection, not a successful format constructor. Existing capture flag4 does not satisfy allocation mask1 required by6029b85a.',
                'Native class selection and the actual caller argument suffix execute with two explicit enclosing-frame pointers. The outer branch, queue transport and whole controller event are not executed.',
                '84 reviewed output bytes start withA5. Original ROM/property code writes intermediate fields, but record+88 remainsA5 when the guard rejects; the partial record is never handed to population.',
                'No flag is patched to5 and no ID0 alternative is substituted. The native writer6029be82 depends on actual resource allocation through603db792; that lifecycle is the next required work.',
                'Second population/finish, active COLOR, relay/worker lifecycle, residency and recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        format_probe_machine=machine,format_probe_result=attempted)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(request_format_guard_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
