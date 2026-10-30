#!/usr/bin/env python3
"""Exact E-P7 1100 read-only capture snapshot evidence; not an atomicity or race proof."""
import argparse,json,struct,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE,require
from oly_container import parse,sha256
from ep7_gui_bridge import require_instruction

def tables(main):
    mappings={111:(0x9481,0),211:(0x9d11,0),908:(0xf6b1,0),973:(0xf731,0)}
    for pid,expected in mappings.items():
        require(struct.unpack_from('<HH',main,0x604d6c14-BASE+4*pid)==expected,'mode/profile typed map mismatch')
    require(struct.unpack_from('<3I',main,0x60078968-BASE)==(0x6005c8cc,0x60067100,0x60067100),'address dispatch entries changed')
    return dict(mode_profile_map={str(pid):[hex(key),index] for pid,(key,index) in mappings.items()},
        capture_mode_offset=24053,capture_selector_offset=24083,capture_S_offset=24058,
        sequential_S_reads=12,atomicity_proven=False,actual_race_demonstrated=False,
        admission_candidate='0x602a86b7',hook_implemented=False,
        limitations=[
            'No spanning lock identified within reviewed windows; not a global no-lock claim.',
            'Runtime scheduler/writer serialization and address-dispatch selector range remain unqualified.',
            'Rawmode 11 is not public mode 54; selector range/conversion are not established by this probe.',
            'Candidate admission point supplies neither spare storage nor coherent generation/lifetime ownership.'
        ])

