#!/usr/bin/env python3
"""Execute the public COLOR4 setter, native dependencies and composite getter.

Reuse the existing descriptor/callback/dependency registries. Two original
resource headers and one static semaphore are initialized from their real
callers/ROM row; complete kernel startup and fresh capture remain unqualified.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, require
from ep7_candidate_state_sim import CALL_SP, objects, ready_lock
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_publish_sim import COUNTS, SEM_TABLE
from ep7_candidate_message_sim import native_call, result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_device_state_sim import admit
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_postpopulation_finish_sim import postpopulation_finish_context


RESOURCE_HEADERS = (0xa269fe84,0xa269fed8)
SEM_SOURCE, SEM_OBJECT = 0x60039f7c,0x6219ae58


def color_property_context(directory,prefix,engine):
    upstream,contexts = postpopulation_finish_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    syms = base['syms']
    context = contexts['cases'][0]
    original = context['postpopulation_machine']
    machine = original.clone()
    capture = machine.read(CAPTURE,SIZE)
    sidecar = syms['_ep7_controller_sidecar_unresolved']
    old_sidecar = machine.read(sidecar,104)
    kernel_counts = machine.read(COUNTS,32)
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    require(machine.read(0x604ccd10,20) == bytes.fromhex('6f008000fca84b60c8dd4a604008400000060000') and
            machine.read(0x604bacfc,64) == struct.pack('<16I',11,4,*([0]*14)) and
            machine.read(0x604addc8+16*4,4) == struct.pack('<I',64) and
            machine.read(0x604d6c14+111*4,4) == struct.pack('<HH',0x9481,0) and
            machine.read(0x604d6c14+908*4,4) == struct.pack('<HH',0xf6b1,0) and
            machine.read(0x604d6c14+973*4,4) == struct.pack('<HH',0xf731,0),
            'original composite COLOR4 descriptor, public row or raw member maps changed')
    require(machine.read(0x603db775,5) == bytes.fromhex('cd110c0004') and
            machine.read(0x603dc8f8,10) == bytes.fromhex('f8fef82c00104204fcdc') and
            machine.read(0x60032a8b,6) == bytes.fromhex('f070f0035120'),
            'native resource constructors or static semaphore row initializer changed')
    capacity = missing_bytes(machine,list(range(0xa269fe7c,0xa269fe82))+
        [address+offset+i for address in RESOURCE_HEADERS for offset,size in ((0,54),(80,2)) for i in range(size)]+
        list(range(SEM_OBJECT,SEM_OBJECT+28))+[0xa26a1ca4],0xa5,'native_COLOR4_dependencies')
    require(len(capacity) == 147, 'native COLOR dependency store extent changed')
    # Explicit first-request conditions; a live resource request is not
    # cleared to force this setting through its cancellation path.
    require(machine.read(0x60020068,12) == bytes.fromhex('fccd886879a2fccc00af1c62') and
            all(0x621caf00 <= address-0x40000000 < address+size-0x40000000 <= 0x62796888
                for address,size in ((0xa269cdd0,2),(0xa26a1ca8,4))),
            'conditional resource debug/request state is outside original BSS')
    admit(machine,'conditional_resource_reconfigure_debug',0xa269cdd0,bytes(2),'r')
    admit(machine,'conditional_no_active_resource_request',0xa26a1ca8,bytes(4))
    reset = native_call(machine,syms,0x603dc386,0,4,limit=2000)
    initialized = native_call(machine,syms,0x603dc8f8,0,0,limit=2000)
    require(machine.read(0xa269fe7c,6) == bytes(6) and
            [machine.read(address,20).hex() for address in RESOURCE_HEADERS] ==
                ['00e0cec940c939dbc01601008003000000100000','00a06cd5404338dbc05c00008003000000100000'] and
            all(machine.read(address+80,2) == struct.pack('<H',4096) for address in RESOURCE_HEADERS),
            'native resource reset, headers or initial availability changed')
    # Execute one real static-initializer iteration, selecting its exact ROM
    # row. Do not reset all semaphores or overwrite the existing private one.
    require(machine.read(0x600411a4+132,4) == struct.pack('<I',0x6003999c) and
            machine.read(SEM_SOURCE,16) == struct.pack('<4I',0x5e,0,1,1) and
            machine.read(SEM_TABLE+(0x5e-1)*4,4) == struct.pack('<I',SEM_OBJECT) and
            machine.read(0x60040ab0,2) == struct.pack('<H',0x5e),
            'original static semaphore5e descriptor or its actual caller changed')
    semaphore = machine.run(0x60032a72,0x60032aad,
        overrides=dict(sp=CALL_SP,d2=SEM_TABLE,a2=SEM_SOURCE),full_trace=True,limit=2000)
    result_ok(machine,semaphore,0x60032aad,CALL_SP)
    sem_expected = struct.pack('<HH6I',0x5e,4,SEM_OBJECT+4,SEM_OBJECT+4,0,1,1,1)
    require(machine.read(SEM_OBJECT,28) == sem_expected and machine.read(COUNTS,32) == kernel_counts,
            'native selected static semaphore initialization changed')
    # Public API request is explicit: COLOR4 is public64, not raw11 and not
    # standalone child908 value3. All raw writes, dependencies and callbacks
    # execute the original function bodies, including real semaphore wait/signal.
    selected = native_call(machine,syms,0x602afa11,0xc0,16,dict(d0=111,d1=64),limit=500000)
    read_back = native_call(machine,syms,0x602afa81,0,4,dict(d0=111),limit=30000)
    trace = selected['trace']
    pairs = [(t['d0'],t['d1']) for t in trace if t['pc'] == 0x602b0b20]
    typed = [(t['d0'],t['a1']) for t in trace if t['pc'] == 0x6005ea22 and
             t['d0'] in (0x9481,0xf6b1,0xf731)]
    records = {r['key']:r for r in base['property_records']}
    require(selected['registers']['d0'] == 0 and read_back['registers']['d0'] == 64 and
            pairs[:3] == [(111,11),(908,4),(973,0)] and
            typed == [(0x9481,11),(0xf6b1,4),(0xf731,0)] and
            [machine.read(records[key]['data'],1) for key in (0x9481,0xf6b1,0xf731)] ==
                [b'\x0b',b'\x04',b'\0'] and
            machine.read(0xa269fe7c,6) == struct.pack('<3H',1,0,0) and
            machine.read(0xa26a1ca4,1) == b'\0' and machine.read(0xa26a1ca8,4) == bytes(4),
            'complete COLOR4 setting, raw unpack or composite readback changed')
    require([t['d0'] for t in trace if t['pc'] == 0x600370af] == [0x5e,0x5e] and
            [t['d0'] for t in trace if t['pc'] == 0x60035b62] == [0x5e,0x5e] and
            machine.read(SEM_OBJECT,28) == sem_expected and machine.read(0xa26a0808,4) == bytes(4) and
            machine.read(COUNTS,32) == kernel_counts and
            not any(t['pc'] in (0x600313ef,0x6003853e,0x6003057f,0x60061808,0x6040e126) for t in trace) and
            machine.read(CAPTURE,SIZE) == capture and machine.read(sidecar,104) == old_sidecar,
            'setting failed to release native locks or changed capture/sidecar/kernel allocations')
    _,_,_,provider = objects(machine,syms)
    ready_lock(machine,provider)
    differences = []
    for record in base['property_records']:
        size = record['count']*record['width']
        before,after = original.read(record['data'],size),machine.read(record['data'],size)
        if before != after:
            differences.append(dict(key=hex(record['key']),changed=[dict(offset=i,before=a,after=z)
                for i,(a,z) in enumerate(zip(before,after)) if a != z]))
    require([r['key'] for r in differences] == ['0x8b54','0x8b91','0x9481','0xf6b1'],
            'COLOR4 property mutation set changed')
    rows = [stage(name,result) for name,result in (
        ('native_resource_reconfiguration_reset',reset),('native_two_resource_headers_initialize',initialized),
        ('native_static_semaphore5e_initialize_iteration',semaphore),
        ('complete_native_public_COLOR4_set',selected),('native_composite_COLOR4_readback',read_back))]
    original_counts = list(struct.unpack('<2H',machine.read(0x6003c1fc,4)))
    require(original_counts == [133,132], 'original domain0 semaphore count recipe changed')
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        native_store_capacity_added=147,conditional_BSS_bytes_added=6,
        public_setting=dict(id=111,requested_value=64,native_set_return=0,native_get_return=64,
            raw_member_pairs=pairs[:3],raw_typed_writes=[dict(key=hex(k),value=v) for k,v in typed],
            raw_pair_helper_calls=len(pairs),complete_setter=True,GUI_event_executed=False),
        resource_headers=[dict(address=hex(address),mapped_members=[[0,54],[80,2]],capacity=4096,
            available=4096,backing_mapped=False) for address in RESOURCE_HEADERS],
        native_semaphore=dict(handle='0x5e',source=hex(SEM_SOURCE),object=hex(SEM_OBJECT),
            attributes=0,initial_count=1,maximum=1,final_count=1,wait_calls=2,signal_calls=2,
            actual_static_initializer_iteration=True,full_kernel_initialize=False),
        original_kernel_semaphore_recipe=dict(next_automatic_id=original_counts[0],used_count=original_counts[1],
            inherited_probe_counts=list(struct.unpack('<2H',kernel_counts[4:8])),
            original_counts_installed=False,private_runtime_id_production_qualified=False),
        property_changes=differences,capture_unchanged=True,sidecar_unchanged=True,
        fresh_capture_allocated=False,active_COLOR_capture_qualified=False,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Public111=64 is an explicit API input. Native reverse translation, composite unpack, raw writes, dependency callbacks and readback execute; GUI input delivery and NVM persistence are not qualified.',
                'Two original resource constructors map only56 actual store bytes each, preserving holes and unmapped payload backing. Resource reconfiguration and native locks complete in the inherited single-contender model.',
                'Only the exact semaphore5e ROM-row iteration executes. Other static semaphores, whole kernel startup and tasks remain outside this probe; no raw wait/signal return is replaced.',
                'The original kernel recipe has132 used semaphores and next automatic ID133. The inherited S2 fixture has one private semaphore and next ID2; selected static-row initialization does not establish production allocation or boot ordering.',
                'Six BSS bytes explicitly mean disabled resource debug and no published first resource request. Active cancellation/free, competing owners and running task exclusion remain unproven.',
                'The completed public setting does not regenerate a capture. The prior capture and unsealed sidecar stay unchanged; fresh native allocation/generation and new two-stage population remain next.',
                'Input provenance, asynchronous worker/lifetime, code/RAM residency and backup/recovery remain unresolved.'])
    # Release the large per-instruction setter trace after retaining the
    # semantic checkpoints and complete summary; downstream does not resume it.
    selected = dict(selected,trace=[t for t in trace if t['pc'] in
        (0x602b0b20,0x6005ea22,0x602b0d64,0x600370af,0x60035b62)],trace_complete=False,
        trace_selection='native raw writes, composite unpack and semaphore entries')
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        color_machine=machine,color_setting_result=selected,color_readback_result=read_back)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(color_property_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
