#!/usr/bin/env python3
"""Fixed associated pool provenance, zero-refcount return and reset seams; no SHA."""
import argparse,json,struct
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE
WINDOWS=[(0x6029c66f,0x6029c697),(0x602972aa,0x602973c6),
    (0x6020b949,0x6020b962),(0x602a3189,0x602a319e),
    (0x602a29e4,0x602a2a16),(0x602a2c9d,0x602a2cce)]
W={
    0x6029c66f:('mov','1646518492,a0'),0x6029c675:('mov','a0,(0x6223e0d8)'),
    0x6029c67b:('mov','1646518624,d0'),0x6029c681:('mov','d0,(4,sp)'),
    0x6029c683:('mov','1070,d0'),0x6029c686:('mov','d0,(8,sp)'),
    0x6029c688:('mov','1646518524,a1'),0x6029c68e:('mov','25,d0'),
    0x6029c690:('mov','16,d1'),0x6029c692:('call','0x602972aa,[d2,d3,a2,a3],28'),
    0x602972aa:('mov','d1,d2'),0x602972ab:('mov','(36,sp),d1'),
    0x602972ad:('exthu','d0'),0x602972ae:('mov','d1,(a0)'),
    0x602972af:('movhu','d2,(24,a0)'),0x602972b2:('mov','(32,sp),d3'),
    0x602972b4:('mov','d0,a3'),0x602972b6:('mov','d3,(28,a0)'),
    0x602972b9:('inc4','a0'),0x602972ba:('mov','a0,(8,sp)'),
    0x602972bc:('mov','d1,(4,sp)'),0x602972be:('mov','4,d1'),
    0x602972c0:('call','0x6020b949,[d2],4'),0x602972c7:('mov','0,a2'),
    0x602972c9:('cmp','a2,a3'),0x602972ca:('ble','0x602972e0'),
    0x602972cc:('exthu','d2'),0x602972cd:('clr','d0'),0x602972ce:('mov','d3,a0'),
    0x602972d0:('mov','d0,(a0)'),0x602972d1:('mov','(8,sp),a0'),
    0x602972d3:('mov','d3,d0'),0x602972d4:('call','0x6020b98b,[],8'),
    0x602972db:('inc','a2'),0x602972dc:('add','d2,d3'),
    0x602972dd:('cmp','a3,a2'),0x602972de:('blt','0x602972cd'),
    0x602972e0:('ret','[d2,d3,a2,a3],28'),
    0x6020b94c:('movhu','d0,(4,a0)'),0x6020b94f:('movhu','d1,(6,a0)'),
    0x6020b952:('mov','a1,(8,a0)'),
    0x60297316:('mov','d2,a0'),0x60297318:('call','0x6020b9ff,[],24'),
    0x6029731f:('mov','d0,a0'),0x60297321:('mov','1,d0'),
    0x60297323:('mov','d0,(a0)'),0x60297324:('inc4','a0'),
    0x60297325:('ret','[d2,a2],28'),
    0x602a3189:('mov','(0x6223e0d8),a0'),0x602a318f:('call','0x602972e3,[d2,a2],28'),
    0x602a3196:('mov','d2,(a0)'),0x602a3197:('clr','d0'),
    0x602a3198:('movbu','d0,(6,a0)'),0x602a319b:('mov','a0,(8,a2)'),
    0x60297328:('mov','a0,a3'),0x60297329:('cmp','0,a1'),
    0x6029732b:('bne','0x60297330'),0x6029732d:('ret','[d2,d3,a2,a3],56'),
    0x60297334:('mov','a1,d0'),0x60297336:('add','-4,d0'),0x60297338:('mov','d0,a2'),
    0x60297343:('mov','4,d3'),0x60297345:('add','a3,d3'),
    0x6029737d:('mov','(a2),d0'),0x6029737e:('cmp','0,d0'),
    0x60297380:('bls','0x60297387'),0x60297382:('mov','1,d1'),
    0x60297384:('sub','d1,d0'),0x60297386:('mov','d0,(a2)'),
    0x60297387:('mov','(a2),d0'),0x60297388:('cmp','0,d0'),
    0x6029738a:('bhi','0x602973c3'),0x6029738c:('mov','d3,a0'),
    0x6029738e:('call','0x6020b975,[d2],4'),0x60297395:('exthu','d0'),
    0x60297396:('cmp','0,d0'),0x60297398:('beq','0x602973b8'),
    0x602973b6:('bra','0x602973c3'),0x602973b8:('mov','d3,a0'),
    0x602973ba:('mov','a2,d0'),0x602973bc:('call','0x6020b98b,[],8'),
    0x602973c3:('ret','[d2,d3,a2,a3],56'),
    0x602a29e7:('or','16,d0'),0x602a29eb:('and','24,d0'),
    0x602a29ee:('cmp','24,d0'),0x602a29f0:('bne','0x602a2a07'),
    0x602a2a00:('call','0x60022732,[],4'),0x602a2a07:('mov','(0x6223e0d8),a0'),
    0x602a2a0d:('mov','d2,a1'),0x602a2a0f:('call','0x60297328,[d2,d3,a2,a3],56'),
    0x602a2ca9:('bne','0x602a2cc0'),0x602a2cb9:('call','0x60022732,[],4'),
    0x602a2cc0:('mov','(0x6223e0d8),a0'),0x602a2cc6:('mov','a3,a1'),
    0x602a2cc7:('call','0x60297328,[d2,d3,a2,a3],56')}
