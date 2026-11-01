#!/usr/bin/env python3
"""Continue original cold initialization through its two native pool allocations.

Reuses the reviewed fixed-pool layout. Fresh CPU0 allocator words and the two
null buffer pointers are explicit cold-BSS conditions, not an allocator stub.
"""
import struct

from ep7_candidate_startup_sim import CALLER, require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_device_state_sim import admit
from ep7_candidate_message_sim import result_ok
from ep7_ram_ownership import CACHED, STRIDES


def initialize_diagnostic_buffers(machine, syms, cold_prefix):
    pool = next(r for r in CACHED if r[0:2]==(0,2))
    base,capacity,bitmap = pool[2],pool[3],pool[7]
    stride,counter = STRIDES[2],0x62038120
    require(machine.read(0x8050,4)==bytes(4) and
            machine.read(pool[4],6)==b'\xfc\xdf'+struct.pack('<I',base) and
            machine.read(pool[5],2)==bytes([0x80,capacity]) and
            machine.read(pool[6],6)==b'\xfc\xdc'+struct.pack('<I',bitmap) and
            machine.read(0x600228ed,6)==bytes.fromhex('fcd118810362') and
            machine.read(0x60026e3c,4)==struct.pack('<I',stride),
            'native CPU0 big-slot allocator binding changed')
    require(machine.read(0x6002004d,12)==bytes.fromhex('fccd34c90362fccc00810362') and
            machine.read(0x60020068,12)==bytes.fromhex('fccd886879a2fccc00af1c62') and
            all(0x62038100<=a<a+4<=0x6203c934 for a in (counter,bitmap)),
            'cold allocator metadata escaped its original BSS range')
    #Only counter/first bitmap word are mapped: no recycling path or spare
    #payload can accidentally become available in this fresh-two-slot case.
    admit(machine,'cpu0_big_next_conditional_BSS',counter,bytes(4))
    admit(machine,'cpu0_big_bitmap_conditional_BSS',bitmap,bytes(4))
    admit(machine,'diagnostic_ring_state',0xa2788f6c,b'\xa5'*4+bytes(4)+b'\xa5'*4+bytes(4))
    admit(machine,'diagnostic_cold_suffix_state',0x622c60dc,b'\xa5')
    pointers = [base,base+stride]
    for index,address in enumerate(pointers):
        admit(machine,f'native_diagnostic_payload_{index}',address,b'\xa5'*16384)
        require(not any(r.address<address+stride and address+16384<r.address+len(r.data)
                        for r in machine.regions.values()),
                'diagnostic allocation mapping overlaps a native64-byte slot guard')
    #The same pre-kernel lock branch already exercised by the pool-reservation
    #probe. Limit these explicit system-register inputs to the cold suffix.
    admit(machine,'diagnostic_pre_kernel_lock_fixture',0x8ff006fc,bytes(4),'r')
    admit(machine,'diagnostic_restore_mask_fixture',0x8ff00040,bytes(4),'r')
    require(cold_prefix['registers']['pc']==0x60556bb2 and
            machine.read(0x60556bb2,5)==bytes.fromhex('cd680a0004') and
            machine.read(0x60557683,4)==bytes.fromhex('fac80004') and
            machine.read(0x605576b3,4)==bytes.fromhex('fac80004'),
            'original two1024-entry diagnostic ring allocation calls changed')
    result = machine.resume(cold_prefix['registers'],CALLER+7,full_trace=True,limit=60000,
        breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808,0x6002247c,0x60022694,0x60022dcd])
    result_ok(machine,result,CALLER+7,CALL_SP)
    requests = [r for r in result['trace'] if r['pc']==0x60022700]
    returns = [r for r in result['trace'] if r['pc']==0x6002272f]
    require(len(requests)==len(returns)==2 and all(r['d0']==16384 for r in requests) and
            [r['a0'] for r in returns]==pointers and
            machine.read(counter,4)==struct.pack('<I',2) and machine.read(bitmap,4)==struct.pack('<I',3),
            'two original allocations did not exclusively claim CPU0 slots0 and1')
    require(machine.read(0xa2788f6c,16)==struct.pack('<4I',0,pointers[0],0,pointers[1]) and
            machine.read(0x622c60dc,1)==b'\0',
            'native cold suffix did not publish its buffers/cursors')
    expected = (b'\x3f'+b'\xa5'*7+bytes(8))*1024
    require(all(machine.read(a,16384)==expected for a in pointers),
            'native diagnostic ring fields or untouched bytes differ')
    require((result['registers']['psw']&0xf00)==(cold_prefix['registers']['psw']&0xf00) and
            all(not r['psw']&0x700 for r in result['trace'] if 0x600228bf<=r['pc']<0x60022a54),
            'native allocator failed to mask/restore its local IRQ level')
    del machine.regions['diagnostic_pre_kernel_lock_fixture']
    del machine.regions['diagnostic_restore_mask_fixture']
    metadata = dict(native_allocations=2,request_bytes=16384,domain=0,
        pointers=[hex(a) for a in pointers],stride=stride,slots=[0,1],native_pool_capacity=capacity,
        counter=hex(counter),bitmap=hex(bitmap),counter_after=2,bitmap_after=3,
        ring_entries_each=1024,record_bytes=16,all_ring_fields_verified=True,
        seven_unwritten_bytes_per_entry_retained_A5=True,slot_guards_unmapped=True,
        conditional_BSS_allocator_bytes=8,conditional_BSS_pointer_bytes=8,
        temporary_pre_kernel_lock_inputs=['0x8ff006fc=0','0x8ff00040=0'],
        lock_inputs_removed_after_suffix=True,complete_cold_initializer_executed=True,
        hardware_or_whole_lifecycle_ownership_proven=False)
    return result,metadata
