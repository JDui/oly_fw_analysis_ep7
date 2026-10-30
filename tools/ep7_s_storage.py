#!/usr/bin/env python3
"""Exact E-P7 1100 read-only S storage and recall lifecycle evidence. Not a patch or durability test."""
import argparse,json,struct,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE,require
from oly_container import parse,sha256
from ep7_gui_bridge import require_instruction
IDS=tuple(range(927,963))+tuple(range(1655,1667))

def filters(main):
    result=[]
    for i in range(70):
        addr=0x604a8420+12*i
        mode,sub,ptr,count,pad=struct.unpack_from('<HHIHH',main,addr-BASE)
        require(mode!=0 and count in (1337,1338) and pad==0,'filter descriptor mismatch')
        entries=[struct.unpack_from('<HBB',main,ptr-BASE+4*j) for j in range(count)]
        selected=[r for r in entries if r[0] in IDS]
        require(len(selected)==48 and set(r[0] for r in selected)==set(IDS),'S IDs missing/duplicated')
        require(all(part==0 for _,part,_ in selected),'S filter part changed')
        result.append(dict(mode=mode,submode=sub,table=hex(ptr),entry_count=count,selected_S_count=48,selected_part=0,sha256=sha256(main[ptr-BASE:ptr-BASE+4*count])))
    require(struct.unpack_from('<H',main,0x604a8768-BASE)[0]==0,'filter sentinel mismatch')
    return result

def tables(main):
    profiles=[]
    for i,base in enumerate((927,939,951,1655)):
        entries=[struct.unpack_from('<HH',main,0x604d6c14-BASE+4*(base+j)) for j in range(12)]
        require(entries==[(0xf6fa,12*i+j) for j in range(12)],'profile typed map changed')
        profiles.append(dict(profile=i+1,first_property=base,record='0xf6fa',indices=list(range(12*i,12*i+12))))
    require([struct.unpack_from('<HH',main,0x604d6c14-BASE+4*i) for i in range(915,927)]==[(0xf6ea,i) for i in range(12)],'effective map changed')
    headers=[]
    for address,key,count in [(0x600bddd0,0xf6ea,12),(0x600bddec,0xf6fa,48),(0x600bde50,0xf709,4),(0x60097da0,0x85d4,32040),(0x600b74f4,0x8b54,1780),(0x600b90c8,0x8b64,3560)]:
        require(struct.unpack_from('<HH',main,address-BASE)==(key,count),'record header mismatch')
        headers.append(dict(address=hex(address),key=hex(key),count=count,width_bytes=key&3 or 4))
    records={}
    for i in range(439):
        address=0x604317ac+60*i
        row=struct.unpack_from('<15I',main,address-BASE)
        pid=row[0]&65535
        if pid in IDS:
            require(pid not in records,'duplicate S callback descriptor')
            records[pid]=(row[6],row[12])
    for i,base in enumerate((927,939,951,1655)):
        pair=((0x602b5e91,0x602b9288),(0x602b5eaa,0x602b92a6),(0x602b5ec3,0x602b92c4),(0x602b5edc,0x602b92e2))[i]
        require(all(records.get(base+j)==pair for j in range(12)),'profile callback changed')
    return dict(profiles=profiles,effective=dict(first_property=915,record='0xf6ea',count=12),rom_headers=headers,filter_rows=filters(main),S_callback_count=len(records),part1_ownership_qualified=False)

