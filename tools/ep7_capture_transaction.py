#!/usr/bin/env python3
"""Three native refill envelopes, common prewrite entries and27-CALL cohort; no SHA."""
import argparse,json,struct
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE
ROOT=Path(__file__).resolve().parents[1]
REFILLS=[(0x602a31c7,0x602a31ea,0x602a31f7),(0x602a440a,0x602a442c,0x602a443e),
         (0x602a4480,0x602a44a3,0x602a44b5)]
ORIGINALS=[(0x602a3116,'[d2,a2]',28),(0x602a7ea0,'[d2,d3,a2,a3]',20),(0x602a8dbd,'[d2,d3,a2,a3]',48)]
FREE=[0x602a31b1,0x602a4461,0x6029f1c2,0x602a4220,0x6029f6ba,0x602a29ab,0x602a2a00,
      0x602a2a48,0x602a2ab5,0x602a427d,0x602a44d8,0x602a2cb9,0x602a2d0d]
WINDOWS=[(0x602a7ea0,0x602a7eb0),(0x602a8dbd,0x602a8de1),(0x60300055,0x60300068),
    (0x6029b9d1,0x6029ba1e),
    (0x602a31bb,0x602a3204),(0x602a43db,0x602a446d),(0x602a446d,0x602a44e2),
    (0x602a2b32,0x602a2b39),(0x6029cdc6,0x6029ce1b),(0x60289908,0x60289933),
    (0x60289b73,0x60289b9f),(0x60289a3b,0x60289a67)]
W={
    0x602a7ea7:('mov','a0,d3'),0x602a7ea9:('call','0x60300055,[],0'),
    0x602a8dbd:('mov','a0,(24,sp)'),0x602a8dbf:('mov','d0,a2'),
    0x602a8dc1:('mov','a0,d0'),0x602a8dc3:('add','496,d0'),
    0x602a8dc7:('mov','d0,(28,sp)'),0x602a8dc9:('mov','(a1),d0'),
    0x602a8dd1:('mov','a0,(20,sp)'),0x602a8dd3:('call','0x602814ab,[],0'),
    0x602a8dda:('mov','(20,sp),a0'),0x602a8ddc:('extbu','d0'),
    0x602a8ddd:('movhu','d0,(23926,a0)'),
    0x60300055:('mov','1646626860,a1'),0x6030005b:('mov','-6833,d1'),
    0x6030005f:('mov','(a1),d0'),0x60300061:('mov','d0,(a0)'),
    0x6029b9d1:('cmp','1,d0'),0x6029b9d3:('bcs','0x6029b9ec'),
    0x6029b9d5:('cmp','26,d0'),0x6029b9d7:('bcc','0x6029b9ec'),
    0x6029b9d9:('mov','d0,d1'),0x6029b9da:('udfu01','24,d1'),
    0x6029b9dd:('mov','d1,a0'),0x6029b9df:('add','1646514552,a0'),
    0x6029b9e5:('movhu','(a0),d1'),0x6029b9e7:('btst','4,d1'),
    0x6029b9ea:('bne','0x6029ba18'),0x6029ba18:('mov','(12,a0),a0'),
    0x6029ba1b:('ret','[],24'),
    0x602a31cc:('mov','a0,a2'),0x602a31cf:('beq','0x602a31fc'),
    0x602a31d1:('call','0x602a3204,[d2,a2],16'),0x602a31d9:('beq','0x602a31e3'),
    0x602a31db:('mov','a2,a0'),0x602a31dc:('call','0x602a31a9,[a2],8'),
    0x602a31e1:('bra','0x602a31fc'),0x602a31e3:('mov','(0x6223d414),a0'),
    0x602a31e9:('mov','(a0),d0'),0x602a31ef:('mov','a3,a0'),0x602a31f0:('mov','(0x6223d414),a1'),
    0x602a440f:('mov','a0,a2'),0x602a4412:('beq','0x602a4443'),
    0x602a4414:('call','0x602a3204,[d2,a2],16'),0x602a441b:('beq','0x602a4425'),
    0x602a441d:('mov','a2,a0'),0x602a441e:('call','0x602a31a9,[a2],8'),
    0x602a4423:('bra','0x602a4443'),0x602a4425:('mov','(0x6223d414),a1'),
    0x602a442b:('mov','(a1),d0'),0x602a4431:('mov','(0x6223d414),a1'),
    0x602a4437:('mov','1646515228,a0'),0x602a4443:('mov','a3,a1'),
    0x602a4460:('mov','a3,a0'),0x602a446a:('ret','[d2,d3,a2,a3],20'),
    0x602a446d:('mov','a0,a3'),0x602a447e:('bne','0x602a44ba'),0x602a4485:('mov','a0,a2'),
    0x602a4488:('beq','0x602a44ba'),0x602a448a:('call','0x602a3204,[d2,a2],16'),
    0x602a4492:('beq','0x602a449c'),0x602a4494:('mov','a2,a0'),
    0x602a4495:('call','0x602a31a9,[a2],8'),0x602a449a:('bra','0x602a44ba'),
    0x602a449c:('mov','(0x6223d414),a1'),0x602a44a2:('mov','(a1),d0'),
    0x602a44a8:('mov','(0x6223d414),a1'),0x602a44ae:('mov','1646515228,a0'),
    0x602a44ba:('mov','a3,a1'),0x602a44d7:('mov','a3,a0'),0x602a44df:('ret','[a2,a3],12'),
    0x602a2b32:('mov','d2,a0'),0x602a2b34:('call','0x602a446d,[a2,a3],12'),
    0x6029cdd0:('call','0x602a3116,[d2,a2],28'),0x6029cdd5:('mov','a0,a1'),
    0x6029ce01:('mov','(8,a1),a0'),0x6029ce04:('mov','1,d0'),0x6029ce06:('movbu','d0,(6,a0)'),
    0x6029ce09:('mov','(0x6223e314),a0'),0x6029ce0f:('mov','a1,d0'),0x6029ce11:('call','0x6020b98b,[],8'),
    0x60289908:('movhu','(0x62234fc0),d0'),0x60289915:('mov','(16,a0),a0'),
    0x60289926:('mov','(4,a0),a1'),0x60289929:('mov','(28,sp),a0'),0x6028992b:('calls','(a1)'),
    0x60289b73:('movhu','(0x62234fc0),d0'),0x60289b7f:('mov','(16,a0),a0'),
    0x60289b92:('mov','(4,a0),a1'),0x60289b95:('mov','(28,sp),a0'),0x60289b97:('calls','(a1)'),
    0x60289a3b:('movhu','(0x62234fc0),d0'),0x60289a47:('mov','(12,a0),a0'),
    0x60289a5a:('mov','(4,a0),a1'),0x60289a5d:('mov','(32,sp),a0'),0x60289a5f:('calls','(a1)')}
