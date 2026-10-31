#!/usr/bin/env python3
"""Fresh-node population sequence, controller task row and declared free call ABIs; no SHA."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_producer_scope import W as PRODUCER_W
from ep7_lifecycle_inventory import inspect as inspect_inventory
ROOT=Path(__file__).resolve().parents[1]
WINDOWS=[(0x602897d6,0x602897e6),(0x60289852,0x60289857),(0x602a3116,0x602a31a9),
    (0x602a31c7,0x602a3204),(0x602a7ea0,0x602a7eb0),(0x602a8860,0x602a8877),
    (0x602a91d9,0x602a91ee),(0x602a2901,0x602a2925),(0x602ac3d7,0x602ac3e5)]
W={a:PRODUCER_W[a] for a in [0x602ac3d7,0x602ac3d9,0x602ac3de,0x602ac3e3]}
W.update({
    0x602897d6:('clr','d0'),0x602897d7:('movhu','d0,(0x62234fc0)'),
    0x602897dd:('mov','255,d0'),0x602897e0:('movhu','d0,(0x62234fc2)'),
    0x60289852:('movm','[d2,d3,a2,a3],(sp)'),0x60289854:('add','-88,sp'),
    0x602a3145:('call','0x6029b4e7,[d2],8'),0x602a314a:('mov','d0,d2'),
    0x602a314b:('cmp','255,d2'),0x602a314f:('beq','0x602a31a5'),
    0x602a3165:('mov','56,d0'),0x602a3167:('call','0x60022700,[],4'),
    0x602a316e:('mov','a0,a2'),0x602a316f:('mov','d2,(a2)'),
    0x602a3189:('mov','(0x6223e0d8),a0'),0x602a318f:('call','0x602972e3,[d2,a2],28'),
    0x602a3196:('mov','d2,(a0)'),0x602a3197:('clr','d0'),0x602a3198:('movbu','d0,(6,a0)'),
    0x602a319b:('mov','a0,(8,a2)'),0x602a319e:('mov','(0x6223d414),a0'),
    0x602a31a4:('mov','d2,(a0)'),0x602a31a5:('mov','a2,a0'),0x602a31a6:('ret','[d2,a2],28'),
    0x602a31c7:('call','0x602a3116,[d2,a2],28'),0x602a31cc:('mov','a0,a2'),
    0x602a31cd:('cmp','0,a2'),0x602a31cf:('beq','0x602a31fc'),
    0x602a31d1:('call','0x602a3204,[d2,a2],16'),0x602a31d6:('exthu','d0'),
    0x602a31d7:('cmp','0,d0'),0x602a31d9:('beq','0x602a31e3'),
    0x602a31dc:('call','0x602a31a9,[a2],8'),0x602a31e1:('bra','0x602a31fc'),
    0x602a31e3:('mov','(0x6223d414),a0'),0x602a31e9:('mov','(a0),d0'),
    0x602a31ea:('call','0x602a7ea0,[d2,d3,a2,a3],20'),
    0x602a31ef:('mov','a3,a0'),0x602a31f0:('mov','(0x6223d414),a1'),0x602a31f6:('clr','d0'),
    0x602a31f7:('call','0x602a8dbd,[d2,d3,a2,a3],48'),
    0x602a31fc:('inc','d2'),0x602a3201:('ret','[d2,d3,a2,a3],20'),
    0x602a7ea0:('call','0x6029b9d1,[],24'),0x602a7ea7:('mov','a0,d3'),
    0x602a7ea9:('call','0x60300055,[],0'),
    0x602a8860:('mov','61209,d0'),0x602a8866:('mov','0,a0'),0x602a8868:('mov','1,d1'),
    0x602a886a:('call','0x6005e971,[d2,d3],12'),0x602a8871:('movbu','d0,(1,a2)'),
    0x602a8874:('ret','[d2,d3,a2,a3],20'),
    0x602a91d9:('mov','(20,sp),a0'),0x602a91db:('mov','(24,sp),a1'),
    0x602a91dd:('call','0x602a9f16,[a2],4'),0x602a91e2:('mov','(20,sp),a0'),
    0x602a91e4:('call','0x605e61d7,[a2,a3],32'),0x602a91eb:('ret','[d2,d3,a2,a3],48'),
    0x602a2901:('mov','(a3),a0'),0x602a2903:('mov','d2,(8,a0)'),
    0x602a2908:('movbu','(6,a0),d0'),0x602a290d:('bne','0x602a291b'),
    0x602a2912:('call','0x602ac198,[a2],24'),0x602a291b:('mov','(a3),d0'),
    0x602a291c:('mov','d0,a0'),0x602a291e:('call','0x602ac141,[d2],24'),
})
CHECKS=[(0x60039664,'<7I',(0x73,0,0,0x60289852,25,4096,0))]

def inspect(stock,objdump):
    inventory=inspect_inventory()
    manifest=json.loads((ROOT/'research/ep7/lifecycle-hook-inventory.json').read_text())
    frees=[int(r['address'],16) for r in manifest['free_sites'] if r['object_kind']=='node']
    windows=WINDOWS+[(address,address+7) for address in frees]
    witnesses=dict(W);witnesses.update({a:('call','0x60022732,[],4') for a in frees})
    e=inspect_windows(stock,objdump,windows,witnesses,CHECKS)
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],checked_data_rows=len(CHECKS),
        controller_task=dict(row='0x60039664',configured_id=0x73,entry='0x60289852',priority=25,stack_bytes=4096),
        native_initialization='0x602897d7',fresh_call='0x602a31c7',fresh_return='0x602a31cc',
        native_node_bytes=56,node_id_offset=0,node_associated_offset=8,
        queue_publish_call='0x602a31d1',population_call='0x602a31ea',sample_return='0x602a31ef',
        postpopulation_call='0x602a31f7',seal_return='0x602a31fc',
        call_frames=dict(fresh=28,population=20,postpopulation=48),
        selected_associated_backlink='0x602a2903',metadata_scope_call='0x602ac3de',
        early_publication_requires_permanent_neutrality=True,population_d0_is_not_boolean_status=True,
        declared_node_free_calls=[hex(a) for a in frees],declared_free_abi='pointer a0; CALL [],4',
        declared_inventory_consistent=inventory['source_inventory_consistent'],
        all_native_lifetime_paths_closed=False,controller_exclusion_proved=False,source_adapter_installed=False,
        full_task_stack_budget_proved=False,hash_checks_performed=False,
        firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