# Exact instruction witnesses reviewed against the pinned stock image.
WINDOWS={'api_dispatch': (1613439543, 1613439596), 'property_map': (1613544763, 1613544855), 'property_index': (1613545355, 1613545380), 'active_read_write': (1613545590, 1613545721), 'bank_copy': (1613545470, 1613545590), 'reset_both_parts': (1613469231, 1613469287), 'reset_bank_copy': (1613469339, 1613469356), 'filter_read': (1613469637, 1613469738), 'filter_write': (1613469738, 1613469840), 'refresh_callbacks': (1613454993, 1613455093), 'refresh_entry': (1613465878, 1613465900), 'effective_S_writes': (1613466155, 1613466311), 'typed_read_width': (1611001789, 1611001861), 'typed_write_width': (1611000543, 1611000597)}
WITNESSES={1613439549: ('add', '1615051756,d0'), 1613439574: ('add', '1615051780,d0'), 1613544778: ('asl2', 'd2'), 1613544779: ('mov', '1615686676,a0'), 1613544785: ('movhu', '(d2,a0),d0'), 1613545375: ('movhu', '(2,a0),d0'), 1613545610: ('udf00', '3538,d1'), 1613545615: ('udf00', '1769,d2'), 1613545622: ('mov', '34260,d0'), 1613545657: ('udf00', '1769,d1'), 1613545663: ('mov', '35684,d0'), 1613545669: ('call', '0x602cca80,[],4'), 1613545699: ('udf00', '1769,d1'), 1613545705: ('mov', '35684,d0'), 1613545711: ('call', '0x6005ea22,[d2,d3,a2,a3],40'), 1613545492: ('call', '0x602cca80,[],4'), 1613545512: ('call', '0x6005ea22,[d2,d3,a2,a3],40'), 1613545521: ('cmp', '3538,d2'), 1613545533: ('udf00', '3538,d3'), 1613545550: ('call', '0x602cca80,[],4'), 1613545572: ('call', '0x6005ea22,[d2,d3,a2,a3],40'), 1613545581: ('cmp', '3538,d2'), 1613469233: ('call', '0x602b9bad,[d2,d3,a2,a3],20'), 1613469265: ('call', '0x602cc0d0,[d2],8'), 1613469275: ('cmp', '2,d2'), 1613469281: ('cmp', '1768,d3'), 1613469342: ('call', '0x602cc03a,[d2,d3],12'), 1613469352: ('cmp', '9,d2'), 1613469645: ('mov', '1615496224,a0'), 1613469690: ('movbu', '(2,a3),d1'), 1613469693: ('call', '0x602cc0a7,[d2],8'), 1613469703: ('call', '0x602cc122,[],4'), 1613469746: ('mov', '1615496224,a0'), 1613469791: ('call', '0x602cc0fc,[],4'), 1613469802: ('movbu', '(2,a3),d1'), 1613469805: ('call', '0x602cc0d0,[d2],8'), 1613455004: ('cmp', '54,d1'), 1613455009: ('call', '0x602b8916,[d2],164'), 1613455029: ('cmp', '55,d1'), 1613455034: ('call', '0x602b8916,[d2],164'), 1613455054: ('cmp', '56,d1'), 1613455059: ('call', '0x602b8916,[d2],164'), 1613455079: ('cmp', '64,d1'), 1613455084: ('call', '0x602b8916,[d2],164'), 1613465883: ('call', '0x602b7b71,[d2,d3,a2,a3],172'), 1613466160: ('mov', '915,a0'), 1613466163: ('call', '0x602b2250,[d2,a2],12'), 1613466303: ('mov', '926,a0'), 1613466306: ('call', '0x602b2250,[d2,a2],12'), 1611001807: ('cmp', '4,d3'), 1611001817: ('exthu', 'd2'), 1611001819: ('movhu', '(d2,a0),d0'), 1611001821: ('exth', 'd0'), 1611001843: ('exthu', 'd2'), 1611001845: ('mov', '(d2,a0),d0'), 1611000559: ('and', '7,d2'), 1611000562: ('cmp', '4,d2'), 1611000572: ('asl2', 'd3'), 1611000573: ('mov', 'a2,(d3,a3)'), 1611000581: ('add', 'd3,d3'), 1611000582: ('movhu', 'd0,(d3,a3)')}