COHORT={a:('call',f'{target:#x},{mask},{frame}') for row in REFILLS for a,(target,mask,frame) in zip(row,ORIGINALS)}
COHORT.update({a:('call','0x60022732,[],4') for a in FREE})
COHORT.update({a:('call','0x6028a882,[d2,d3,a2,a3],32') for a in (0x60289c5e,0x60289d02)})
COHORT[0x6029be5d]=('call','0x603db89e,[],4')
COHORT.update({a:('call','0x6029b9d1,[],24') for a in (0x602a7ea0,0x602a8dca)})
W.update(COHORT)
for a in COHORT:
    if not any(lo<=a<hi for lo,hi in WINDOWS):WINDOWS.append((a,a+7))
CHECKS=[(0x6042d2dc,'<4I',(0x4b,0x602a281a,0x4c,0x602a2a66)),
    (0x6042d2f4,'<II',(0x4e,0x602a433c)),
    (0x60039664,'<7I',(0x73,0,0,0x60289852,25,4096,0))]
EXPECTED={
    0x602a3116:[0x6029cdd0,0x602a31c7,0x602a440a,0x602a4480],
    0x602a31bb:[0x602a29bf,0x602a2a5c],
    0x602a7ea0:[0x6029586d,0x60298147,0x60298d8e,0x6029cfe4,0x6029d7cd,0x602a161a,0x602a2182,0x602a31ea,0x602a442c,0x602a44a3],
    0x602a8dbd:[0x602996e5,0x6029ddb2,0x6029eeb9,0x6029f3ec,0x6029f94d,0x602a0f1b,0x602a2240,0x602a26fc,0x602a31f7,0x602a443e,0x602a44b5]}
def inspect(stock,objdump):
    inventory={}
    def data_check(data):
        candidates={a:[] for a in EXPECTED}
        for opcode,width in [(0xcd,2),(0xdd,4)]:
            pos=0
            while (i:=data.find(bytes([opcode]),pos))>=0:
                pos=i+1
                if i+width+3<=len(data):
                    target=BASE+i+int.from_bytes(data[i+1:i+1+width],'little',signed=True)
                    if target in candidates:candidates[target].append(BASE+i)
        for target,sites in candidates.items():
            if sorted(sites)!=EXPECTED[target]:raise ValueError(f'CALL reference inventory changed: {target:#x}')
            if data.find(struct.pack('<I',target))>=0:raise ValueError(f'new absolute entry reference: {target:#x}')
            inventory[hex(target)]=[hex(a) for a in sorted(sites)]
    e=inspect_windows(stock,objdump,WINDOWS,W,CHECKS,observe_data=data_check)
    bounds={name:[hex(max(row[i] for row in REFILLS)-32768),hex(min(row[i] for row in REFILLS)+32767)]
        for i,name in enumerate(['fresh','sample','finish'])}
    return dict(scope=__doc__,input_structure=e['input_structure'],objdump_version=e['objdump_version'],
        checked_instructions=e['checked_instructions'],checked_data_rows=len(CHECKS),
        source_envelopes=[[hex(a) for a in row] for row in REFILLS],
        common_prewrite_lookup_calls=['0x602a7ea0','0x602a8dca'],
        lookup_result_register='a0',original_lookup_frame_bytes=24,
        common_entry_precedes_first_capture_store=True,
        new_prewrite_call_relocation_width_bytes=4,
        cohort_call_sites=[hex(a) for a in sorted(COHORT)],cohort_call_count=len(COHORT),
        candidate_short_call_target_intervals=bounds,qualified_code_placement=False,
        full_main_direct_CALL_candidates=inventory,raw_reference_scan_is_control_flow_proof=False,
        unqualified_distinct_fresh_route='0x6029cdd0: associated+6=1, queue6223e314, no matched A2 sample/finish envelope',
        other_population_and_repopulation_paths_qualified=False,
        full_native_alias_and_retirement_closure_proven=False,interrupt_or_other_core_exclusion_proven=False,
        installed=False,target_executed=False,firmware_built=False,hash_checks_performed=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',type=Path,required=True)
    p.add_argument('--objdump',type=Path,required=True);a=p.parse_args()
    print(json.dumps(inspect(a.stock,a.objdump),indent=2))
