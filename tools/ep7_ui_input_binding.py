#!/usr/bin/env python3
"""Current-stock GUI preprocessing, five full-count samples and parent event provenance; no SHA."""
import argparse,json,struct
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE
from ep7_ui_event_mapping import WITNESSES as EXISTING
WINDOWS=[(0x60cfd4d9,0x60cfd55f),(0x60e9fa88,0x60e9fa8e),(0x60e9fb40,0x60e9fb9f),
    (0x60e9fda5,0x60e9fdaa),(0x60ea0037,0x60ea012a),(0x60ea0d39,0x60ea0ea2),
    (0x60ea3b2c,0x60ea3b35),(0x60d11448,0x60d11455),(0x60d114b2,0x60d114e3),
    (0x60dd5250,0x60dd5270),(0x60dd5445,0x60dd5489),(0x60dd55bb,0x60dd55dd),
    (0x60e5da87,0x60e5da9f),(0x60e4d032,0x60e4d039),(0x60e4d0ee,0x60e4d125)]
W={a:v for a,v in EXISTING.items() if
    0x60dd5445<=a<0x60dd5489 or 0x60ea3b2c<=a<0x60ea3b35 or
    a in [0x60ea0d39,0x60ea0d53,0x60ea0d55,0x60ea0d57,0x60ea0d6c,0x60ea0d6f,0x60ea0d70,
        0x60ea0d75,0x60ea0d76,0x60ea0d94,0x60ea0d9a,0x60ea0d9f,
        0x60ea0db4,0x60ea0dce,0x60ea0dd0,0x60ea0dd2,0x60ea0de7,0x60ea0dea,0x60ea0deb,
        0x60ea0df0,0x60ea0df1,0x60ea0e0f,0x60ea0e15,0x60ea0e1a,
        0x60ea0e2f,0x60ea0e49,0x60ea0e4b,0x60ea0e4d,0x60ea0e62,0x60ea0e65,0x60ea0e66,
        0x60ea0e6b,0x60ea0e6c,0x60ea0e82,0x60ea0e88,0x60ea0e8d]}
