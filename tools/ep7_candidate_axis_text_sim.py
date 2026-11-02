#!/usr/bin/env python3
"""Execute final candidate axis paint with native font setup and text layout.

Font resource acquisition, glyph metrics and raster callbacks are explicit
boundaries. No device pixels, display scheduling or live framebuffer is modeled.
"""
import argparse,json,struct,subprocess,tempfile
from pathlib import Path
from ep7_candidate_startup_sim import Machine,SP,CALLER,require
from ep7_offline_candidate import BASE,IMAGE_NAME,ELF_NAME,sections,symbols
from penf_emulator import Region
from ep7_sim_probe import brief
ROOT=Path(__file__).resolve().parents[1]

def inspect(directory,prefix,engine):
    directory=Path(directory)
    build=json.loads((directory/'report.json').read_text())
    require(build['status']=='passed','candidate build did not pass')
    syms={k:v['address'] for k,v in symbols(prefix,directory/ELF_NAME).items()}
    data=(directory/IMAGE_NAME).read_bytes()
    allocated=sections(prefix,directory/ELF_NAME)
    with tempfile.TemporaryDirectory(prefix='ep7-axis-text-') as temporary:
        tmp=Path(temporary)
        for name in ('.ep7_code0','.ep7_code1'):
            section=next(s for s in allocated if s['name']==name)
            path=tmp/(name+'.bin')
            subprocess.run([prefix+'objcopy','-O','binary','-j',name,str(directory/ELF_NAME),str(path)],check=True)
            require(data[section['address']-BASE:section['address']-BASE+section['size']]==path.read_bytes(),'candidate code differs from ELF')
        return execute_probe(directory,prefix,engine,build,syms,data,tmp)

