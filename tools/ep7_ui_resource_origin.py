#!/usr/bin/env python3
"""Startup data-copy recipe and four existing text descriptors; static, no hashes."""
import argparse,json,struct
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE

ROM_START=0x60230800;ROM_END=0x6025eb50
FLASH_START=0x408b0800;PAYLOAD_FLASH=0x406a0020
RAM_UNCACHED=0xa1f98540;RAM_CACHED=0x61f98540
WINDOWS=[(0x600201ab,0x600201b7),(0x600201fe,0x6002021b),
    (0x6002144e,0x60021457),(0x600214c0,0x600214cd),(0x6002156d,0x600215ea),
    (0x60021279,0x6002128e),(0x60d7ac19,0x60d7ac32),
    (0x60d01efa,0x60d01f08),(0x60cfe018,0x60cfe038),
    (0x60cfe04f,0x60cfe06f),(0x60cfe081,0x60cfe0b0)]
W={
    0x600201ab:('mov',str(ROM_END)+',d0'),0x600201b1:('mov','d0,(0x6218d984)'),
    0x600201fe:('mov','(0x6218d984),d0'),0x60020204:('mov',str(FLASH_START)+',a0'),
    0x6002020a:('mov',str(RAM_UNCACHED-0x100000000)+',a1'),
    0x60020210:('add',str(-ROM_START)+',d0'),0x60020216:('call','0x6002144e,[d2,d3,a2,a3],32'),
    0x6002144e:('mov','a0,(8,sp)'),0x60021450:('mov','d0,d2'),0x60021451:('mov','a1,a2'),
    0x600214c0:('mov','a2,(4,sp)'),0x600214c2:('cmp','262144,d2'),
    0x600214c8:('bgt','0x600214cd'),0x600214ca:('jmp','0x6002156d'),
    0x6002156d:('mov','(8,sp),d3'),0x6002156f:('and','2047,d3'),
    0x60021577:('beq','0x600215b4'),0x600215b4:('mov','d2,d3'),
    0x600215b5:('mov','(8,sp),d1'),0x600215b7:('mov','2047,d0'),
    0x600215ba:('and','d2,d0'),0x600215bc:('sub','d0,d3'),
    0x600215be:('mov','(4,sp),d0'),0x600215c0:('mov','d3,a0'),
    0x600215c2:('call','0x60020ba7,[d2,d3,a2,a3],44'),
    0x600215c7:('mov','(4,sp),a3'),0x600215c9:('mov','(8,sp),d1'),
    0x600215cb:('add','d3,a3'),0x600215cd:('add','d3,d1'),
    0x600215ce:('sub','d3,d2'),0x600215d0:('beq','0x600215ea'),
    0x600215d2:('mov',str(0xa26b1270-0x100000000)+',a2'),
    0x600215d8:('mov','a2,d0'),0x600215da:('mov','2048,a0'),
    0x600215dd:('call','0x60020ba7,[d2,d3,a2,a3],44'),
    0x600215e2:('mov','d2,d0'),0x600215e3:('mov','a2,a1'),0x600215e4:('mov','a3,a0'),
    0x600215e5:('call','0x600212f3,[d2,d3,a2,a3],24'),
    0x6002127a:('mov','1073741824,d1'),0x60021286:('sub','d1,d0'),
    0x60021288:('btst','2047,d2'),0x6002128c:('beq','0x600212b6'),
    0x60d7ac19:('mov','(4,sp),a2'),0x60d7ac1b:('add',str(0x61fb7070)+',a2'),
    0x60d7ac21:('mov','(a2),a1'),0x60d7ac24:('movhu','(a1),d0'),
    0x60d7ac28:('mov','(8,sp),d1'),0x60d7ac2a:('call','0x60d337b2,[d2,a2,a3],24'),
    0x60d01efa:('movhu','(82,a0),d0'),0x60d01efd:('exth','d0'),0x60d01efe:('retf','[],0'),
    0x60d01f01:('movhu','(80,a0),d0'),0x60d01f04:('exth','d0'),0x60d01f05:('retf','[],0'),
    0x60cfe021:('mov','(692,a1),a1'),0x60cfe025:('calls','(a1)'),
    0x60cfe027:('mov','d0,d3'),0x60cfe031:('mov','(696,a1),a1'),
    0x60cfe035:('calls','(a1)'),0x60cfe04f:('exth','d2'),0x60cfe050:('asl','3,d2'),
    0x60cfe059:('mov','d2,a0'),0x60cfe05b:('call','0x60d109d1,[],4'),
    0x60cfe066:('mov','a0,(a1)'),0x60cfe068:('cmp','0,a0'),
    0x60cfe06a:('bne','0x60cfe06f'),0x60cfe06c:('clr','d0'),
    0x60cfe081:('exth','d3'),0x60cfe084:('asl','3,d3'),0x60cfe087:('movhu','(d3,a0),d0')}
CHECKS=[(0x60faaab4+692,'<2I',(0x60d01efa,0x60d01f01))]