POOL_CALLS=[0x6029f1bc,0x6029f67c,0x602a29a3,0x602a2a0f,0x602a2a40,0x602a2cc7,0x602a4218]
OTHER_CALLS=[0x60291bca,0x60291c40,0x60291cab,0x60291d05]
INITIALIZER_CALLS=[0x60291a0a,0x60291a31,0x60291a60,0x60291a8f,0x6029c692]
OWNER_LOADS={0x60291bc3:0x62236654,0x60291c39:0x622366c0,0x60291ca4:0x6223672c,0x60291cfe:0x6223675c,
    0x6029f1b6:0x6223e0d8,0x6029f675:0x6223e0d8,0x602a299b:0x6223e0d8,
    0x602a2a07:0x6223e0d8,0x602a2a3a:0x6223e0d8,0x602a2cc0:0x6223e0d8,0x602a4212:0x6223e0d8}
for a,pool in OWNER_LOADS.items():
    W[a]=('mov',f'({pool:#x}),a0')
    if not any(lo<=a<hi for lo,hi in WINDOWS):WINDOWS.append((a,a+6))
for a in INITIALIZER_CALLS:
    W[a]=('call','0x602972aa,[d2,d3,a2,a3],28')
    if not any(lo<=a<hi for lo,hi in WINDOWS):WINDOWS.append((a,a+7))
for a in POOL_CALLS+OTHER_CALLS:
    W[a]=('call','0x60297328,[d2,d3,a2,a3],56')
    if not any(lo<=a<hi for lo,hi in WINDOWS):WINDOWS.append((a,a+7))

def inspect(stock,objdump):
    references={}
    def reference_scan(data):
        expected={0x60297328:POOL_CALLS+OTHER_CALLS,0x602972aa:INITIALIZER_CALLS}
        sites={target:[] for target in expected}
        for opcode,width in [(0xcd,2),(0xdd,4)]:
            pos=0
            while (i:=data.find(bytes([opcode]),pos))>=0:
                pos=i+1
                if i+width+3<=len(data):
                    target=BASE+i+int.from_bytes(data[i+1:i+1+width],'little',signed=True)
                    if target in sites:sites[target].append(BASE+i)
        for target,actual in sites.items():
            if sorted(actual)!=sorted(expected[target]):raise ValueError(f'associated pool CALL inventory changed: {target:#x}')
            if data.find(struct.pack('<I',target))>=0:raise ValueError(f'new absolute pool entry reference: {target:#x}')
            references[hex(target)]=[hex(a) for a in sorted(actual)]
    e=inspect_windows(stock,objdump,WINDOWS,W,observe_data=reference_scan)
    return dict(scope=__doc__,input_structure=e['input_structure'],objdump_version=e['objdump_version'],
        checked_instructions=e['checked_instructions'],pool='0x6223e0dc',pool_pointer='0x6223e0d8',
        queue_backing='0x6223e0fc',slot_backing='0x6223e160',slot_count=25,slot_bytes=16,
        refcount_bytes=4,payload_bytes=12,recycle_CALL='0x602973bc',initializer_CALL='0x6029c692',
        initializer_incoming_stack_offsets=[32,36],initializer_requires_tail_transfer=True,
        initializer_short_CALL_target_interval=['0x60294692','0x602a4691'],
        other_pool_calls=[hex(a) for a in OTHER_CALLS],references=references,
        zero_refcount_and_nonfull_free_list_precede_recycle=True,
        node_can_remain_live_after_associated_release=True,
        raw_reference_scan_is_control_flow_proof=False,udf_pointer_bound_math_emulated=False,
        full_native_alias_closure_proven=False,installed=False,target_executed=False,
        firmware_built=False,hash_checks_performed=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',type=Path,required=True)
    p.add_argument('--objdump',type=Path,required=True);a=p.parse_args()
    print(json.dumps(inspect(a.stock,a.objdump),indent=2))
