#!/usr/bin/env python3
"""Run original format-module state initialization before resuming its getter.

The60556b1e RAM prefix stops before two diagnostic-buffer allocations. The
module publication helper executes independently; full startup is not claimed.
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
from ep7_candidate_snapshot_sim import snapshot_context, call_prefix, stage
from ep7_candidate_message_sim import native_call, result_ok
from ep7_candidate_geometry_sim import map_initializer_storage
from ep7_candidate_device_state_sim import admit


def format_storage(machine, directory, prefix):
    #13 original diagnostic-record string copies. Only their actual NUL-ended
    #source extents are writable, not the unused tail of every48-byte record.
    strings = []
    for index in range(13):
        pc, destination = 0x6066da75+34*index, 0xa2787d95+48*index
        require(machine.read(pc,6) == b'\xfc\xdc'+struct.pack('<I',destination) and
                machine.read(pc+6,2) == b'\xfc\xdd' and
                machine.read(pc+12,7) == b'\xdd'+struct.pack('<i',0x60022f4b-(pc+12))+bytes([0x20,4]),
                'original diagnostic string initialization shape changed')
        source = struct.unpack('<I',machine.read(pc+8,4))[0]
        require(0x60719bfa <= source < 0x60719d3f,'diagnostic string source escaped reviewed ROM')
        data = machine.read(source,43)
        require(b'\0' in data,'diagnostic string does not fit its original record')
        data = data[:data.index(0)+1]
        strings.append(dict(pc=pc,source=source,destination=destination,data=data))
    # a2788cac points at a2788cb0;606d6982 writes its byte297 indirectly.
    require(machine.read(0x60556b25,6) == bytes.fromhex('fcccb08c78a2') and
            machine.read(0x606d6982,6) == bytes.fromhex('fca0ac8c78a2') and
            machine.read(0x606d698b,4) == bytes.fromhex('fa502901'),
            'module state pointer/indirect reset destination changed')
    windows = [(0x60556b1e,0x60556bb2),(0x606bbffc,0x606bc084),
               (0x606ba198,0x606ba1f0),(0x606ba9a6,0x606ba9f1),
               (0x606bb540,0x606bb57f),(0x6066da62,0x6066dc23),
               (0x606934f5,0x60693526)]
    stores, ranges = map_initializer_storage(machine,directory,prefix,windows,
        [(0xa2787d8c,0xa2788f7d),(0xa2788fb4,0xa2788fb5),(0x622c5430,0x622c5448)],
        [(s['destination'],s['destination']+len(s['data'])) for s in strings]+[(0xa2788dd9,0xa2788dda)],
        name_prefix='native_format_module')
    return stores,ranges,strings


def prepare_mode_fields(machine, directory, prefix, syms, property_records):
    require(machine.read(0x606bc08c,7) == bytes.fromhex('dd4dab01000004') and
            machine.read(0x606d6f45,3) == bytes.fromhex('df0004') and
            machine.read(0x606d47fc,9) == bytes.fromhex('fca0ac8c78a2f8400f'),
            'module property cache or conditional mode refresh entry changed')
    fields = [(0x606d4827,5),(0x606d4838,6),(0x606d4855,7),
              (0x606d4866,8),(0x606d4877,9),(0x606d4895,10)]
    require(all(machine.read(pc,3)==bytes([0xf8,0x50,offset]) for pc,offset in fields),
            'original mode refresh indirect stores changed')
    stores,ranges = map_initializer_storage(machine,directory,prefix,[(0x606d6bd9,0x606d6f48)],
        [(0xa2788e08,0xa2788ec8)],[(0xa2788cb5,0xa2788cbb)],name_prefix='native_format_mode')
    cache = native_call(machine,syms,0x606d6bd9,0,4,limit=10000)
    by_index = {r['key']>>4:r for r in property_records}
    by_pc = {r['pc']:r for r in stores}
    bindings, key = {}, None
    for row in cache['trace']:
        if row['pc'] == 0x6005e947:
            key = row['d0']&0xffff
        if row['pc'] in by_pc:
            require(key is not None and key>>4 in by_index and
                    row['a0'] == by_index[key>>4]['data'],
                    'native module cached property differs from its original bank')
            bindings[by_pc[row['pc']]['address']] = dict(key=hex(key),pointer=hex(row['a0']))
    require(len(bindings) == 48 and all(machine.read(a,4)==struct.pack('<I',int(r['pointer'],16))
            for a,r in bindings.items()),'module property cache did not retain its48 original pointers')
    #One idle byte of the original state object, conditional on the already
    #witnessed boot BSS clear and cached/uncached alias identity. This permits
    #the original refresh predicate; it is not supplied as a camera measurement.
    require(0x621caf00 <= 0xa2788cbf-0x40000000 < 0x62796888 and
            machine.read(0x60020068,12)==bytes.fromhex('fccd886879a2fccc00af1c62'),
            'format state idle byte escaped the original BSS range')
    admit(machine,'format_idle_conditional_BSS',0xa2788cbf,b'\0')
    modes = call_prefix(machine,0x606d47fc,0,4,0x606d4898,limit=10000)
    result_ok(machine,modes,0x606d4898,CALL_SP-4)
    writes = [r for r in modes['trace'] if r['pc'] in dict(fields)]
    require(len(writes)==6 and all(r['a0']==0xa2788cb0 and
            machine.read(r['a0']+dict(fields)[r['pc']],1)==bytes([r['d0']&255]) for r in writes),
            'native mode refresh did not write all six getter results')
    return [stage('native_format_property_cache_initialize',cache),
            stage('native_format_mode_fields_refresh_prefix',modes)],dict(
        mapped_state_bytes=1+sum(b-a for a,b in ranges),source_direct_stores=len(stores),
        bindings={hex(a):r for a,r in bindings.items()},conditional_BSS_bytes=1,
        mode_fields=machine.read(0xa2788cb5,6).hex(),
        getter_keys=[hex(r['d0']&0xffff) for r in modes['trace'] if r['pc']==0x6005e971])


def format_context(directory, prefix, engine, without_mode_fields=False, without_core_prefix=False,
                   diagnostic_setup=None):
    upstream, contexts = snapshot_context(directory,prefix,engine)
    syms = contexts['upstream']['upstream']['upstream']['syms']
    rows, outputs = [], []
    for index, context in enumerate(contexts['cases']):
        machine = context['machine']
        capture = machine.read(CAPTURE,SIZE)
        producer_stack, producer_caller = machine.regions['stack'],machine.regions['caller']
        machine.regions['stack'] = replace(producer_stack,data=b'\xcc'*len(producer_stack.data))
        stores,ranges,strings = format_storage(machine,directory,prefix)
        require(machine.read(0x60190fd3,7)==bytes.fromhex('dd4b5b3c000004') and
                machine.read(0x6019139a,7)==bytes.fromhex('dd62ac52000004'),
                'original cold/module-publication CALL sites changed')
        cold = call_prefix(machine,0x60556b1e,0,4,0x60556bb2,limit=1000)
        result_ok(machine,cold,0x60556bb2,CALL_SP-4)
        require(machine.read(0xa2788ca8,1) == b'\0' and
                machine.read(0xa2788cac,4) == struct.pack('<I',0xa2788cb0),
                'native cold prefix did not reset readiness and publish its state pointer')
        diagnostic_result,diagnostics = None,None
        if diagnostic_setup is not None:
            diagnostic_result,diagnostics = diagnostic_setup(machine,syms,cold)
        core = None
        core_bytes = 0
        if not without_core_prefix:
            require(machine.read(0x6019138c,7)==bytes.fromhex('dd64ac4c000004') and
                    machine.read(0x6065c011,6)==bytes.fromhex('fc8284ea2b62') and
                    machine.read(0x606a46cf,3)==bytes.fromhex('de0000'),
                    'original format core initialization prefix changed')
            core_stores,core_ranges = map_initializer_storage(machine,directory,prefix,
                [(0x6065bff0,0x6065c01e)],[(0x622be666,0x622bea85),(0xa2787a48,0xa2787a4a)],
                name_prefix='native_format_core')
            core_bytes = sum(b-a for a,b in core_ranges)
            core = call_prefix(machine,0x6065bff0,0,4,0x6065c01e,limit=1000)
            result_ok(machine,core,0x6065c01e,CALL_SP-4)
            require(len(core_stores)==6 and machine.read(0x622bea84,1)==b'\1',
                    'original format core did not publish its native branch state')
        #Read the original2af4 property through its native pointer getter. The
        #24-byte debug mask record is copied by the original startup prefix.
        require(machine.read(0x606bb540,10) ==
                b'\x2c\xf4\x2a\xdd'+struct.pack('<i',0x6005e947-0x606bb543)+bytes([0,4]),
                'native debug-mask property getter changed')
        masks = machine.run(0x606bb540,0x606bb57f,overrides=dict(sp=CALL_SP),
            full_trace=True,limit=2000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
        result_ok(machine,masks,0x606bb57f,CALL_SP)
        pointer = masks['registers']['a0']
        require(machine.read(0x622c5430,24) == machine.read(pointer,24),
                'original debug-mask property copy differs')
        initialized = call_prefix(machine,0x606bbffc,0,4,CALLER+7,limit=10000)
        result_ok(machine,initialized,CALLER+7,CALL_SP)
        setup = [stage('native_format_module_cold_RAM_prefix',cold),
                 *([stage('native_diagnostic_buffer_allocation_and_cold_suffix',diagnostic_result)]
                   if diagnostic_result is not None else []),
                 *([stage('native_format_core_initialization_prefix',core)] if core is not None else []),
                 stage('native_debug_mask_property_copy_prefix',masks),
                 stage('native_format_module_publish',initialized)]
        produced = None
        mode_info = None
        if initialized['status'] == 'returned':
            result_ok(machine,initialized,CALLER+7,CALL_SP)
            require(machine.read(0xa2788ca8,1) == b'\1' and
                    all(machine.read(s['destination'],len(s['data'])) == s['data'] for s in strings) and
                    sum(r['pc']==0x60022f4b for r in initialized['trace']) == 13,
                    'native format publication/string initialization did not complete')
            if not without_mode_fields:
                mode_cases,mode_info = prepare_mode_fields(machine,directory,prefix,syms,
                    contexts['upstream']['upstream']['upstream']['property_records'])
                setup.extend(mode_cases)
            machine.regions['stack'],machine.regions['caller'] = producer_stack,producer_caller
            produced = machine.resume(context['producer_result']['registers'],0x60409ecb,
                full_trace=True,limit=80000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
            setup.append(stage('native_snapshot_resume_with_format_module',produced))
        require(machine.read(CAPTURE,SIZE) == capture,'format-module probe changed partial capture')
        last = produced if produced is not None else initialized
        if without_mode_fields:
            pc,address,width,return_pc = 0x606d674d,0xa2788cb6,1,0x6065e66c
        elif without_core_prefix:
            pc,address,width,return_pc = 0x6065f55c,0x622bea84,1,0x6069345c
        else:
            pc,address,width,return_pc = 0x606d673a,0xa2788cec,2,0x60664e1e
        require(last['status']=='memory_fault' and last['fault']==dict(
                kind=1,pc=pc,map=0,address=address,size=width,access='read') and
                last['registers']['mdr']==return_pc and
                any(r['pc']==0x6065e658 for r in last['trace']),
                'original format producer frontier changed: '+str(last['fault']))
        record_stores = {r['pc']:r for r in stores if 0x606934f5<=r['pc']<0x60693526}
        record_writes = [r for r in last['trace'] if r['pc'] in record_stores]
        record_produced = not without_mode_fields and not without_core_prefix
        require(len(record_writes)==7*int(record_produced),
                'original format parameter record store count changed')
        for row in record_writes:
            spec = record_stores[row['pc']]
            expected = (row[spec['register']]&((1<<(8*spec['width']))-1)).to_bytes(spec['width'],'little')
            require(machine.read(spec['address'],spec['width'])==expected,
                    'native format parameter record differs from its original stores')
        rows.append(dict(gpio80_input_bit4=index,cases=setup,
            mapped_state_bytes=sum(b-a for a,b in ranges),source_direct_stores=len(stores),
            format_core_prefix_completed=core is not None,format_core_mapped_bytes=core_bytes,
            diagnostic_string_records=len(strings),diagnostic_string_bytes=sum(len(s['data']) for s in strings),
            debug_mask_source=hex(pointer),debug_masks=machine.read(0x622c5430,24).hex(),
            mode_refresh=mode_info,
            total_mapped_state_bytes=sum(b-a for a,b in ranges)+core_bytes+
                (mode_info['mapped_state_bytes'] if mode_info is not None else 0),
            format_parameter_record_produced=record_produced,
            format_parameter_record_address='0xa2788aa4',format_parameter_record_bytes=10,
            format_parameter_record=machine.read(0xa2788aa4,10).hex() if record_produced else None,
            complete_format_core_initializer_executed=False,complete_mode_refresh_executed=False,
            complete_format_getter_executed=False,
            native_cold_prefix_completed=True,complete_cold_initializer_executed=diagnostics is not None,
            diagnostic_buffer_allocations_executed=diagnostics is not None,diagnostic_buffers=diagnostics,
            native_module_publication_completed=initialized['status']=='returned',
            snapshot_producer_completed=bool(produced is not None and produced['status']=='returned'),
            frontier=dict(status=last['status'],fault=last['fault'],
                pc=hex(last['registers']['pc']),native_return_pc=hex(last['registers']['mdr'])),
            capture_unchanged=True,geometry_consumer_resumed=False))
        outputs.append(dict(machine=machine,configuration_result=context['configuration_result'],
            configuration_stack=context['configuration_stack'],producer_result=produced,
            diagnostic_result=diagnostic_result,diagnostic_buffers=diagnostics))
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),cases=rows,
        native_instructions=sum(c['completed'] for row in rows for c in row['cases']),
        maximum_observed_new_stack_depth=max(c['stack_depth_from_call_sp'] for row in rows for c in row['cases']),
        population_resumed=False,hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=[('Cold60556b1e is executed only to60556bb2 before two diagnostic-buffer allocations. Its complete initializer and allocation ownership are not claimed.'
                 if diagnostic_setup is None else
                 'The original cold prefix and suffix execute continuously through two native fixed-pool allocations under explicit fresh-BSS and temporary pre-kernel lock conditions; complete startup ordering/ownership remains unproven.'),
            'Debug masks come from the original2af4 property and native getter/copy, not from forcibly disabling logs.',
            'The606bbffc publication helper executes independently; its ready byte does not prove initialization of all downstream format records or the complete startup schedule.',
            'Only reviewed native direct stores, one indirect byte and13 bounded ROM strings are mapped from A5. Unknown neighboring fields remain unmapped.',
            'Optional48-slot original property cache and six-field mode refresh execute independently. One idle predicate byte assumes original BSS clear/alias identity; the refresh stops before its remaining fields and service queries.',
            'Optional6065bff0 core prefix executes six RAM stores and the original one-instruction606a46cf helper, then stops before606baeb0 and the remaining core initializers.',
            'The10-byte parameter record comes from seven real stores after native property queries; the following10-byte state-record copy remains incomplete at its first halfword.',
            'Original snapshot producer registers and stack resume only after native publication. Geometry consumer and capture population remain unresumed.'])
    return report,dict(upstream=contexts,cases=outputs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--without-mode-fields',action='store_true')
    parser.add_argument('--without-core-prefix',action='store_true')
    args = parser.parse_args()
    print(json.dumps(format_context(args.candidate,args.tool_prefix,args.engine,args.without_mode_fields,
                                    args.without_core_prefix)[0],indent=2))
