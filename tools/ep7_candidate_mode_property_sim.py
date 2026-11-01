#!/usr/bin/env python3
"""Trace the original ID24 public setting path before a fresh geometry call.

The requested value3 has both a ROM descriptor and a native conditional caller.
The caller's enclosing policy is a cut point, not a simulated mode-dial event.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import native_call, result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_device_state_sim import admit
from ep7_candidate_geometry_measurement_sim import geometry_measurement_context
from ep7_candidate_geometry_sim import map_initializer_storage
from ep7_ui_resource_origin import ROM_START, RAM_CACHED


def check_registry(machine, roots, nodes, source, buckets, count, stride):
    """Verify the actual native linked buckets against their complete ROM list."""
    groups=[[] for _ in range(buckets)]
    for i in range(count):
        key=struct.unpack('<H',machine.read(source+i*stride,2))[0]
        groups[key & (buckets-1)].append(i)
    for bucket, indices in enumerate(groups):
        require(machine.read(roots+bucket*4,4)==struct.pack('<I',nodes+indices[0]*8 if indices else 0),
                'native registry bucket root differs from ROM insertion order')
        for position,i in enumerate(indices):
            following=nodes+indices[position+1]*8 if position+1<len(indices) else 0
            require(machine.read(nodes+i*8,8)==struct.pack('<II',source+i*stride,following),
                    'native registry node differs from its descriptor or next link')


def public_setting(machine, syms):
    # Keep semantic checkpoints instead of retaining a million full register
    # snapshots in the parent context. Every segment is still traced in full.
    checkpoints={0x602b0bd5,0x602b0be0,0x602b0bf5,0x602b148f,0x602b1954,
                 0x6005ea22,0x6005eafb,0x6005eaff,0x6005eb04,0x6005eb06,
                 0x6005eb0e,0x6005eb10,0x602b0d3b,0x602b16f0,0x602b0df1,
                 0x6020de9e,0x602b1e6f}
    trace, segments, summaries=[],[],[]
    total=0
    result=machine.run(0x60924a96,0x60924aa1,overrides=dict(sp=CALL_SP),
        full_trace=True,limit=100000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
    while True:
        require(len(result['trace'])==result['completed'],'public setting trace was truncated')
        total+=result['completed']
        summaries.append(stage('native_conditional_public_ID24_value3_set',result))
        trace.extend(t for t in result['trace'] if t['pc'] in checkpoints)
        segments.append(dict(status=result['status'],completed=result['completed'],pc=hex(result['registers']['pc'])))
        if result['status']!='instruction_limit' or total>=2000000:
            break
        result=machine.resume(result['registers'],0x60924aa1,full_trace=True,limit=100000,
            breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
    result.update(trace=trace,completed=total,trace_complete=False,
                  trace_selection='fixed semantic checkpoints from complete per-segment traces')
    row=stage('native_conditional_public_ID24_value3_set',result)
    row['stack_depth_from_call_sp']=max(s['stack_depth_from_call_sp'] for s in summaries)
    for key in row:
        if key.endswith('_entries'):
            row[key]=sum(s[key] for s in summaries)
    row['native_lock_calls']=[v for s in summaries for v in s['native_lock_calls']]
    row['execution_segments']=segments
    return row,result


def mode_property_context(directory, prefix, engine):
    upstream, contexts = geometry_measurement_context(directory, prefix, engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    # The indexed property path has no GPIO input. Follow the existing GPIO0
    # case first, without multiplying this source investigation into a matrix.
    context = contexts['cases'][0]
    machine = context['machine'].clone()
    original = context['machine']
    capture = machine.read(CAPTURE, SIZE)
    machine.regions['stack'] = replace(machine.regions['stack'], data=b'\xcc'*len(machine.regions['stack'].data))
    require(machine.read(0x604d6c14+24*4,4) == struct.pack('<HH',0xc011,0) and
            machine.read(0x604d2954,20) == struct.pack('<HHIIHHBBBB',24,128,0x604cc68a,0,149,1,0,1,0,0) and
            machine.read(0x604cc68a,1) == b'\x03' and
            machine.read(0x60924a96,11) == bytes.fromhex('80188503dd77af98ffc010'),
            'original ID24 descriptor, typed binding or conditional value3 caller changed')
    # All are exact full native initializer destinations, initially poisoned.
    # The two-byte gap after the special halfword stays unmapped.
    storage = [(0xa2699cb0,2),(0xa2699cb4,8885),(0x62253590,12),(0x62257b04,1),
               (0x62248528,128*4+1333*8),(0x62245f48,64*4+439*8),
               (0x62246e0c,2),(0x62246e10,32*4+201*8),
               (0x622457fc,2),(0x62245a44,20*64),(0xa2743aec,8)]
    for address, size in storage:
        admit(machine, f'native_property_registry_{address:x}', address, b'\xa5'*size)
    rows = []
    for name, target, mask, frame, limit in (
            ('native_indexed_property_cache_initialize',0x602cbb21,0x80,8,40000),
            ('native_public_descriptor_registry_initialize',0x602ba4cc,0xb0,12,100000),
            ('native_public_callback_registry_initialize',0x602b16f7,0xb0,12,60000),
            ('native_dependency_registry_initialize',0x602b294c,0,4,30000),
            ('native_property_mode_gate_initialize',0x602b1ecb,0,0,100)):
        result = native_call(machine,base['syms'],target,mask,frame,limit=limit)
        rows.append(stage(name,result))
    check_registry(machine,0x62248528,0x62248728,0x604cc98c,128,1333,20)
    check_registry(machine,0x62245f48,0x62246048,0x604317ac,64,439,60)
    check_registry(machine,0x62246e10,0x62246e90,0x6045e5fc,32,201,20)
    by_key={r['key']:r for r in base['property_records']}
    require(machine.read(0xa2699cb4,8884)==bytes(8884) and
            machine.read(0xa2699cb0,2)==machine.read(0x604d8e6e,2) and
            machine.read(0xa269bf68,1)==machine.read(by_key[0x0db1]['data'],1)==b'\0' and
            machine.read(0x62257b04,1)==b'\0' and machine.read(0x622457fc,2)==b'\1\0' and
            machine.read(0x62253590,12)==struct.pack('<3I',*(by_key[k]['data'] for k in (0x85d4,0x8b64,0x8b54))),
            'native indexed cache, inhibit, gate or bank pointers changed')
    mode = next(r for r in base['property_records'] if r['key']==0xc011)
    staging = next(r for r in base['property_records'] if r['key']==0x8b54)
    # Reuse the already natively initialized RAM banks as shared backing. These
    # are aliases, not additional independent/default/NVM copies. The original
    # 60067102 conversion and typed writer use both CPU0 addresses.
    aliases=[]
    for name in ('property_default_bank','property_configuration_defaults',
                 'property_capture_defaults','property_factory_records'):
        region=machine.regions[name]
        alias=name+'_native_alias'
        admit(machine,alias,region.address+0x40000000,region.data)
        machine.regions[alias]=replace(machine.regions[alias],alias_of=name)
        aliases.append(dict(source=hex(region.address),alias=hex(region.address+0x40000000),
                            bytes=len(region.data),shared_backing=True))
    # Explicit before-logging-initialization scenario, plus original initialized
    # data source. No logger is stubbed and no diagnostic entry is skipped.
    require(machine.read(0x60020068,12)==bytes.fromhex('fccd886879a2fccc00af1c62') and
            0x621caf00<=0x6224bd3c<0x6224bd3e<=0x62796888,
            'logging flags no longer have the reviewed startup BSS provenance')
    admit(machine,'mode_property_logging_preinit_BSS',0x6224bd3c,bytes(2))
    admit(machine,'native_composite_return_selector_preinit_BSS',0x62245f44,b'\0')
    data_sources=[]
    for address,size in ((0x61f9ec18,8),(0x61f9ec34,8),(0x61f9feb2,2)):
        source=ROM_START+address-RAM_CACHED
        admit(machine,f'mode_property_initialized_data_{address:x}',address,machine.read(source,size),'r')
        data_sources.append(dict(ROM=hex(source),RAM=hex(address),bytes=size,value=machine.read(source,size).hex()))
    _, reset_ranges=map_initializer_storage(machine,directory,prefix,
        [(0x60169930,0x60169949),(0x6016819a,0x601681a4)],
        [(0x62221d8e,0x62221d90),(0x62221d91,0x62221d96),(0x62221968,0x6222196a)],
        name_prefix='native_mode_device_reset')
    reset=machine.run(0x60169930,0x6016994e,overrides=dict(sp=CALL_SP),full_trace=True,limit=100)
    result_ok(machine,reset,0x6016994e,CALL_SP)
    require(all(machine.read(low,high-low)==bytes(high-low) for low,high in reset_ranges),
            'native device reset fields changed')
    rows.append(stage('native_device_mode_field_reset_slice',reset))
    require(machine.read(0x60615b0a,6)==bytes.fromhex('f89304f8bd04') and
            machine.read(0x60615b1c,19)==bytes.fromhex('60f81028f8102cf8103050db04644050a008d3') and
            machine.read(0x6020d016,11)==bytes.fromhex('fcdc9ede2060cd15f30004'),
            'native resource counter reset or descriptor callback registration changed')
    admit(machine,'native_resource_counter_reset',0xa2786f14,b'\xa5'*52)
    reset=machine.run(0x60615b0a,0x60615b2f,overrides=dict(sp=CALL_SP,d0=0),full_trace=True,limit=1000)
    result_ok(machine,reset,0x60615b2f,CALL_SP)
    require(machine.read(0xa2786f14,52)==bytes(52),'native resource counter reset was incomplete')
    rows.append(stage('native_resource_counter_reset_prefix',reset))
    registered=machine.run(0x6020d016,0x6020d021,overrides=dict(sp=CALL_SP),full_trace=True,limit=100)
    result_ok(machine,registered,0x6020d021,CALL_SP)
    require(machine.read(0xa2743aec,8)==struct.pack('<II',0x6020de9e,0),
            'original descriptor callback was not registered')
    rows.append(stage('native_property_descriptor_callback_registration',registered))
    public_row,configured=public_setting(machine,base['syms'])
    rows.append(public_row)
    result_ok(machine,configured,0x60924aa1,CALL_SP)
    primary=[t for t in configured['trace'] if t['pc']==0x602b1954 and t['sp']==CALL_SP-84]
    dependent_source,dependent_count=struct.unpack('<IH',machine.read(0x6045f9bc,6))
    dependent_ids=list(struct.unpack('<96H',machine.read(dependent_source,192)))
    require(dependent_count==96 and [t['d0'] for t in primary]==dependent_ids and
            configured['registers']['d0']==0 and machine.read(0x62246e0c,2)==bytes(2) and
            machine.read(mode['data'],1)==machine.read(mode['data']+0x40000000,1)==b'\3' and
            machine.read(staging['data']+24*4,4)==struct.pack('<I',3) and
            [t['d0'] for t in configured['trace'] if t['pc']==0x602b0bd5 and t['sp']==CALL_SP-32]==[2] and
            [t['a0'] for t in configured['trace'] if t['pc']==0x602b0be0 and t['sp']==CALL_SP-32]==[0] and
            [t['d0'] for t in configured['trace'] if t['pc']==0x602b0bf5 and t['sp']==CALL_SP-32]==[3],
            'public setter, complete96-ID propagation or typed C011 publication changed')
    changes=[]
    for prop in base['property_records']:
        address,width,count=prop['data'],prop['width'],prop['count']
        old,new=original.read(address,width*count),machine.read(address,width*count)
        if old!=new:
            elements=[dict(index=i,before=old[i*width:(i+1)*width].hex(),after=new[i*width:(i+1)*width].hex())
                      for i in range(count) if old[i*width:(i+1)*width]!=new[i*width:(i+1)*width]]
            changes.append(dict(key=hex(prop['key']),address=hex(address),width=width,count=count,elements=elements))
    require({int(p['key'],16) for p in changes}==
            {0x68f1,0x69f1,0x80ea,0x8141,0x81d2,0x81e1,0x8301,0x8321,0x8a81,0x8b54,0x8f41,0xc011,0xd752},
            'native mode update changed an unreviewed property')
    require(machine.read(CAPTURE,SIZE)==capture,'mode property path changed partial capture')
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),gpio80_input_bit4=0,cases=rows,
        native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(row['stack_depth_from_call_sp'] for row in rows),
        native_store_bytes_added=sum(size for _,size in storage)+9+52,
        native_registry_validation=dict(descriptors=1333,callbacks=439,dependency_rules=201,
            all_bucket_links_match_ROM=True),
        property_aliases=aliases,alias_storage_bytes=sum(a['bytes'] for a in aliases),
        conditional_BSS_bytes_added=3,conditional_initialized_data=data_sources,
        property_id=24,typed_key='0xc011',native_value_before=0,native_value_after=3,
        native_public_setter_completed=True,dependent_property_ids=dependent_ids,
        primary_dependency_iterations=len(primary),all_dependency_iterations=sum(
            t['pc']==0x602b1954 for t in configured['trace']),
        changed_properties=changes,descriptor_callback='0x6020de9e',
        frontier=dict(status=configured['status'],fault=configured['fault'],
            pc=hex(configured['registers']['pc']),native_return_pc=hex(configured['registers']['mdr'])),
        capture_unchanged=True,population_resumed=False,geometry_restarted=False,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['The original60924a96 conditional setting slice executes all the way to60924aa1. Its enclosing policy predicates, physical mode dial and task scheduling are not executed.',
                'All1973 descriptor/callback/dependency nodes and the indexed cache are initialized by their complete native helpers. The resource counter reset is only its52-byte prefix; queue draining and its enclosing service lifecycle are not claimed.',
                'Three explicit cold BSS bytes cover the composite-return selector and logging enable flags. Eighteen bytes retain the original initialized-data ROM recipe, including null post-hook pointers; physical startup storage/cache copy and later hook registration are not executed.',
                'RAM aliases share already-native property-bank backing in the engine. CPU0 alias conversion and typed writes execute, but hardware cache coherence and NVM persistence remain unproven.',
                'The cold failure with C011=0 remains upstream. The completed value3 update does not revive its suspended configuration frame; snapshot refresh and a fresh geometry entry are separate next steps.',
                'No valid active shot, complete capture population, worker lifecycle or installability is established.'])
    return report,dict(upstream=contexts,upstream_report=upstream,
        cases=[dict(context,machine=machine,mode_property_result=configured)])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(mode_property_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
