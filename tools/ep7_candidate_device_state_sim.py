#!/usr/bin/env python3
"""Execute native board-code publication and follow device inputs without inventing them.

Only the three board-identification input bits are an explicit register fixture.
Native code must restore all modeled control words. Device sampling stops at its
first unprovided dependency; no camera GPIO state or successful boot is asserted.
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
from ep7_candidate_geometry_sim import geometry_context
from ep7_ui_resource_origin import ROM_START,RAM_CACHED
from penf_emulator import Region


def admit(machine,name,address,data,permissions='rw'):
    require(not any(address<r.address+len(r.data) and r.address<address+len(data)
                    for r in machine.regions.values()),'device input region overlaps existing state')
    machine.regions[name]=Region(name,address,data,permissions,permissions=='rw')


def at_frontier(machine,syms,name,target,mask,frame,stop,expected,limit=20000):
    machine.regions['caller']=Region('caller',CALLER,
        b'\xdd'+struct.pack('<i',target-CALLER)+bytes([mask,frame]),'rx')
    result=machine.run(CALLER,stop,overrides=dict(sp=CALL_SP),full_trace=True,limit=limit,
        breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808])
    pc,address,width=expected
    require(result['status']=='memory_fault' and result['fault']==dict(
        kind=1,pc=pc,map=0,address=address,size=width,access='read'),
        'native device input frontier changed: '+str(result['fault']))
    row=summarize_message(name,result,CALL_SP)
    row['d0_at_stop']=row.pop('returned_d0')
    row['stop_registers']={k:hex(v) for k,v in result['registers'].items()}
    return row,result


def device_context(directory,prefix,engine):
    upstream,context=geometry_context(directory,prefix,engine)
    machine,syms=context['machine'],context['syms']
    require(upstream['frontier']['kind']=='device_state_query','geometry prerequisite changed')
    capture=machine.read(CAPTURE,SIZE)
    context['geometry_stack']=machine.regions['stack']
    machine.regions['stack']=replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    # Existing ep7_flash_gpio_probe identified this initializer and the empty
    # remap descriptors. Execute its source copy here using the current strict
    # engine, without importing the historical probe's SHA-based entry point.
    require(machine.read(0x60020117,34)==bytes.fromhex(
        'fcdce8e80260fcdd20e00260fcdee00fb261f1d0f114c80c850479516a52f104c1fa'),
        'original early initialized-data copy changed')
    admit(machine,'device_early_initialized_data',0x61b20fe0,b'\xa5'*2248)
    copied=machine.run(0x60020117,0x60020139,overrides=dict(sp=CALL_SP),full_trace=True,limit=5000)
    result_ok(machine,copied,0x60020139,CALL_SP)
    require(machine.read(0x61b20fe0,2248)==machine.read(0x6002e020,2248) and
            sum(r['pc']==0x60020133 for r in copied['trace'])==562,
            'original562-word initialized-data copy differs from ROM')
    remaps=list(struct.iter_unpack('<II',machine.read(0x61b217cc,48)))
    require(remaps==[(0x61b217a4+i*8,0) for i in range(5)]+[(0,0)],
            'original six GPIO remap descriptors changed')
    ports=[0x9b800b2c,0x9b800b4c,0x9b8010ec]
    require([struct.unpack('<I',machine.read(p,4))[0] for p in
             (0x6002419c,0x600241a0,0x6002421c)]==ports and
            machine.read(0x60022044,5)==bytes.fromhex('cd5e02f02c') and
            machine.read(0x60022301,5)==bytes.fromhex('cdba038004') and
            machine.read(0x60116082,5)==bytes.fromhex('cd9b07f014') and
            machine.read(0x60026ce0,18)==bytes.fromhex('00070106020503030404050206010701ffff') and
            machine.read(0x601aa02c,16)==bytes.fromhex('00000100020003010402050206020702'),
            'original board input/publication/table-selection binding changed')
    for i,address in enumerate(ports):
        admit(machine,f'board_port_{i}',address,struct.pack('<2I',0,0x31415926+i))
    admit(machine,'board_control',0x9b800188,struct.pack('<I',0x27182818))
    admit(machine,'board_code',0x8ff00198,b'\xa5')
    admit(machine,'board_gpio_selector',0x6203c794,b'\xa5')
    admit(machine,'device_table_column',0xa272ba94,b'\xa5'*4)
    clears=[0xa272bae8+100*i for i in range(5)]
    for address in clears:
        admit(machine,f'device_initial_clear_{address:x}',address,b'\xa5')
    code_table=[7,6,5,3,4,2,1,1]
    column_table=[2,2,2,1,2,0,0,0]
    cases=[]
    selected=None
    for bits in range(8):
        current=machine.clone()
        for i,address in enumerate(ports):
            # Distractor bits and saved control words make an incorrect mask or
            # omitted restore observable. They are inputs, not hardware facts.
            value=(0x76543201+i*0x10200)&~16 | ((bits>>i)&1)*16
            current.mutate(f'board_port_{i}',0,struct.pack('<I',value))
        before={name:r.data for name,r in current.regions.items()
                if name.startswith('board_port_') or name=='board_control'}
        published=native_call(current,syms,0x600222a2,0xf0,44,limit=3000)
        require(all(current.regions[name].data==data for name,data in before.items()) and
                current.read(0x8ff00198,1)==bytes([code_table[bits]]) and
                sum(r['pc']==0x600226bb for r in published['trace'])==1,
                'native board publication changed input/control words or code')
        initialized=native_call(current,syms,0x6011681d,0xf0,20,limit=2000)
        require(current.read(0xa272ba94,4)==struct.pack('<I',column_table[bits]) and
                all(current.read(a,1)==b'\0' for a in clears),
                'native device table selector or sparse initialization changed')
        require(current.read(0x60022049,5)==bytes.fromhex('cd4700f020'),
                'original GPIO configuration CALL binding changed')
        current.regions['caller']=Region('caller',CALLER,
            b'\xdd'+struct.pack('<i',0x60022090-CALLER)+bytes([0xf0,32]),'rx')
        aliased=current.run(CALLER,0x600220a9,overrides=dict(sp=CALL_SP),full_trace=True,
            limit=1000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808])
        result_ok(current,aliased,0x600220a9,CALL_SP-32)
        require(current.read(0x6203c794,1)==bytes([min(code_table[bits],5)]),
                'native GPIO selector prefix differs from original capped board code')
        cases.append(dict(input_bits=bits,input_register_words={hex(a):hex(
            struct.unpack('<I',current.read(a,4))[0]) for a in ports},
            published_code=code_table[bits],device_table_column=column_table[bits],
            gpio_remap_selector=min(code_table[bits],5),
            controls_restored=True,cases=[
                summarize_message('native_board_code_publish',published,CALL_SP),
                summarize_message('native_device_column_initialize',initialized,CALL_SP),
                summarize_message('native_gpio_selector_prefix',aliased,CALL_SP)]))
        if bits==0:
            selected=current
    machine=selected
    # The group1 GPIO table and query map are identical in all three reachable
    # columns. Reuse the same proven startup data recipe as the property cache.
    for address,length in [(0x61f99910,12),(0x61f99928,24)]:
        source=ROM_START+address-RAM_CACHED
        admit(machine,f'device_data_table_{address:x}',address,machine.read(source,length),'r')
    require(machine.read(0x61f99928,24)==struct.pack('<6I',
        *([0x601aa1e0]*3+[0x601aa228]*3)), 'reachable device GPIO/query tables differ')
    require(machine.read(0x60020068,12)==bytes.fromhex('fccd886879a2fccc00af1c62') and
            0x621caf00<=0x6272bce8<0x6272bcea<=0x62796888 and
            machine.read(0x6011689b,5)==bytes.fromhex('cdf817f03c') and
            machine.read(0x600c1b70,4)==struct.pack('<I',0x60022056),
            'GPIO snapshot caller, startup BSS or dispatch binding changed')
    # Original snapshot ORs sampled bits, so this exact two-byte region assumes
    # the reviewed BSS clear completed. No additional unknown BSS is supplied.
    admit(machine,'device_gpio_bitmap',0xa272bce8,bytes(2))
    admit(machine,'device_gpio_shadow',0x621db584,b'\xa5'*2)
    admit(machine,'device_gpio_pointers',0x621db588,b'\xa5'*8)
    admit(machine,'device_gpio_counters',0x621db590,b'\xa5'*18)
    gpio,gpio_result=at_frontier(machine,syms,'native_device_gpio_snapshot_prefix',
        0x60118093,0xf0,60,0x6011813d,(0x60022085,0x9b80108c,4))
    require(machine.read(0x621db590,18)==bytes(18) and
            machine.read(0x621db588,8)==struct.pack('<2I',0x601aa228,0x601aa1e0) and
            machine.read(0xa272bce8,2)==bytes(2) and
            machine.read(0x621db584,2)==b'\xa5'*2,
            'GPIO frontier must retain initialized pointers/counters and unpublished snapshot')
    # Independent dependency of601168ba's initial256 query: no pin sample or
    # successful reset is supplied. Original600668b4 must stop at its first read.
    hardware=machine.clone()
    admit(hardware,'device_direct_pin_snapshot',0xa272bcec,b'\xa5')
    admit(hardware,'device_direct_pin_shadow',0x621db5a4,b'\xa5')
    pins,pin_result=at_frontier(hardware,syms,'native_device_direct_pin_snapshot',
        0x60118545,0,4,CALLER+7,(0x600668b4,0x98e00058,4))
    require(hardware.read(0xa272bcec,1)==hardware.read(0x621db5a4,1)==b'\xa5',
            'unavailable direct pin sample was published')
    require(machine.read(CAPTURE,SIZE)==hardware.read(CAPTURE,SIZE)==capture,
            'independent device input probes changed partial capture')
    report=dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),board_publication_and_selection_passed=True,board_input_cases=cases,
        early_data_copy=dict(source='0x6002e020',destination='0x61b20fe0',bytes=2248,
            native_words=562,cases=[summarize_message('native_early_initialized_data_copy',copied,CALL_SP)],
            remap_counts=[r[1] for r in remaps],gpio_remap_descriptors=6),
        selected_input_bits=0,selected_device_table_column=2,selected_input_is_camera_evidence=False,
        cases=[gpio,pins],gpio_snapshot_passed=False,direct_pin_snapshot_passed=False,
        gpio_frontier=dict(pc='0x60022085',address='0x9b80108c',width=4,
            port_number_at_entry=102,lookup='0x60022254',table='0x61b217cc'),
        direct_pin_frontier=dict(pc='0x600668b4',address='0x98e00058',width=4),
        native_device_query='0x1215',query_table_same_for_reachable_columns=True,
        startup_BSS_supplied_bytes=2,startup_BSS_DMA_executed=False,
        geometry_resumed=False,population_resumed=False,capture_unchanged=True,
        hash_checks_performed=False,native_api_success_stubs=False,firmware_files_modified=False,
        hardware_executed=False,installable=False,
        limits=['Three bit4 board-identification inputs and reversible control words are explicit modeled registers, not measurements of this camera. Timing and peripheral side effects are not modeled.',
                'All8 board input combinations execute original600222a2/600226bb and6011681d. This proves software conversion/restoration only, not physical board identity or complete boot.',
                'Only36 bytes of ROM-derived device tables are supplied using the conditional startup data-copy recipe; actual NAND/ECC/cache synchronization remains unexecuted.',
                'GPIO selector prefix60022090 stops before hardware configuration. Its selector and six remap descriptors have native origins; the full211-port configuration is not executed.',
                'GPIO snapshot initial two-byte BSS is conditional. The first actual pin102 read at9b80108c remains unavailable; no pin value or success stub bypasses it.',
                'The independent direct-pin sampler stops at98e00058 before publishing anything. Actual switch state and the complete601168ba reset remain unexecuted.',
                'Original geometry stack and fault registers are retained. Neither geometry configuration nor capture population resumes with incomplete input snapshots.'])
    context.update(machine=machine,device_gpio_result=gpio_result)
    return report,context


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(device_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
