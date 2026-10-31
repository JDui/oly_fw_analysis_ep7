#!/usr/bin/env python3
"""Deferred associated FIFO and both metadata producer routes; exact static evidence, no SHA."""
import argparse,json,struct
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE

WINDOWS=[(0x602abe7b,0x602abe9d),(0x602ac3c9,0x602ac3fd),
         (0x602ac5d0,0x602ac646),(0x602ac8d0,0x602ac916),
         (0x6020b949,0x6020b965),(0x6020b98b,0x6020ba9f),
         (0x602ad758,0x602ad765),(0x602ac4fd,0x602ac502),
         (0x602ac5a6,0x602ac5ab),(0x602ac66c,0x602ac671)]
W={
    0x602abe7b:('mov','1646520288,a0'),0x602abe81:('mov','a0,(0x6223e7dc)'),
    0x602abe87:('mov','182,d0'),0x602abe8a:('mov','d0,(4,sp)'),
    0x602abe8c:('mov','1646520308,a1'),0x602abe92:('mov','25,d0'),
    0x602abe94:('mov','4,d1'),0x602abe96:('call','0x6020b949,[d2],4'),
    0x602ac3d7:('mov','a2,d0'),0x602ac3d9:('call','0x602ac8d0,[],0'),
    0x602ac3de:('call','0x602ac748,[d2,a2,a3],32'),0x602ac3e3:('bra','0x602ac3fd'),
    0x602ac3ee:('mov','(0x6223e7dc),a0'),0x602ac3f4:('mov','a2,d0'),
    0x602ac3f6:('call','0x6020b98b,[],8'),
    0x602ac4fd:('call','0x602ac5d0,[d2],8'),0x602ac5a6:('call','0x602ac5d0,[d2],8'),
    0x602ac66c:('call','0x602ac5d0,[d2],8'),
    0x602ac5d0:('mov','(0x6223e7dc),a0'),0x602ac5d6:('call','0x6020b962,[],0'),
    0x602ac5e0:('ble','0x602ac62d'),0x602ac5e2:('mov','(0x6223e7dc),a0'),
    0x602ac5e8:('call','0x6020b9ff,[],24'),0x602ac5ef:('mov','d0,d2'),
    0x602ac5f0:('call','0x602ac88a,[d2],4'),0x602ac5f8:('beq','0x602ac615'),
    0x602ac602:('mov','d2,(0x6223e7b0)'),0x602ac608:('mov','d2,d0'),
    0x602ac609:('call','0x602ac8d0,[],0'),0x602ac60e:('call','0x602ac748,[d2,a2,a3],32'),
    0x602ac613:('bra','0x602ac643'),0x602ac615:('mov','d2,d0'),
    0x602ac616:('call','0x602ac93a,[d2,d3,a2],36'),0x602ac61b:('mov','(0x6223e7dc),a0'),
    0x602ac621:('call','0x6020b962,[],0'),0x602ac62b:('bgt','0x602ac5e2'),
    0x602ac643:('ret','[d2],8'),
    0x602ac8d6:('mov','d0,a0'),0x602ac8dc:('mov','(a0),d0'),0x602ac8dd:('retf','[],0'),
    0x602ac8e0:('mov','(0x6223e7dc),a0'),0x602ac8e6:('call','0x6020b962,[],0'),
    0x602ac8f0:('ble','0x602ac916'),0x602ac8f2:('mov','(0x6223e7dc),a0'),
    0x602ac8f8:('call','0x6020b9ff,[],24'),0x602ac8ff:('call','0x602ac93a,[d2,d3,a2],36'),
    0x602ac904:('mov','(0x6223e7dc),a0'),0x602ac90a:('call','0x6020b962,[],0'),
    0x602ac914:('bgt','0x602ac8f2'),0x602ad758:('mov','(0x6223e7dc),a0'),
    0x602ad75e:('call','0x6020b962,[],0'),
    0x6020b949:('mov','(8,sp),d2'),0x6020b94b:('mov','d2,(a0)'),
    0x6020b94c:('movhu','d0,(4,a0)'),0x6020b94f:('movhu','d1,(6,a0)'),
    0x6020b952:('mov','a1,(8,a0)'),0x6020b955:('clr','d0'),
    0x6020b956:('movhu','d0,(12,a0)'),0x6020b959:('movhu','d0,(14,a0)'),
    0x6020b95c:('movhu','d0,(16,a0)'),0x6020b95f:('retf','[d2],4'),
    0x6020b962:('movhu','(12,a0),d0'),
    0x6020b98b:('mov','d0,(4,sp)'),0x6020b98d:('mov','sp,a1'),0x6020b98e:('inc4','a1'),
    0x6020b98f:('call','0x6020b998,[d2,d3,a2,a3],40'),0x6020b995:('ret','[],8'),
    0x6020b998:('mov','a0,a2'),0x6020b999:('mov','12,d3'),
    0x6020b9a8:('bne','0x6020b9c9'),0x6020b9bf:('call','0x60061808,[d2,d3,a2,a3],112'),
    0x6020b9c6:('clr','d0'),0x6020b9c7:('bra','0x6020b9fc'),
    0x6020b9c9:('mov','(8,a2),a0'),0x6020b9cc:('mov','14,a3'),
    0x6020b9d0:('movhu','(a3),d1'),0x6020b9d2:('add','6,a2'),
    0x6020b9d8:('udf00','d2,d1'),0x6020b9da:('add','d1,a0'),
    0x6020b9dc:('call','0x47001052,[d2,d3,a2,a3],28'),
    0x6020b9e7:('inc','d0'),0x6020b9e8:('movhu','d0,(a0)'),
    0x6020b9ea:('movhu','(a3),d0'),0x6020b9ec:('inc','d0'),0x6020b9ed:('movhu','d0,(a3)'),
    0x6020b9f5:('bne','0x6020b9fa'),0x6020b9f7:('clr','d0'),0x6020b9f8:('movhu','d0,(a3)'),
    0x6020b9fa:('movhu','(a2),d0'),0x6020b9fc:('ret','[d2,d3,a2,a3],40'),
    0x6020b9ff:('movhu','(12,a0),d0'),0x6020ba04:('bne','0x6020ba25'),
    0x6020ba22:('clr','d0'),0x6020ba23:('bra','0x6020ba2f'),
    0x6020ba25:('mov','sp,a1'),0x6020ba26:('add','20,a1'),
    0x6020ba28:('call','0x6020ba32,[d2,d3,a2,a3],44'),0x6020ba2d:('mov','(20,sp),d0'),
    0x6020ba2f:('ret','[],24'),0x6020ba5f:('mov','(8,a2),a1'),
    0x6020ba62:('mov','16,d3'),0x6020ba68:('movhu','(a0),d1'),
    0x6020ba76:('udf00','d2,d1'),0x6020ba78:('add','d1,a1'),
    0x6020ba7a:('call','0x47001052,[d2,d3,a2,a3],28'),
    0x6020ba85:('add','-1,d0'),0x6020ba87:('movhu','d0,(a3)'),
    0x6020ba8b:('inc','d0'),0x6020ba8c:('movhu','d0,(a0)'),
    0x6020ba93:('bne','0x6020ba98'),0x6020ba95:('clr','d0'),0x6020ba96:('movhu','d0,(a0)'),
    0x6020ba9c:('ret','[d2,d3,a2,a3],44')}
