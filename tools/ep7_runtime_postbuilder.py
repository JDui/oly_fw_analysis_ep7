#!/usr/bin/env python3
"""Current postbuilder seam witnesses reused without running the legacy hash guard."""
import argparse,ast,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'prototypes/ep7_volatile_hl/target/postbuilder/seam_probe.py'
def witnesses():
    values={}
    for node in ast.parse(SOURCE.read_text()).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in {'WINDOWS','W'}:values[name]=ast.literal_eval(node.value)
    if set(values)!={'WINDOWS','W'}:raise ValueError('legacy seam witness declarations changed')
    return values
def inspect(stock,objdump):
    data=witnesses();evidence=inspect_windows(stock,objdump,data['WINDOWS'],data['W'])
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],input_structure=evidence['input_structure'],
        witness_source=str(SOURCE.relative_to(ROOT)),checked_instructions=evidence['checked_instructions'],
        hook_call='0x603b02d9',stock_builder='0x603b0068',continuation='0x603b02de',
        native_save=['d2','d3','a2','a3'],native_frame_bytes=96,setup_request_offset=4,setup_output_offset=12,
        continuation_replaces_condition_flags=True,extra_native_builder_depth=96,
        stack_headroom_proved=False,hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
