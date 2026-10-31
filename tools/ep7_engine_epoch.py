#!/usr/bin/env python3
"""Engine workrecord order and reset epochs; exact bounded static checks, no SHA or CPU emulation."""
import argparse,json,re,struct
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE

WINDOWS=[(0x6029acd8,0x6029ae52),(0x6029aeb2,0x6029af38),(0x6029afce,0x6029b354),(0x6029b354,0x6029b3e1),
         (0x602a2731,0x602a27e9),(0x602a2ec7,0x602a2edd),(0x602a302b,0x602a3052),
         (0x6029e93e,0x6029e956),(0x602a2faf,0x602a2fbf)]
W={
    0x6029acd8:('mov','1646514400,a0'),0x6029acde:('mov','a0,(0x6223d0dc)'),
    0x6029ace8:('mov','1646514420,a1'),0x6029acee:('mov','4,d0'),0x6029acf0:('mov','d0,d1'),
    0x6029acf1:('call','0x6020b949,[d2],4'),0x6029acf8:('clr','d2'),0x6029acf9:('clr','d3'),
    0x6029acfa:('extbu','d2'),0x6029acfb:('udfu01','12,d2'),0x6029acfe:('add','1646514436,d2'),
    0x6029ad04:('mov','d2,a0'),0x6029ad06:('call','0x6029b354,[],0'),
    0x6029ad0b:('mov','(0x6223d0dc),a0'),0x6029ad11:('mov','d2,d0'),
    0x6029ad12:('call','0x6020b98b,[],8'),0x6029ad19:('inc','d3'),0x6029ad1c:('cmp','4,d3'),
    0x6029ad1e:('blt','0x6029acfa'),0x6029ad20:('ret','[d2,d3],16'),
    0x6029ad23:('mov','a0,a2'),0x6029ad24:('mov','1646514484,a0'),0x6029ad2a:('mov','-17,d1'),
    0x6029ad2d:('mov','(a1),d0'),0x6029ad2e:('inc4','a1'),0x6029ad2f:('mov','d0,(a0)'),
    0x6029ad30:('inc4','a0'),0x6029ad31:('inc','d1'),0x6029ad32:('lne',''),
    0x6029ad34:('mov','1,d0'),0x6029ad36:('movhu','d0,(0x6223d0d0)'),0x6029ad3c:('clr','d0'),
    0x6029ad3d:('movhu','d0,(0x6223d0d2)'),0x6029ad43:('movhu','d0,(0x6223d0d4)'),
    0x6029ad49:('mov','d0,(0x6223d0d8)'),0x6029ad4f:('mov','1646514392,a1'),
    0x6029ad55:('call','0x6029ada9,[d2,a2,a3],12'),
    0x6029ada9:('add','68,a0'),0x6029adab:('mov','76,d2'),0x6029adad:('add','a0,d2'),
    0x6029adb2:('btst','1,d0'),0x6029adb8:('or','1,d0'),
    0x6029adbc:('mov','60,a2'),0x6029adbe:('add','a0,a2'),
    0x6029adc1:('btst','1,d0'),0x6029adc7:('or','2,d0'),
    0x6029adcb:('mov','80,a3'),0x6029adcd:('add','a0,a3'),
    0x6029add0:('btst','1,d0'),0x6029add6:('or','4,d0'),
    0x6029adda:('mov','(44,a0),d0'),0x6029addd:('mov','524288,d1'),0x6029ade3:('and','d1,d0'),
    0x6029ade8:('or','8,d0'),0x6029adec:('mov','d2,a0'),0x6029adef:('btst','2,d0'),
    0x6029adf5:('or','65536,d0'),0x6029adfd:('btst','2,d0'),0x6029ae03:('or','131072,d0'),
    0x6029ae0b:('btst','2,d0'),0x6029ae11:('or','262144,d0'),
    0x6029ae19:('btst','32,d0'),0x6029ae1f:('or','d1,d0'),
    0x6029ae23:('btst','64,d0'),0x6029ae29:('or','1048576,d0'),
    0x6029ae40:('movhu','d0,(0x6223d0d2)'),
    0x6029aeb2:('mov','(0x6223d134),a2'),0x6029aeb8:('calls','(a2)'),
    0x6029aeba:('mov','(4,sp),a1'),0x6029aebc:('mov','a0,(a1)'),
    0x6029aec1:('mov','(4,a0),d2'),0x6029aec4:('mov','(0x6223d0d8),d1'),
    0x6029aeca:('and','65535,d2'),0x6029aece:('and','65535,d1'),0x6029aed3:('bne','0x6029aef5'),
    0x6029aed5:('mov','(a0),d0'),0x6029aed8:('beq','0x6029aef0'),
    0x6029aedb:('movhu','d0,(0x6223d0d0)'),0x6029aee7:('call','0x6020b9ff,[],24'),
    0x6029aef0:('call','0x6029b354,[],0'),
    0x6029aef8:('mov','a1,a3'),0x6029aef9:('mov','(4,a3),d3'),0x6029aefc:('mov','-65536,d2'),
    0x6029af02:('mov','(0x6223d0d8),d1'),0x6029af08:('and','d2,d3'),0x6029af0a:('and','d2,d1'),
    0x6029af0c:('cmp','d1,d3'),0x6029af0d:('bne','0x6029af35'),
    0x6029af0f:('mov','(0x6223d138),d1'),0x6029af17:('beq','0x6029af20'),
    0x6029af1b:('mov','(a3),a1'),0x6029af1e:('calls','(a2)'),
    0x6029af21:('call','0x6029b354,[],0'),0x6029af2c:('mov','a3,d0'),
    0x6029af2e:('call','0x6020b98b,[],8'),
    0x6029b354:('clr','d0'),0x6029b355:('mov','d0,(a0)'),
    0x6029b356:('mov','d0,(4,a0)'),0x6029b359:('mov','d0,(8,a0)'),0x6029b35c:('retf','[],0'),
    0x6029b35f:('movhu','(0x6223d0d0),d0'),0x6029b367:('bne','0x6029b384'),
    0x6029b369:('mov','(4,a0),d0'),0x6029b36c:('btst','65535,d0'),0x6029b370:('bne','0x6029b384'),
    0x6029b372:('movhu','(0x6223d0d2),d0'),0x6029b37a:('beq','0x6029b384'),
    0x6029b37c:('mov','1,d0'),0x6029b37e:('movhu','d0,(0x6223d0d4)'),
    0x6029b387:('mov','a0,(8,sp)'),0x6029b38c:('mov','1646514536,a3'),
    0x6029b394:('add','4,d1'),0x6029b396:('mov','d1,(12,sp)'),
    0x6029b39b:('mov','1646514540,a2'),0x6029b3a1:('mov','(a3),d0'),
    0x6029b3a8:('mov','(a2),d1'),0x6029b3a9:('mov','(a0),d3'),
    0x6029b3ac:('mov','(a2),d0'),0x6029b3ad:('mov','(8,a0),d2'),
    0x6029b3b0:('and','d1,d3'),0x6029b3b2:('and','d0,d2'),0x6029b3b4:('cmp','d2,d3'),
    0x6029b3b5:('beq','0x6029b3c9'),0x6029b3b9:('mov','(a0),d2'),
    0x6029b3ba:('and','d0,d2'),0x6029b3bc:('cmp','d1,d2'),0x6029b3bd:('bne','0x6029b3c9'),
    0x6029b3c1:('mov','(a3),a1'),0x6029b3c3:('mov','(a0),a0'),0x6029b3c7:('calls','(a1)'),
    0x6029b3cb:('add','8,a3'),0x6029b3d0:('add','8,a2'),0x6029b3d2:('cmp','2,d0'),
    0x6029b3d4:('blt','0x6029b3a1'),0x6029b3d8:('mov','(4,a0),d0'),0x6029b3db:('mov','d0,(8,a0)'),
    0x602a2731:('mov','sp,a1'),0x602a2732:('inc4','a1'),
    0x602a2733:('mov','35,d0'),0x602a2735:('mov','d0,(0x6223d930)'),
    0x602a273b:('mov','3,d0'),0x602a273d:('mov','d0,(0x6223d920)'),0x602a2743:('mov','d0,(0x6223d934)'),
    0x602a2749:('mov','532480,d0'),0x602a274f:('mov','d0,(0x6223d910)'),
    0x602a279d:('clr','d0'),0x602a279e:('mov','d0,(44,sp)'),
    0x602a27b8:('mov','52,a0'),0x602a27ba:('add','a1,a0'),0x602a27cc:('add','8,a0'),
    0x602a27de:('mov','1646516384,a0'),0x602a27e4:('call','0x6029ad23,[a2],8'),
    0x602a2ecc:('mov','a1,a2'),0x602a2ecd:('inc4','a2'),0x602a2ece:('mov','(a2),d1'),
    0x602a2ed0:('or','32,d1'),0x602a2ed3:('mov','d1,(a2)'),0x602a2ed5:('call','0x602a302b,[],4'),
    0x602a302b:('mov','(4,a0),d1'),0x602a302e:('and','36,d1'),0x602a3031:('cmp','36,d1'),
    0x602a3033:('bne','0x602a303f'),0x602a3036:('mov','76,d1'),0x602a3038:('call','0x6020c0f0,[],16'),
    0x602a3046:('mov','75,d1'),0x602a3048:('call','0x6020c0f0,[],16'),
    0x6029e942:('or','4,d1'),0x6029e945:('mov','d1,(a0)'),0x6029e947:('call','0x602a302b,[],4'),
    0x6029e94d:('movbu','d0,(0x6223dd51)'),0x602a2fb5:('or','4,d1'),0x602a2fba:('call','0x602a302b,[],4')}
