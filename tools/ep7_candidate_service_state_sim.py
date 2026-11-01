#!/usr/bin/env python3
"""Continue both native geometry branches using witnessed cold service state.

Original initialization slices run on independent stacks. Their enclosing
peripheral setup and service/task lifecycle remain explicit prerequisites.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER,require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import native_call,summarize_message,result_ok
from ep7_candidate_device_inputs_sim import input_context
from ep7_candidate_device_state_sim import admit
from ep7_candidate_geometry_sim import map_initializer_storage
from penf_emulator import Region


def service_state_context(directory,prefix,engine):
    upstream,contexts=input_context(directory,prefix,engine)
    rows=[]
    outputs=[]
    for index,context in enumerate(contexts['cases']):
        machine=context['machine']
        syms=contexts['upstream']['syms']
        capture=machine.read(CAPTURE,SIZE)
        configuration_stack=machine.regions['stack']
        machine.regions['stack']=replace(configuration_stack,data=b'\xcc'*len(configuration_stack.data))
        windows=[(0x6016227a,0x60162367),(0x60163bc8,0x60163bfe),(0x60169011,0x60169018),
                 (0x601696d3,0x601698bf),(0x601613f9,0x60161406)]
        require(machine.read(0x60173826,7)==b'\xdd'+struct.pack('<i',0x60162162-0x60173826)+bytes([0x80,8]) and
                machine.read(0x60162303,6)==bytes.fromhex('fcdc32122262') and
                machine.read(0x60162312,2)==bytes.fromhex('a506') and
                machine.read(0x6016232d,6)==bytes.fromhex('fcdcdc102262') and
                machine.read(0x60162340,2)==bytes.fromhex('8528') and
                machine.read(0x60163bdb,9)==bytes.fromhex('fcdc6c1222622d0003') and
                machine.read(0x6016900c,5)==bytes.fromhex('cdc7068008') and
                machine.read(0x60162c4c,5)==bytes.fromhex('cdade70000') and
                machine.read(0x6016982b,6)==bytes.fromhex('fcdcee192262') and
                machine.read(0x60169837,2)==bytes.fromhex('a00c') and
                machine.read(0x60169011,7)==bytes.fromhex('00fc83801d2262'),
                'original service initializer/array/reset witnesses changed')
        stores,ranges=map_initializer_storage(machine,directory,prefix,windows,
            [(0x62221000,0x62221e00)],
            [(0x62221232,0x6222123e),(0x622210dc,0x62221104),(0x6222126c,0x6222156c),
             (0x622219ee,0x622219fa)],
            name_prefix='native_service_state')
        # Begin at the self-contained RAM-reset suffix, after the original
        # peripheral acquire/configure/release calls; do not stub those calls.
        initialized=machine.run(0x6016227a,0x60162367,overrides=dict(sp=CALL_SP),
            full_trace=True,limit=5000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808])
        result_ok(machine,initialized,0x60162367,CALL_SP)
        require(machine.read(0x622211dc,7)==bytes(7) and
                machine.read(0x622211e4,2)==struct.pack('<H',5000) and
                machine.read(0x62221232,12)==bytes(12) and
                machine.read(0x622210dc,40)==bytes(16)+b'\x10\0'+bytes(22),
                'native service RAM suffix produced unexpected reset state')
        diagnostic=native_call(machine,syms,0x60163bc8,0,4,limit=10000)
        require(machine.read(0x6222125c,7)==bytes(7) and
                machine.read(0x6222126c,768)==bytes(768),
                'native diagnostic state initializer changed')
        reset_parameters=machine.run(0x601696d3,0x601698bf,overrides=dict(sp=CALL_SP),
            full_trace=True,limit=3000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808])
        result_ok(machine,reset_parameters,0x601698bf,CALL_SP)
        require(machine.read(0x62221a14,2)==bytes(2) and
                machine.read(0x6222199a,6)==struct.pack('<3H',1,1,1) and
                machine.read(0x622219ee,12)==bytes(12) and
                machine.read(0x62221db6,2)==struct.pack('<H',7),
                'native task parameter reset prefix changed')
        # The original getter exposes a78-byte record copied as39 halfwords.
        # Exactly one padding byte was not assigned by its field initializer.
        require(machine.read(0x6016bc84,6)==bytes.fromhex('fcdc98192262') and
                machine.read(0x601739dd,2)==bytes.fromhex('85d9') and
                machine.read(0x60020068,12)==bytes.fromhex('fccd886879a2fccc00af1c62') and
                0x621caf00<=0x62221998<0x622219e6<=0x62796888,
                'native parameter-record extent or startup BSS evidence changed')
        gaps=[a for a in range(0x62221998,0x622219e6) if not any(
            r.address<=a<r.address+len(r.data) for r in machine.regions.values())]
        require(gaps==[0x622219e1],'parameter record has additional uninitialized holes')
        admit(machine,'native_parameter_record_BSS_padding',0x622219e1,b'\0','r')
        # The strict engine needs a halfword to fit one explicit region. Merge
        # only this fully sourced record, preserving every native field byte.
        record_parts=[(name,r) for name,r in machine.regions.items()
            if r.address<0x622219e6 and 0x62221998<r.address+len(r.data)]
        require(all(0x62221998<=r.address<r.address+len(r.data)<=0x622219e6
                    for name,r in record_parts),'record merge would consume adjacent state')
        record=b''.join(machine.read(a,1) for a in range(0x62221998,0x622219e6))
        for name,r in record_parts:
            del machine.regions[name]
        admit(machine,'native_parameter_record',0x62221998,record)
        reset_pending=native_call(machine,syms,0x601613f9,0,0,limit=100)
        require(machine.read(0x62221040,2)==machine.read(0x62221044,2)==bytes(2),
                'native pending state reset changed')
        task_reset=machine.run(0x60169011,0x60169018,overrides=dict(sp=CALL_SP),
            full_trace=True,limit=100,breakpoints=[syms['_ep7_gcc_quarantine']])
        result_ok(machine,task_reset,0x60169018,CALL_SP)
        require(machine.read(0x62221d80,2)==bytes(2),'original task reset store changed')
        setup=[summarize_message(name,result,CALL_SP) for name,result in (
            ('native_service_RAM_reset_suffix',initialized),('native_diagnostic_state_initialize',diagnostic),
            ('native_task_parameter_reset_prefix',reset_parameters),('native_pending_state_reset',reset_pending),
            ('native_task_state_reset_slice',task_reset))]
        machine.regions['stack']=configuration_stack
        machine.regions['caller']=Region('caller',CALLER,
            b'\xdd'+struct.pack('<i',0x6042760c-CALLER)+bytes([0xf0,16]),'rx')
        configured=machine.resume(context['configuration_result']['registers'],CALLER+7,
            full_trace=True,limit=80000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808])
        row=summarize_message('native_geometry_resume_with_cold_service_state',configured,CALL_SP)
        if configured['status']!='returned':
            row['d0_at_stop']=row.pop('returned_d0')
        row['stop_registers']={k:hex(v) for k,v in configured['registers'].items()}
        require(configured['status']=='memory_fault' and configured['fault']==dict(
                kind=1,pc=0x6041a5bb,map=0,address=0x6229fc44,size=1,access='read') and
                configured['registers']['mdr']==0x60419f58 and
                not any(r['pc']==0x6042805e for r in configured['trace']),
                'native geometry snapshot frontier changed: '+str(configured['fault']))
        copied=[r for r in configured['trace'] if r['pc']==0x601739e4]
        require(len(copied)==39*index and all(
            r['a0']==0x62221998+2*(i+1) and r['a1']==copied[0]['a1']+2*i and
            r['d0']==struct.unpack_from('<H',record,2*i)[0] for i,r in enumerate(copied)),
            'native parameter record copy did not preserve all39 halfwords')
        require(machine.read(CAPTURE,SIZE)==capture,'service-state probe changed partial capture')
        rows.append(dict(gpio80_input_bit4=index,cases=setup+[row],
            mapped_state_bytes=1+sum(high-low for low,high in ranges),
            mapped_state_ranges=[[hex(low),hex(high)] for low,high in ranges]+[['0x622219e1','0x622219e2']],
            source_direct_stores=len(stores),cold_service_state_supplied=True,
            conditional_BSS_padding_bytes=1,parameter_record_address='0x62221998',
            parameter_record_bytes=78,parameter_record=machine.read(0x62221998,78).hex(),
            parameter_record_coalesced_for_native_halfword_reads=True,
            native_parameter_record_halfword_copies=len(copied),
            native_parameter_record_copy_values_verified=True,
            frontier=dict(pc='0x6041a5bb',address='0x6229fc44',width=1,native_return_pc='0x60419f58'),
            complete_service_initializer_executed=False,complete_task_startup_executed=False,
            geometry_configuration_passed=configured['status']=='returned',
            geometry_dynamic_setter_executed=any(r['pc']==0x6042805e for r in configured['trace']),
            capture_unchanged=True))
        outputs.append(dict(machine=machine,configuration_result=configured))
    report=dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=rows,population_resumed=False,hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['The6016227a RAM suffix is independent of preceding peripheral clock/acquire/configure/release calls, which are not executed. Its cold values are an explicit lifecycle scenario, not active hardware measurements.',
                'The60163bc8 diagnostic initializer executes completely. The60169011 task reset is a two-instruction slice; its preceding task helpers and following queue registration are unexecuted prerequisites.',
                'The601696d3 parameter reset prefix stops before601698bf property-service lookup; its whole helper is not claimed. The601613f9 pending-state reset executes completely.',
                'Only reviewed direct-store destinations and bounded arrays are mapped from A5. Unknown adjacent state remains unmapped.',
                'Exactly one padding byte622219e1 within the witnessed78-byte parameter record assumes original BSS clear success. All other record bytes come from the executed native field reset; DMA remains unexecuted.',
                'Both original configuration frames resume after real device sampling/predicates. Partial capture is unchanged and no completion or successful dynamic update is forged.',
                'Upstream board/GPIO and conditional BSS/ROM inputs remain; complete boot, real peripheral effects, scheduling and installation qualification are not established.'])
    return report,dict(upstream=contexts,cases=outputs)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(service_state_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
