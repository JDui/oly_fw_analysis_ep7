#!/usr/bin/env python3
"""Run a fresh first capture population and its real candidate return observer.

Rebuild from the native template after the completed mode/geometry update. The
subsequent postpopulation call stops at its first unprovided register input.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_capture_sim import CAPTURE, NODE
from ep7_candidate_capture_template_sim import TEMPLATE, SIZE
from ep7_candidate_message_sim import native_call, result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_relay_sim import task_fixture
from ep7_candidate_reconfigured_geometry_sim import reconfigured_geometry_context


def fresh_population_context(directory,prefix,engine):
    upstream,contexts = reconfigured_geometry_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    context = contexts['cases'][0]
    machine = context['machine'].clone()
    syms = base['syms']
    task_fixture(machine,0x73,0x60039664,0x60289852,25,4096)
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    old_template = machine.read(TEMPLATE,SIZE)
    template = native_call(machine,syms,0x6030002c,0,4,limit=100000)
    require(machine.read(TEMPLATE,SIZE) == old_template and
            sum(t['pc'] == 0x6005d924 for t in template['trace']) == 16,
            'fresh native template or its property lookups changed')
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    machine.regions['capture'] = replace(machine.regions['capture'],data=b'\xa5'*SIZE,permissions='rw',capture=True)
    require(machine.regions['capture_after'].address == CAPTURE+SIZE and
            machine.read(NODE,4) == struct.pack('<I',1) and
            machine.read(0x60300055,10) == bytes.fromhex('fcdd2c8825622d4fe5db'),
            'owned capture identity or native template-copy bound changed')
    # The actual patched caller enters both stock population and the candidate
    # normal-return observer. Its already-owned node/ID are explicit fixtures;
    # this does not execute node/pool allocation or the preceding global load.
    copied = machine.run(0x602a44a3,0x602a7eb0,overrides=dict(sp=CALL_SP,d0=1,a2=NODE),
        full_trace=True,limit=70000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
    result_ok(machine,copied,0x602a7eb0,CALL_SP-40)
    require(machine.read(CAPTURE,SIZE) == machine.read(TEMPLATE,SIZE) and
            sum(t['pc'] == syms['_ep7cn_prewrite'] for t in copied['trace']) == 1 and
            sum(t['pc'] == 0x60300061 for t in copied['trace']) == 6833,
            'real candidate caller did not prewrite and copy the complete native template')
    populated = machine.resume(copied['registers'],0x602a44a8,full_trace=True,limit=40000,
        breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
    result_ok(machine,populated,0x602a44a8,CALL_SP)
    lookups = [dict(key=hex(t['d0'] & 0xffff),return_pc=hex(t['mdr']))
               for t in populated['trace'] if t['pc'] == 0x6005d924]
    observer = [t for t in populated['trace'] if t['pc'] == syms['_ep7cn_population']]
    geometry = [t for t in populated['trace'] if t['pc'] == 0x604288d5]
    require(len(lookups) == 98 and len(observer) == len(geometry) == 1 and
            observer[0]['d0'] == NODE and observer[0]['d1'] == 0 and
            populated['registers']['a2'] == NODE and
            geometry[0]['a0'] == CAPTURE+24178 and geometry[0]['a1'] == CAPTURE+24180 and
            machine.read(CAPTURE+24178,4) == machine.read(0x622a064a,2)+machine.read(0x622a0648,2),
            'first population, geometry getter or normal-return observer changed')
    records = {r['key']:r for r in base['property_records']}
    require(machine.read(CAPTURE+24053,1) == machine.read(records[0x9481]['data'],1) == b'\0' and
            machine.read(CAPTURE+24083,1) == b'\0' and
            machine.read(CAPTURE+24058,24) == machine.read(records[0xf6ea]['data'],24),
            'native cold mode/selector or twelve saturation values changed')
    data = machine.read(CAPTURE,SIZE)
    changed = [dict(offset=i,before=a,after=b)
               for i,(a,b) in enumerate(zip(machine.read(TEMPLATE,SIZE),data)) if a!=b]
    require([r['offset'] for r in changed] == [24009,24042,24138,24142,24179,24181,24195,24197,24792],
            'native first-population output extent changed')
    rows = [stage('native_template_refresh_after_geometry',template),
            stage('actual_candidate_caller_prewrite_and_template_copy',copied),
            stage('native_first_population_and_candidate_normal_return',populated)]
    # Explore the real second caller separately, retaining the completed first
    # population context. A1 uses the owned node's same ID1 member in place of
    # the unexecuted global-current-ID load; the original caller supplies A0.
    second = machine.clone()
    second.regions['stack'] = replace(second.regions['stack'],data=b'\xcc'*len(second.regions['stack'].data))
    require(second.read(0x602a44ae,7) == bytes.fromhex('fcdc1cd4236200') and
            second.read(0x6006d68c,13) == bytes.fromhex('fca49c00e098f8c4051cde0000'),
            'native postpopulation object binding or register conversion changed')
    post = second.run(0x602a44ae,0x602a44ba,overrides=dict(sp=CALL_SP,a1=NODE,a2=NODE),
        full_trace=True,limit=40000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
    require(post['status'] == 'memory_fault' and post['fault'] == dict(
            kind=1,pc=0x6006d68c,map=0,address=0x98e0009c,size=4,access='read') and
            post['registers']['mdr'] == 0x602a8de8 and
            sum(t['pc'] == syms['_ep7cn_prewrite'] for t in post['trace']) == 1 and
            not any(t['pc'] == syms['_ep7cn_population'] for t in post['trace']),
            'postpopulation no longer stops before the unprovided register input')
    rows.append(stage('native_second_population_register_frontier',post))
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        fresh_template_initialized=True,template_bytes=SIZE,template_native_words_copied=6833,
        original_failed_population_resumed=False,first_population_completed=True,
        candidate_normal_return_observer_entries=len(observer),native_property_lookups=lookups,
        capture_changes_from_template=changed,capture_geometry_halfwords=list(struct.unpack('<2H',data[24178:24182])),
        raw_mode=0,selector=0,saturation_source='0xf6ea',native_saturation_source_equal=True,
        second_population_completed=False,
        second_population_frontier=dict(status=post['status'],fault=post['fault'],
            native_return_pc=hex(post['registers']['mdr']),native_input_object='0x6223d41c',
            ID_pointer_fixture=hex(NODE),register_input_provided=False,finish_observer_executed=False),
        new_mapped_data_bytes=0,conditional_BSS_bytes_added=0,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['The first population runs from the actual patched602a44a3 caller, after native template refresh and a complete new template copy. The pre-mode partial population frame is never resumed.',
                'Controller task handover, owned node/ID/capture registry and capture capacity remain fixtures. Allocation, preceding global-current-ID load and the enclosing controller loop are not executed.',
                'Native raw mode0 and selector0 do not qualify for H/L COLOR capture. The first normal-return observer executes; no valid frozen/sealed snapshot is manufactured.',
                'Second population is an independent continuation probe: the native caller supplies object6223d41c, while A1 points at the same owned ID1. Its original global ID source and full request producer remain unproven.',
                'The second function stops at the actual98e0009c register read. No counter/measurement meaning or value is invented and the finish observer has not executed.',
                'Unconfigured format, unavailable device, active-shot validity, relay preprocessing, worker lifecycle, residency and backup/recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,machine=machine,
        population_result=populated,postpopulation_machine=second,postpopulation_result=post)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(fresh_population_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
