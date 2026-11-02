#!/usr/bin/env python3
"""Native E-P7 dequeued tuple -> frozen five-slot H1 -> job -> COLOR CPU probe.

The 68-byte dequeued tuple, native owners/settings/job RAM are explicit fixtures.
Unrelated acquisition conversion and typed Sat getters are serviced boundaries.
Native copy, S loop, setter/converters, H1 getter and COLOR CPU instructions run.
No ISP pixels, task scheduling, hardware or hash checks are modeled.
"""
import json,struct
from pathlib import Path
from dataclasses import replace
from ep7_candidate_startup_sim import Machine,SP,CALLER,BASE,require,candidate_inputs
from penf_emulator import Region
from ep7_sim_probe import brief

def inspect(directory,engine):
    D=Path(directory)
    image,syms,build=candidate_inputs(D,'/work/install/bin/mn10300-elf-')
    m=Machine(image,Path(engine))
    stock=(Path(__file__).resolve().parents[1]/'generated/ep7/full-input/main.decoded.bin').read_bytes()
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
    def native(start,stop,regs=None,machine=m,services=False):
        boundaries=(0x6031be74,0x6005e971,0x6030bd72) if services else ()
        r=machine.run(start,stop,overrides=regs or {},breakpoints=boundaries,full_trace=True,limit=100000)
        trace=list(r['trace']);count=r['completed']
        while r['status']=='breakpoint' and r['registers']['pc'] in boundaries:
            state=r['registers'];pc=state['pc']
            if pc==0x6030bd72:
                # The S loop has finished. H1's ACTIVE getter uses the same
                # typed service internally, so run the complete observer with
                # no serviced boundary from this native RET onward.
                r=machine.resume(state,stop,full_trace=True,limit=100000)
                trace+=r['trace'];count+=r['completed'];break
            require(pc!=0x6005e971 or state['mdr'] in (0x6030bd18,0x6030bd45,0x6030bd64),'typed boundary escaped native S acquisition')
            value=state['d1']-5 if pc==0x6005e971 and state['d0']==0xf6ea and state['d1']<11 else 0
            state=dict(state,pc=SERVICE+(0 if pc==0x6031be74 else 4),d0=value&0xffffffff)
            r=machine.resume(state,stop,breakpoints=boundaries,full_trace=True,limit=100000)
            trace+=r['trace'];count+=r['completed']
        r['trace']=trace;r['completed']=count
        if r['status']!='returned':
            print(json.dumps(dict(stage=hex(start),result=brief(r),tail=r['trace'][-4:]),indent=2))
            raise ValueError('native live slice did not complete')
        return r
    def gcc(name,d0,d1=0):
        target=syms[name];m.regions['caller']=Region('caller',CALLER,b'\xdd'+struct.pack('<i',target-CALLER)+bytes(2),'rx')
        r=native(CALLER,CALLER+7,dict(d0=d0&0xffffffff,d1=d1&0xffffffff))
        require(r['registers']['sp']==SP,'GCC helper changed stack');return r
    ACTIVE=0x624f0000;SLOTS=0xa2731098;QUEUE=0x19710000;JOB=0x19800000
    COMPACT=0x19720000;HEADER=0x19730000;INDEX=0x19740000;OUT=0x19600000;SETUP=0x19700000;SERVICE=0x19001000
    add('settings_roots',0x62253590,struct.pack('<3I',0,ACTIVE,0))
    add('active',ACTIVE,bytes(3560*4));add('active_alias',ACTIVE+0x40000000,bytes(3560*4))
    m.regions['active_alias']=replace(m.regions['active_alias'],alias_of='active')
    add('five_slots',SLOTS,bytes(5*980));add('dequeued_tuple',QUEUE,bytes(68))
    add('native_diagnostic_flags',0xa272e4a8,bytes(32))
    add('job',JOB,bytes(15512+16));add('compact',COMPACT,bytes(3096));add('header',HEADER,bytes(8));add('index',INDEX,bytes(4))
    add('output',OUT,b'\x5a'*3400);add('setup',SETUP,bytes(64))
    add('native_early_helpers',0x47000800,m.read(0x6143ca00,6144))
    m.regions['native_early_helpers']=replace(m.regions['native_early_helpers'],permissions='rx')
    m.regions['serviced_returns']=Region('serviced_returns',SERVICE,bytes.fromhex('dff03cffdfc00cffdff030'),'rx')
    H=[i%11-5 for i in range(12)];L=[5-i%11 for i in range(12)];expected=struct.pack('<24b',*(H+L));S=list(range(-5,6))+[0]
    def settings(base,h=H,l=L):
        for i in range(12):
            pair=(h[i]&15)|((l[i]&15)<<4);word(ACTIVE+4*(1769+base+i),0x48310000|((pair^255)<<8)|pair)
    settings(1655)
    def publish(index,mode=11,selector=4):
        # Execute the stock 68-byte memcpy call using its actual caller frame.
        # +29/+32 are typed9481/f6b1; HDR/Creator fields use ordinary values.
        block=bytearray(68);block[29]=mode;block[32]=selector;block[33]=4;block[34]=3;block[35]=2
        write(QUEUE,block);half(INDEX,index);word(SP+32,INDEX)
        r=native(0x6030cc39,0x6030cc56,dict(a2=QUEUE))
        slot=SLOTS+980*index
        require(m.read(slot+912,68)==bytes(block),'native queue tuple copy differs')
        require(m.read(slot+941,1)==bytes([mode]) and m.read(slot+944,1)==bytes([selector]),'real source schema differs')
        return slot,r
    def acquire(slot):
        word(SP+12,slot)
        regs=dict(a0=slot,a1=slot+676,d0=slot+912)
        baseline=m.clone();write(0x6030bb19,stock[0x6030bb19-BASE:0x6030bb1e-BASE],baseline)
        reference=native(0x6030bb19,0x6030bb1e,regs,machine=baseline,services=True)
        r=native(0x6030bb19,0x6030bb1e,regs,services=True)
        require(reference['registers']==r['registers'],'live acquisition changed caller registers/SP/MDR/PSW')
        require(m.read(slot+704,24)==baseline.read(slot+704,24),'live acquisition changed native Sat')
        require(m.read(slot+704,24)==struct.pack('<12h',*S),'native Sat loop did not execute')
        return r
    slot,copied=publish(2);sampled=acquire(slot)
    require(any(t['pc']==syms['_ep7h_snapshot'] for t in sampled['trace']),'live acquisition never read actual H1')
    # Mutating current settings and another source profile cannot replace this row.
    write(ACTIVE,bytes(3560*4));other_h=[2]*12;other_l=[-3]*12;settings(927,other_h,other_l)
    second,_=publish(1,selector=1);acquire(second)
    # A real compact schema: HDR=4, CreatorHue=3, CreatorSat=2; Sat already frozen.
    write(COMPACT+2116,bytes([4,3,2]));write(COMPACT+2119,struct.pack('<12b',*S))
    word(HEADER,JOB);word(HEADER+4,COMPACT);word(SP+8,slot);word(SP+16,JOB)
    regs=dict(a0=HEADER,d0=0,d1=0)
    baseline=m.clone();write(0x603119bb,stock[0x603119bb-BASE:0x603119c2-BASE],baseline)
    reference=native(0x603119bb,0x603119c2,regs,machine=baseline)
    converted=native(0x603119bb,0x603119c2,regs)
    require(reference['registers']==converted['registers'],'live setter changed caller registers/SP/MDR/PSW')
    require(m.read(JOB+15488,24)==expected,'live native setter lost frozen owner H/L')
    require(m.read(JOB+36+5532,1)==b'\x04' and m.read(JOB+36+5536,2)==b'\x03\x02','native HDR/Creator schema was changed')
    require(m.read(JOB+36+5538,12)==struct.pack('<12b',*S),'native setter lost Sat')
    require(any(t['pc']==0x60324071 for t in converted['trace']),'native compact converter did not execute')
    # Same captured job reaches the actual native COLOR CPU output.
    REQ=JOB+11364;OP=JOB+14576+15*56
    word(REQ,0x60355fd4);word(REQ+4,OP);word(OP,JOB);word(OP+8,REQ);write(REQ+8,bytes.fromhex('00000b00'))
    write(REQ+1816,struct.pack('<12b',*S));word(SETUP+4,REQ);word(SETUP+12,OUT)
    control=struct.unpack('<H',m.read(0x6051e9fc,2))[0]
    regs=dict(d0=control,d1=OUT,a0=0x6051de2c,a1=REQ+1816,a2=SETUP)
    baseline=m.clone();write(0x603b02d9,stock[0x603b02d9-BASE:0x603b02de-BASE],baseline)
    reference=native(0x603b02d9,0x603b02de,regs,machine=baseline)
    processed=native(0x603b02d9,0x603b02de,regs)
    require(reference['registers']==processed['registers'],'COLOR CPU observer changed native caller ABI')
    base=baseline.read(OUT,3400);output=m.read(OUT,3400);allowed=set()
    hlut=[5000,4000,3000,2000,1000,0,-1000,-2000,-3000,-4000,-5000];llut=[-200,-150,-100,-50,-25,0,25,50,100,150,200]
    for k,i in enumerate([0,2,4,6,8,10,1,3,5,7,9,11]):
        for offset,value,lut in ((706+24*k,H[i],hlut),(710+24*k,L[i],llut)):
            require(output[offset:offset+2]==(struct.pack('<h',lut[value+5]) if value else base[offset:offset+2]),'frozen live H/L missing in CPU output')
            if value:allowed.update((offset,offset+1))
    require(all(a==b or i in allowed for i,(a,b) in enumerate(zip(base,output))),'live H/L changed native Sat/control')
    # Existing skip flag retains the row and does not sample later GUI edits.
    write(slot+181,b'\x40');write(JOB+15488,bytes(24));skipped=acquire(slot)
    require(not any(t['pc']==syms['_ep7h_snapshot'] for t in skipped['trace']),'native skipped acquisition refreshed H/L')
    gcc('_ep7h_live_to_job',slot,JOB);require(m.read(JOB+15488,24)==expected,'native skip lost retained snapshot')
    # Non-COLOR native slot reuse must clear the row without reading settings.
    write(slot+181,b'\x00');publish(2,mode=9);neutral=acquire(slot)
    require(not any(t['pc']==syms['_ep7h_snapshot'] for t in neutral['trace']),'non-COLOR acquired H1')
    gcc('_ep7h_live_to_job',slot,JOB);require(m.read(JOB+15488,24)==bytes(24),'non-COLOR slot retained COLOR H/L')
    gcc('_ep7h_live_to_job',second+1,JOB);require(m.read(JOB+15488,24)==bytes(24),'unknown owner retained H/L')
    # Native setter failure returns through the same real f0/48 frame, with no
    # sidecar mutation. The successful full setter was executed above.
    write(JOB+15488,b'\x5a'*24);word(SP+8,second)
    first=m.run(0x603119bb,0x603119c2,overrides=dict(a0=HEADER,d0=0,d1=0),breakpoints=[0x603220ea],full_trace=True)
    require(first['registers']['pc']==0x603220ea,'setter wrapper missed original call')
    failed=m.resume(dict(first['registers'],pc=SERVICE+8,d0=0x9d07),0x603119c2,full_trace=True)
    require(failed['status']=='returned' and failed['registers']['sp']==SP and failed['registers']['d0']==0x9d07 and m.read(JOB+15488,24)==b'\x5a'*24,'failed setter changed H/L or return')
    return dict(status='passed',candidate_directory=str(D),hash_checks_performed=False,hardware_executed=False,
        source_snapshot_equals_current_sources=True,actual_elf_code_equals_decoded_candidate=True,
        cases=['native_dequeued_tuple68_copy_real_mode941_selector944','native_S_loop_then_actual_ACTIVE_H1_snapshot','native_acquisition_full_register_SP_MDR_PSW_preservation','two_native_owners_and_later_edit_freeze','native_full_compact_setter_real_HDR_Creator_schema_and_S','native_setter_full_register_SP_MDR_PSW_preservation','frozen_live_job_to_native_COLOR_CPU_lanes_stock_S_unchanged','native_skip_keeps_owner_row','non_COLOR_and_unknown_owner_neutral','failed_setter_retains_row_and_native_return'],
        acquisition_instructions=sampled['completed'],setter_instructions=converted['completed'],color_instructions=processed['completed'],
        limits=['68-byte dequeued tuple and native RAM owners/settings/job are explicit fixtures.','Unrelated acquisition conversion and Sat typed getter are serviced boundaries; native S loop, H1 getter, setter/converters and CPU execute.','No ISP pixels, full live scheduling, physical storage or hardware acceptance is emulated.'])

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('candidate_directory',type=Path)
    parser.add_argument('--engine',type=Path,default=Path('/work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu'));parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=inspect(args.candidate_directory,args.engine)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],cases=len(result['cases']),candidate_directory=str(args.candidate_directory),hash_checks_performed=False)))