W.update({
    0x60cfd4d9:('mov','sp,a3'),0x60cfd4da:('add','396,a3'),0x60cfd4e4:('mov','a3,a0'),
    0x60cfd4e7:('call','0x60d10133,[d2,d3,a2,a3],20'),
    0x60cfd539:('mov','a3,a0'),0x60cfd53a:('call','0x60e9fa88,[d2,a2,a3],224'),
    0x60cfd541:('exthu','d0'),0x60cfd542:('cmp','1,d0'),0x60cfd544:('beq','0x60cfd4e4'),
    0x60cfd546:('mov','(396,sp),d0'),0x60cfd54a:('mov','(408,sp),a1'),
    0x60cfd54e:('mov','(412,sp),d1'),0x60cfd552:('mov','(0x61fb2564),a0'),
    0x60cfd558:('call','0x60d1144d,[d2,d3,a2,a3],48'),
    0x60e9fa88:('mov','a0,a3'),0x60e9fa8c:('mov','(a3),d1'),
    0x60e9fb40:('add','-36868,d1'),0x60e9fb47:('and','127,d0'),0x60e9fb4a:('asl','3,d0'),
    0x60e9fb4d:('mov','1629407584,a1'),0x60e9fb6f:('mov','(4,a0),a0'),0x60e9fb72:('jmp','(a0)'),
    0x60e9fb74:('mov','a3,a0'),0x60e9fb75:('call','0x60ea0037,[d2,d3,a2,a3],36'),
    0x60e9fb7d:('mov','a3,a0'),0x60e9fb7e:('call','0x60ea00c0,[d2,a2,a3],28'),
    0x60e9fb86:('mov','a3,a0'),0x60e9fb87:('call','0x60ea0d39,[d2,d3,a2,a3],32'),
    0x60e9fb8f:('mov','a3,a0'),0x60e9fb90:('call','0x60ea0db4,[d2,d3,a2,a3],32'),
    0x60e9fb98:('mov','a3,a0'),0x60e9fb99:('call','0x60ea0e2f,[d2,d3,a2,a3],32'),
    0x60e9fda5:('mov','d2,d0'),0x60e9fda6:('exthu','d0'),0x60e9fda7:('ret','[d2,a2,a3],224'),
    0x60ea0037:('mov','a0,a3'),0x60ea0051:('mov','1,d0'),0x60ea0053:('calls','(a2)'),
    0x60ea0055:('mov','d0,d2'),0x60ea006c:('movhu','(16,sp),d0'),0x60ea006f:('exth','d0'),
    0x60ea0070:('call','0x60ea3b2c,[],0'),0x60ea0075:('cmp','d3,d2'),0x60ea0076:('bne','0x60ea00b0'),
    0x60ea007f:('mov','2,d0'),0x60ea0084:('cmp','d0,d1'),0x60ea0085:('bge','0x60ea0094'),
    0x60ea0087:('mov','1,d0'),0x60ea008c:('cmp','d3,d1'),0x60ea008d:('bgt','0x60ea0094'),
    0x60ea008f:('mov','-1,d0'),0x60ea00ab:('mov','d0,(12,a3)'),
    0x60ea00c0:('mov','a0,a3'),0x60ea00da:('clr','d0'),0x60ea00db:('calls','(a2)'),
    0x60ea00dd:('mov','d0,a2'),0x60ea00f3:('movhu','(12,sp),d0'),0x60ea00f6:('exth','d0'),
    0x60ea00f7:('call','0x60ea3b2c,[],0'),0x60ea00fc:('cmp','0,a2'),0x60ea00fe:('bne','0x60ea011a'),
    0x60ea0103:('mov','1,d1'),0x60ea0109:('cmp','d2,d0'),0x60ea010a:('bgt','0x60ea0111'),
    0x60ea010c:('mov','-1,d0'),0x60ea0115:('mov','d0,(12,a3)'),
    0x60d11448:('movm','[d2,d3,a2,a3],(sp)'),0x60d1144a:('add','-32,sp'),
    0x60d1144d:('mov','d1,(20,sp)'),0x60d1144f:('mov','a1,(24,sp)'),
    0x60d11451:('mov','d0,(16,sp)'),0x60d11453:('mov','a0,(8,sp)'),
    0x60d114b2:('mov','(8,sp),a3'),0x60d114b4:('add','8,a3'),0x60d114b6:('movhu','d0,(a3)'),
    0x60d114bc:('mov','(12,a0),a0'),0x60d114c1:('mov','(d0,a0),a2'),
    0x60d114ce:('mov','(16,sp),d0'),0x60d114d0:('mov','(24,sp),a1'),
    0x60d114d2:('mov','(20,sp),d1'),0x60d114d4:('calls','(a2)'),
    0x60d114df:('mov','-1,d1'),0x60d114e1:('movhu','d1,(a3)'),
    0x60dd525a:('mov','d3,(24,a3)'),0x60dd525d:('mov','d1,(28,a3)'),
    0x60dd5260:('mov','(0x61fc3808),a0'),0x60dd5268:('beq','0x60dd5270'),
    0x60dd526a:('mov','200,d0'),0x60dd526d:('movhu','d0,(36,a3)'),
    0x60dd55bb:('mov','(0x61fc1bac),a0'),0x60dd55c1:('cmp','0,a0'),0x60dd55c3:('bne','0x60dd55d0'),
    0x60dd55c9:('mov','(68,a1),a1'),0x60dd55cc:('calls','(a1)'),
    0x60dd55d0:('mov','36884,d0'),0x60dd55d6:('call','0x60d1050a,[d2,d3,a2],16'),
    0x60e5da90:('mov','(0x61fc436c),a0'),0x60e5da96:('mov','a1,d1'),
    0x60e5da98:('call','0x60e4d032,[d2,d3,a2,a3],60'),
    0x60e4d032:('mov','d1,(8,sp)'),0x60e4d034:('mov','a0,a3'),0x60e4d035:('mov','d0,d2'),
    0x60e4d0f5:('mov','(a3),d0'),0x60e4d0f6:('mov','(8,sp),d1'),
    0x60e4d0f8:('mov','d0,a0'),0x60e4d0fa:('mov','d2,d0'),0x60e4d0fd:('mov','(a1),a1'),
    0x60e4d0ff:('calls','(a1)'),0x60e4d101:('cmp','0,d0'),0x60e4d115:('cmp','1,d0'),
    0x60e4d11d:('mov','(a3),a0'),0x60e4d123:('calls','(a1)')})