WINDOWS={'population_entry': (1613397664, 1613397680), 'template_copy': (1613758549, 1613758568), 'mode_profile_S': (1613399406, 1613399735), 'getter': (1611000177, 1611000211), 'registry': (1610996004, 1610996103), 'typed_reader': (1611001789, 1611001861), 'immediate_caller': (1613382765, 1613382842), 'registry_helper': (1613347876, 1613347979), 'address_dispatch': (1610991820, 1610991842)}
WITNESSES={1613397664: ('call', '0x6029b9d1,[],24'), 1613397671: ('mov', 'a0,d3'), 1613397673: ('call', '0x60300055,[],0'), 1613758549: ('mov', '1646626860,a1'), 1613758555: ('mov', '-6833,d1'), 1613758559: ('mov', '(a1),d0'), 1613758561: ('mov', 'd0,(a0)'), 1613758564: ('lne', ''), 1613399406: ('mov', '38017,d0'), 1613399412: ('mov', '0,a0'), 1613399414: ('clr', 'd1'), 1613399415: ('call', '0x6005e971,[d2,d3],12'), 1613399422: ('mov', '24053,a2'), 1613399425: ('add', 'd3,a2'), 1613399427: ('movbu', 'd0,(a2)'), 1613399429: ('extbu', 'd0'), 1613399430: ('cmp', '6,d0'), 1613399432: ('bne', '0x602a859c'), 1613399434: ('mov', '40209,d0'), 1613399440: ('mov', '0,a0'), 1613399442: ('clr', 'd1'), 1613399443: ('call', '0x6005e971,[d2,d3],12'), 1613399450: ('movbu', 'd0,(a2)'), 1613399452: ('movbu', '(a2),d0'), 1613399454: ('cmp', '11,d0'), 1613399456: ('bne', '0x602a85aa'), 1613399458: ('mov', '63153,d0'), 1613399464: ('bra', '0x602a85b4'), 1613399466: ('cmp', '12,d0'), 1613399468: ('bne', '0x602a85c4'), 1613399470: ('mov', '63281,d0'), 1613399476: ('mov', '0,a0'), 1613399478: ('clr', 'd1'), 1613399479: ('call', '0x6005e971,[d2,d3],12'), 1613399486: ('mov', 'd3,a0'), 1613399488: ('movbu', 'd0,(24083,a0)'), 1613399492: ('mov', '63210,d0'), 1613399498: ('mov', '0,a0'), 1613399500: ('clr', 'd1'), 1613399501: ('call', '0x6005e971,[d2,d3],12'), 1613399508: ('mov', '24058,a2'), 1613399511: ('add', 'd3,a2'), 1613399513: ('movhu', 'd0,(a2)'), 1613399515: ('mov', '63210,d0'), 1613399521: ('mov', '0,a0'), 1613399523: ('mov', '1,d1'), 1613399525: ('call', '0x6005e971,[d2,d3],12'), 1613399532: ('movhu', 'd0,(2,a2)'), 1613399535: ('mov', '63210,d0'), 1613399541: ('mov', '0,a0'), 1613399543: ('mov', '2,d1'), 1613399545: ('call', '0x6005e971,[d2,d3],12'), 1613399552: ('movhu', 'd0,(4,a2)'), 1613399555: ('mov', '63210,d0'), 1613399561: ('mov', '0,a0'), 1613399563: ('mov', '3,d1'), 1613399565: ('call', '0x6005e971,[d2,d3],12'), 1613399572: ('movhu', 'd0,(6,a2)'), 1613399575: ('mov', '63210,d0'), 1613399581: ('mov', '0,a0'), 1613399583: ('mov', '4,d1'), 1613399585: ('call', '0x6005e971,[d2,d3],12'), 1613399592: ('movhu', 'd0,(8,a2)'), 1613399595: ('mov', '63210,d0'), 1613399601: ('mov', '0,a0'), 1613399603: ('mov', '5,d1'), 1613399605: ('call', '0x6005e971,[d2,d3],12'), 1613399612: ('movhu', 'd0,(10,a2)'), 1613399615: ('mov', '63210,d0'), 1613399621: ('mov', '0,a0'), 1613399623: ('mov', '6,d1'), 1613399625: ('call', '0x6005e971,[d2,d3],12'), 1613399632: ('movhu', 'd0,(12,a2)'), 1613399635: ('mov', '63210,d0'), 1613399641: ('mov', '0,a0'), 1613399643: ('mov', '7,d1'), 1613399645: ('call', '0x6005e971,[d2,d3],12'), 1613399652: ('movhu', 'd0,(14,a2)'), 1613399655: ('mov', '63210,d0'), 1613399661: ('mov', '0,a0'), 1613399663: ('mov', '8,d1'), 1613399665: ('call', '0x6005e971,[d2,d3],12'), 1613399672: ('movhu', 'd0,(16,a2)'), 1613399675: ('mov', '63210,d0'), 1613399681: ('mov', '0,a0'), 1613399683: ('mov', '9,d1'), 1613399685: ('call', '0x6005e971,[d2,d3],12'), 1613399692: ('movhu', 'd0,(18,a2)'), 1613399695: ('mov', '63210,d0'), 1613399701: ('mov', '0,a0'), 1613399703: ('mov', '10,d1'), 1613399705: ('call', '0x6005e971,[d2,d3],12'), 1613399712: ('movhu', 'd0,(20,a2)'), 1613399715: ('mov', '63210,d0'), 1613399721: ('mov', '0,a0'), 1613399723: ('mov', '11,d1'), 1613399725: ('call', '0x6005e971,[d2,d3],12'), 1613399732: ('movhu', 'd0,(22,a2)'), 1611000179: ('cmp', '0,a0'), 1611000181: ('bne', '0x6005e987'), 1611000184: ('call', '0x6005d924,[d2],20'), 1611000196: ('mov', '(4,a0),a0'), 1611000203: ('call', '0x6005efbd,[d2,d3],12'), 1610996004: ('movhu', '(0xa26ffa84),d1'), 1610996012: ('asr', '4,d2'), 1610996017: ('beq', '0x6005d947'), 1610996026: ('add', '-1569686904,a0'), 1610996045: ('add', '-1569719672,a0'), 1610996056: ('bne', '0x6005d984'), 1611001791: ('call', '0x6005c8cf,[],4'), 1611001819: ('movhu', '(d2,a0),d0'), 1611001821: ('exth', 'd0'), 1613382765: ('mov', 'a0,a3'), 1613382766: ('mov', '(a3),d0'), 1613382767: ('call', '0x6029bc24,[d2],28'), 1613382774: ('movhu', '(0x6223e33c),d0'), 1613382780: ('cmp', '0,d0'), 1613382782: ('bne', '0x602a44ba'), 1613382784: ('call', '0x602a3116,[d2,a2],28'), 1613382790: ('cmp', '0,a2'), 1613382792: ('beq', '0x602a44ba'), 1613382794: ('call', '0x602a3204,[d2,a2],16'), 1613382800: ('cmp', '0,d0'), 1613382802: ('beq', '0x602a449c'), 1613382812: ('mov', '(0x6223d414),a1'), 1613382818: ('mov', '(a1),d0'), 1613382819: ('call', '0x602a7ea0,[d2,d3,a2,a3],20'), 1613382824: ('mov', '(0x6223d414),a1'), 1613382830: ('mov', '1646515228,a0'), 1613382836: ('clr', 'd0'), 1613382837: ('call', '0x602a8dbd,[d2,d3,a2,a3],48'), 1613347949: ('call', '0x6005168d,[d2,d3,a2],40'), 1613347957: ('call', '0x6029bf01,[a2],8'), 1613347969: ('call', '0x60051762,[d2,d3],36'), 1613347976: ('ret', '[d2],28'), 1610991823: ('mov', '(0x8050),d0'), 1610991826: ('mov', '1611106664,a1'), 1610991833: ('mov', '(d0,a1),a1'), 1610991837: ('calls', '(a1)')}
def inspect(raw,objdump):
    identity=audit(raw)
    main=parse(raw)[0].payload
    report=tables(main)
    version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0]
    windows={}
    with tempfile.TemporaryDirectory(prefix='ep7-capture-snapshot-') as tmp:
        image=Path(tmp)/'main.bin';image.write_bytes(main)
        for name,(start,end) in WINDOWS.items():
            assembly=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={end:#x}',str(image)],text=True)
            addresses=[a for a in WITNESSES if start<=a<end]
            for a in addresses:require_instruction(assembly,a,*WITNESSES[a])
            windows[name]=dict(start=hex(start),end_exclusive=hex(end),sha256=sha256(main[start-BASE:end-BASE]),witness_count=len(addresses))
    return dict(scope='Exact stock static capture mode/profile and twelve sequential S reads; atomicity not established',source_sha256=identity['source_sha256'],facts=report,windows=windows,instruction_witness_count=len(WITNESSES),objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),camera_accessed=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True);a=p.parse_args()
    print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
