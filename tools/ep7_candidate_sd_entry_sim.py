#!/usr/bin/env python3
"""E-P7 native SD filename selection and message route, with explicit filesystem boundaries.

No SD media, camera, flash backend or physical boot trigger is exercised.
The package has already been checked by the separate shared-updater probe.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import BASE, CALLER, STACK, STACK_BYTES, SP, Machine, require
from ep7_sim_probe import brief
from penf_boot_emulator import BootState, HOOK_RETURN
from penf_emulator import Region, execute

CLIENT, WORKER, UPDATER = 0x60c95bab, 0x60c96030, 0x60c964c1
SEARCH, SEND, RECEIVE = 0x60c95e7a, 0x600514b6, 0x600513e6
BUFFER, DATA = 0xa43a3ec0, 0x19030000
PATTERNS = 0x61fb013c
LOGS = {0x6002247c, 0x6002266d}
NOTIFY = {0x601e7094, 0x601e71b6, 0x601e7186, 0x601e739f}


class SdMachine(Machine):
    def __init__(self, code, engine, header):
        self.engine = engine
        # The actual initialized-data mapping, not host-generated pattern pointers.
        source = 0x60230800 + PATTERNS - 0x61f98540
        rows = [Region('candidate', BASE, code, 'rx'),
                Region('stack', STACK, b'\xcc'*STACK_BYTES, 'rw', True),
                Region('data', DATA, bytes(256), 'rw', True),
                Region('patterns', PATTERNS, code[source-BASE:source-BASE+72], 'rw', True),
                Region('package_header', BUFFER, header, 'r'),
                Region('return_trampoline', HOOK_RETURN, b'\xcb'*8, 'rx')]
        self.regions = {r.name:r for r in rows}
        self.initial = dict(sp=SP, psw=0x800, d2=0x22334455, d3=0x33445566,
                            a2=0x44556677, a3=0x55667788)

    def write(self, address, data):
        for name,r in self.regions.items():
            if r.address <= address and address+len(data) <= r.address+len(r.data):
                self.mutate(name,address-r.address,data)
                return
        raise ValueError('model write outside explicit region '+hex(address))

    def word(self, address):
        return struct.unpack('<I',self.read(address,4))[0]

    def string(self, address):
        result = bytearray()
        for i in range(80):
            ch = self.read(address+i,1)
            if ch==b'\0':
                return result.decode('ascii')
            result.extend(ch)
        raise ValueError('unterminated native string')

    def advance(self, stop, hooks):
        r = execute(list(self.regions.values()),self.regs,stop,limit=20000,
                    trace_limit=16,trace_tail=True,breakpoints=hooks,
                    timeout=20,engine=self.engine,record_hashes=False)
        for row in r['memory']:
            self.regions[row['name']] = replace(self.regions[row['name']],data=bytes.fromhex(row['hex']))
        self.regs = r['registers']
        require(r['status'] in ('returned','breakpoint'), 'unexpected native stop: '+str(brief(r)))
        return r


def inspect(candidate, package, engine):
    code = candidate.read_bytes()
    with package.open('rb') as stream:
        header = stream.read(32)
    length = package.stat().st_size
    require(len(code)==26214336 and length==111017984,'unexpected candidate/package size')
    for addr,expected in (
        (CLIENT,bytes.fromhex('cff0fafe68ff9f00')),
        (WORKER,bytes.fromhex('cff0f8fe98080c')),
        (0x60c95f05,bytes.fromhex('cf30f8fefc96f00c')),
        (0x60c95fd8,bytes.fromhex('950008961cf1e3bb')),
        (0x60c96114,bytes.fromhex('cdad03f010'))):
        require(code[addr-BASE:addr-BASE+len(expected)]==expected,'native witness changed at '+hex(addr))
    tasks = []
    for addr,tid,entry,priority in ((0x60039370,88,CLIENT,45),(0x60038bc8,18,WORKER,55)):
        row = struct.unpack_from('<7I',code,addr-BASE)
        require(row==(tid,0,0,entry,priority,2048,0),'SD task configuration changed')
        tasks.append(dict(row=hex(addr),id=tid,entry=hex(entry),priority=priority,stack=2048))
    m = SdMachine(code,engine,header)
    patterns = [m.string(m.word(PATTERNS+i*4)) for i in range(17)]
    require(patterns[1:5]==['E142????BIN','G142????BIN','H142????BIN','W142????BIN'],
            'main update pattern group changed')
    last = struct.unpack_from('<5I',code,0x60f2cbf0+10*20-BASE)
    require(last==(0,0,PATTERNS+4,4,1),'main update scan row changed')
    require(struct.unpack_from('<H',code,0x60040dca-BASE)[0]==119 and
            struct.unpack_from('<H',code,0x60040d22-BASE)[0]==35,'SD queue route changed')

    # Actual callback + FAT32 cluster/size/attribute getters. The filesystem has
    # already pattern-matched these explicit short directory entries.
    selection = []
    for suffix,attribute,cluster,size in (
        ('1100',0x20,10,100),('9999',0x20,11,length),
        ('1200',0x20,12,200),('FFFF',0x10,13,300),('9999',0x20,14,400)):
        name = ('E142'+suffix+'BIN').encode()+b'\0'
        raw = bytearray(32)
        raw[:11] = name[:11]
        raw[11] = attribute
        struct.pack_into('<H',raw,20,cluster>>16)
        struct.pack_into('<HI',raw,26,cluster&65535,size)
        entry = bytearray(32)
        struct.pack_into('<3I',entry,0,DATA+128,DATA+160,0x60621138)
        m.write(DATA+64,entry)
        m.write(DATA+128,raw)
        m.write(DATA+160,name)
        m.write(DATA+192,struct.pack('<I',DATA))
        r = m.call(0x60c95f05,overrides=dict(a0=DATA+192,a1=DATA+64))
        require(r['status']=='returned' and r['registers']['sp']==SP and r['registers']['d0']==0,
                'native selection callback did not return')
        selection.append(dict(name=name[:-1].decode(),attributes=attribute,
                              selected_suffix=hex(m.word(DATA+36)),cluster=m.word(DATA+32),
                              bytes=m.word(DATA+28),execution=brief(r)))
    require([(r['selected_suffix'],r['cluster'],r['bytes']) for r in selection]==
            [('0x1100',10,100)]+[('0x9999',11,length)]*4,
            'native highest-suffix/attributes/tie behavior changed')

    # Execute the full task body until its terminal log loop. The existing
    # pattern wrapper is native; only its filesystem-search/read boundary is
    # modeled. There is one E-family file, no earlier group file.
    m.regions['stack'] = replace(m.regions['stack'],data=b'\xcc'*STACK_BYTES)
    m.regs = dict(m.initial,pc=CLIENT)
    hooks = LOGS | NOTIFY | {SEARCH,SEND,RECEIVE,0x60022319,0x60c974c0,0x60c95e4a,0x60c95e0a}
    searches, sent, notifications, stages = [],[],[],[]
    packet = None
    for _ in range(160):
        r = m.advance(0x60c95da1,hooks)
        stages.append(brief(r))
        if r['status']=='returned':
            break
        pc,reg = m.regs['pc'],m.regs
        result = 0
        if pc==SEARCH:
            context = reg['a0']
            pattern = m.string(m.word(context+8))
            folder = m.string(m.word(context+4))
            searches.append(dict(pattern=pattern,folder=folder,buffer=hex(m.word(context+12))))
            require(folder=='DCOLYMP    ' and m.word(context+12)==BUFFER,
                    'native SD path/buffer differs: '+str(searches[-1]))
            result = 0 if pattern=='E142????BIN' else 3596
            if result==0:
                m.write(context+28,struct.pack('<I',length))
        elif pc==SEND:
            wrapper = reg['a0']
            require(reg['d0']==119 and m.word(wrapper+4)==32,'unexpected SD message destination/size')
            packet = m.read(m.word(wrapper),32)
            sent.append(dict(queue=reg['d0'],message=packet.hex()))
        elif pc==RECEIVE:
            require(reg['d0']==35,'unexpected client reply queue')
            m.write(m.word(reg['a0']),bytes(12))
        elif pc in NOTIFY:
            notifications.append(dict(entry=hex(pc),d0=reg['d0'],d1=reg['d1']))
            require(pc not in (0x601e7186,0x601e71b6),'SD client entered error branch')
        BootState.return_from_model(m,result)
    require(m.regs['pc']==0x60c95da1 and packet is not None and len(sent)==1,
            'SD client did not reach successful terminal loop')
    require(len(searches)==11 and searches[-1]['pattern']=='E142????BIN',
            'native pattern priority/early success changed')
    require(struct.unpack_from('<II',packet)==(BUFFER,length) and packet[8]==0 and
            struct.unpack_from('<I',packet,12)[0]==35 and struct.unpack_from('<H',packet,16)[0]==1,
            'SD main packet fields differ')

    # Deliver the actual copied 32-byte packet to the original task18 receiver.
    # Stop at the shared updater; its actual five-component execution is already
    # recorded separately. This does not repeat decode or run any write backend.
    m.regions['stack'] = replace(m.regions['stack'],data=b'\xcc'*STACK_BYTES)
    m.regs = dict(m.initial,pc=WORKER)
    worker_stages,received = [],0
    worker_hooks = LOGS | {RECEIVE,0x6006757a,0x6015bafd,UPDATER}
    for _ in range(20):
        r = m.advance(UPDATER,worker_hooks)
        worker_stages.append(brief(r))
        if m.regs['pc']==UPDATER:
            break
        if m.regs['pc']==RECEIVE:
            require(m.regs['d0']==119 and m.word(m.regs['a0']+4)==32,
                    'worker receive does not match SD sender')
            m.write(m.word(m.regs['a0']),packet)
            received += 1
        BootState.return_from_model(m,0)
    require(m.regs['pc']==UPDATER and received==1 and
            (m.regs['a0'],m.regs['d0'],m.regs['d1'])==(BUFFER,length,0),
            'SD message did not reach native shared updater mode0 unchanged')
    return dict(scope=__doc__,status='passed',tasks=tasks,patterns=patterns,
                selection=selection,searches=searches,sent=sent,notifications=notifications,
                client_execution=stages,worker_execution=worker_stages,
                shared_updater=dict(entry=hex(UPDATER),buffer=hex(m.regs['a0']),
                                    bytes=m.regs['d0'],mode=m.regs['d1']),
                native_instructions=sum(r['completed'] for r in stages+worker_stages)+
                                    sum(r['execution']['completed'] for r in selection),
                hash_checks_performed=False,physical_sd_executed=False,
                physical_boot_trigger_verified=False,installable=False,
                limits=['Directory entries and FAT32 object shape are explicit inputs, after filesystem pattern matching; raw card and wildcard matching are not emulated.',
                        'Timer, watchdog, SD preparation, filesystem search/read, queue delivery, device preparation and notifications are modeled boundaries. Native pattern iteration, packet construction, callback ranking and receiver dispatch execute.',
                        'Message padding is copied verbatim. No original packet field is silently initialized by the probe.',
                        'Task registration does not prove which physical power/button condition starts the SD client.',
                        'Suffix 9999 is a filename selection priority; it does not change component build/version metadata.',
                        'Shared updater acceptance is separate prior evidence; no native flash, independent recovery, whole camera boot or H/L hardware behavior is proved.'])


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.package,args.engine),indent=2))