CALLBACKS=[0x602a2d43,0x602a2ec7,0x602a2ef7,0x602a2f57,0x602a2f62,0x602a2f91,
           0x602a2f6d,0x602a2f73,0x602a2f70,0x602a2f7e,0,0x602a301b,0x602a2f81,
           0x602a3042,0x60000,0x602a2edd,0x70000]
WRITES=[(0,0x602a2755,0x602a275b,'(4,sp)'),(1,0x602a275d,0x602a2763,'(8,sp)'),
    (2,0x602a2765,0x602a276b,'(12,sp)'),(3,0x602a276d,0x602a2773,'(16,sp)'),
    (4,0x602a2775,0x602a277b,'(20,sp)'),(5,0x602a27a8,0x602a27ae,'(24,sp)'),
    (6,0x602a277d,0x602a2783,'(28,sp)'),(7,0x602a2785,0x602a278b,'(32,sp)'),
    (8,0x602a278d,0x602a2793,'(36,sp)'),(9,0x602a2795,0x602a279b,'(40,sp)'),
    (11,0x602a27b0,0x602a27b6,'(48,sp)'),(12,0x602a27a0,0x602a27a6,'(52,sp)'),
    (13,0x602a27bc,0x602a27c2,'(a0)'),(14,0x602a27c3,0x602a27c9,'(4,a0)'),
    (15,0x602a27ce,0x602a27d4,'(a0)'),(16,0x602a27d5,0x602a27db,'(4,a0)')]