def execute_probe(directory,prefix,engine,build,syms,data,tmp):
    m=Machine(data,engine)
    m.regions['native_helpers']=Region('native_helpers',0x47000800,m.read(0x6143ca00,6144),'rx')
    def add(n,p,data):m.regions[n]=Region(n,p,data,'rwx',True)
    def write(p,data):
     for n,r in m.regions.items():
      if r.address<=p and p+len(data)<=r.address+len(r.data):m.mutate(n,p-r.address,data);return
     raise ValueError(hex(p))
    def word(p,v):write(p,struct.pack('<I',v&0xffffffff))
    def half(p,v):write(p,struct.pack('<H',v))
    def readw(p):return struct.unpack('<I',m.read(p,4))[0]
    add('gui_static',0x61f98540,m.read(0x60230800,0x2e350));add('fixture',0x19700000,bytes(0x10000))
    # Run actual native font creation and text layout, model only the resource/font
    # backend acquisition, glyph metrics and eventual raster submission boundary.
    OWNER=0x19700000;HEAD=OWNER+0x800;TEXT=OWNER+0x900;CTX=OWNER+0x1000;JOB=OWNER+0x1400
    FONT=OWNER+0x1800;META=OWNER+0x1900;DESC=OWNER+0x2000;MEM=OWNER+0x3000;SERVER=OWNER+0x8000
    word(OWNER+872,HEAD);half(HEAD+8,456);half(HEAD+4,0x8008) # nontext Color heading
    # Use the actual first native text child, not a synthetic white style. Its
    # foreground0 is transparent in the shooting text CLUT and exposed the013
    # empty-fill regression once the backdrop was present.
    text_resource=0x61032d88
    source_font=struct.unpack_from('<H',data,text_resource-BASE+48)[0]
    source_style=data[text_resource-BASE+24:text_resource-BASE+48]
    require(struct.unpack_from('<3I',source_style)==(0,15,15),'native source text style changed')
    word(OWNER+792+4*7,TEXT);half(TEXT+4,0x8010);half(TEXT+128,source_font)
    write(TEXT+132,source_style)
    # Mode1 layer2 selects surface1/palette6. Shooting's runtime text CLUT54
    # updates that same surface. Check the real opaque ink entries in both.
    layer_descriptor=0x61122494
    require(struct.unpack_from('<H',data,0x60f942a4-BASE+2)[0]==1 and
            layer_descriptor==0x6112242c+2*52,'native root mode/layer descriptor changed')
    require(struct.unpack_from('<I',data,layer_descriptor-BASE)[0]==1 and
            struct.unpack_from('<H',data,layer_descriptor-BASE+8)[0]==6,
            'native layer2 palette binding changed')
    text_palettes=[]
    for resource in (6,54):
        descriptor=struct.unpack_from('<I',data,0x60259904-BASE+4*resource)[0]
        palette=struct.unpack_from('<I',data,descriptor-BASE+4)[0]
        colors={index:struct.unpack_from('<I',data,palette-BASE+4*index)[0]
                for index in (0,4,16)}
        require(colors=={0:0x00ffffff,4:0xfffefefe,16:0xff000000},
                'native text ink palette changed')
        text_palettes.append(dict(resource=resource,transparent_foreground_index=0,
            fill_index=4,fill_ARGB=hex(colors[4]),outline_index=16,outline_ARGB=hex(colors[16])))
    write(CTX+4,struct.pack('<4H',0,0,639,479));write(CTX+16,struct.pack('<4H',0,0,639,479));write(CTX+24,struct.pack('<4H',0,0,639,479));word(CTX+72,SERVER)
    word(JOB+8,CTX);half(JOB+4,2);word(FONT+4,META);half(FONT+2,1)
    write(DESC+66,bytes([16,16,0,0,0,0,0,0]));half(CTX+676,20)
    write(syms['_ep7h_visible'],bytes.fromhex('8001de0000'))
    # Native leaf paint boundary deliberately leaves local geometry changed. The
    # axis painter must use the incoming container geometry saved before recursion.
    (tmp/'textbackend.s').write_text('''
    .text
    .global stockpaint
    stockpaint:
     mov (8,a1),a0
     mov 350,d0
     movhu d0,(12,a0)
     movhu d0,(14,a0)
     movhu d0,(24,a0)
     movhu d0,(26,a0)
     retf [],0
    .global metrics
    metrics:
     mov (a1),a0
     add 2,a0
     mov a0,(4,a1)
     mov 16,d0
     movhu d0,(8,a1)
     mov 20,d0
     movhu d0,(10,a1)
     clr d0
     mov d0,(12,a1)
     mov d0,(16,a1)
     mov d0,(20,a1)
     mov 1,d0
     retf [],0
    ''')
    subprocess.run([prefix+'as','-o',str(tmp/'textbackend.o'),str(tmp/'textbackend.s')],check=True);subprocess.run([prefix+'ld','-e','stockpaint','-Ttext','0x1970e000','-o',str(tmp/'textbackend.elf'),str(tmp/'textbackend.o')],check=True);subprocess.run([prefix+'objcopy','-O','binary',str(tmp/'textbackend.elf'),str(tmp/'textbackend.bin')],check=True)
    write(0x1970e000,(tmp/'textbackend.bin').read_bytes())
    backend_syms={l.split()[2]:int(l.split()[0],16) for l in subprocess.check_output([prefix+'nm',str(tmp/'textbackend.elf')],text=True).splitlines() if len(l.split())==3}
    # Full native paint entry uses its own prologue, no extra frame.
    write(0x60d02f93,b'\xdc'+struct.pack('<i',backend_syms['stockpaint']-0x60d02f93))
    # Catalog is a documented fixture boundary; font creation itself executes.
    write(0x60d10b88,b'\xfc\xdc'+struct.pack('<I',DESC)+bytes.fromhex('df8008'))
    write(0x1970f020,b'\xfc\xdc'+struct.pack('<I',FONT)+bytes.fromhex('de0000'));word(0x61fb25e8,0x1970f020)
    write(0x1970f030,bytes.fromhex('8001de0000'));word(0x61fb25f4,0x1970f030);word(0x61fb2614,0x1970f030)
    word(0x61fb2608,backend_syms['metrics']);word(0x61fb2604,0x1970f040);write(0x1970f040,bytes.fromhex('8001de0000'))
    # Allocation/release used by native text layout; backing content is native-owned.
    write(0x60d109d1,b'\xfc\xdc'+struct.pack('<I',MEM)+bytes.fromhex('df0004'))
    write(0x60d109db,bytes.fromhex('8001df0004'))
    # Native layer1 fill: run real pen/brush/rectangle/clip until the surface's
    # rectangle submission. Only its final raster backend is a fixture.
    word(SERVER+92,0x1970f060);write(0x1970f060,bytes.fromhex('00de0000'))
    half(JOB+4,1)
    code=b'\xdd'+struct.pack('<i',syms['ep7h_paint']-CALLER)+bytes(2)
    m.regions['caller']=Region('caller',CALLER,code,'rx')
    background=m.run(CALLER,0x1970f060,overrides=dict(a0=OWNER,a1=JOB),full_trace=True,limit=100000)
    require(background['status']=='returned','native title backdrop did not reach surface rectangle: '+str(brief(background)))
    t=background['registers'];rect=(t['d0'],t['d1'],readw(t['sp']+4),readw(t['sp']+8))
    require(rect==(432,12,96,40),'title backdrop geometry changed: '+str(rect))
    require(readw(t['sp']+12)==1,'title backdrop did not select native translucent CLUT entry1')
    require(all(pc in [r['pc'] for r in background['trace']] for pc in (0x60d0fc05,0x60d0f9c2,0x60d0c227,0x60d0ca9a)),'native backdrop functions were bypassed')
    require(m.read(CTX+54,10)==bytes(10),'backdrop changed shared drawing-context brush')
    palette_entries=[]
    for resource in (5,53):
        descriptor=struct.unpack_from('<I',data,0x60259904-BASE+4*resource)[0]
        palette=struct.unpack_from('<I',data,descriptor-BASE+4)[0]
        argb=struct.unpack_from('<I',data,palette-BASE+4)[0]
        require(argb==0x88000000,'native OSD translucent black entry changed')
        palette_entries.append(dict(resource=resource,index=1,ARGB=hex(argb)))
    done=m.resume(background['registers'],CALLER+7,full_trace=True,limit=100000)
    require(done['status']=='returned' and done['registers']['sp']==SP,'backdrop did not return with native stack')
    require(all(done['registers'][k]==m.initial[k] for k in ('d2','d3','a2','a3')),'backdrop changed callee-saved registers')
    backdrop=dict(layer=1,native_rectangle_submission=True,rectangle=list(rect),color_index=1,native_palette_entries=palette_entries)
    half(JOB+4,2)
    results=[]
    for axis,label in [(0,'Sat'),(1,'Hue'),(2,'Lum')]:
     word(syms['_ep7h_axis'],axis)
     write(CTX+12,bytes(4));write(CTX+24,struct.pack('<4H',0,0,639,479))
     code=b'\xdd'+struct.pack('<i',syms['ep7h_paint']-CALLER)+bytes(2);m.regions['caller']=Region('caller',CALLER,code,'rx')
     r=m.run(CALLER,0x60d075a7,overrides=dict(a0=OWNER,a1=JOB),full_trace=True,limit=100000)
     if r['status']!='returned':
      print(json.dumps(dict(result=brief(r),tail=r['trace'][-8:]),indent=2));raise RuntimeError('did not enter native text')
     t=r['registers'];assert m.read(t['d1'],8).decode('utf-16-le')==label+'\0'
     paintctx=t['a0'];assert m.read(paintctx+12,4)==bytes(4)
     assert m.read(paintctx+24,8)==struct.pack('<4H',0,0,639,479)
     style=m.read(t['d0'],24)
     require(struct.unpack_from('<3I',style)==(4,16,16),
             'axis text still borrows transparent fill or has wrong outline ink')
     require(any(t['pc']==0x60d0fce0 and t['d0']==source_font for t in r['trace']),
             'axis text did not reuse the native font')
     first=r['completed']
     r=m.resume(r['registers'],0x1970f040,full_trace=True,limit=100000)
     if r['status']!='returned':
      print(json.dumps(dict(result=brief(r),tail=r['trace'][-8:]),indent=2));raise RuntimeError('did not reach glyph raster boundary')
     require(any(t['pc']==0x60d0fc05 and t['d0']==4 for t in r['trace']),
             'native text layout did not apply the opaque foreground')
     require(readw(paintctx+36)==4 and readw(paintctx+652)==16 and readw(paintctx+656)==16,
             'glyph submission received transparent fill or wrong outline colors')
     total=first+r['completed']
     r=m.resume(r['registers'],CALLER+7,full_trace=True,limit=100000)
     require(r['status']=='returned' and r['registers']['sp']==SP,'axis text did not restore caller stack')
     require(all(r['registers'][k]==m.initial[k] for k in ('d2','d3','a2','a3')),'axis text changed callee-saved registers')
     results.append(dict(axis=label,native_font_id=source_font,native_text_raster_boundary_reached=True,
        native_glyph_fill_index=4,native_glyph_outline_index=16,native_glyph_shadow_index=16,
        full_paint_returned=True,style_foreground=hex(struct.unpack_from('<I',style)[0]),instructions=total+r['completed']))
    # Another category draws its own native children, with neither title layer.
    write(syms['_ep7h_visible'],bytes.fromhex('00de0000'))
    for layer in (1,2):
        half(JOB+4,layer)
        hidden=m.run(CALLER,CALLER+7,overrides=dict(a0=OWNER,a1=JOB),full_trace=True,limit=100000)
        require(hidden['status']=='returned' and hidden['registers']['sp']==SP,'hidden axis paint did not return')
        pcs=[t['pc'] for t in hidden['trace']]
        require(not any(p in pcs for p in (0x60d0fc05,0x60d0f9c2,0x60d0c227,0x60d075a7)),'another category repainted axis overlay')
    root_damage=probe_root_damage(m,syms)
    category_cleanup=probe_category_cleanup(m,syms)
    return dict(status='passed',candidate_directory=str(directory.resolve()),candidate_build_revision=build['source_revision'],
        candidate_build_report=build,cases=results,backdrop=backdrop,
        text_ink=dict(native_source_resource=hex(text_resource),native_source_style=[0,15,15],
            layer2_descriptor=hex(layer_descriptor),surface=1,palettes=text_palettes),
        root_damage=root_damage,category_cleanup=category_cleanup,hash_checks_performed=False,hardware_executed=False,
        limits=['Font catalog/acquire/configure and metrics are explicit fixtures.',
            'Actual native font setup, text layout/clipping, foreground/outline setters and layer1 rectangle submission execute; final pixel backends are fixtures.',
            'Native OSD CLUT resources5/53 provide the backdrop; layer2 palette6 and shooting palette54 provide opaque white4 and black16. Physical display blending remains unverified.',
            'Actual current-root getter, root invalidation, bounds calculation and damage-region merge execute; viewer/display queue service backends are explicit boundaries.'])

