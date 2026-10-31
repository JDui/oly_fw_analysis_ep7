#!/usr/bin/env python3
"""Bounded audit of two early-loaded padding interiors; no free-space approval or SHA."""
import argparse
import json
import re
import struct
import subprocess
from pathlib import Path

from penf_code_space_audit import pointer_candidates,branch_candidates
from ep7_request_ownership import require_instruction
from ep7_load_regions import W as LOAD_W

BASE=0x60020020
RANGES=[(0x60048040,0x6004ffc0),(0x600c8040,0x600cffc0)]
# Reviewed local instruction containing each raw transfer candidate. A decoded
# containing instruction is not a whole-program proof excluding alternate entry.
CONTAINERS={
    0x60041e32:(0x60041e2f,'mov','(0x6222cd9c),d0'),
    0x60041e85:(0x60041e82,'mov','(0x6222cd9c),d0'),
    0x60041ea5:(0x60041ea2,'mov','(0x6222cd9c),d0'),
    0x60041ee5:(0x60041ee2,'mov','(0x6222cd9c),d0'),
    0x60041eee:(0x60041eeb,'mov','d0,(0x6222cd9c)'),
    0x600441c4:(0x600441c3,'jmp','0x60044290'),
    0x600457bd:(0x600457bc,*LOAD_W[0x600457bc]),
    0x600457d5:(0x600457d4,*LOAD_W[0x600457d4]),
    0x60045e57:(0x60045e56,'mov','385892362,d0'),
    0x60045ea8:(0x60045ea7,'mov','385892362,d0'),
    0x6005166a:(0x60051667,'add','-1569731262,a2'),
    0x60051aca:(0x60051ac9,'mov','48879,d0'),
    0x60051b9f:(0x60051b9e,'mov','48879,d0'),
    0x60051c70:(0x60051c6d,'add','-1569731262,a0'),
    0x60051c80:(0x60051c7f,'mov','48879,d0'),
    0x60051cde:(0x60051cdb,'add','-1569731262,a0'),
    0x60051d05:(0x60051d02,'add','-1569731262,a0'),
    0x60051d58:(0x60051d57,'mov','48879,d0'),
    0x60051f20:(0x60051f1f,'mov','-559038737,d0'),
    0x600523ed:(0x600523ec,'mov','1167693824,d1'),
    0x60052c7c:(0x60052c7b,'call','0x60052447,[d2,a2],8'),
    0x60053622:(0x60053621,'call','0x600525ed,[d2,a2],12'),
    0x602fcbd3:(0x602fcbd0,'call','0x602c1291,[d2,d3],12')}
PRIORITY_CALLS={0x613c3311:(0x613c330d,'0x60022fab,[d2],4'),
                0x6061ecfe:(0x6061ecfa,'0x6005e971,[d2,d3],12'),
                0x6061ed51:(0x6061ed4d,'0x6005e971,[d2,d3],12')}
PRIORITY_SPLIT=[0x60c9bbb3,0x60c9bca6,0x60c9c142,0x60c9c17a,0x60c9c3f1,0x60c9c58b]
NUMERIC=0x60c34b61


