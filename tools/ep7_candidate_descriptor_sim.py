#!/usr/bin/env python3
"""Continue actual queue4b receipt through native kind19 descriptor materialization.

The 148-byte metadata and idle identity slot are explicit fixtures; the received
command, ticket, runtime and capture registry come from the preceding execution.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_publish_sim import u32,released
from ep7_candidate_state_sim import guarded
from ep7_candidate_capture_sim import CAPTURE,summarize_capture
from ep7_candidate_message_sim import message_context,METADATA,RECEIVE_SP
from ep7_sim_probe import brief


def descriptor_context(directory,prefix,engine,expect_legacy_mulqu=False,*,prepare_kernel=None):
    upstream,context = message_context(directory,prefix,engine,prepare_kernel=prepare_kernel)
    machine,syms = context['machine'],context['syms']
    descriptor,wire = context['descriptor'],context['wire']
    metadata = bytearray(148)
    struct.pack_into('<3I',metadata,0,0x12345678,0x55667788,1)
    struct.pack_into('<H',metadata,72,0x2001)
    guarded(machine,'kind19_metadata',METADATA,bytes(metadata),'r')
    # Explicit disabled trace mask, not a stub for either native logger.
    guarded(machine,'native_trace_enable_mask',0x622930e8,bytes(2),'r')
    # Native 600d8fc9 fills the locale structure from candidate ROM. Start it
    # nonzero, and allow only that structure and the formatter's pointer cell.
    guarded(machine,'libc_locale',0xa26c1b00,b'\xa5'*48)
    guarded(machine,'libc_printf_locale_pointer',0xa26c1e40,b'\xa5'*4)
    identity = 0xa26a080c+216  # Class1, capture ID1, 8-byte entry.
    guarded(machine,'descriptor_identity_entry',identity,b'\xa5'*8)
    result = machine.resume(context['received']['registers'],0x603dfb7d,
        full_trace=True,limit=40000,breakpoints=[syms['_ep7_gcc_quarantine']])
    if expect_legacy_mulqu:
        require(result['status']=='memory_fault' and result['fault']==dict(
            kind=1,pc=0x603e050b,map=1,address=0xa26a07e8,size=4,access='write') and
            machine.read(identity,8)==b'\xa5'*8,
            'known unsigned-immediate error did not stop at the wrong native table write: '+str(brief(result)))
        return dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
            expectation='known_mulqu_engine_defect',all_assertions_passed=True,materialization_passed=False,
            case=brief(result),expected_identity_entry=hex(identity),wrong_identity_entry='0xa26a07e4',
            expected_slot_unchanged=True,wrong_slot_unmapped=True,firmware_files_modified=False,
            hash_checks_performed=False,hardware_executed=False,installable=False),context
    require(result['status']=='returned' and result['registers']['sp']==RECEIVE_SP+440 and
            result['registers']['d0']==1 and result['fault'] is None,
            'native materializer stopped: '+str(brief(result)))
    released(machine)
    require(machine.read(descriptor+300,12)==wire[16:] and u32(machine,descriptor+48)==METADATA and
            u32(machine,descriptor+52)==19 and u32(machine,descriptor+116)==1 and
            u32(machine,descriptor+28)==CAPTURE and machine.read(descriptor+194,2)==b'\x01\x20' and
            machine.read(descriptor+56,60)==bytes(metadata[8:68]),
            'native materializer changed ticket, metadata identity or capture selection')
    require(machine.read(descriptor,8)==struct.pack('<2I',identity+4,identity) and
            machine.read(identity,8)==struct.pack('<2I',0,1),
            'native identity entry initialization changed')
    row = summarize_capture('stock_kind19_materializer_after_receive',result)
    row['stack_depth_from_call_sp'] = RECEIVE_SP-min(r['sp'] for r in result['trace'])
    for label,pc in [('native_identity_lookup_entries',0x603e0681),
                     ('native_formatter_entries',0x600d9ded),('native_locale_setup_entries',0x600d8fc9),
                     ('native_logger_entries',0x613e5ac3),('native_string_logger_entries',0x613e5a4a)]:
        row[label]=sum(r['pc']==pc for r in result['trace'])
    multiply = next(r for r in result['trace'] if r['pc']==0x603e06c2)
    require(multiply['d0']==216 and multiply['mdrq']==0 and row['native_identity_lookup_entries']==1 and
            row['native_lookup_entries']==1 and u32(machine,0xa26c1e40)==0xa26c1b00,
            'native class stride, lookup or libc setup changed')
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        all_assertions_passed=True,materialization_passed=True,case=row,descriptor_address=hex(descriptor),
        metadata_address=hex(METADATA),metadata_bytes=148,metadata_fixture=True,
        selected_capture=hex(CAPTURE),ticket_bytes_preserved=True,
        identity_entry=dict(address=hex(identity),status=0,count=1),
        original_unsigned_multiply=dict(pc='0x603e06bf',opcode='f914d8',result=216,high_word=0),
        upstream_message_carriage_passed=upstream['message_carriage_passed'],
        upstream_capture_fifo_instructions=upstream['capture_upstream_instructions'],
        upstream_message_cases=upstream['cases'],
        hash_checks_performed=False,native_api_success_stubs=False,firmware_files_modified=False,
        hardware_executed=False,installable=False,
        limits=['All S2/controller/message fixtures and conditional residency/ownership remain; no actual task launch/switch or full boot.',
                'Metadata is a guarded read-only 148-byte fixture with ID1/dispatch0x2001. Its producer allocation/construction and lifetime are not executed.',
                'Native materializer resumes the real received CALL state and retains the same ticket; the outer router/relay/worker/ISP and ACK still remain.',
                'The trace-enable mask is explicitly zero. Loggers and formatter execute original code with native ROM locale initialization; logging output is not modeled.',
                'The eight-byte identity table slot is independent fixture storage, not a generation lease or a proved full-table lifetime.',
                'Observed stack depth excludes outer task and IRQ paths. Corrected instruction semantics are a manufacturer-based model, not silicon acceptance.'])
    context['materialized'] = result
    return report,context


def inspect(directory,prefix,engine,expect_legacy_mulqu=False):
    return descriptor_context(directory,prefix,engine,expect_legacy_mulqu)[0]


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--expect-legacy-mulqu',action='store_true',help='record the old engine failure only')
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine,args.expect_legacy_mulqu),indent=2))
