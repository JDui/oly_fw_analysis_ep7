#!/usr/bin/env python3
"""Trace native geometry service initialization and its configuration producer.

Reuse the observed capture-population frontier. Only original initializer write
destinations become writable state; gaps remain unmapped, not a zero-filled heap.
This is an independent service-call scenario, not the complete startup schedule.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import re
import struct
import subprocess

from ep7_candidate_startup_sim import CALLER,require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import native_call,summarize_message,result_ok
from ep7_candidate_population_sim import population_context
from ep7_descriptor_frames import instructions
from ep7_offline_candidate import BASE,IMAGE_NAME
from ep7_ui_resource_origin import ROM_START,ROM_END,RAM_CACHED,RAM_UNCACHED,FLASH_START
from penf_emulator import Region


def map_initializer_storage(machine,directory,prefix,windows,allowed_ranges,array_ranges=(),name_prefix='geometry_state'):
    """Map only reviewed native direct-store destinations and bounded arrays."""
    stores=[]
    for start,end in windows:
        asm=subprocess.check_output([prefix+'objdump','-D','-z','-b','binary','-m','mn10300',
            '--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',
            f'--stop-address={end:#x}',str(directory/IMAGE_NAME)],text=True)
        for pc,size,mn,operand in instructions(asm):
            match=re.fullmatch(r'([ad][0-3]),\(0x([0-9a-f]+)\)',operand)
            if mn not in ('mov','movhu','movbu') or match is None:
                continue
            width={'mov':4,'movhu':2,'movbu':1}[mn]
            address=int(match[2],16)
            require(size==6 and any(low<=address<address+width<=high for low,high in allowed_ranges),
                    'initializer gained an unreviewed state destination')
            stores.append(dict(pc=pc,address=address,width=width,register=match[1]))
    addresses=set()
    for low,high in array_ranges:
        addresses.update(range(low,high))
    for row in stores:
        addresses.update(range(row['address'],row['address']+row['width']))
    intervals=[]
    for address in sorted(addresses):
        if intervals and address==intervals[-1][1]:
            intervals[-1][1]+=1
        else:
            intervals.append([address,address+1])
    for low,high in intervals:
        require(not any(low<r.address+len(r.data) and r.address<high for r in machine.regions.values()),
                'native service state overlaps an existing mapping')
        name=f'{name_prefix}_{low:x}'
        machine.regions[name]=Region(name,low,b'\xa5'*(high-low),'rw',True)
    return stores,intervals


def initializer_storage(machine,directory,prefix,service_prefixes=True):
    windows=[(0x6020d024,0x6020daec),(0x60421330,0x60421540)]
    arrays=[(0x622a06fc,0x622a070c),(0x622a0848,0x622a08c8)]
    if service_prefixes:
        windows += [(0x602ad810,0x602ad86d),(0x60421540,0x604215b4),
                    (0x603b6297,0x603b62c8),(0x603b700e,0x603b7100)]
        arrays.append((0xa27396d8,0xa2739720))
    require(machine.read(0x60421365,6)==bytes.fromhex('fcdcfc062a62') and
            machine.read(0x604214ed,6)==bytes.fromhex('fcdc48082a62') and
            machine.read(0x604214f6,3)==bytes.fromhex('2d8000'),
            'native bounded state array initialization changed')
    return map_initializer_storage(machine,directory,prefix,windows,
        [(0x622a063c,0x622a0c19),(0x6223ec9c,0x6223ed54),
         (0xa2739688,0xa2739721),(0xa2743b94,0xa2743ba0)],arrays)


def prepare_request_mode(machine,syms):
    request=0x19b00000
    # A single-request branch is an explicit scenario input. The original
    # controller code, not this fixture, translates it into request mode1.
    # Only the three branch inputs are admitted; no controller BSS is filled.
    fixtures=[('geometry_request',request,b'\xa5'*48,'rw'),
        ('geometry_controller_mode',0x6223ed08,bytes(4),'r'),
        ('geometry_controller_variant',0x6223eca3,bytes(1),'r'),
        ('geometry_controller_flags',0x6223ed28,bytes(4),'r'),
        ('geometry_request_mode',0x622a0780,b'\xa5','rw')]
    for name,address,data,permissions in fixtures:
        require(not any(address<r.address+len(r.data) and r.address<address+len(data)
                        for r in machine.regions.values()),'request fixture overlaps existing state')
        machine.regions[name]=Region(name,address,data,permissions,permissions=='rw')
    require(machine.read(0x602add0a,9)==bytes.fromhex('8030ddf449d7ff0004') and
            machine.read(0x602add5b,3)==bytes.fromhex('2c0004') and
            machine.read(0x60040d9a,2)==struct.pack('<H',0x5f) and
            machine.read(0x6054aaa0,8)==struct.pack('<2I',0x401,0x604216ad) and
            machine.read(0x604216b0,5)==bytes.fromhex('cd3210b01c'),
            'original48-byte request allocation/command/queue/consumer binding changed')
    produced=machine.run(0x602add13,0x602add5b,overrides=dict(sp=CALL_SP,a0=request),
        full_trace=True,limit=1000,breakpoints=[syms['_ep7_gcc_quarantine']])
    result_ok(machine,produced,0x602add5b,CALL_SP)
    require(machine.read(request,48)==b'\xa5'*36+b'\x01\x00\x01'+b'\xa5'*9,
            'original controller did not construct just the observed request fields')
    # This is the original request-field consumption slice. Enclosing service
    # transitions/log reset, allocation and queue transport are explicit gaps.
    consumed=machine.run(0x6042270f,0x6042273c,overrides=dict(sp=CALL_SP,a2=request),
        full_trace=True,limit=1000,breakpoints=[syms['_ep7_gcc_quarantine']])
    result_ok(machine,consumed,0x6042273c,CALL_SP)
    require(machine.read(0x622a0780,1)==machine.read(0x622a0781,1)==b'\x01' and
            machine.read(0x622a0844,1)==b'\0' and machine.read(0x622a097c,1)==b'\x01',
            'native request consumption did not copy the constructed mode/flags')
    return [summarize_message(name,result,CALL_SP) for name,result in (
        ('native_request_mode_fields_produce',produced),('native_request_mode_fields_consume',consumed))],dict(
        address=hex(request),bytes=48,initial_fill='a5',native_request_fields=[1,0,1],
        controller_inputs={'0x6223ed08':0,'0x6223eca3':0,'0x6223ed28':0},
        controller_inputs_are_fixture=True,allocation_executed=False,queue_transport_executed=False,
        complete_request_handler_executed=False)


def prepare_device_property_cache(machine,syms,records):
    # Reuse the already reviewed startup data-copy recipe. Only this table's
    # source bytes are admitted; this does not execute NAND/ECC/cache startup.
    address,count=0x61f9ad74,117
    source=ROM_START+address-RAM_CACHED
    require(source==0x60233034 and source+count*8<=ROM_END and
            machine.read(0x600201ab,12)==bytes.fromhex('fccc50eb2560fc8184d91862') and
            machine.read(0x60020204,23)==bytes.fromhex(
                'fcdc00088b40fcdd4085f9a1fcc000f8dc9fcd3812f020') and
            machine.read(0x6017383b,6)==bytes.fromhex('00cd54fee010') and
            machine.read(0x60173692,6)==bytes.fromhex('fcde74adf961'),
            'original startup data-copy/cache-initializer binding changed')
    data=machine.read(source,count*8)
    rows=list(struct.iter_unpack('<HHI',data))
    by_index={r['key']>>4:r for r in records}
    require(all(pointer==0 and key>>4 in by_index for key,index,pointer in rows),
            'device cache has an unreviewed initial pointer or missing property')
    require(not any(address<r.address+len(r.data) and r.address<address+len(data)
                    for r in machine.regions.values()),'device cache overlaps existing state')
    machine.regions['geometry_device_property_cache']=Region(
        'geometry_device_property_cache',address,data,'rw',True)
    initialized=native_call(machine,syms,0x60173690,0xe0,16,dict(d0=0),limit=10000)
    expected=b''.join(struct.pack('<HHI',key,index,by_index[key>>4]['data'])
                      for key,index,pointer in rows)
    require(machine.read(address,len(expected))==expected,
            'native device cache pointers differ from original property banks')
    row=summarize_message('native_device_property_cache_initialize',initialized,CALL_SP)
    row.update(table=hex(address),decoded_initializer=hex(source),entries=count,
        unique_keys=len({r[0] for r in rows}),native_pointer_getters=sum(
            r['pc']==0x6005e947 for r in initialized['trace']),
        startup_copy_source=hex(FLASH_START),startup_copy_destination=hex(RAM_UNCACHED),
        startup_copy_bytes=ROM_END-ROM_START,conditional_startup_data_copy=True,
        startup_storage_copy_executed=False)
    require(row['native_pointer_getters']==count,'native device cache getter count changed')
    return row


def geometry_context(directory,prefix,engine,without_request=False,without_service_prefixes=False,
                     without_device_cache=False):
    upstream,context=population_context(directory,prefix,engine)
    machine,syms=context['machine'],context['syms']
    source=machine.read(CAPTURE,SIZE)
    population_stack=machine.regions['stack']
    machine.regions['stack']=replace(population_stack,data=b'\xcc'*len(population_stack.data))
    stores,intervals=initializer_storage(machine,directory,prefix,not without_service_prefixes)
    require(machine.read(0x60190ffb,7)==bytes.fromhex('dd350329008008'),
            'original service initializer CALL binding changed')
    initialized=native_call(machine,syms,0x60421330,0x80,8,limit=30000)
    by_index={r['key']>>4:r for r in context['property_records']}
    cache_stores={r['pc']:r for r in stores if 0x6020d024<=r['pc']<0x6020daec}
    bindings={}
    key=None
    for row in initialized['trace']:
        if row['pc']==0x6005e947:
            key=row['d0']&0xffff
        if row['pc'] in cache_stores:
            store=cache_stores[row['pc']]
            require(key is not None and key>>4 in by_index and
                    row['a0']==by_index[key>>4]['data'],
                    'native cached property pointer differs from its original bank')
            bindings[store['address']]=dict(key=hex(key),pointer=hex(row['a0']))
    require(len(bindings)==147 and all(machine.read(address,4)==struct.pack('<I',int(r['pointer'],16))
            for address,r in bindings.items()),'native property cache did not retain its registered pointers')
    require(machine.read(0x622a0644,16)==bytes(16) and
            machine.read(0x622a06fc,16)==bytes(16) and
            machine.read(0x622a0848,128)==b'\xff'*128 and
            machine.read(0x622a0c18,1)==b'\x01' and
            machine.read(0x622a098c,4)==bytes(4),
            'original service state or array initialization differs from known writes')
    initialized_row=summarize_message('native_geometry_service_initializer',initialized,CALL_SP)
    initialized_row.update(cached_property_cells=len(bindings),
        native_pointer_getters=sum(r['pc']==0x6005e947 for r in initialized['trace']))
    require(initialized_row['native_pointer_getters']==148,'service pointer-getter count changed')
    prefix_rows=[]
    if not without_service_prefixes:
        reset=machine.run(0x602ad810,0x602ad86d,overrides=dict(sp=CALL_SP),full_trace=True,limit=1000)
        result_ok(machine,reset,0x602ad86d,CALL_SP)
        require(machine.read(0x6223ed22,1)==b'\0' and
                machine.read(0x6223ed2c,4)==struct.pack('<I',32768) and
                machine.read(0x6223ed3c,4)==struct.pack('<I',32768),
                'native controller reset prefix changed')
        prefix_rows.append(summarize_message('native_controller_reset_prefix',reset,CALL_SP))
        started=machine.run(0x60421540,0x604215b4,overrides=dict(sp=CALL_SP),
            full_trace=True,limit=2000,breakpoints=[syms['_ep7_gcc_quarantine']])
        result_ok(machine,started,0x604215b4,CALL_SP-80)
        require(machine.read(0x622a063c,7)==b'\xff\x00'+bytes(5),
                'native geometry task state prefix changed')
        prefix_rows.append(summarize_message('native_geometry_task_initialization_prefix',started,CALL_SP))
        require(machine.read(0x603b62c1,7)==bytes.fromhex('8003cd4b0df030') and
                machine.read(0x603b7029,6)==bytes.fromhex('fcd3d89673a2') and
                machine.read(0x603b7031,6)==bytes.fromhex('fcd18c345360'),
                'original mode snapshot reset binding changed')
        mode=machine.run(0x603b6297,0x603b62c8,overrides=dict(sp=CALL_SP),full_trace=True,
            limit=3000,breakpoints=[syms['_ep7_gcc_quarantine']])
        result_ok(machine,mode,0x603b62c8,CALL_SP-44)
        expected=bytearray(machine.read(0x60533564,24))
        require(expected[0]==3,'original fallback mode table row changed')
        expected[1:8]=bytes(7)
        require(machine.read(0xa27396d8,72)==bytes(expected)*3 and
                machine.read(0xa2739720,1)==b'\0' and machine.read(0xa2739688,2)==b'\x03\0',
                'original mode snapshot initialization differs from ROM fallback row')
        mode_row=summarize_message('native_mode_snapshot_reset_prefix',mode,CALL_SP)
        mode_row.update(table_row='0x60533564',mode_code=3,record_bytes=24,record_count=3,
                        record=bytes(expected).hex(),selector=0,active_shooting_mode_proven=False)
        prefix_rows.append(mode_row)
    request_rows,request=[],None
    if not without_request:
        request_rows,request=prepare_request_mode(machine,syms)
    device_rows=[]
    if not without_device_cache:
        device_rows.append(prepare_device_property_cache(machine,syms,context['property_records']))
    # Actual producer allocates its local84/16/480/76/26/36/4-byte objects and
    # prepares the76-byte configuration consumed by6042805e. No object is forged.
    machine.regions['caller']=Region('caller',CALLER,
        b'\xdd'+struct.pack('<i',0x6042760c-CALLER)+bytes([0xf0,16]),'rx')
    configured=machine.run(CALLER,CALLER+7,overrides=dict(sp=CALL_SP,d0=0),full_trace=True,
        limit=80000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808])
    row=summarize_message('native_geometry_configuration_producer',configured,CALL_SP)
    if configured['status']!='returned':
        row['d0_at_stop']=row.pop('returned_d0')
    if without_request:
        frontier=('request_mode',0x6020e0e3,0x622a0780,1)
    elif without_service_prefixes:
        frontier=('controller_reset_flag',0x60555c80,0x6223ed22,1)
    elif without_device_cache:
        frontier=('device_property_cache',0x601736d0,0x61f9b0ce,2)
    else:
        frontier=('device_state_query',0x601168ee,0xa272bcde,1)
    kind,pc,address,width=frontier
    require(configured['status']=='memory_fault' and configured['fault']==dict(
            kind=1,pc=pc,map=0,address=address,size=width,access='read'),
            'native geometry configuration frontier changed: '+str(row))
    require(not any(r['pc']==0x6042805e for r in configured['trace']),
            'geometry dynamic setter unexpectedly executed before its known frontier')
    row['stop_registers']={k:hex(v) for k,v in configured['registers'].items()}
    require(machine.read(CAPTURE,SIZE)==source,'geometry service changed the partial capture')
    report=dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),service_initialization_passed=True,
        configuration_producer_passed=configured['status']=='returned',
        frontier=dict(kind=kind,pc=hex(pc),address=hex(address),width=width,
            native_return_pc=hex(configured['registers']['mdr'])),
        cases=[initialized_row]+prefix_rows+request_rows+device_rows+[row],request_mode_source=request,
        native_service_prefixes_executed=not without_service_prefixes,complete_service_startup_executed=False,
        mapped_state_bytes=sum(high-low for low,high in intervals),
        mapped_state_ranges=[[hex(low),hex(high)] for low,high in intervals],
        native_cached_properties={hex(address):binding for address,binding in sorted(bindings.items())},
        capture_unchanged=True,population_resumed=False,geometry_dynamic_setter_executed=any(
            r['pc']==0x6042805e for r in configured['trace']),
        hash_checks_performed=False,native_api_success_stubs=False,firmware_files_modified=False,
        hardware_executed=False,installable=False,
        limits=['Property/runtime/capture fixtures and conditional template BSS remain inherited. No complete boot, task scheduling or real NVM/calibration input.',
                'Only witnessed initializer destinations and two bounded arrays are admitted with A5 input; adjacent unknown state stays unmapped, including guard-like readable padding.',
                '60421330 and its pointer-cache helper execute; zero geometry values are cold reset state, not a claim about an active shot.',
                'Optional602ad810 controller reset and60421540 task initialization prefixes execute to their known continuation points. Event registration, receive/wait and the complete task loop remain outside this independent-call scenario.',
                'Optional request mode uses original producer/consumer slices and explicit single-request controller branch inputs; its allocation, queue transport, enclosing service transitions and complete handler are not executed.',
                'Optional117-row device property cache uses the reviewed startup ROM data-copy recipe and executes60173690. NAND/ECC and a1/61 RAM alias cache coherence remain conditional.',
                '6042760c executes on an independent fresh stack using D0=0 from its original caller. The enclosing semaphore/task loop and configuration inputs remain incomplete.',
                'Partial capture is unchanged; no completion observer, successful dynamic update, full population or worker execution is inferred from service initialization.'])
    context.update(population_stack=population_stack,geometry_configuration=configured)
    return report,context


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--without-request',action='store_true',help='reproduce the missing request-mode byte frontier')
    parser.add_argument('--without-service-prefixes',action='store_true',help='omit controller reset/task prefixes for the earlier frontiers')
    parser.add_argument('--without-device-cache',action='store_true',help='reproduce the uninitialized device property cache frontier')
    args=parser.parse_args()
    print(json.dumps(geometry_context(args.candidate,args.tool_prefix,args.engine,args.without_request,
        args.without_service_prefixes,args.without_device_cache)[0],indent=2))