def probe_root_damage(m,syms,native_only=False):
    def write(p,data):
        for n,r in m.regions.items():
            if r.address<=p and p+len(data)<=r.address+len(r.data):
                m.mutate(n,p-r.address,data);return
        raise ValueError(hex(p))
    def word(p,v):write(p,struct.pack('<I',v))
    def u32(p):return struct.unpack('<I',m.read(p,4))[0]
    root=0x1970a000
    require(u32(0x60faaab4+168)==0x60d00ef1 and u32(0x60faaab4+276)==0x60d0184a,'native root invalidation methods changed')
    write(root,bytes(1600));word(root,0x60faaab4)
    write(root+8,struct.pack('<4H',0,0,640,480))
    word(0x61fb3138,root)
    # Execute root methods and their actual region merge. Only the completed
    # GUI command service/queue and viewer/display backends are modeled.
    for target,code in [(0x60e26ab0,'00de0000'),(0x60ea250b,'00dff024'),(0x60d0ffb4,'00dff02c'),(0x60d0ffe0,'00dff018')]:
        write(target,bytes.fromhex(code))
    target=0x60d00ef1 if native_only else syms['_ep7h_redraw']
    m.regions['caller']=Region('caller',CALLER,b'\xdd'+struct.pack('<i',target-CALLER)+bytes(2),'rx')
    result=m.run(CALLER,CALLER+7,overrides=dict(d0=1 if native_only else 0x19700300,a0=root,a1=0),full_trace=True,limit=30000)
    require(result['status']=='returned' and result['registers']['sp']==SP,'native root damage failed or changed caller stack: '+str(brief(result)))
    require(all(result['registers'][k]==m.initial[k] for k in ('d2','d3','a2','a3')),'native root damage changed callee-saved registers')
    require(struct.unpack('<H',m.read(root+1372,2))[0]==1,'axis switch did not dirty whole root')
    require(m.read(root+1392,8)==struct.pack('<4H',0,0,639,479) and u32(root+1392+24)==1,'native root damage region does not cover full bounds')
    pcs=[t['pc'] for t in result['trace']]
    require(0x60d0184a in pcs and 0x60d0f217 in pcs,'root damage methods were bypassed')
    if not native_only:
        require(0x60d3379b in pcs and 0x60ea250b in pcs and pcs.index(0x60d00ef1)<pcs.index(0x60ea250b),'axis redraw did not invalidate live root before FFE4')
        # A temporarily absent root must retain the graph request and return.
        word(0x61fb3138,0)
        null=m.run(CALLER,CALLER+7,overrides=dict(d0=0x19700300),full_trace=True,limit=30000)
        require(null['status']=='returned' and null['registers']['sp']==SP,'null-root redraw did not return')
        null_pcs=[t['pc'] for t in null['trace']]
        require(0x60d00ef1 not in null_pcs and 0x60ea250b in null_pcs,'null-root redraw entered invalidation or lost graph request')
    return dict(native_current_root_resolved=not native_only,native_whole_root_dirty_flag=True,native_full_bounds_region=[0,0,639,479],native_region_merge_executed=True,caller_registers_and_stack_preserved=True)


