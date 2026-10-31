#!/usr/bin/env python3
"""Execute the linked E-P7 candidate startup prefix in the existing strict GNU model.

Real candidate instructions, explicit resident-image/TCB/RAM fixtures, no API
success stubs. Stop before semaphore creation; this is not a full boot proof.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct
import subprocess
import tempfile

from ep7_offline_candidate import BASE, CODE, ELF_NAME, IMAGE_NAME, RAM_START, RAM_BYTES
from ep7_offline_candidate import check_sources_at_revision, sections, symbols
from ep7_sim_probe import brief
from penf_emulator import Region, execute

STACK, STACK_BYTES, SP = 0x19010000, 2048, 0x190107f0
CALLER, TCB = 0x19000000, 0x19020000
CLEAR_SITE, CLEAR_RESUME = 0x600201fe, 0x60020204
INIT_SITE, INIT_RESUME = 0x602897d7, 0x602897dd
BOOT_SITE, ORIGINAL_BOOT = 0x60191371, 0x6011f620
CREATE = 0x6003057f
COHORTS = ('_ep7r_native_early_cohort_present','_ep7cn_native_cohort_present',
           '_ep7q_native_cohort_present','_ep7n_postbuilder_cohort_present',
           '_ep7i_native_cohort_present','_ep7m_native_cohort_present','_ep7u_native_cohort_present')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def candidate_inputs(directory, prefix):
    report = json.loads((directory/'report.json').read_text(encoding='utf-8'))
    require(report['status']=='passed' and report['whole_candidate_linked'] and
            report['decoded_candidate_synthesized'], 'candidate build did not pass')
    check_sources_at_revision(report['source_revision'])
    data = (directory/IMAGE_NAME).read_bytes()
    require(len(data)==26214336, 'candidate decoded length changed')
    elf = directory/ELF_NAME
    syms = symbols(prefix,elf)
    allocated = [s for s in sections(prefix,elf) if 'ALLOC' in s['flags'] and s['size']]
    require({s['name'] for s in allocated}=={'.ep7_code0','.ep7_code1','.bss'},
            'candidate allocated sections changed')
    bss = next(s for s in allocated if s['name']=='.bss')
    require(bss['address']==RAM_START and bss['size']<=RAM_BYTES and 'CONTENTS' not in bss['flags'],
            'candidate BSS no longer matches the cold-clear fixture')
    with tempfile.TemporaryDirectory(prefix='ep7-candidate-code-') as tmp:
        for i,(low,high) in enumerate(CODE):
            section = next(s for s in allocated if s['name']==f'.ep7_code{i}')
            require(section['address']==low and section['size']<=high-low,
                    'candidate code bank moved')
            path = Path(tmp)/f'{i}.bin'
            subprocess.run([prefix+'objcopy','-O','binary','-j',section['name'],str(elf),str(path)],check=True)
            block = path.read_bytes()
            require(len(block)==section['size'] and data[low-BASE:low-BASE+len(block)]==block,
                    'candidate decoded bytes differ from the actual linked ELF')
    for name in (*COHORTS,'_ep7_gcc_quarantine','_ep7_native_runtime_slot',
                 '_ep7_controller_sidecar_unresolved','ep7_capture_far_60289c5e'):
        require(name in syms, 'missing linked symbol '+name)
    return data,{name:row['address'] for name,row in syms.items()},report


class Machine:
    def __init__(self, data, engine):
        task = bytearray(96)
        struct.pack_into('<H',task,16,0x2d)
        struct.pack_into('<H',task,48,1)
        struct.pack_into('<I',task,76,0x601912fb)
        struct.pack_into('<II',task,84,STACK_BYTES,STACK)
        # Every mutable field is fixture-owned. The real candidate image stays
        # read/execute only; native calls cannot silently acquire more mappings.
        self.engine = engine
        rows = [Region('candidate',BASE,data,'rx'),
            Region('private_before',RAM_START-64,b'\x5a'*64),
            Region('private',RAM_START,b'\xa5'*RAM_BYTES,'rw',True),
            Region('private_after',RAM_START+RAM_BYTES,b'\x5a'*64),
            Region('stack_before',STACK-64,b'\x5a'*64),
            Region('stack',STACK,b'\xcc'*STACK_BYTES,'rw',True),
            Region('stack_after',STACK+STACK_BYTES,b'\x5a'*64),
            Region('state',0x62234fc0,b'\x7e\x7e','rw',True),
            Region('next_copy',0x6218d984,struct.pack('<I',0xa1f98540)),
            Region('load_flags',0xa272e41c,struct.pack('<2I',15,15)),
            Region('cpu_id',0x8050,bytes(4)),
            Region('root_cell',0x8ff00004,struct.pack('<I',0x600411a4)),
            Region('task_cell',0x621a630c,struct.pack('<I',TCB)+bytes(16),'rw',True),
            Region('lock_cell',0x621a63b0,bytes(4),'rw',True),
            Region('tcb',TCB,bytes(task),'rw',True)]
        self.regions = {r.name:r for r in rows}
        self.initial = dict(d0=0x11223344,d1=0x55667788,d2=0x22334455,d3=0x33445566,
            a0=0x19200000,a1=0x19300000,a2=0x19400000,a3=0x19500000,
            sp=SP,mdr=0x13579bdf,psw=0x800,lir=0x12345678,lar=0x23456789)

    def clone(self):
        other = object.__new__(Machine)
        other.engine,other.regions,other.initial = self.engine,dict(self.regions),dict(self.initial)
        return other

    def read(self,address,size):
        for region in self.regions.values():
            if region.address<=address and address+size<=region.address+len(region.data):
                return region.data[address-region.address:address-region.address+size]
        raise ValueError('fixture read outside explicit mapping '+hex(address))

    def mutate(self,name,offset,data):
        region = self.regions[name]
        require(0<=offset and offset+len(data)<=len(region.data),'fixture mutation outside mapping')
        self.regions[name] = replace(region,data=region.data[:offset]+data+region.data[offset+len(data):])

    def run(self,start,stop,*,overrides=None,breakpoints=(),full_trace=False,limit=30000):
        result = execute(list(self.regions.values()),dict(self.initial,pc=start,**(overrides or {})),stop,
            limit=limit,trace_limit=limit if full_trace else 16,trace_tail=not full_trace,
            breakpoints=breakpoints,timeout=20,engine=self.engine,record_hashes=False)
        require(result.get('hash_checks_performed') is False,'unexpected provenance mode')
        for row in result['memory']:
            self.regions[row['name']] = replace(self.regions[row['name']],data=bytes.fromhex(row['hex']))
        return result

    def call(self,target):
        code = b'\xdd'+struct.pack('<i',target-CALLER)+bytes(2)
        self.regions['caller'] = Region('caller',CALLER,code,'rx')
        return self.run(CALLER,CALLER+7)


def returned(result,stop):
    require(result['status']=='returned' and result['registers']['pc']==stop and
            result['registers']['sp']==SP and result['fault'] is None,
            'candidate did not return normally: '+str(brief(result)))


def inspect(directory,prefix,engine):
    data,syms,build = candidate_inputs(directory,prefix)
    machine = Machine(data,engine)
    initial_stack = machine.regions['stack'].data
    cleared = machine.run(CLEAR_SITE,CLEAR_RESUME)
    returned(cleared,CLEAR_RESUME)
    require(machine.regions['private'].data==bytes(RAM_BYTES),'cold clear missed private payload bytes')
    expected = dict(machine.initial,d0=0xa1f98540)
    require(all(cleared['registers'][name]==value for name,value in expected.items()),
            'linked cold clear changed preserved registers')
    stack = machine.regions['stack'].data
    require(stack[:SP-STACK-16]==initial_stack[:SP-STACK-16] and
            stack[SP-STACK:]==initial_stack[SP-STACK:],'cold clear wrote outside its 16-byte frame')
    initialized = machine.run(INIT_SITE,INIT_RESUME,overrides={'d0':0},
                              breakpoints=[syms['_ep7_gcc_quarantine']])
    returned(initialized,INIT_RESUME)
    expected_private = bytearray(RAM_BYTES)
    expected_private[syms['_ep7_controller_sidecar_unresolved']-RAM_START] = 1
    require(machine.regions['private'].data==bytes(expected_private) and
            machine.regions['state'].data==bytes(2),'capture initializer state differs from fresh native state')
    for name in ('d1','d2','d3','a0','a1','a2','a3','mdr'):
        require(initialized['registers'][name]==machine.initial[name],
                'capture initializer bridge did not preserve '+name)
    baseline = machine.clone()
    cohorts = []
    for name in COHORTS:
        case = baseline.clone()
        result = case.call(syms[name])
        returned(result,CALLER+7)
        require(result['registers']['d0']==1,'actual linked cohort rejected the candidate: '+name)
        require(case.regions['private'].data==baseline.regions['private'].data,
                'read-only installation check changed private state')
        cohorts.append(dict(symbol=name,address=hex(syms[name]),result=brief(result),returned_d0=1))

    negative = []
    for name,address,value in [('_ep7r_native_early_cohort_present',0x600229ba,b'\x20'),
        ('_ep7cn_native_cohort_present',syms['ep7_capture_far_60289c5e']+26,
         bytes([data[syms['ep7_capture_far_60289c5e']+26-BASE]^1]))]:
        case = baseline.clone()
        case.mutate('candidate',address-BASE,value)
        result = case.call(syms[name])
        returned(result,CALLER+7)
        require(result['registers']['d0']==0,'linked cohort accepted its corrupted in-memory input')
        negative.append(dict(symbol=name,corrupted_address=hex(address),result=brief(result),returned_d0=0))

    startup = baseline.clone()
    front = startup.run(BOOT_SITE,ORIGINAL_BOOT,breakpoints=[CREATE,syms['_ep7_gcc_quarantine']],full_trace=True)
    require(front['status']=='breakpoint' and front['registers']['pc']==CREATE,
            'bootstrap failed before native creation: '+str(brief(front)))
    require(len(front['trace'])==front['completed'],'startup trace incomplete')
    spec_address = front['registers']['a0']
    require(struct.unpack('<3I',startup.read(spec_address,12))==(0,1,1),
            'actual GCC/native creation bridge supplied the wrong semaphore specification')
    require(startup.read(syms['_ep7_native_runtime_slot'],4)==bytes(4),
            'runtime was published before native semaphore creation')
    get_tid_calls = sum(row['pc']==0x600317ac for row in front['trace'])
    # Two observations in ep7n_query_task, then ep7b_prepare's own current-ID
    # observation before invoking its creation callback.
    require(get_tid_calls==3,'native task/creation checks changed their three get_tid observations')

    wrong_context = baseline.clone()
    wrong_context.mutate('tcb',48,bytes(2))
    rejected = wrong_context.run(BOOT_SITE,ORIGINAL_BOOT,breakpoints=[CREATE,syms['_ep7_gcc_quarantine']])
    require(rejected['status']=='breakpoint' and rejected['registers']['pc']==syms['_ep7_gcc_quarantine'] and
            rejected['registers']['d0']==0xf06 and
            wrong_context.read(syms['_ep7_native_runtime_slot'],4)==bytes(4),
            'invalid cold context did not quarantine before native creation')
    duplicate = baseline.clone()
    repeated = duplicate.run(INIT_SITE,INIT_RESUME,overrides={'d0':0},
                             breakpoints=[syms['_ep7_gcc_quarantine']])
    require(repeated['status']=='breakpoint' and repeated['registers']['d0']==0xe01,
            'duplicate native capture initialization was not rejected')
    # Exercise the actual terminal body once, retaining the reason and frame.
    held = execute(list(duplicate.regions.values()),repeated['registers'],INIT_RESUME,
        limit=6,trace_limit=6,engine=engine,record_hashes=False,timeout=10)
    require(held['status']=='instruction_limit' and held['registers']['pc']==syms['_ep7_gcc_quarantine']+4 and
            held['registers']['d0']==0xe01 and not held['registers']['psw']&0x800 and
            held['registers']['sp']==repeated['registers']['sp'], 'actual terminal body did not hold safely')

    return dict(scope=__doc__,candidate_build_revision=build['source_revision'],
        candidate_object_revision=build.get('object_source_revision',build['source_revision']),
        actual_elf_code_equals_decoded_candidate=True,unchanged_implementation_inputs=True,
        engine=str(engine),hash_checks_performed=False,all_assertions_passed=True,
        cold_clear=dict(result=brief(cleared),private_bytes_zeroed=RAM_BYTES,read_only_boundary_guards=True,
            preserved_registers_checked=sorted(expected),stack_writes_confined_to_bytes=16),
        native_capture_initialize=dict(result=brief(initialized),fresh_private_state_checked=True),
        linked_cohort_functions=cohorts,corrupted_candidate_rejections=negative,
        bootstrap_creation_frontier=dict(result=brief(front),native_get_tid_executions=get_tid_calls,
            creation_specification=[0,1,1],specification_address=hex(spec_address),
            executed_prefix_stack_depth=SP-min(front['registers']['sp'],
                min(row['sp'] for row in front['trace'])),
            runtime_still_unpublished=True,native_create_executed=False),
        invalid_tcb_flag=dict(result=brief(rejected),quarantine_reason='0xf06'),
        repeated_capture_initialize=dict(result=brief(repeated),quarantine_reason='0xe01',terminal_hold=brief(held)),
        firmware_files_modified=False,full_boot_executed=False,runtime_publication_executed=False,
        hardware_executed=False,installable=False,
        limits=['Decoded candidate is explicitly supplied resident and executable; loading, cache and region ownership are not proven.',
                'TCB, current-task root, CPU ID, load flags, stack and private RAM are explicit fixtures; no scheduler or hardware interrupt occurs.',
                'The bootstrap run stops BEFORE the original semaphore-create entry. No API success value or initialized kernel object is fabricated.',
                'Prefix stack usage covers this one executed path only, not complete bootstrap, IRQ, callback or recursion bounds.',
                'Cohort functions accept current bytes; that does not prove all native aliases, lifecycle closures or updater acceptance.',
                'User reports no validated firmware backup or independent recovery method; offline work continues without camera access.'])


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine),indent=2))
