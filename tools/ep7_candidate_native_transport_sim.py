#!/usr/bin/env python3
"""Native E-P7 H1 capture ownership, constructor tail, COLOR CPU/upload probe.

The last unrelated capture getter is an explicit serviced boundary. Native H1
getters, both converter seams, constructor memset, COLOR builder and register
upload instructions execute; no pixels, scheduling or hardware are modeled.
"""
import json,struct
from pathlib import Path
from dataclasses import replace
from ep7_candidate_startup_sim import Machine,SP,CALLER,BASE,require
from penf_emulator import Region
from ep7_sim_probe import brief

def inspect(directory,engine):
    D=Path(directory)
    ENGINE=Path(engine)
    syms={k:int(v['address'],16) for k,v in json.loads((D/'symbols.json').read_text()).items()}
    image=(D/'EP7HSL-NONINSTALLABLE.decoded-main.bin').read_bytes();stock=(Path(__file__).resolve().parents[1]/'generated/ep7/full-input/main.decoded.bin').read_bytes()
    m=Machine(image,ENGINE)
    def add(n,p,data):m.regions[n]=Region(n,p,data,'rw',True)
    def write(p,data,machine=m):
     for n,r in machine.regions.items():
      if r.address<=p and p+len(data)<=r.address+len(r.data):
       machine.mutate(n,p-r.address,data)
       for an,ar in list(machine.regions.items()):
        if ar.alias_of==n:machine.regions[an]=replace(ar,data=machine.regions[n].data)
       return
     raise ValueError(hex(p))
    def word(p,v):write(p,struct.pack('<I',v&0xffffffff))
    def half(p,v):write(p,struct.pack('<H',v))
    def native(start,stop,overrides=None,limit=50000,machine=m):
     r=machine.run(start,stop,overrides=overrides or {},full_trace=True,limit=limit)
     if r['status']!='returned':print(json.dumps(dict(stage=hex(start),result=brief(r),tail=r['trace'][-3:]),indent=2));raise ValueError('native slice did not complete')
     return r
    def gcc(name,d0=0,d1=0):
     target=syms[name]
     m.regions['caller']=Region('caller',CALLER,b'\xdd'+struct.pack('<i',target-CALLER)+b'\0\0','rx')
     r=native(CALLER,CALLER+7,dict(d0=d0&0xffffffff,d1=d1&0xffffffff))
     require(r['registers']['sp']==SP,'GCC helper stack mismatch');return r
    ACTIVE=0x624f0000
    add('settings_roots',0x62253590,struct.pack('<3I',0,ACTIVE,0))
    add('active',ACTIVE,bytes(3560*4));add('active_alias',ACTIVE+0x40000000,bytes(3560*4));m.regions['active_alias']=replace(m.regions['active_alias'],alias_of='active')
    CAP=0xaf6037c0;JOB=0x19800000;OUT=0x19600000;SETUP=0x19700000;CLONE=0xaf900000
    add('capture',CAP,bytes(41984));add('job',JOB,b'\xa5'*(15512+16));add('output',OUT,b'\x5a'*3400);add('setup',SETUP,bytes(64));add('clone',CLONE,bytes(27332))
    add('native_early_helpers',0x47000800,m.read(0x6143ca00,6144));m.regions['native_early_helpers']=replace(m.regions['native_early_helpers'],permissions='rx')
    H=[i%11-5 for i in range(12)];L=[5-i%11 for i in range(12)];expected=struct.pack('<24b',*(H+L))
    for i in range(12):
     pair=(H[i]&15)|((L[i]&15)<<4);word(ACTIVE+4*(1769+1655+i),0x48310000|((pair^255)<<8)|pair)
    write(CAP+24053,b'\x0b');write(CAP+24083,b'\x04');write(CAP+24086,b'\x39')
    # The final unrelated hardware/property getter is a named boundary. H1 snapshot
    # below executes the actual ACTIVE registry getter and H1 decoder, not a stub.
    m.regions['last_getter_boundary']=Region('last_getter_boundary',0x19001000,bytes.fromhex('805adfc00c'),'rx')
    first=m.run(0x602a886a,0x602a8874,overrides=dict(d3=CAP,a2=CAP+24802,d0=0xef19,d1=1,a0=0),breakpoints=[0x6005e971],full_trace=True)
    require(first['registers']['pc']==0x6005e971,'sample missed original getter')
    sampled=m.resume(dict(first['registers'],pc=0x19001000),0x602a8874,full_trace=True,limit=50000)
    require(sampled['status']=='returned','sample wrapper did not return');sampled['trace']=first['trace']+sampled['trace'];sampled['completed']+=first['completed']
    require(sampled['registers']['d0']==0x5a and m.read(CAP+24803,1)==b'\x5a','last native capture byte/return changed')
    require(any(t['pc']==syms['_ep7h_snapshot'] for t in sampled['trace']),'capture hook never loaded H1')
    write(ACTIVE,bytes(3560*4)) # later edit must not change the captured image
    word(SP+20,CAP)
    converted=native(0x603e669f,0x603e66a5,dict(d3=JOB+36))
    require(m.read(JOB+15488,24)==expected,'native capture conversion did not freeze H/L')
    require(converted['registers']['sp']==SP and converted['registers']['d0']==0x39,'converter displaced native result changed')
    for reg in ('d1','d2','a1','a2','a3','mdr','psw','lir','lar'):
     require(converted['registers'][reg]==m.initial[reg],'converter changed caller '+reg)
    # Both converter variants must carry the same snapshot, independently of GUI.
    write(JOB+15488,b'\xcc'*24);word(SP+24,CAP);word(SP+20,JOB+36)
    alternate=native(0x603e91e4,0x603e91ea)
    require(m.read(JOB+15488,24)==expected and alternate['registers']['sp']==SP,'alternate converter missed H/L')
    # Native temporary clone copy also carries the owner row, before native memcpy.
    cloned=native(0x603edbce,0x47001052,dict(a0=CLONE,a1=CAP,d0=27332))
    require((cloned['registers']['a0'],cloned['registers']['a1'],cloned['registers']['d0'])==(CLONE,CAP,27332),'clone changed native memcpy arguments')
    write(CLONE,m.read(CAP,27332));word(SP+20,CLONE)
    native(0x603e669f,0x603e66a5,dict(d3=JOB+36))
    require(m.read(JOB+15488,24)==expected,'temporary clone lost H/L')
    # Native constructor: request15512 and memset40 at15472 exactly cover the new tail.
    size=native(0x603537f0,0x603537f3)
    require(size['registers']['d0']==15512,'constructor still requests stock size')
    cleared=native(0x60353906,0x60353915,dict(a3=JOB))
    require(m.read(JOB+15472,40)==bytes(40) and m.read(JOB+15512,16)==b'\xa5'*16,'constructor tail clear extent incorrect')
    # Use the captured immutable row, after the real H1 source was changed.
    gcc('_ep7h_capture_to_job',CAP,JOB+36)
    require(m.read(JOB+15488,24)==expected,'capture-frozen job changed after settings edit')
    # Execute actual native COLOR builder plus new observer. Stock-reference output
    # is rebuilt under identical S/ROM inputs, with only the original CALL restored.
    REQ=JOB+11364;OP=JOB+14576+15*56
    word(REQ,0x60355fd4);word(REQ+4,OP);word(OP,JOB);word(OP+8,REQ)
    write(REQ+8,bytes.fromhex('00000b00'))
    write(REQ+1816,struct.pack('<12b',*(list(range(-5,6))+[0])))
    word(SETUP+4,REQ);word(SETUP+12,OUT)
    control=struct.unpack('<H',m.read(0x6051e9fc,2))[0]
    regs=dict(d0=control,d1=OUT,a0=0x6051de2c,a1=REQ+1816,a2=SETUP)
    baseline=m.clone();write(0x603b02d9,stock[0x603b02d9-BASE:0x603b02de-BASE],baseline)
    base_result=native(0x603b02d9,0x603b02de,regs,machine=baseline)
    processed=native(0x603b02d9,0x603b02de,regs)
    base=baseline.read(OUT,3400);data=m.read(OUT,3400)
    bins=[0,2,4,6,8,10,1,3,5,7,9,11]
    hlut=[7000,5000,3000,2000,1000,0,-1000,-2000,-3000,-5000,-7000]
    llut=[-300,-200,-100,-50,-25,0,25,50,100,200,300]
    allowed=set()
    for k,i in enumerate(bins):
     for off,val,lut in [(706+24*k,H[i],hlut),(710+24*k,L[i],llut)]:
      require(data[off:off+2]==(struct.pack('<h',lut[val+5]) if val else base[off:off+2]),'CPU lane differs')
      if val:allowed.update((off,off+1))
    require(all(a==b or i in allowed for i,(a,b) in enumerate(zip(base,data))),'H/L overwrote stock S/control/calibration')
    require(processed['registers']['sp']==SP,'postbuilder stack mismatch')
    require(base_result['registers']==processed['registers'],'COLOR observer changed native caller registers')
    # Execute the exact native COLOR upload loop into two explicit MMIO windows.
    require(control!=0,'native COLOR control unexpectedly disabled')
    for i,destination in enumerate((0x9f001000,0x9f805000)):
     add('modeled_MMIO_'+str(i),destination,bytes(1200))
     word(SP,destination)
     native(0x603466ff,0x6034672c,dict(d1=OUT,d3=destination))
     require(m.read(destination+752,292)==data[688:980],'native COLOR upload omitted changed H/L')
    # Real selector borrowed-owner branch. It skips the ordinary COLOR call.
    # A native borrowed resource supplies its immutable prepared table at+16.
    OWNER=0x19710000
    add('borrowed_table_owner',OWNER,bytes(32));word(OWNER+16,0x6051de2c)
    word(REQ+1524,OWNER);word(SETUP+56,0);word(SETUP+60,0x10000000)
    borrowed_table=m.read(0x6051de2c,3028)
    m.regions['caller']=Region('caller',CALLER,b'\xdd'+struct.pack('<i',0x603b0252-CALLER)+bytes([0xf0,20]),'rx')
    generic_base=m.clone()
    write(0x603b027c,stock[0x603b027c-BASE:0x603b0281-BASE],generic_base)
    base_generic=native(CALLER,CALLER+7,dict(a0=SETUP),machine=generic_base)
    result_generic=native(CALLER,CALLER+7,dict(a0=SETUP))
    reference=generic_base.read(OUT,3400);generic_data=m.read(OUT,3400)
    require(any(t['pc']==0x603afb94 for t in result_generic['trace']) and
        not any(t['pc']==0x603b0068 for t in result_generic['trace']),
        'borrowed branch unexpectedly ran ordinary COLOR builder')
    for k,i in enumerate(bins):
     for off,val,lut in [(706+24*k,H[i],hlut),(710+24*k,L[i],llut)]:
      require(generic_data[off:off+2]==(struct.pack('<h',lut[val+5]) if val else reference[off:off+2]),
          'borrowed COLOR lane differs')
    require(all(a==b or i in allowed for i,(a,b) in enumerate(zip(reference,generic_data))),
        'borrowed H/L changed native Sat/control/calibration')
    require(base_generic['registers']==result_generic['registers'],
        'borrowed observer changed native caller registers')
    require(m.read(0x6051de2c,3028)==borrowed_table,'borrowed table was modified')
    for destination in (0x9f001000,0x9f805000):
     word(SP,destination)
     native(0x603466ff,0x6034672c,dict(d1=OUT,d3=destination))
     require(m.read(destination+752,292)==generic_data[688:980],
         'borrowed COLOR upload omitted changed H/L')
    # The generic packer also handles non-COLOR. That native output stays exact.
    write(REQ+8,bytes.fromhex('00000900'))
    noncolor_reference=m.clone()
    write(0x603b027c,stock[0x603b027c-BASE:0x603b0281-BASE],noncolor_reference)
    noncolor_base=native(CALLER,CALLER+7,dict(a0=SETUP),machine=noncolor_reference)
    noncolor_generic=native(CALLER,CALLER+7,dict(a0=SETUP))
    require(m.read(OUT,3400)==noncolor_reference.read(OUT,3400) and
        noncolor_generic['registers']==noncolor_base['registers'],
        'non-COLOR borrowed output or ABI changed')
    write(REQ+8,bytes.fromhex('00000b00'));word(REQ+1524,0)
    # Unknown source becomes neutral, never a previous capture's stale snapshot.
    gcc('_ep7h_capture_to_job',0xaf901234,JOB+36)
    require(m.read(JOB+15488,24)==bytes(24),'unknown owner retained stale H/L')
    # Reuse the same capture slot outside COLOR. Its previous nonzero snapshot
    # must clear without consulting H1/settings, while the stock getter result
    # and its final native byte store still complete unchanged.
    write(CAP+24053,b'\x00');write(JOB+15488,expected)
    noncolor_first=m.run(0x602a886a,0x602a8874,
        overrides=dict(d3=CAP,a2=CAP+24802,d0=0xef19,d1=1,a0=0),
        breakpoints=[0x6005e971],full_trace=True)
    require(noncolor_first['registers']['pc']==0x6005e971,'non-COLOR missed stock getter')
    noncolor=m.resume(dict(noncolor_first['registers'],pc=0x19001000),
        0x602a8874,full_trace=True,limit=50000)
    require(noncolor['status']=='returned' and noncolor['registers']['sp']==SP and
        noncolor['registers']['d0']==0x5a and m.read(CAP+24803,1)==b'\x5a',
        'non-COLOR changed the stock getter/store or return')
    require(not any(t['pc'] in (syms['_ep7h_snapshot'],syms['_ep7h_active_get'],0x6005e971)
        for t in noncolor['trace']),'non-COLOR consulted H1/settings')
    word(SP+20,CAP)
    native(0x603e669f,0x603e66a5,dict(d3=JOB+36))
    require(m.read(JOB+15488,24)==bytes(24),'non-COLOR reused an old COLOR snapshot')
    report=dict(status='passed',candidate_directory=str(D),hash_checks_performed=False,hardware_executed=False,
     cases=['native_H1_snapshot_at_capture_last_getter','both_native_S_converter_seams_frozen_values','native_temporary_clone_arguments_and_sidecar','constructor15512_and_native_memset40','actual_COLOR_builder_CPU_HL_lanes_stockS_unchanged','native_COLOR_upload_both_MMIO_windows','borrowed_selector_native_packer_and_HL_upload_stock_S_ABI_preserved','non_COLOR_borrowed_output_and_ABI_unchanged','unknown_owner_neutral','reused_non_COLOR_capture_neutral_without_H1_reads'],
     capture_instructions=sampled['completed'],color_instructions=processed['completed'],
     max_capture_stack=SP-min(t['sp'] for t in sampled['trace']),max_color_stack=SP-min(t['sp'] for t in processed['trace']),
     limits=['Settings RAM and capture/job owners are explicit fixtures.','Last unrelated property getter is modeled; H1 getter/decoder, native COLOR builders and memset execute.','Native MMIO writes target explicit RAM windows; no ISP pixels or full preview/capture scheduling is emulated.'])

    return report

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate_directory',type=Path)
    parser.add_argument('--engine',type=Path,default=Path('/work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu'))
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=inspect(args.candidate_directory,args.engine)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],cases=len(result['cases']),candidate_directory=str(args.candidate_directory),hash_checks_performed=False)))
