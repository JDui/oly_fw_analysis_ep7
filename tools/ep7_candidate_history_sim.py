#!/usr/bin/env python3
"""Execute the original no-history scaling fallback on an explicit cold scenario.

Only the two-byte selector and four-byte mode assume witnessed startup BSS.
No active history record is produced; all its other payload bytes stay unmapped.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_device_state_sim import admit
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_format_record_sim import record_context


def history_context(directory, prefix, engine, without_cold_fallback=False):
    upstream, contexts = record_context(directory,prefix,engine)
    rows, outputs = [], []
    for index,context in enumerate(contexts['cases']):
        machine = context['machine']
        capture = machine.read(CAPTURE,SIZE)
        require(machine.read(0x60020068,12)==bytes.fromhex('fccd886879a2fccc00af1c62') and
                0x621caf00<=0x6273104a<0x6273104c<=0x62796888 and
                machine.read(0x6030b752,6)==bytes.fromhex('fcaf4a1073a2') and
                machine.read(0x60309e64,11)==bytes.fromhex('fb15d403fcc1981073a266'),
                'history selector BSS or native980-byte record selection changed')
        admit(machine,'history_selector_conditional_cold_BSS',0xa273104a,bytes(2))
        selected = machine.resume(context['producer_result']['registers'],0x60409ecb,
            full_trace=True,limit=20000,breakpoints=[0x60061808,0x6040e126])
        fault=selected['fault'] or {}
        require(selected['status']=='memory_fault' and
                (fault.get('pc'),fault.get('address'),fault.get('size'),fault.get('access'))==
                (0x60304091,0xa2731148,4,'read'),
                'native history selector did not stop at the original mode-field read')
        pointer_writes = [dict(pc=hex(r['pc']),destination=hex(r['a2']),pointer=hex(r['d1']))
                          for r in selected['trace'] if r['pc']==0x60309e6e]
        require(len(pointer_writes)==1 and pointer_writes[0]['pointer']=='0xa2731098' and
                machine.read(int(pointer_writes[0]['destination'],16),4)==struct.pack('<I',0xa2731098),
                'native history selector did not publish exactly the cold slot0 pointer')
        stages=[stage('native_cold_history_selection',selected)]
        result,returns,copies=selected,[],[]
        if not without_cold_fallback:
            witnesses=[(0x6030408b,bytes.fromhex('fcce00000100fa04b000a501c805ccc800')),
                       (0x60304161,bytes.fromhex('88dfa020')),
                       (0x6030c36b,bytes.fromhex('5c1cfa004c015c18fa10b000'))]
            require(all(machine.read(pc,len(code))==code for pc,code in witnesses) and
                    not any(r.address<0xa2731098+5*980 and 0xa2731098<r.address+len(r.data)
                            for r in machine.regions.values()),
                    'native scaling fallback, mode producer or unmapped history boundary changed')
            # Original BSS alias range contains this word. Its cold value only
            # selects the existing unity fallback; it is not an active record.
            admit(machine,'history_mode_conditional_cold_BSS',0xa2731148,bytes(4),'r')
            result=machine.resume(selected['registers'],0x60409ecb,
                full_trace=True,limit=80000,breakpoints=[0x60061808,0x6040e126])
            returns=[r['d0'] for r in result['trace'] if r['pc']==0x60664cd5]
            require(returns and all(value==65536 for value in returns),
                    'original cold history path did not return its native16.16 unity scale')
            fault=result['fault'] or {}
            require(result['status']=='memory_fault' and
                    (fault.get('pc'),fault.get('address'),fault.get('size'),fault.get('access'))==
                    (0x47001070,0xa271ca80,4,'read') and result['registers']['mdr']==0x601f6916,
                    'native cold snapshot did not stop at the unknown16-byte cache')
            copies=[dict(source=hex(r['a1']),destination=hex(r['a0']),bytes=r['d0'])
                    for r in result['trace'] if r['pc']==0x47001052]
            require(len(copies)==1 and copies[0]['source']=='0xa271ca80' and copies[0]['bytes']==16,
                    'original cache getter did not request exactly16 bytes')
            stages.append(stage('native_unpublished_history_scaling_fallback',result))
        require(machine.read(CAPTURE,SIZE)==capture,'history dependency trace changed capture')
        rows.append(dict(gpio80_input_bit4=index,cases=stages,
            pointer_writes=pointer_writes,
            conditional_BSS_selector_bytes=2,conditional_BSS_mode_bytes=0 if without_cold_fallback else 4,
            native_unity_scale_returns=returns,active_history_record_produced=False,
            mode_producer=dict(entry='0x6030c095',read_pc='0x6030c36d',source_offset=332,
                store_pc='0x6030c373',destination_offset=176,executed=False),
            native_cache_copy_requests=copies,
            frontier=dict(status=result['status'],fault=result['fault'],
                pc=hex(result['registers']['pc']),native_return_pc=hex(result['registers']['mdr'])),
            other_history_payload_bytes_unmapped=True,capture_unchanged=True,
            snapshot_producer_completed=result['status']=='returned'))
        outputs.append(dict(context,producer_result=result))
    report=dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),cases=rows,
        native_instructions=sum(c['completed'] for r in rows for c in r['cases']),
        maximum_observed_new_stack_depth=max(c['stack_depth_from_call_sp'] for r in rows for c in r['cases']),
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=[f'Only {2 if without_cold_fallback else 6} named bytes use the witnessed startup BSS clear plus cached/uncached alias condition; no active history record, valid-bit publication or camera scale is claimed.',
                f'The original mode-field producer6030c095 and success-only index stores6030992a/60309a48 remain unexecuted. All other{4900 if without_cold_fallback else 4896} history payload bytes are unmapped.',
                'The native16-byte cache copy stops on its first source read. Its original writer601f66f7 receives a parameter block from60293a65; that enclosing producer and source object are not executed.',
                'Geometry consumer and capture population remain paused; complete task ordering, resource ownership, updater and recovery remain unproven.'])
    return report,dict(upstream=contexts,cases=outputs)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--without-cold-fallback',action='store_true')
    args=parser.parse_args()
    print(json.dumps(history_context(args.candidate,args.tool_prefix,args.engine,args.without_cold_fallback)[0],indent=2))