CALLS={0x602ac748:[0x602ac3de,0x602ac60e],0x602ac5d0:[0x602ac4fd,0x602ac5a6,0x602ac66c]}
LITERALS={0x6223e7dc:[0x602abe83,0x602ac3f0,0x602ac5d2,0x602ac5e4,0x602ac61d,
                    0x602ac8e2,0x602ac8f4,0x602ac906,0x602ad75a],
          0x6223e7e0:[0x602abe7d],0x6223e7f4:[0x602abe8e]}

def inspect(stock,objdump):
    def references(data):
        sites={t:[] for t in CALLS}
        for opcode,width in [(0xcd,2),(0xdd,4)]:
            pos=0
            while (i:=data.find(bytes([opcode]),pos))>=0:
                pos=i+1
                if i+width+3<=len(data):
                    target=BASE+i+int.from_bytes(data[i+1:i+1+width],'little',signed=True)
                    if target in sites:sites[target].append(BASE+i)
        for t,actual in sites.items():
            if sorted(actual)!=CALLS[t]:raise ValueError(f'waiting producer CALL inventory changed: {t:#x}')
            if data.find(struct.pack('<I',t))>=0:raise ValueError(f'new absolute entry reference: {t:#x}')
        for t,expected in LITERALS.items():
            actual=[];pos=0
            while (i:=data.find(struct.pack('<I',t),pos))>=0:
                actual.append(BASE+i);pos=i+1
            if actual!=expected:raise ValueError(f'waiting queue literal inventory changed: {t:#x}')
    e=inspect_windows(stock,objdump,WINDOWS,W,observe_data=references)
    return dict(scope=__doc__,input_structure=e['input_structure'],objdump_version=e['objdump_version'],
        checked_instructions=e['checked_instructions'],queue='0x6223e7e0',backing='0x6223e7f4',capacity=25,element_bytes=4,
        count_offset=12,write_offset=14,read_offset=16,enqueue_result_full=0,enqueue_result_success=4,
        enqueue_CALL='0x602ac3f6',pop_CALLs=['0x602ac5e8','0x602ac8f8'],reset_CALL='0x602abe96',
        deferred_associated_register='d2',immediate_associated_register='a2',
        call_references={hex(t):[hex(a) for a in v] for t,v in CALLS.items()},
        literal_references={hex(t):[hex(a) for a in v] for t,v in LITERALS.items()},
        service_short_CALL_common_target_interval=['0x602a466c','0x602b44fc'],
        raw_scan_is_control_flow_proof=False,udf00_emulated=False,controller_exclusion_proven=False,
        installed=False,target_executed=False,firmware_built=False,hash_checks_performed=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',type=Path,required=True)
    p.add_argument('--objdump',type=Path,required=True);a=p.parse_args()
    print(json.dumps(inspect(a.stock,a.objdump),indent=2))
