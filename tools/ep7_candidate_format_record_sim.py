#!/usr/bin/env python3
"""Execute the native cold format-record reset and resume the actual producer.

Seven source-record bytes assume the witnessed startup BSS clear. Native field
reset supplies the other three; the current record is populated by native copy.
This is a cold lifecycle scenario, not measured active camera state.
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
from ep7_candidate_snapshot_sim import call_prefix, stage
from ep7_candidate_message_sim import result_ok
from ep7_candidate_device_state_sim import admit
from ep7_candidate_format_state_sim import format_context
from ep7_candidate_diagnostic_buffers import initialize_diagnostic_buffers


STATE, CURRENT, RESET_SOURCE = 0xa2788cb0,0xa2788cec,0xa2788cf6


def missing_bytes(machine, addresses, value, name):
    gaps = sorted(a for a in addresses if not any(
        r.address<=a<r.address+len(r.data) for r in machine.regions.values()))
    intervals = []
    for address in gaps:
        if intervals and intervals[-1][1] == address:
            intervals[-1][1] += 1
        else:
            intervals.append([address,address+1])
    for low,high in intervals:
        admit(machine,f'{name}_{low:x}',low,bytes([value])*(high-low))
    return gaps


def coalesce_record(machine, address, size, name):
    parts = [(key,r) for key,r in machine.regions.items()
             if r.address<address+size and address<r.address+len(r.data)]
    require(all(address<=r.address<r.address+len(r.data)<=address+size for key,r in parts),
            'record merge would consume adjacent state')
    record = b''.join(machine.read(a,1) for a in range(address,address+size))
    for key,r in parts:
        del machine.regions[key]
    admit(machine,name,address,record)
    return record


def prepare_record_reset(machine):
    require(machine.read(0x60556b40,6)==bytes.fromhex('fc83f88c78a2') and
            machine.read(0x60556b53,6)==bytes.fromhex('fc82fe8c78a2') and
            machine.read(0x606d4615,2)==bytes.fromhex('9546') and
            machine.read(0x606d4634,2)==bytes.fromhex('903c') and
            machine.read(0x606d4620,2)==bytes.fromhex('85fb') and
            machine.read(0x606d463b,10)==bytes.fromhex('f0612102f070200244d9') and
            machine.read(0x606d6733,13)==bytes.fromhex('953cf16185fbdbf0612102f070'),
            'native record initialization/copy extent changed')
    #The native reset wrote percentage100 and byte8=0. The remaining source
    #bytes are a named cold-BSS precondition, never generic unmapped zero-fill.
    require(machine.read(RESET_SOURCE+2,2)==struct.pack('<H',100) and
            machine.read(RESET_SOURCE+8,1)==b'\0' and
            machine.read(0x60020068,12)==bytes.fromhex('fccd886879a2fccc00af1c62') and
            0x621caf00<=RESET_SOURCE-0x40000000<RESET_SOURCE+10-0x40000000<=0x62796888,
            'native reset source or BSS provenance changed')
    source_gaps = missing_bytes(machine,range(RESET_SOURCE,RESET_SOURCE+10),0,'format_reset_source_BSS')
    require(source_gaps == [RESET_SOURCE+i for i in (0,1,4,5,6,7,9)],
            'format reset source has unexpected unwritten bytes')
    current_gaps = missing_bytes(machine,range(CURRENT,CURRENT+10),0xa5,'format_current_copy_destination')
    require(current_gaps == [CURRENT+i for i in (0,1,4,5,6,7,9)],
            'current format record has unexpected write coverage')
    source = coalesce_record(machine,RESET_SOURCE,10,'native_format_reset_record')
    previous = coalesce_record(machine,CURRENT,10,'native_format_current_record')
    #Only actual indirect reset store destinations become writable; existing
    #native state bytes are preserved. All stores use the published STATE.
    writes = [(0x606d45b9,55,1),(0x606d45c2,54,1),(0x606d45cb,53,1),
              (0x606d45d4,57,1),(0x606d45e0,56,1),(0x606d45ea,94,2),
              (0x606d45f3,35,1),(0x606d460c,43,1),(0x606d4617,44,1),
              (0x606d4622,41,1),(0x606d462b,42,1)]
    addresses = set()
    for pc,offset,width in writes:
        require(machine.read(pc,3)==bytes([0xf8,0x50 if width==1 else 0x70,offset]),
                'record-reset prefix gained an unreviewed indirect store')
        addresses.update(range(STATE+offset,STATE+offset+width))
    state_gaps = missing_bytes(machine,addresses,0xa5,'native_format_reset_state')
    return source,previous,source_gaps,current_gaps,state_gaps


def record_context(directory, prefix, engine):
    upstream, contexts = format_context(directory,prefix,engine,diagnostic_setup=initialize_diagnostic_buffers)
    syms = contexts['upstream']['upstream']['upstream']['upstream']['syms']
    rows, outputs = [], []
    for index,context in enumerate(contexts['cases']):
        machine = context['machine']
        capture = machine.read(CAPTURE,SIZE)
        producer_stack, producer_caller = machine.regions['stack'],machine.regions['caller']
        machine.regions['stack'] = replace(producer_stack,data=b'\xcc'*len(producer_stack.data))
        source,previous,source_gaps,current_gaps,state_gaps = prepare_record_reset(machine)
        require(machine.read(0x60022321,12)==bytes.fromhex('fca54c019098fcccffffff3f'),
                'original diagnostic timestamp register/subtraction changed')
        timer_input,timestamp = 0x3fffedcb,0x1234
        admit(machine,'explicit_diagnostic_timestamp_register',0x9890014c,
              struct.pack('<I',timer_input),'r')
        reset = call_prefix(machine,0x606d4593,0,4,0x606d4645,limit=10000)
        result_ok(machine,reset,0x606d4645,CALL_SP-4)
        copied = [r for r in reset['trace'] if r['pc']==0x606d463f]
        require(len(copied)==5 and machine.read(CURRENT,10)==source and all(
            r['a0']==CURRENT+2*i and r['a1']==RESET_SOURCE+2*(i+1) and
            r['d0']==struct.unpack_from('<H',source,2*i)[0] for i,r in enumerate(copied)),
            'native reset did not copy all five source halfwords')
        times = [r for r in reset['trace'] if r['pc']==0x6002231e]
        require(len(times)==1 and times[0]['d0']==timestamp,
                'native diagnostic timestamp did not reflect the explicit input')
        ring_counts = [struct.unpack('<I',machine.read(a,4))[0] for a in (0xa2788f6c,0xa2788f74)]
        buffers = [int(a,16) for a in context['diagnostic_buffers']['pointers']]
        log_text = machine.read(0x60727f2e,8).split(b'\0',1)[0].ljust(8,b' ')
        log_entry = machine.read(buffers[0],16)
        require(ring_counts==[1,0] and
                log_entry==log_text+struct.pack('<II',timestamp,0) and
                machine.read(buffers[1],16)==b'\x3f'+b'\xa5'*7+bytes(8),
                'native reset diagnostic entry, timestamp or ring cursors differ')
        machine.regions['stack'],machine.regions['caller'] = producer_stack,producer_caller
        destination = context['producer_result']['registers']['a0']
        produced = machine.resume(context['producer_result']['registers'],0x60409ecb,
            full_trace=True,limit=80000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
        fault = produced['fault'] or {}
        require(produced['status']=='memory_fault' and
                (fault.get('pc'),fault.get('address'),fault.get('size'),fault.get('access')) ==
                (0x6030b752,0xa273104a,2,'read') and
                produced['registers']['mdr']==0x60309e5c,
                'snapshot producer did not stop at the uninitialized history selector')
        consumer_writes = [r for r in produced['trace'] if r['pc']==0x606d673e]
        require(len(consumer_writes)>=5 and all(r['a0']==destination+2*i and
            r['a1']==CURRENT+2*(i+1) and r['d0']==struct.unpack_from('<H',source,2*i)[0]
            for i,r in enumerate(consumer_writes[:5])),
            'resumed original getter did not copy the native current record')
        require(machine.read(CAPTURE,SIZE)==capture,'format-record probe changed partial capture')
        cases = [stage('native_diagnostic_buffer_allocation_and_cold_suffix',context['diagnostic_result']),
                 stage('native_format_record_reset_prefix',reset),stage('native_snapshot_resume_with_cold_record',produced)]
        rows.append(dict(gpio80_input_bit4=index,cases=cases,
            reset_source=hex(RESET_SOURCE),reset_source_bytes=source.hex(),
            diagnostic_buffers=context['diagnostic_buffers'],
            timestamp_register=hex(0x9890014c),timestamp_input=hex(timer_input),
            native_timestamp=timestamp,native_timestamp_returns=len(times),
            diagnostic_ring_cursors_after_reset_prefix=ring_counts,
            diagnostic_first_entry=log_entry.hex(),diagnostic_entry_verified=True,
            second_diagnostic_ring_first_entry_unchanged=True,
            current_record=hex(CURRENT),current_before_native_copy=previous.hex(),
            source_conditional_BSS_bytes=[hex(a) for a in source_gaps],
            destination_native_copy_bytes=len(current_gaps),additional_native_reset_state_bytes=len(state_gaps),
            reset_halfword_copies=len(copied),consumer_halfword_copies=len(consumer_writes),
            first_consumer_copy_destination=hex(destination),halfword_values_and_addresses_verified=True,
            complete_record_reset_executed=False,snapshot_producer_completed=produced['status']=='returned',
            frontier=dict(status=produced['status'],fault=produced['fault'],
                pc=hex(produced['registers']['pc']),native_return_pc=hex(produced['registers']['mdr'])),
            capture_unchanged=True,geometry_consumer_resumed=False))
        outputs.append(dict(machine=machine,configuration_result=context['configuration_result'],
            configuration_stack=context['configuration_stack'],producer_result=produced))
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=rows,native_instructions=sum(c['completed'] for r in rows for c in r['cases']),
        maximum_observed_new_stack_depth=max(c['stack_depth_from_call_sp'] for r in rows for c in r['cases']),
        population_resumed=False,hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Exactly seven reset-source bytes assume original BSS clear and cached/uncached alias identity; the other three retain actual native reset stores. Active camera/zoom state is not established.',
            'Seven missing current-record bytes start A5 and are overwritten by the original five-halfword copy. Only these two fully sourced10-byte records are coalesced for strict halfword access.',
            '606d4593 runs only through606d4645 after the copy, before its remaining state stores and dependent mode helper. Complete reset/startup/task ordering is not claimed.',
            'Read-only9890014c=3fffedcb is an explicit fixed counter input for native diagnostic timestamps1234. Clock frequency, elapsed time, IRQ delivery and real hardware are not modeled.',
            'Original producer registers and stack resume; the separate geometry consumer, partial capture and population remain untouched.'])
    return report,dict(upstream=contexts,cases=outputs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(record_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