for index,load,store,dest in WRITES:
    W[load]=('mov',f'{CALLBACKS[index]},d0');W[store]=('mov',f'd0,{dest}')
for flag,add,write,after in [(0x10000,0x6029b078,0x6029b07e,0x6029b09a),
        (0x20000,0x6029b14f,0x6029b155,0x6029b171),(0x40000,0x6029b227,0x6029b22d,0x6029b249),
        (0x80000,0x6029b2eb,0x6029b2f1,0x6029b30d),(0x100000,0x6029b326,0x6029b32c,0x6029b348)]:
    W[add]=('or',f'{flag},d0');W[write]=('mov','d0,(a0)')
    W[after]=('mov','(4,sp),a0');W[after+2]=('mov','a3,a1');W[after+3]=('mov','d2,d0')
W.update({0x6029b2b6:('or','8,d0'),0x6029b2b9:('mov','d0,(a1)'),
    0x6029b2ba:('mov','(0x6223d148),a1'),0x6029b2c5:('mov','(a3),a1'),0x6029b2cb:('calls','(a2)')})
CALLS={0x6029acd8:[0x6029ce9d],0x6029ad23:[0x6029ef4c,0x602a27e4],
       0x6029aef8:[0x6029b09e,0x6029b175,0x6029b24d,0x6029b311,0x6029b34c],
       0x6029b387:[0x6029b05d,0x6029b095,0x6029b134,0x6029b16c,0x6029b20c,0x6029b244,0x6029b2d0,0x6029b308,0x6029b343]}