def inspect(decoded,objdump):
    main=decoded.read_bytes()
    if len(main)!=26214336:raise ValueError('unsupported decoded main length')
    instructions={}
    def witness(pc,mn,operands):
        asm=subprocess.check_output([str(objdump),'-D','-z','-b','binary','-m','mn10300',
            '--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={pc:#x}',
            f'--stop-address={pc+8:#x}',str(decoded)],text=True)
        require_instruction(asm,pc,mn,operands)
        line=next(x for x in asm.splitlines() if x.startswith(f'{pc:x}:'))
        raw=re.search(r':\s*((?:[0-9a-f]{2}[ \t]+)+)',line).group(1).split()
        instructions[pc]=dict(address=hex(pc),mnemonic=mn,operands=operands,bytes=len(raw))
        return len(raw)

    # Reuse just the actual early-copy tuple, not all historical load checks.
    for pc in [0x600201db,0x600201e7,0x600201ed,0x600201f3,0x600201f9]:
        witness(pc,*LOAD_W[pc])
    witness(0x600201fe,'mov','(0x6218d984),d0')
    witness(0x60020392,'call','0x6003009c,[],0')
    direct=branch_candidates(main,BASE,RANGES)
    sites={int(hit['site'],16) for group in direct for hit in group}
    if sites!=set(CONTAINERS):raise ValueError('relative candidate inventory changed')
    for site,(pc,mn,operands) in CONTAINERS.items():
        size=witness(pc,mn,operands)
        if not pc<site<pc+size:raise ValueError('raw opcode is not inside reviewed instruction')
    relocated=branch_candidates(main[0x6143ca00-BASE:0x6143e200-BASE],0x47000800,RANGES)
    if any(relocated):raise ValueError('relocated helper has a new transfer candidate')
    priority_seen=set();regions=[]
    for (lo,hi),hits in zip(RANGES,direct):
        block=lo-0x40
        if main[block-BASE:block-BASE+16]!=bytes(16):raise ValueError('empty block header changed')
        if main[block+16-BASE:hi+64-BASE]!=b'\xff'*(hi+64-block-16):
            raise ValueError('candidate padding changed')
        literals=[]
        for alias,delta in [('cached',0),('uncached',0x40000000),
                            ('logical_flash',-0x1f980000),('flash_alias',0x20680000)]:
            matches=pointer_candidates(main,lo+delta,hi+delta);priority=[]
            for h in matches:
                offset=int(h['offset'],16);site=BASE+offset
                # Triage only. FC can itself be a previous instruction's operand.
                if offset>=2 and main[offset-2]==0xfc:
                    priority.append(dict(site=hex(site),value=h['value']))
                    priority_seen.add(site)
            literals.append(dict(alias=alias,start=hex(lo+delta),end_exclusive=hex(hi+delta),
                raw_match_count=len(matches),fc_prefix_triage=priority,
                nonpriority_matches_not_classified=len(matches)-len(priority)))
        classified=[]
        for hit in hits:
            site=int(hit['site'],16);pc,_,_=CONTAINERS[site]
            classified.append(dict(site=hit['site'],raw_target=hit['target'],encoding=hit['encoding'],
                containing_instruction=instructions[pc],
                classification='Inside reviewed local instruction; alternate-entry CFG not closed'))
        regions.append(dict(start=hex(lo),end_exclusive=hex(hi),bytes=hi-lo,
            decoded_padding_start=hex(block+16),padding_bytes=32752,
            unchanged_zero_header_bytes=16,preserved_ff_prefix_bytes=48,preserved_ff_suffix_bytes=64,
            early_copy_cached_span=['0x60030000','0x600d0800'],
            actual_copy_alias_start=hex(lo+0x40000000),logical_flash_start=hex(lo-0x1f980000),
            raw_literal_scans=literals,relative_local_classification=classified,
            relocated_helper_raw_transfers=len(relocated[len(regions)]),approved_for_placement=False))
    if priority_seen!=set(PRIORITY_CALLS)|set(PRIORITY_SPLIT)|{NUMERIC}:
        raise ValueError('literal triage inventory changed')
    priorities=[]
    for site,(pc,target) in PRIORITY_CALLS.items():
        witness(pc,'call',target)
        priorities.append(dict(site=hex(site),classification='Crosses wide CALL operands and following instruction',
                               instruction=instructions[pc]))
    for site in PRIORITY_SPLIT:
        witness(site-4,'add','-4,sp');witness(site-1,'cmp','15,d0')
        priorities.append(dict(site=hex(site),classification='FC is ADD immediate; candidate spans CMP/branch bytes',
            instruction_addresses=[hex(site-4),hex(site-1)]))
    numeric_w={
        0x60c34b5e:('clr','d0'),0x60c34b5f:('mov','1080868864,d1'),
        0x60c34b65:('call','0x60c3eb6f,[d2,d3,a2],16'),
        0x60c34b6c:('mov','d0,(68,a2)'),0x60c34b6f:('mov','d1,(72,a2)'),
        0x60c3eb6f:('mov','d0,d2'),0x60c3eb70:('mov','d1,d3'),
        0x60c3eb71:('call','0x60c3a4a6,[],0'),0x60c3eb7d:('beq','0x60c3eb9e'),
        0x60c3eb8c:('beq','0x60c3eb9e'),0x60c3eb95:('call','0x600da83c,[a2],12'),
        0x60c3eb9c:('mov','d0,d2'),0x60c3eb9d:('mov','d1,d3'),
        0x60c3eb9e:('mov','d2,d0'),0x60c3eb9f:('mov','d3,d1'),
        0x60c3eba0:('ret','[d2,d3,a2],16')}
    for pc,ins in numeric_w.items():witness(pc,*ins)
    priorities.append(dict(site=hex(NUMERIC),value='0x406cc000',
        classification='Real immediate in D1, paired with D0=0 and stored in parameter record; later meaning unresolved',
        if_interpreted_as_ieee754_binary64=struct.unpack('<d',struct.pack('<II',0,0x406cc000))[0],
        called_wrapper='0x60c3eb6f',record_word_offsets=[68,72],pointer_use_excluded_globally=False))
    return dict(scope=__doc__,decoded_bytes=len(main),instruction_witness_count=len(instructions),
        instruction_witnesses=list(instructions.values()),regions=regions,
        total_proposed_capacity=sum(hi-lo for lo,hi in RANGES),literal_priority_classification=priorities,
        post_copy_seam=dict(address='0x600201fe',original_instruction_bytes=6,resume='0x60020204',
            original_operation='reload D0 from6218d984 before next data copy',
            previous_copy_returned_locally=True,other_cpu_order_proven=False,bootstrap_implemented=False),
        qualified_free_code_regions=[],firmware_modified=False,firmware_built=False,
        target_executed=False,camera_executed=False,hash_checks_performed=False,
        limits=['Only decoded main literal matches and main/known-helper raw relative transfers were scanned.',
            'Nonpriority literal matches and other update components remain unclassified.',
            'Local instruction decoding does not rule out alternate instruction entry or computed addressing.',
            'No DMA, later writes, boot success, execute/cache permission or cross-core ordering proof.',
            'Padding/header shape and source load coverage are capacity evidence, not allocation ownership.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded',type=Path,required=True)
    parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.decoded,args.objdump),indent=2))
