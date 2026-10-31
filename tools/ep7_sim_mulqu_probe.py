#!/usr/bin/env python3
"""Pin the unsigned immediate multiplication discrepancy without a board model.

Manufacturer MULQIU requires zero extension for imm8/imm16. Check low/high product
and defined N/Z flags, retain the signed sibling, and leave C/V unspecified.
"""
import argparse
import json
from pathlib import Path

from penf_emulator import Region,execute
from ep7_candidate_startup_sim import require


CASES = [('native_class_stride',bytes.fromhex('f914d8'),1,216,False),
         ('unsigned8_high_word',bytes.fromhex('f91480'),0xffffffff,128,False),
         ('unsigned16_high_word',bytes.fromhex('fb140080'),0xffffffff,32768,False),
         ('low_immediate_unchanged',bytes.fromhex('f9147f'),3,127,False),
         ('zero_product',bytes.fromhex('f914ff'),0,255,False),
         ('signed_sibling_unchanged',bytes.fromhex('f900d8'),1,-40,True)]


def inspect(engine,expect_legacy=False):
    rows=[]
    for name,code,value,immediate,is_signed in CASES:
        result=execute([Region('instruction',0x19000000,code,'rx')],
            dict(pc=0x19000000,sp=0x19010000,d0=value,psw=0x800,mdrq=0x12345678),
            0x19000000+len(code),limit=2,trace_limit=2,timeout=10,engine=engine,record_hashes=False)
        require(result['status']=='returned' and result['completed']==1 and result['fault'] is None,
                'single instruction stopped: '+name)
        expected=(value*immediate)&0xffffffffffffffff
        regs=result['registers']
        actual=(regs['mdrq']<<32)|regs['d0']
        matches=actual==expected
        wanted=not (expect_legacy and name in ('native_class_stride','unsigned8_high_word','unsigned16_high_word'))
        require(matches==wanted,'unexpected immediate multiply result: '+name)
        require(bool(regs['psw']&2)==bool(regs['d0']&0x80000000) and
                bool(regs['psw']&1)==(regs['d0']==0),'defined N/Z flags inconsistent: '+name)
        rows.append(dict(name=name,opcode=code.hex(),input=value,immediate=immediate,signed=is_signed,
                         expected_product=hex(expected),actual_product=hex(actual),
                         product_matches=matches,defined_nz_flags_consistent=True))
    return dict(scope=__doc__,engine=str(engine),cases=rows,all_assertions_passed=True,
        expectation='known_sign_extension_defect' if expect_legacy else 'manufacturer_zero_extension',
        multiplication_passed=not expect_legacy,hash_checks_performed=False,hardware_executed=False,
        manual='https://www.manualslib.com/manual/119167/Panasonic-Mn103001g-F01k.html?page=70',
        limits=['Only immediate multiplication and its defined output flags are tested; this is not general CPU, pipeline timing or silicon acceptance.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--expect-legacy',action='store_true')
    args=parser.parse_args()
    print(json.dumps(inspect(args.engine,args.expect_legacy),indent=2))