for target,sites in CALLS.items():
    frame={0x6029acd8:'[d2,d3],16',0x6029ad23:'[a2],8',0x6029aef8:'[d2,d3,a2,a3],20',0x6029b387:'[d2,d3,a2,a3],36'}[target]
    for a in sites:
        W[a]=('call',f'{target:#x},{frame}')
        if not any(lo<=a<hi for lo,hi in WINDOWS):WINDOWS.append((a,a+7))

def inspect(stock,objdump):
    def scan(data):
        actual={t:[] for t in CALLS}
        for op,width in [(0xcd,2),(0xdd,4)]:
            pos=0
            while (i:=data.find(bytes([op]),pos))>=0:
                pos=i+1
                if i+width+3<=len(data):
                    target=BASE+i+int.from_bytes(data[i+1:i+width+1],'little',signed=True)
                    if target in actual:actual[target].append(BASE+i)
        for target,sites in actual.items():
            if sorted(sites)!=CALLS[target]:raise ValueError(f'engine CALL inventory changed: {target:#x} {sites}')
            if data.find(struct.pack('<I',target))>=0:raise ValueError(f'new absolute engine entry reference: {target:#x}')
    e=inspect_windows(stock,objdump,WINDOWS,W,observe_data=scan)
    source=(Path(__file__).resolve().parents[1]/'prototypes/ep7_volatile_hl/controller_sidecar/native_binding.c').read_text()
    table=re.search(r'callbacks\[17\]\s*=\s*\{([^}]+)\}',source)
    if not table or [int(x.strip(),0) for x in table[1].split(',')]!=CALLBACKS:
        raise ValueError('native capture callback qualification differs from checked state33 table')
    if 'word(0x6223d0d8u)!=0xf000fu' not in re.sub(r'\s+','',source):raise ValueError('required engine mask qualification changed')
    return dict(scope=__doc__,input_structure=e['input_structure'],objdump_version=e['objdump_version'],
        checked_instructions=e['checked_instructions'],callback_table='0x6223d134',callbacks=[hex(x) for x in CALLBACKS],
        required_mask='0x000f000f',selected_event_mask='0x00060000',all_complete_mask='0x000f0000',
        workrecord_words=['node','current_flags','last_reported_flags'],workrecord_count=4,
        workrecord_backing='0x6223d104',native_workrecord_stride_opcode_emulated=False,
        call_references={hex(t):[hex(a) for a in sites] for t,sites in CALLS.items()},
        configure_short_CALL_common_target_interval=['0x6029a7e4','0x602a6f4b'],
        pool_short_CALL_target_interval=['0x60294e9d','0x602a4e9c'],
        selected_precedes_all_complete_in_one_serialized_normal_cycle=True,
        event4c_requires_node_flags='0x24',stop_request_is_not_completion_or_drain=True,
        callback_serialization_proven=False,duplicate_completion_excluded=False,
        raw_scan_is_control_flow_proof=False,installed=False,target_executed=False,firmware_built=False,hash_checks_performed=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',type=Path,required=True)
    p.add_argument('--objdump',type=Path,required=True);a=p.parse_args()
    print(json.dumps(inspect(a.stock,a.objdump),indent=2))