CHECKS=[(0x6118957c,'<I',(0x60dd5250,)),(0x6114041c,'<II',(0x11,0x60dd55bb)),
    (0x6114047c,'<4I',(0x2e,0x60dd5467,0x2f,0x60dd5445)),
    (0x611a2c08+4*137,'<I',(0x60e5da87,))]
def tables(data):
    raw=struct.unpack_from('<256I',data,1629407584-BASE)
    for event,target in [(0x9031,0x60e9fb74),(0x9032,0x60e9fb7d),(0x904f,0x60e9fb86),(0x9050,0x60e9fb98),(0x9051,0x60e9fb8f)]:
        key=event-0x9004;slot=key&127
        for _ in range(128):
            k,address=raw[2*slot:2*slot+2]
            if k==key:
                if address!=target:raise ValueError('preprocessor branch changed')
                break
            if k==0:raise ValueError('preprocessor key missing')
            slot=(slot+1)&127
        else:raise ValueError('preprocessor hash cycle')
    events=dict(struct.unpack_from('<II',data,0x611a2888+i*8-BASE) for i in range(112))
    for event in (0x9031,0x9032,0x9014):
        if event not in events or events[event]>=112 or data[0x611a2e30+29*events[event]+28-BASE]!=137:
            raise ValueError('GUI041d handler137 route changed')
def inspect(stock,objdump):
    e=inspect_windows(stock,objdump,WINDOWS,W,CHECKS,observe_data=tables)
    sites=[0x60ea0070,0x60ea00f7,0x60ea0d70,0x60ea0deb,0x60ea0e66]
    return dict(scope=__doc__,input_structure=e['input_structure'],objdump_version=e['objdump_version'],
        checked_instructions=e['checked_instructions'],checked_fixed_data_rows=len(CHECKS),
        checked_preprocessor_hash_routes=5,checked_gui041d_event_routes=3,
        preprocess_call='0x60cfd53a',preprocess_frame=224,engine_call='0x60cfd558',engine_frame=48,
        source_packet_offset_in_gui_loop=396,source_packet_bytes=28,
        sample_sites=[hex(a) for a in sites],sample_all_call_frames=0,
        sample_status_registers=['d2','a2','d2','d2','d2'],
        sample_bridge_start_interval=[hex(max(sites)-32768),hex(min(sites)+32767)],
        parent_caller_return='0x60e4d101',parent_caller_a3_is_container=True,
        input_modal_gate='0x61fc1bac',wheel_and_info_require_zero_gate=True,
        info_drop_queued_event='0x60d1050a',info_drop_native_frame=16,
        native_handler_137=True,private_delta_copied_before_global_can_change=True,
        native_task_exclusion_and_installation_proven=False,physical_wheel_identity_proven=False,
        installed=False,target_executed=False,firmware_built=False,hash_checks_performed=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',type=Path,required=True)
    p.add_argument('--objdump',type=Path,required=True);a=p.parse_args()
    print(json.dumps(inspect(a.stock,a.objdump),indent=2))