def inspect_data(data):
    size=ROM_END-ROM_START
    if FLASH_START-PAYLOAD_FLASH!=ROM_START-BASE:raise ValueError('component/flash recipe differs')
    def image_address(ram,count):
        if not RAM_CACHED<=ram<ram+count<=RAM_CACHED+size:raise ValueError('outside startup copy')
        return ROM_START+ram-RAM_CACHED
    def unpack(address,fmt):
        if not BASE<=address<address+struct.calcsize(fmt)<=BASE+len(data):raise ValueError('outside main')
        return struct.unpack_from(fmt,data,address-BASE)
    table=image_address(0x61fb7070,58*4)
    if table!=0x6024f330:raise ValueError('resource table image mapping')
    pointers=unpack(table,'<58I');resources=[]
    expected={7:(0x61032d88,6559,0x61031b54,0x610308ec,257),
        11:(0x61032de8,6563,0x61031b64,0x6103090c,257),
        51:(0x61032e48,6603,0x61031b74,0x61030a4c,256),
        53:(0x61032ea8,6605,0x61031b84,0x61030a5c,256)}
    if pointers[0]!=0:raise ValueError('resource index0 changed')
    for index,pointer in enumerate(pointers[1:],1):
        kind,ident,layout,flags,opaque=unpack(pointer,'<HHIII')
        if kind!=0x8010:continue
        want=expected.get(index)
        if want is None or (pointer,ident,layout,opaque)!=want[:4]:raise ValueError('text descriptor changed')
        font=unpack(pointer+48,'<H')[0];resource_id=unpack(pointer+20,'<H')[0]
        guard68=unpack(pointer+68,'<B')[0];guard84=unpack(pointer+84,'<B')[0]
        style=unpack(pointer+24,'<6I');opaque56=unpack(pointer+56,'<I')[0]
        if (flags,font,resource_id,guard68,guard84,opaque56)!=(9,1,0,0,0,7):raise ValueError('text fields changed')
        if style!=(0,15,15,want[4],0,0):raise ValueError('text style changed')
        if unpack(opaque,'<4I')!=(0,0,0,0):raise ValueError('opaque resource data changed')
        unpack(pointer,'<94B') # Exact minimum reviewed initializer extent exists.
        rects=unpack(layout,'<8h')
        if any(v<=0 for v in (rects[2],rects[3],rects[6],rects[7])):raise ValueError('empty rectangle')
        resources.append(dict(table_index=index,descriptor=hex(pointer),type=hex(kind),id=ident,
            layout_pointer=hex(layout),reviewed_rectangles=[list(rects[:4]),list(rects[4:])],
            readable_descriptor_minimum=94,font_selector=font,resource_string_id=resource_id,
            opaque12_pointer=hex(opaque),opaque12_reviewed_zero_words=4,opaque56_value=opaque56,
            rollback_guard_descriptor_offsets=[68,84],rollback_guard_values=[guard68,guard84],
            opaque12_semantics_or_null_substitution_qualified=False))
    if len(resources)!=len(expected):raise ValueError('text descriptor count changed')
    callbacks_at=image_address(0x61fc3874,28)
    callbacks=unpack(callbacks_at,'<7I')
    if callbacks!=(0x60e261f0,0x60e26215,0x60e26270,0x60e262c0,0x60e26397,0x60e2642a,0x60e26609):
        raise ValueError('parent callbacks changed')
    return dict(startup_copy=dict(source=hex(FLASH_START),decoded_source=hex(ROM_START),
        decoded_end_exclusive=hex(ROM_END),destination=hex(RAM_UNCACHED),cached_alias=hex(RAM_CACHED),
        bytes=size,cached_end_exclusive=hex(RAM_CACHED+size),
        component_payload_flash=hex(PAYLOAD_FLASH),full_page_bytes=size&~2047,tail_bytes=size&2047),
        resource_table=dict(runtime=hex(0x61fb7070),decoded_initializer=hex(table),entries=58),
        text_descriptors=resources,parent_callbacks=dict(runtime=hex(0x61fc3874),
            decoded_initializer=hex(callbacks_at),entries=[hex(x) for x in callbacks]),
        alias_relation='0xa1/0x61 RAM mapping used by existing firmware analysis; cache coherence and board behavior not executed')

def inspect(stock,objdump):
    data_report={}
    e=inspect_windows(stock,objdump,WINDOWS,W,CHECKS,observe_data=lambda data:data_report.update(inspect_data(data)))
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],**data_report,
        service_layout_count_offset=80,service_layout_index_offset=82,
        admitted_template_requirement='count=2, signed index=0 or 1, stable live service and loaded ROM references',
        later_runtime_table_writes_excluded=False,opaque_fields_fully_qualified=False,glyph_rendering_verified=False,
        conditional_startup_copy_recipe_joined=True,whole_boot_executed=False,storage_ecc_cache_modeled=False,
        hash_checks_performed=False,firmware_modified=False,renderer_ready=False,flash_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
