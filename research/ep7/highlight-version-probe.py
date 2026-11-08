#!/usr/bin/env python3
"""Replay actual version renderer call sites; stop at native widget text setter."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from ep7_candidate_ui_owner_sim import OwnerMachine
from ep7_candidate_state_sim import CALL_SP, guarded
from ep7_candidate_startup_sim import STACK
from penf_boot_emulator import BootState, HOOK_RETURN
from penf_emulator import Region

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate',type=Path,required=True)
parser.add_argument('--engine',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
report=json.loads((args.candidate/'report.json').read_text())
m=OwnerMachine((args.candidate/report['image']).read_bytes(),args.engine)
assert m.read(0x61041f5c,16)==struct.pack('<8H',352,145,116,40,392,145,116,40)
assert m.read(0x61041f9c,16)==struct.pack('<8H',311,145,108,40,351,145,108,40)
m.configure({'_ep7_gcc_quarantine':0xdeadbeef,**{
    f'ep7_native_ui_owner_{s}_bridge':0xdeadbeef for s in ('cleanup','bulk','destructor')}})
m.regions['stack']=replace(m.regions['stack'],data=bytes(16384))
m.regions['stack_after']=replace(m.regions['stack_after'],address=STACK+16384)
m.regions['boundary_return']=Region('boundary_return',HOOK_RETURN,bytes(8),'rx')
VIEWER, RECORD, WIDGETS=0x19310000,0x19311000,0x19400000
guarded(m,'viewer',VIEWER,bytes(928))
guarded(m,'wire_record',RECORD,b'\xa5'*1004)

def word(a,v):m.write(a,struct.pack('<I',v))
def resolve(m):
    assert m.regs['a0']==VIEWER
    m.regs['a0']=WIDGETS+4*m.regs['d0']
    BootState.return_from_model(m,0)
texts=[]
def set_text(m):
    pointer=m.regs['a1'];units=[]
    for i in range(16):
        value=m.read(pointer+2*i,2)
        if value==bytes(2):break
        units.append(value)
    else:raise AssertionError('unterminated version text')
    texts.append((m.regs['a0'],b''.join(units).decode('utf-16le')))
    # Tail delegation retains each native CALL's f0/24 frame; its immediate
    # target is the veneer, so the generic direct-call stub cannot infer it.
    assert m.read(m.regs['mdr']-2,2)==bytes((0xf0,24))
    m.write(HOOK_RETURN,b'\xdf\xf0\x18'+b'\xcb'*5)
    m.regs.update(pc=HOOK_RETURN,d0=1)
m.boundaries={0x60d7ef32:resolve,0x60d4c9df:set_text}
cases=[]
for start,stop,field,widget,body in (
        (0x60d7f25c,0x60d7f278,940,26,True),
        (0x60d7f2bd,0x60d7f2d4,300,18,True),
        (0x60d7f278,0x60d7f28f,948,27,False),
        (0x60d7f2d4,0x60d7f2eb,308,19,False)):
    for original in ('1.1','','2.3'):
        m.write(RECORD+field,(original+'\0').encode('utf-16le').ljust(8,b'\0'))
        before=m.read(RECORD,1004)
        word(CALL_SP+4,RECORD)
        texts.clear()
        row=m.call_native(start,entry=start,stop=stop,values={'a3':VIEWER},preserved=())
        expected=report['displayed_body_version'] if body and original=='1.1' else original
        assert texts==[(WIDGETS+4*widget,expected)],(hex(start),texts)
        assert m.read(RECORD,1004)==before, 'original fixed-size transport record changed'
        cases.append(dict(site=hex(start),before=original,displayed=expected,
                          instructions=row['instructions']))
result=dict(status='passed',displayed_body_version=report['displayed_body_version'],
    cases=cases,native_renderer_sites_executed=True,fixed_wire_buffer_unchanged=True,
    lens_versions_unchanged=True,hash_checks_performed=False,hardware_executed=False,
    body_text_rectangles_widened=[116,108],
    limits=['Native text widget setter is the boundary; LCD layout is not exercised.'])
args.out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
