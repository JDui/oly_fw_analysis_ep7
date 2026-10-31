#!/usr/bin/env python3
"""Execute native property defaults and registration before capture initialization.

Four original ROM/default banks supply this bounded scenario. Camera NVM, other
property banks, startup DMA and full service startup remain separate dependencies.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER,require
from ep7_candidate_publish_sim import u32
from ep7_candidate_state_sim import CALL_SP,guarded
from ep7_candidate_message_sim import native_call,summarize_message,result_ok
from ep7_candidate_descriptor_sim import descriptor_context
from ep7_candidate_capture_template_sim import TEMPLATE,SIZE
from ep7_candidate_capture_sim import CAPTURE
from penf_emulator import Region

BASE_INDEX,OVERRIDE_FLAG,OVERRIDE_ROOT = 0xa26ffa88,0xa26ffa84,0x62496400
ROM_RECORDS,ROM_END = 0x60078e2c,0x6008e9cc
DEFAULTS,DEFAULT_END,DEFAULT_RAM = 0x6008e9d0,0x60090e94,0x624b6400


def initialize_rom_properties(machine,syms):
    # Exact original assignment in6005daeb, and original boot registration slice.
    require(machine.read(0x6005daeb,12)==bytes.fromhex('fccc2c8e0760fc81881a71a2') and
            machine.read(0x6005d71e,19)==bytes.fromhex('fca0881a71a29500fccc88fa6fa2cd5b02f030'),
            'ROM-property bank binding or native registration call changed')
    guarded(machine,'property_base_index',OVERRIDE_FLAG,b'\xa5'*(4+4096*8))
    guarded(machine,'property_override_root',OVERRIDE_ROOT,b'\xa5'*4)
    cleared = native_call(machine,syms,0x6005dabf,0,0,dict(a0=BASE_INDEX,d0=4096),limit=50000)
    reset = native_call(machine,syms,0x6005d914,0,0)
    require(machine.read(OVERRIDE_FLAG,2)==bytes(2) and u32(machine,OVERRIDE_ROOT)==0 and
            all(machine.read(BASE_INDEX+8*i,8)==b'\xa5'*4+bytes(4) for i in range(4096)),
            'native base-index pointer clearing or override reset changed')
    registered = native_call(machine,syms,0x6005d987,0xf0,48,
        dict(a0=ROM_RECORDS,a1=0,d0=BASE_INDEX),limit=60000)
    records,seen,pc = [],set(),ROM_RECORDS
    while pc<ROM_END:
        key,count = struct.unpack('<HH',machine.read(pc,4))
        require(key and key>>4 not in seen,'duplicate or early terminated ROM-property record')
        width=(key&3) or 4
        require(pc+4+width*count<=ROM_END,'ROM-property value overran its observed bank')
        row = BASE_INDEX+8*(key>>4)
        require(machine.read(row,8)==struct.pack('<HHI',key,count,pc+4),
                'actual native property row differs from its source record')
        seen.add(key>>4)
        records.append(dict(key=key,count=count,width=width,header=pc,data=pc+4))
        pc=(pc+4+width*count+3)&~3
    require(pc==ROM_END and machine.read(pc,4)==bytes(4) and len(records)==449,
            'ROM-property bank bound or record count changed')
    require(all(u32(machine,BASE_INDEX+8*i+4)==0 for i in range(4096) if i not in seen),
            'native ROM registration invented another property')
    return [summarize_message(name,result,CALL_SP) for name,result in (
        ('native_property_base_index_clear',cleared),('native_property_override_reset',reset),
        ('native_ROM_property_registration',registered))],records


def initialize_default_properties(machine,syms):
    size=DEFAULT_END+4-DEFAULTS
    require(size==2354*4 and
            machine.read(0x6005e117,9)==bytes.fromhex('fcdd00644b622c3209'),
            'native default-copy destination or word count changed')
    guarded(machine,'property_ROM_bank_pointers',0xa2711a88,b'\xa5'*8)
    guarded(machine,'property_default_bank',DEFAULT_RAM,b'\xa5'*size)
    # Original trace helper600230c7 checks bit2 before touching its ring/timer.
    # This explicit disabled-trace fixture is not a property-value override.
    guarded(machine,'native_boot_trace_mask',0x6218d9c0,struct.pack('<H',2),'r')
    assigned=machine.run(0x6005daeb,0x6005db03,overrides=dict(sp=CALL_SP),full_trace=True)
    result_ok(machine,assigned,0x6005db03,CALL_SP)
    require(machine.read(0xa2711a88,8)==struct.pack('<2I',ROM_RECORDS,DEFAULTS),
            'original property-bank pointer assignment changed')
    copied=native_call(machine,syms,0x6005e111,0,4,limit=30000)
    require(machine.read(DEFAULT_RAM,size)==machine.read(DEFAULTS,size),
            'original default bank copy differs from its ROM source')
    registered=machine.run(0x6005d77c,0x6005d78f,overrides=dict(sp=CALL_SP),
                           full_trace=True,limit=40000,breakpoints=[0x60061808])
    result_ok(machine,registered,0x6005d78f,CALL_SP)
    pc,records=DEFAULTS,[]
    while pc<DEFAULT_END:
        key,count=struct.unpack('<HH',machine.read(pc,4))
        require(key,'early default record terminator')
        width=(key&3) or 4
        pointer=DEFAULT_RAM+pc-DEFAULTS+4
        require(pc+4+width*count<=DEFAULT_END and
                machine.read(BASE_INDEX+8*(key>>4),8)==struct.pack('<HHI',key,count,pointer),
                'native default property index differs from copied data')
        records.append(dict(key=key,count=count,width=width,header=pc,data=pointer))
        pc=(pc+4+width*count+3)&~3
    require(pc==DEFAULT_END and len(records)==522,'default property bank bound/count changed')
    return [summarize_message(name,result,CALL_SP) for name,result in (
        ('native_property_bank_pointer_assignment',assigned),('native_default_bank_copy',copied),
        ('native_default_bank_registration',registered))],records


def initialize_configuration_defaults(machine,syms):
    source,end,destination,capacity=0x600921dc,0x60096f00,0x624da400,65536
    # Original6005dbab..dc18 binds this ROM header+8, destination and capacity.
    require(machine.read(0x6005dbec,6)==bytes.fromhex('fcddd4210960') and
            machine.read(0x6005dbfd,6)==bytes.fromhex('fcdd00a44d62') and
            machine.read(0x6005dc0e,6)==bytes.fromhex('fccc00000100'),
            'configuration default bank binding changed')
    pc,expected,records=source,bytearray(b'\xa5'*8),[]
    while pc<end:
        key,count=struct.unpack('<HH',machine.read(pc,4))
        width=(key&3) or 4
        require(key and width in (1,2,4) and pc+4+width*count<=end,
                'configuration default record outside known bank')
        expected.extend(b'\xa5'*((-len(expected))%width))
        pointer=destination+len(expected)
        expected.extend(machine.read(pc+4,width*count))
        records.append(dict(key=key,count=count,width=width,header=pc,data=pointer))
        pc=(pc+4+width*count+3)&~3
    require(pc==end and len(records)==125 and len(expected)==19145 and
            machine.read(end,4)==bytes(4),'configuration record extent or terminator changed')
    guarded(machine,'property_configuration_defaults',destination,b'\xa5'*len(expected))
    guarded(machine,'property_configuration_ends',0xa2715ab4,b'\xa5'*16)
    initialized=native_call(machine,syms,0x6005e309,0xf0,52,
        dict(a0=destination,a1=source,d0=capacity),limit=250000)
    require(machine.read(destination,len(expected))==bytes(expected) and
            u32(machine,0xa2715abc)==destination+len(expected),
            'original configuration packing differs from ROM defaults or recorded extent')
    registered=native_call(machine,syms,0x6005d987,0xf0,48,
        dict(a0=source,a1=destination+8,d0=BASE_INDEX),limit=20000)
    for r in records:
        require(machine.read(BASE_INDEX+8*(r['key']>>4),8)==struct.pack('<HHI',r['key'],r['count'],r['data']),
                'original packed configuration property registration changed')
    rows=[summarize_message(name,result,CALL_SP) for name,result in (
        ('native_configuration_default_packing',initialized),
        ('native_configuration_default_registration',registered))]
    rows[0]['execution_segments']=initialized['execution_segments']
    return rows,records


def initialize_factory_record_defaults(machine,syms):
    source,end,destination=0x60090ea0,0x600921d0,0x624ba400
    # Native object creation owns the first previously free28-byte slot; other
    # slots stay unmapped. No imported camera/NVM record is supplied (A0=0).
    obj=bytearray(b'\xa5'*28)
    struct.pack_into('<I',obj,24,0)
    guarded(machine,'property_config_object',0xa26ff940,bytes(obj))
    pointers=machine.regions['property_ROM_bank_pointers']
    machine.regions['property_ROM_bank_pointers']=replace(pointers,data=pointers.data+b'\xa5'*4)
    machine.regions['property_ROM_bank_pointers_after']=replace(
        machine.regions['property_ROM_bank_pointers_after'],address=0xa2711a94)
    created=machine.run(0x6005db03,0x6005db62,overrides=dict(sp=CALL_SP),full_trace=True,limit=5000)
    result_ok(machine,created,0x6005db62,CALL_SP)
    require(u32(machine,0xa2711a90)==0xa26ff940 and
            machine.read(0xa26ff940+12,16)==struct.pack('<4I',source-8,destination,131072,1),
            'native property configuration object binding changed')
    size=8+end-source+4
    expected=bytearray(b'\xa5'*8+machine.read(source,end-source+4))
    expected[:2]=machine.read(source-8,2)
    guarded(machine,'property_factory_records',destination,b'\xa5'*size)
    packed=native_call(machine,syms,0x6005e129,0xf0,76,dict(a0=0),limit=30000)
    require(packed['registers']['d0']==0 and machine.read(destination,size)==bytes(expected) and
            u32(machine,0xa2715ab4)==destination+size-4,
            'native property record defaults differ from ROM source or endpoint')
    registered=machine.run(0x6005d731,0x6005d744,overrides=dict(sp=CALL_SP),
        full_trace=True,limit=10000,breakpoints=[0x60061808])
    result_ok(machine,registered,0x6005d744,CALL_SP)
    pc,records=source,[]
    while pc<end:
        key,count=struct.unpack('<HH',machine.read(pc,4))
        width=(key&3) or 4
        pointer=destination+8+pc-source+4
        require(key and pc+4+count*width<=end and
                machine.read(BASE_INDEX+8*(key>>4),8)==struct.pack('<HHI',key,count,pointer),
                'native factory record registration changed')
        records.append(dict(key=key,count=count,width=width,header=pc,data=pointer))
        pc=(pc+4+count*width+3)&~3
    require(pc==end and len(records)==113 and size==4924,'factory default record bound changed')
    return [summarize_message(name,result,CALL_SP) for name,result in (
        ('native_property_configuration_object_create',created),
        ('native_factory_record_defaults',packed),
        ('native_factory_record_registration',registered))],records


def property_context(directory,prefix,engine,rom_only=False,poison_template=False):
    upstream,context=descriptor_context(directory,prefix,engine)
    machine=context['machine'].clone()
    stack=machine.regions['stack']
    machine.regions['stack']=replace(stack,data=b'\xcc'*len(stack.data))
    cases,records=initialize_rom_properties(machine,context['syms'])
    if not rom_only:
        default_cases,default_records=initialize_default_properties(machine,context['syms'])
        cases+=default_cases
        records+=default_records
        config_cases,config_records=initialize_configuration_defaults(machine,context['syms'])
        cases+=config_cases
        records+=config_records
        factory_cases,factory_records=initialize_factory_record_defaults(machine,context['syms'])
        cases+=factory_cases
        records+=factory_records
    require(machine.read(0x60020068,12)==bytes.fromhex('fccd886879a2fccc00af1c62') and
            0x621caf00<=TEMPLATE<TEMPLATE+SIZE<=0x62796888,
            'template no longer lies within the original startup BSS clear range')
    # The native initializer writes only part of this static object. Its normal
    # input is the documented startup-BSS zero state, conditional on DMA success.
    # Poison mode is diagnostic only and never a populated-capture input.
    guarded(machine,'native_capture_template',TEMPLATE,(b'\xa5' if poison_template else b'\0')*SIZE)
    machine.regions['caller']=Region('caller',CALLER,
        b'\xdd'+struct.pack('<i',0x6030002c-CALLER)+bytes([0,4]),'rx')
    result=machine.run(CALLER,CALLER+7,overrides=dict(sp=CALL_SP),full_trace=True,limit=100000,
        breakpoints=[context['syms']['_ep7_gcc_quarantine'],0x60061808])
    row=summarize_message('capture_template_after_native_property_registration',result,CALL_SP)
    if result['status']!='returned':
        row['d0_at_stop']=row.pop('returned_d0')
    lookups=[dict(key=hex(r['d0'] & 0xffff),return_pc=hex(r['mdr']))
             for r in result['trace'] if r['pc']==0x6005d924]
    if result['status']=='returned':
        result_ok(machine,result,CALLER+7,CALL_SP)
        require(machine.read(0x6225e590,12)==struct.pack('<3I',20192,29664,18912) and
                machine.read(TEMPLATE+1480,24)==machine.read(0x6007de70,23)+b'\0' and
                len(lookups)==16,
                'native template constants, property string or lookup count changed: '+json.dumps(dict(
                    constants=struct.unpack('<3I',machine.read(0x6225e590,12)),
                    company=machine.read(TEMPLATE+1480,24).hex(),
                    source=machine.read(0x6007de70,24).hex(),lookups=len(lookups))))
    elif rom_only:
        require(result['status']=='breakpoint' and result['registers']['pc']==0x60061808 and
                lookups[-1]['key']=='0xc082','ROM-only missing-default frontier changed')
    else:
        require(False,'native template initialization did not complete: '+str(row))
    require(machine.read(CAPTURE,24084)==context['machine'].read(CAPTURE,24084),
            'independent template initializer changed the source capture')
    indexed={r['key']>>4 for r in records}
    require(len(indexed)==len(records) and
            all(u32(machine,BASE_INDEX+8*i+4)==0 for i in range(4096) if i not in indexed),
            'registered property sets overlap or filled an unrelated index')
    row['native_property_lookups']=lookups
    cases.append(row)
    report=dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),native_property_registration_passed=True,registered_records=len(records),
        ROM_bank=dict(start=hex(ROM_RECORDS),terminator=hex(ROM_END)),
        default_bank=None if rom_only else dict(ROM=hex(DEFAULTS),terminator=hex(DEFAULT_END),RAM=hex(DEFAULT_RAM),records=522),
        configuration_defaults=None if rom_only else dict(ROM='0x600921dc',RAM='0x624da400',records=125,packed_extent=19145,
                                                          camera_NVM_read=False),
        factory_record_defaults=None if rom_only else dict(ROM='0x60090ea0',RAM='0x624ba400',records=113,extent=4924,
                                                           imported_camera_records=False),
        cases=cases,template_initialization_passed=result['status']=='returned',
        template=dict(address=hex(TEMPLATE),bytes=SIZE,initial_fill='a5' if poison_template else '00',
                      startup_BSS_range=['0x621caf00','0x62796888'],startup_DMA_executed=False,
                      usable_default_fixture=result['status']=='returned' and not poison_template,
                      native_constant_words=[20192,29664,18912] if result['status']=='returned' else None),
        partial_template_copied_to_capture=False,
        source_capture_unchanged=machine.read(CAPTURE,24084)==context['machine'].read(CAPTURE,24084),
        hash_checks_performed=False,native_api_success_stubs=False,firmware_files_modified=False,
        hardware_executed=False,installable=False,
        limits=['Property index storage, one fresh configuration object slot and upstream kernel/runtime are explicit bounded fixtures, not full property-service boot or allocation proof.',
                'All property values come from original ROM records/defaults. No camera NVM/calibration data is imported, persisted or claimed to match a physical camera.',
                'Original record pointers, default copy, typed packing, registration and getters execute. Additional property banks and override activation remain outside this scenario.',
                'Original boot trace helper executes with explicit disable bit2. No trace ring/timer or hardware logging is modeled.',
                'Normal template storage assumes the witnessed original BSS DMA clear completed. Poison mode demonstrates the initializer does not initialize every byte; neither mode proves DMA completion.',
                'Template remains separate from the capture: full population, relay preprocessing, worker allocation/processing/cleanup and ACK are later stages.'])
    context.update(machine=machine,template_result=result,property_records=records)
    return report,context


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--rom-only',action='store_true',help='omit RAM default banks to reproduce the missing c082 frontier')
    parser.add_argument('--poison-template',action='store_true',help='diagnose partial field initialization without the conditional BSS-zero input')
    args=parser.parse_args()
    print(json.dumps(property_context(args.candidate,args.tool_prefix,args.engine,args.rom_only,args.poison_template)[0],indent=2))