LIFECYCLE_WINDOWS = {'recall_active_selection': (1613444041, 1613444111), 'recall_gate': (1613444277, 1613444317), 'recall_commit_release': (1613444366, 1613444508), 'staging_context_copy': (1613546476, 1613546597), 'typed_commit_loop': (1613546816, 1613546880), 'staging_sync': (1613547032, 1613547057), 'write_inhibit': (1613547206, 1613547224), 'ordinary_setter_gate': (1613544536, 1613544564)}
LIFECYCLE_WITNESSES = {1613444047: ('call', '0x602cc076,[d2,d3],12'), 1613444067: ('call', '0x602cc076,[d2,d3],12'), 1613444075: ('clr', 'd0'), 1613444076: ('call', '0x602cbffe,[d2,d3],12'), 1613444087: ('call', '0x602b97c5,[d2,d3,a2,a3],24'), 1613444093: ('bne', '0x602b3406'), 1613444100: ('bne', '0x602b340f'), 1613444104: ('call', '0x602cbffe,[d2,d3],12'), 1613444287: ('bne', '0x602b34dd'), 1613444296: ('bne', '0x602b34dd'), 1613444305: ('bne', '0x602b34dd'), 1613444312: ('bne', '0x602b34dd'), 1613444314: ('jmp', '0x602b35a0'), 1613444371: ('call', '0x602cc122,[],4'), 1613444384: ('call', '0x602cc122,[],4'), 1613444391: ('mov', '1,d0'), 1613444393: ('call', '0x602cc6c6,[],0'), 1613444400: ('call', '0x602cc3ec,[d2,d3,a2,a3],20'), 1613444407: ('call', '0x602cc4d2,[],4'), 1613444419: ('call', '0x602b6753,[d2],8'), 1613444430: ('call', '0x602b6937,[],8'), 1613444435: ('mov', '1,d0'), 1613444437: ('mov', '3200,d1'), 1613444440: ('call', '0x602b322b,[d2,d3,a2,a3],36'), 1613444445: ('mov', '1,d0'), 1613444447: ('call', '0x602b1de2,[d2,d3,a2],16'), 1613444471: ('call', '0x602cc540,[d2,d3,a2,a3],36'), 1613444478: ('mov', 'd0,d2'), 1613444479: ('call', '0x602cc618,[],4'), 1613444486: ('clr', 'd0'), 1613444487: ('call', '0x602cc6c6,[],0'), 1613444494: ('clr', 'd0'), 1613444495: ('call', '0x602b1de2,[d2,d3,a2],16'), 1613444500: ('exthu', 'd2'), 1613444501: ('mov', 'd2,d0'), 1613444502: ('mov', 'a2,a0'), 1613444503: ('call', '0x602b1ea0,[d3,a2,a3],20'), 1613546476: ('mov', '1646614608,d2'), 1613546581: ('mov', '(0x62253598),a1'), 1613546587: ('mov', '7076,d0'), 1613546590: ('call', '0x47001052,[d2,d3,a2,a3],28'), 1613546823: ('call', '0x602cbc13,[d2,d3,a2],20'), 1613546833: ('add', '1646605724,a3'), 1613546840: ('cmp', 'd1,d0'), 1613546841: ('beq', '0x602cc56f'), 1613546855: ('movhu', 'd3,(d0,a0)'), 1613546865: ('call', '0x602cbc74,[d2,d3,a2],20'), 1613546874: ('cmp', '1769,d2'), 1613546878: ('blt', '0x602cc546'), 1613547032: ('mov', '(0x62253598),a0'), 1613547038: ('mov', '1646614608,a1'), 1613547044: ('mov', '7076,d0'), 1613547047: ('call', '0x47001052,[d2,d3,a2,a3],28'), 1613547206: ('movbu', 'd0,(0x62257b04)'), 1613547215: ('movbu', '(0x62257b04),d0'), 1613544543: ('call', '0x602cc6cf,[],0'), 1613544549: ('cmp', '1,d0'), 1613544551: ('beq', '0x602cbc71'), 1613544556: ('call', '0x602cbc74,[d2,d3,a2],20')}
WINDOWS.update(LIFECYCLE_WINDOWS)
WITNESSES.update(LIFECYCLE_WITNESSES)
def lifecycle_facts():
    return dict(
        conditional_path=True,
        ordered_call_sites=[hex(a) for a in (0x602b33ec,0x602b33f7,0x602b3408,0x602b3529,0x602b3530,0x602b3577,0x602b357f,0x602b3587,0x602b358f,0x602b3597)],
        inhibit_byte='0x62257b04',
        ordinary_setter_gate='0x602cbc5f',
        direct_inner_commit='0x602cc571',
        main_commit_property_count=1769,
        changed_id_list_record='0x602cc567',
        postcallback='0x602b1ea0',
        limitations=[
            'Addresses establish static ordering on the admitted recall path, not unconditional execution for every entry.',
            'The inhibit byte is not proven to provide mutual exclusion or a durable transaction.',
            'Transitive callbacks and additional commit ranges are not fully qualified.',
            'ROM record headers are not fully joined to runtime bank registration.',
            'No physical NVM flush, backup integrity, power-cycle durability, or part-1 ownership qualification.',
            'No H/L hook, image-lifetime consistency, or flash-ready patch is established.'
        ])

def inspect(raw,objdump):
    identity=audit(raw)
    main=parse(raw)[0].payload
    report=tables(main)
    report["recall_lifecycle"]=lifecycle_facts()
    version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0]
    windows={}
    with tempfile.TemporaryDirectory(prefix='ep7-storage-') as tmp:
        image=Path(tmp)/'main.bin';image.write_bytes(main)
        for name,(start,end) in WINDOWS.items():
            assembly=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={end:#x}',str(image)],text=True)
            addresses=[a for a in WITNESSES if start<=a<end]
            for a in addresses:require_instruction(assembly,a,*WITNESSES[a])
            windows[name]=dict(start=hex(start),end_exclusive=hex(end),sha256=sha256(main[start-BASE:end-BASE]),witness_count=len(addresses))
    return dict(scope='Exact stock static S schema/filter/refresh and conditional recall lifecycle evidence; not free-space or durability qualification',source_sha256=identity['source_sha256'],facts=report,windows=windows,instruction_witness_count=len(WITNESSES),objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),camera_accessed=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True);a=p.parse_args()
    print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
