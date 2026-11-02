#!/usr/bin/env python3
"""Focused native same-wheel/H1/CPU probes. Explicit graphics/backend fixtures; no SHA."""
import argparse,json
from pathlib import Path
from ep7_candidate_startup_sim import candidate_inputs,require

def editor_and_storage(directory,prefix,engine):
    import sys,struct,json
    from pathlib import Path
    from dataclasses import replace
    from ep7_candidate_startup_sim import Machine,SP,CALLER,STACK,BASE,require
    from penf_emulator import Region
    from ep7_sim_probe import brief
    D=directory
    syms={k:int(v['address'],16) for k,v in json.loads((D/'symbols.json').read_text()).items()}
    m=Machine((D/'EP7HSL-NONINSTALLABLE.decoded-main.bin').read_bytes(),engine)
    def add(n,p,data):m.regions[n]=Region(n,p,data,'rw',True)
    def write(p,data):
     for n,r in m.regions.items():
      if r.address<=p and p+len(data)<=r.address+len(r.data):m.mutate(n,p-r.address,data);return
     raise ValueError(hex(p))
    def u32(p):return struct.unpack('<I',m.read(p,4))[0]
    def word(p,v):write(p,struct.pack('<I',v&0xffffffff))
    def half(p,v):write(p,struct.pack('<H',v))
    def call(target,d0=0,d1=0,a0=0,a1=0,mask=0,frame=0,stop=None,limit=30000):
     if isinstance(target,str):target=syms[target]
     m.regions['caller']=Region('caller',CALLER,b'\xdd'+struct.pack('<i',target-CALLER)+bytes([mask,frame]),'rx')
     r=m.run(CALLER,stop or CALLER+7,overrides=dict(d0=d0&0xffffffff,d1=d1&0xffffffff,a0=a0,a1=a1),full_trace=True,limit=min(limit,100000))
     total=r['completed'];trace=list(r['trace'])
     while r['status']=='instruction_limit' and total<limit:
      r=m.resume(r['registers'],stop or CALLER+7,full_trace=True,limit=min(limit-total,100000));total+=r['completed'];trace+=r['trace']
     r['trace']=trace;r['completed']=total
     if r['status']!='returned' or (not stop and r['registers']['sp']!=SP):
      print(json.dumps(dict(result=brief(r),tail=[{k:v for k,v in t.items() if k in ('pc','sp','d0','d1','a0','a1','mdr')} for t in r['trace'][-4:]]),indent=2));raise RuntimeError('native call failed')
     return r
    ACTIVE=0x624f0000;BANK=0x62510000
    add('settings_roots',0x62253590,struct.pack('<3I',BANK,ACTIVE,0))
    add('active',ACTIVE,bytes(3560*4));add('bank',BANK,bytes(32040*4))
    add('active_alias',ACTIVE+0x40000000,bytes(3560*4));m.regions['active_alias']=replace(m.regions['active_alias'],alias_of='active')
    add('bank_alias',BANK+0x40000000,bytes(32040*4));m.regions['bank_alias']=replace(m.regions['bank_alias'],alias_of='bank')
    # Refresh service boundary is modeled: no camera preview hardware is emulated.
    for p in (0x602b5e91,0x602b5eaa,0x602b5ec3,0x602b5edc):write(p,bytes.fromhex('00de0000'))
    add('ROM_bank_root',0xa2711a88,struct.pack('<I',0x60078e2c))

    rows=[]
    def check(r,msg):require(r,msg)
    def signed(v):return v if v<0x80000000 else v-0x100000000
    # Setters/getters execute real ACTIVE read, typed write and shared CPU0 aliases.
    for profile,base in enumerate((927,939,951,1655)):
     for axis,val in ((1,3-profile),(2,profile-3)):
      word(syms['_ep7h_axis'],axis)
      for i in range(12):
       v=max(-5,min(5,val+(i%3)-1))
       r=call('_ep7h_set',base+i,v);check(r['registers']['d0']==1,'H/L store refused')
       r=call('_ep7h_value',base+i,axis);check(signed(r['registers']['d0'])==v,'H/L readback differs')
     check(m.read(ACTIVE+4*base,48)==bytes(48),'H/L changed native S part0')
    rows.append('all48sectors_both_axes_native_typed_write_and_readback')
    expected=m.read(ACTIVE,3538*4)
    # Execute actual native ACTIVE -> bank2 -> ACTIVE, no storage/API success stub.
    call(0x602cc03a,2,mask=0xc0,frame=12,limit=800000)
    check(m.read(BANK+2*3538*4,3538*4)==expected,'native bank save differs')
    write(ACTIVE,bytes(3538*4));write(ACTIVE+0x40000000,bytes(3538*4))
    call(0x602cbffe,2,mask=0xc0,frame=12,limit=800000)
    check(m.read(ACTIVE,3538*4)==expected,'native bank recall differs')
    rows.append('native3538cell_bank_save_and_recall')
    # The initialized GUI objects below are explicit fixtures with original layout.
    add('gui_static',0x61f98540,m.read(0x60230800,0x2e350))
    add('ui_objects',0x19700000,bytes(0x10000))
    M=0x19700000;C=M+0x100;P=M+0x200;V=M+0x300;SEL=M+0x500;CT=M+0x600;CUR=M+0x700
    write(M,bytes([4,29]));word(0x61fc436c,C);word(C,P);word(C+4,V)
    word(P,0x6118957c);word(P+76,SEL);word(P+80,CT);word(V,0x61189ba8);word(V+384,P)
    half(SEL+86,1);word(CT,0x61187534);half(CT+120,13);word(CT+124,CUR);half(CUR+90,7)
    word(0x61fc1ba8,0);word(0x61fc1bac,0)
    # Native viewport backend/frame boundary only, original bridge instructions run.
    write(0x60e26ab0,bytes.fromhex('00de0000'))
    write(0x60ea250b,bytes.fromhex('00dff024'))
    write(0x602afa81,bytes.fromhex('00df0004'))
    for pr,base in enumerate((927,939,951,1655)):
     half(CT+100,0x13b3+pr if pr<3 else 0x140c)
     for i in range(12):
      ch=M+0x1000+i*0x100;eligible=ch+144;values=ch+176
      word(CT+128+4*i,ch);half(ch+84,base+i);half(ch+88,11);half(ch+90,5)
      word(ch+96,eligible);word(ch+100,values)
      write(values,struct.pack('<11i',*range(5,-6,-1)))
     word(syms['_ep7h_axis'],0)
     for wanted in (2,1,0):
      r=call(0x60d11448,0x9016,a0=M)
      check(r['registers']['d0']==0 and u32(syms['_ep7h_axis'])==wanted,'Delete dispatch did not cycle')
      check(struct.unpack('<H',m.read(CUR+90,2))[0]==7,'axis switch moved cursor')
      for i in range(12):
       ch=u32(CT+128+4*i);idx=struct.unpack('<H',m.read(ch+90,2))[0]
       pair=u32(ACTIVE+4*(1769+base+i))&255
       n=(pair>>(4 if wanted==2 else 0))&15;v=n if n<8 else n-16
       check(idx==(5-v if wanted else 5),'cached child index remained on prior axis')
      req=[t for t in r['trace'] if t['pc']==0x60ea250b]
      check(len(req)==1 and req[0]['d0']==65508,'axis switch missed native graph request')
    rows.append('actual_native_FSM_Delete_S_L_H_S_all4profiles_shared_cursor_and_graph_request')
    # Other categories, held gestures, unrelated properties stay original/decline.
    half(SEL+86,3);r=call('_ep7h_cycle',M);check(r['registers']['d0']==0,'curve consumed Delete');half(SEL+86,1)
    word(CT+16,1);r=call('_ep7h_cycle',M);check(r['registers']['d0']==0,'held gesture switched');word(CT+16,0)
    # CALLS-style get/default ABI and inner GUI commit hook, real storage mutation.
    OUT=M+0x8000
    word(syms['_ep7h_axis'],1)
    r=call('ep7h_get_bridge',1655,a1=OUT);check(signed(u32(OUT))==-1,'native service H getter')
    r=call('ep7h_default_bridge',1655,a1=OUT);check(u32(OUT)==0,'native reset default')
    r=call(0x607fa355,1655,-4,a0=P,stop=0x608274b3)
    check((r['registers']['d2'],signed(r['registers']['d3']),r['registers']['a2'])==(1655,-4,P),'native manager finish lost inputs')
    check((u32(ACTIVE+4*(1769+1655))&15)==12,'native GUI edit did not save H')
    # Graph read must use current axis rather than native S.
    r=call(0x609330f9,1655,stop=0x60933100)
    check(signed(r['registers']['d0'])==-4,'graph still reads S')
    rows.append('native_GUI_property_get_default_commit_finish_and_wheel_read')
    return dict(status='passed',cases=rows,hash_checks_performed=False,hardware_executed=False,
     limits=['Native settings RAM and GUI objects are explicit fixtures.','Profile preview callbacks and display backend are modeled boundaries.','Bank save/recall executes native code; physical NVM writes and power-cycle acceptance are not emulated.'])


