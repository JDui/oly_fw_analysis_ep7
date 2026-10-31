#!/usr/bin/env python3
"""Current-input static alias continuation; no SHA, execution or patching."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import tempfile

from ep7_prepare_input import prepare, BASE
from ep7_request_ownership import require_instruction

WINDOWS = [(0x602a2937,0x602a3116),(0x602a433c,0x602a446d),
           (0x6029e8f1,0x6029e956),(0x6010b2d5,0x6010b3a1),(0x6010bf9f,0x6010c079)]
W = {
    0x602a293f: ('mov', '(0x6223dd54),a2'),
    0x602a294a: ('mov', '(8,a0),a3'),
    0x602a2f9d: ('mov', '(8,a1),a2'),
    0x602a2fa0: ('movbu', '(6,a2),d1'),
    0x602a2fa5: ('bne', '0x602a3018'),
    0x602a2fa7: ('movbu', '(0x6223dd51),d1'),
    0x602a2fad: ('cmp', '1,d1'),
    0x602a2faf: ('bne', '0x602a2fce'),
    0x602a2fb5: ('or', '4,d1'),
    0x602a2fba: ('call', '0x602a302b,[],4'),
    0x602a2fd0: ('movbu', 'd0,(46,a1)'),
    0x602a2fd3: ('movbu', 'd0,(0x6223dd51)'),
    0x602a2fdf: ('mov', '1646518108,a0'),
    0x602a2feb: ('mov', '39,d0'),
    0x602a2fed: ('movhu', 'd0,(0x6223df5c)'),
    0x602a2ff9: ('mov', 'd0,(0x6223df68)'),
    0x602a2fff: ('mov', '1613359345,d0'),
    0x602a3005: ('mov', 'd0,(0x6223df60)'),
    0x602a300b: ('mov', 'a1,(0x6223df64)'),
    0x602a3011: ('call', '0x6010b2d5,[],4'),
    0x602a3064: ('mov', 'a2,(0x6223dd54)'),
    0x602a3084: ('call', '0x6060b54c,[d2,a2],12'),
    0x602a30af: ('mov', '(0x6223dd54),d0'),
    0x602a4342: ('mov', '(0x6223dd54),a3'),
    0x602a43db: ('mov', '(0x6223e2f0),a0'),
    0x602a43e1: ('call', '0x6020b962,[],0'),
    0x602a43f2: ('call', '0x6020b9ff,[],24'),
    0x602a43f9: ('mov', 'd0,a2'),
    0x602a43fb: ('mov', '(a2),a0'),
    0x602a43fd: ('call', '0x602a3052,[a2],20'),
    0x602a4402: ('mov', 'a2,a0'),
    0x602a4403: ('call', '0x60022732,[],4'),
    0x6029e8f6: ('mov', '(8,a0),a2'),
    0x6029e8f9: ('mov', '(12,a0),a0'),
    0x6029e93e: ('mov', 'a2,a0'),
    0x6029e940: ('mov', '(a0),d1'),
    0x6029e942: ('or', '4,d1'),
    0x6029e945: ('mov', 'd1,(a0)'),
    0x6029e947: ('call', '0x602a302b,[],4'),
    0x6029e94c: ('clr', 'd0'),
    0x6029e94d: ('movbu', 'd0,(0x6223dd51)'),
    0x6010b2e5: ('add', '-7,d0'),
    0x6010b2e7: ('asl2', 'd0'),
    0x6010b2e8: ('mov', '1612353944,a1'),
    0x6010b2ee: ('mov', '(d0,a1),a1'),
    0x6010b2f0: ('jmp', '(a1)'),
    0x6010b351: ('call', '0x6010bf9f,[d2],8'),
    0x6010bfc1: ('mov', '1611710434,d0'),
    0x6010bfc7: ('mov', 'd0,(0x621d9e68)'),
    0x6010bfcd: ('mov', 'a0,(0x621d9e6c)'),
    0x6010bfd9: ('call', '0x6011209b,[a2],8'),
    0x6010bfe8: ('mov', '(8,a2),d3'),
    0x6010bff2: ('mov', 'd3,a0'),
    0x6010bff4: ('mov', '(12,a0),a3'),
    0x6010c04c: ('mov', 'd3,a0'),
    0x6010c04e: ('inc4', 'a0'),
    0x6010c04f: ('mov', '(a0),d1'),
    0x6010c050: ('cmp', '0,d1'),
    0x6010c052: ('beq', '0x6010c05b'),
    0x6010c054: ('mov', '(a0),a1'),
    0x6010c056: ('mov', 'd3,a0'),
    0x6010c059: ('calls', '(a1)'),
}


def inspect(stock, objdump, windows=WINDOWS, witnesses=W, data_checks=(), observe=None, observe_data=None):
    version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0]
    checked=0
    unknown=[]
    with tempfile.TemporaryDirectory(prefix='ep7-async-alias-') as temp:
        out=Path(temp)/'input'
        identity=prepare(stock,out)
        image=out/'main.decoded.bin'
        data=image.read_bytes()
        table=0x601a9198+(39-7)*4
        if struct.unpack_from('<I',data,table-BASE)[0]!=0x6010b351:
            raise ValueError('type39 dispatch row mismatch')
        for address,fmt,expected in data_checks:
            if struct.unpack_from(fmt,data,address-BASE)!=expected:
                raise ValueError(f'data row mismatch at {address:#x}')
        if observe_data is not None:
            observe_data(data)
        for start,stop in windows:
            asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z',
                '--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',
                f'--stop-address={stop:#x}',str(image)],text=True)
            for address,(mn,op) in witnesses.items():
                if start<=address<stop:
                    require_instruction(asm,address,mn,op)
                    checked+=1
            if observe is not None:
                observe(start,stop,asm)
            for line in asm.splitlines():
                if '\tudf' in line:
                    unknown.append(line.split(':',1)[0].strip())
    if checked!=len(witnesses):raise ValueError('uncovered witness')
    return dict(scope=__doc__,objdump_version=version,input_structure=identity,
        checked_instructions=checked,type39_dispatch_row=hex(table),
        async_descriptor='0x6223df5c',node_field_offset=8,callback='0x6029e8f1',
        lower_request='0x621d9e64',lower_callback='0x6010bfe2',
        wrapper_only_free='0x602a4403',unknown_instruction_addresses=unknown,
        callback_scheduling_and_cancellation_proven=False,controller_exclusion_proven=False,
        complete_lifetime_closure=False,hash_checks_performed=False,
        firmware_executed=False,firmware_modified=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True)
    parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.stock,args.objdump),indent=2))