def probe_category_cleanup(m,syms):
    def write(p,data):
        for n,r in m.regions.items():
            if r.address<=p and p+len(data)<=r.address+len(r.data):m.mutate(n,p-r.address,data);return
        raise ValueError(hex(p))
    def word(p,v):write(p,struct.pack('<I',v))
    root=0x1970a000
    # Original screen data update and child damage are independent boundaries;
    # real native current-root/full-region methods must handle the overlay.
    write(0x60d7ae23,bytes.fromhex('80ffdf2008'))
    write(0x60cfe266,bytes.fromhex('00de0000'))
    word(0x61fb3138,root)
    for start,resume in ((0x60d7ad2a,0x60d7ad2f),(0x60d7adb4,0x60d7adb9)):
        write(root+1372,bytes(2));write(root+1392,bytes(28))
        result=m.run(start,resume,overrides=dict(a0=0x19700000),full_trace=True,limit=30000)
        require(result['status']=='returned' and result['registers']['sp']==SP,'category update did not restore native stack')
        require(result['registers']['d0']==0xffffffff,'category cleanup lost native update return')
        require(all(result['registers'][k]==m.initial[k] for k in ('d2','d3','a2','a3')),'category cleanup changed caller saved registers')
        require(m.read(root+1372,2)==b'\1\0' and m.read(root+1392,8)==struct.pack('<4H',0,0,639,479),'category change did not cover old title with full-root damage')
        pcs=[t['pc'] for t in result['trace']]
        require(0x60d3379b in pcs and 0x60d00ef1 in pcs and 0x60d0f217 in pcs,'category cleanup bypassed native root damage')
    return dict(initial_and_changed_updates_dirty_full_root=True,hidden_categories_skip_both_overlay_layers=True,native_update_return_and_saved_registers_preserved=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',default='/work/install/bin/mn10300-elf-')
    parser.add_argument('--engine',type=Path,default=Path('/work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu'))
    parser.add_argument('--output',type=Path,default=ROOT/'research/ep7/candidate-014-axis-text.json')
    args=parser.parse_args()
    result=inspect(args.candidate,args.tool_prefix,args.engine)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='candidate_build_report'},indent=2))