def paint_and_capture(directory,prefix,engine):
    import sys,struct,json
    from pathlib import Path
    from dataclasses import replace
    from ep7_candidate_startup_sim import Machine,SP,CALLER,STACK,BASE,require
    from penf_emulator import Region
    from ep7_sim_probe import brief
    D=directory
    syms={k:int(v['address'],16) for k,v in json.loads((D/'symbols.json').read_text()).items()}
    m=Machine((D/'EP7HSL-NONINSTALLABLE.decoded-main.bin').read_bytes(),engine)
    def add(n,p,data):m.regions[n]=Region(n,p,data,'rw',True)
    def write(p,data):
     for n,r in m.regions.items():
      if r.address<=p and p+len(data)<=r.address+len(r.data):m.mutate(n,p-r.address,data);return
     raise ValueError(hex(p))
    def u32(p):return struct.unpack('<I',m.read(p,4))[0]
    def word(p,v):write(p,struct.pack('<I',v&0xffffffff))
    def half(p,v):write(p,struct.pack('<H',v))
    def call(target,d0=0,d1=0,a0=0,a1=0,mask=0,frame=0,stop=None,limit=30000):
     if isinstance(target,str):target=syms[target]
     m.regions['caller']=Region('caller',CALLER,b'\xdd'+struct.pack('<i',target-CALLER)+bytes([mask,frame]),'rx')
     r=m.run(CALLER,stop or CALLER+7,overrides=dict(d0=d0&0xffffffff,d1=d1&0xffffffff,a0=a0,a1=a1),full_trace=True,limit=min(limit,100000))
     total=r['completed'];trace=list(r['trace'])
     while r['status']=='instruction_limit' and total<limit:
      r=m.resume(r['registers'],stop or CALLER+7,full_trace=True,limit=min(limit-total,100000));total+=r['completed'];trace+=r['trace']
     r['trace']=trace;r['completed']=total
     if r['status']!='returned' or (not stop and r['registers']['sp']!=SP):
      print(json.dumps(dict(result=brief(r),tail=[{k:v for k,v in t.items() if k in ('pc','sp','d0','d1','a0','a1','mdr')} for t in r['trace'][-4:]]),indent=2));raise RuntimeError('native call failed')
     return r
    ACTIVE=0x624f0000;BANK=0x62510000
    add('settings_roots',0x62253590,struct.pack('<3I',BANK,ACTIVE,0))
    add('active',ACTIVE,bytes(3560*4));add('bank',BANK,bytes(32040*4))
    add('active_alias',ACTIVE+0x40000000,bytes(3560*4));m.regions['active_alias']=replace(m.regions['active_alias'],alias_of='active')
    add('bank_alias',BANK+0x40000000,bytes(32040*4));m.regions['bank_alias']=replace(m.regions['bank_alias'],alias_of='bank')
    # Refresh service boundary is modeled: no camera preview hardware is emulated.
    for p in (0x602b5e91,0x602b5eaa,0x602b5ec3,0x602b5edc):write(p,bytes.fromhex('00de0000'))
    add('ROM_bank_root',0xa2711a88,struct.pack('<I',0x60078e2c))

    add('gui_static',0x61f98540,m.read(0x60230800,0x2e350))
    add('ui_objects',0x19700000,bytes(0x10000))
    M=0x19700000;C=M+0x100;P=M+0x200;V=M+0x300;SEL=M+0x500;CT=M+0x600;CUR=M+0x700
    write(M,bytes([4,29]));word(0x61fc436c,C);word(C,P);word(C+4,V)
    word(P,0x6118957c);word(P+76,SEL);word(P+80,CT);word(V,0x61189ba8);word(V+384,P)
    half(SEL+86,1);word(CT,0x61187534);half(CT+120,13);word(CT+124,CUR);half(CUR+90,7)
    word(0x61fc1ba8,0);word(0x61fc1bac,0)
    # Native viewport backend/frame boundary only, original bridge instructions run.
    write(0x60e26ab0,bytes.fromhex('00de0000'))
    write(0x60ea250b,bytes.fromhex('00dff024'))
    write(0x602afa81,bytes.fromhex('00df0004'))

    require(m.read(0x60d0f7e6,3)==bytes.fromhex('24ac02') and
            m.read(0x60d0f7f7,3)==bytes.fromhex('2dac02'), 'native drawing context size changed')
    # Paint bounds, layers, native frames and cloned drawing context.
    OWNER=M+0x9000;HEAD=M+0x9600;DRAW=M+0xa000;JOBP=M+0xa400;FONT=M+0xa500
    word(OWNER+872,HEAD);half(HEAD+8,456);word(JOBP+8,DRAW)
    write(DRAW,bytes((i*13)&255 for i in range(684)));before=m.read(DRAW,684)
    for target,code in [(0x60d02f93,'00de0000'),(0x60d0fc05,'00dff010'),(0x60d0f9c2,'00dfe010'),(0x60d0c227,'00dfb034'),(0x60d10708,'00df0004'),(0x60d075a7,'00dff0fc')]:write(target,bytes.fromhex(code))
    write(0x60d0fce0,b'\xfc\xdc'+struct.pack('<I',FONT)+bytes.fromhex('df2008'))
    paint=[]
    for axis in (0,2,1):
     word(syms['_ep7h_axis'],axis)
     for layer in (1,2,3):
      half(JOBP+4,layer);r=call('ep7h_paint',a0=OWNER,a1=JOBP)
      require(m.read(DRAW,684)==before,'paint mutated shared drawing state')
      tx=[t for t in r['trace'] if t['pc']==0x60d075a7]
      texts=[]
      for t in tx:
       raw=b'';ptr=t['d1']
       while m.read(ptr,2)!=bytes(2):raw+=m.read(ptr,2);ptr+=2
       texts.append(raw.decode('utf-16-le'))
      require(texts==([['Saturation','Hue','Lightness'][axis],'S/L/H @A047@'] if layer==2 else []),'wrong axis text/layer')
      paint.append(dict(axis=axis,layer=layer,texts=texts,depth=SP-min(t['sp'] for t in r['trace'])))
    # Native initial/changed adapters must preserve the enclosing owner's registers.
    write(0x60d7ae23,bytes.fromhex('80ffdf2008'))
    write(0x60cfe266,bytes.fromhex('00de0000'))
    for site,resume in [(0x60d7ad2a,0x60d7ad2f),(0x60d7adb4,0x60d7adb9)]:
     r=m.run(site,resume,overrides=dict(a0=OWNER),full_trace=True)
     require(r['status']=='returned' and r['registers']['sp']==SP and r['registers']['d0']==0xffffffff,'owner update native frame/result')
     require(all(r['registers'][k]==m.initial[k] for k in ('d2','d3','a2','a3')),'owner update clobbered saved registers')
    # Actual bootstrap semaphore and capture CPU observer; no lock stubs.
    from ep7_candidate_static_kernel_sim import inspect
    from ep7_candidate_state_sim import gcc_call,job_fixture,JOB,EXTENT,SNAPSHOT,TOKEN,OUTPUT,OUTPUT_BYTES,SETUP
    settings=bytearray(3560*4)
    expected_values=[-4,2,0,1,-1,3,4,-2,5,-3,0,1]+[2,-1,3,0,1,-2,4,-3,0,2,-4,5]
    for i in range(12):
     pair=(expected_values[i]&15)|((expected_values[12+i]&15)<<4)
     struct.pack_into('<I',settings,4*(1769+1655+i),0x48310000|((pair^255)<<8)|pair)
    m,syms,build,ctx=inspect(D,prefix,m.engine,context_only=True)
    add('hsl_active',ACTIVE,bytes(settings));add('hsl_roots',0x62253590,struct.pack('<3I',BANK,ACTIVE,0))
    add('snapshot',SNAPSHOT,bytes(25));add('token',TOKEN,bytes(8));add('output',OUTPUT,b'\x5a'*OUTPUT_BYTES)
    job=bytearray(job_fixture())
    add('job',JOB,bytes(job));add('setup',SETUP,struct.pack('<4I',0,JOB+11364,0,OUTPUT))
    core=ctx['core']
    gcc_call(m,syms,'_ep7h_load_profile',[core,4],wanted=1)
    gcc_call(m,syms,'_ep7p_capture',[core,11,4,SNAPSHOT],wanted=1)
    frozen=m.read(SNAPSHOT,25)
    require(frozen==bytes([3]+[v&255 for v in expected_values]),'persisted H/L not captured')
    write(ACTIVE,bytes(len(settings)))
    gcc_call(m,syms,'_ep7h_load_profile',[core,4],wanted=1)
    require(m.read(SNAPSHOT,25)==frozen,'later settings changed frozen capture')
    gcc_call(m,syms,'_ep7p_register_job',[core,JOB,EXTENT,SNAPSHOT,TOKEN],wanted=1)

    gcc_call(m,syms,'_ep7_gcc_postbuilder_observer',[SETUP])
    expected=bytearray(b'\x5a'*OUTPUT_BYTES)
    hue=[7000,6000,5000,4000,3000,2000,1000,0,-1000,-2000,-3000,-4000,-5000,-6000,-7000]
    lum=[-300,-250,-200,-150,-100,-50,-25,0,25,50,100,150,200,250,300]
    for i,band in enumerate([0,2,4,6,8,10,1,3,5,7,9,11]):
     for offset,table,value in [(706,hue,expected_values[band]),(710,lum,expected_values[12+band])]:
      if value:struct.pack_into('<h',expected,offset+24*i,table[value+7])
    require(m.read(OUTPUT,OUTPUT_BYTES)==expected,'stored H/L failed actual CPU coefficient observer')
    return dict(status='passed',hash_checks_performed=False,paint=paint,
     native_bootstrap_and_private_semaphore=True,persistent_profile_loaded_and_frozen=True,
     frozen_capture_survives_later_edit=True,actual_CPU_coefficient_writes_equal_expected=True,
     hardware_executed=False,limits=['Paint backend and native font/text APIs are explicit frame/argument stubs; pixels are not rendered.','Actual native semaphore, H1 decoder, core capture and CPU observer execute; image buffers and task ownership are fixtures.'])


def inspect(directory,prefix,engine):
    _,_,build=candidate_inputs(directory,prefix)
    editor=editor_and_storage(directory,prefix,engine)
    paint=paint_and_capture(directory,prefix,engine)
    return dict(status='passed',scope=__doc__,candidate_directory=str(directory.resolve()),
        candidate_build_revision=build['source_revision'],candidate_build_report=build,
        editor_and_storage=editor,paint_and_capture=paint,
        hash_checks_performed=False,hardware_executed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--tool-prefix',required=True)
    p.add_argument('--engine',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(inspect(a.candidate,a.tool_prefix,a.engine),indent=2))
