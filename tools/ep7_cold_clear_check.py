#!/usr/bin/env python3
"""Assemble the cold-clear candidate and check its bounded writes using GNU instruction bodies."""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from ep7_far_call_check import body, REFERENCE

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'prototypes/ep7_volatile_hl/target/cold_clear.s'
GNU_BASE = REFERENCE.rsplit('/', 1)[0]

PRELUDE = r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef uint32_t unsigned32;
enum { REG_D0=0,REG_A0=4,REG_SP=8,REG_PC=9,REG_MDR=10 };
enum { PSW_Z=1,PSW_N=2,PSW_C=4,PSW_V=8 };
struct machine { uint32_t regs[32]; unsigned char ram[32768]; } State;
#define PC State.regs[REG_PC]
#define PSW State.regs[11]
#define FETCH16(a,b) ((uint32_t)(a)|((uint32_t)(b)<<8))
#define FETCH32(a,b,c,d) (FETCH16(a,b)|(FETCH16(c,d)<<16))
#define EXTEND8(x) ((int32_t)(int8_t)(x))
#define EXTEND16(x) ((int32_t)(int16_t)(x))
#define RAM 0x18020000u
#define PAYLOAD (RAM+0x1000u)
#define PAYLOAD_END (PAYLOAD+16384u)
#define ENTRY_SP (RAM+0x6000u)
#define REPLAY_SOURCE (RAM+0x7000u)
#define CODE 0x19010000u
#define RESUME 0x18010000u
static unsigned writes,payload_writes,stack_writes,guard_writes;
static uint32_t load_word(uint32_t a) {
 uint32_t v; assert(!(a&3u)&&a>=RAM&&a<=RAM+32764u);
 memcpy(&v,State.ram+a-RAM,4); return v;
}
static void store_word(uint32_t a,uint32_t v) {
 assert(!(a&3u)&&a>=RAM&&a<=RAM+32764u); writes++;
 if(a>=PAYLOAD&&a<PAYLOAD_END)payload_writes++;
 else if(a>=ENTRY_SP-16&&a<ENTRY_SP)stack_writes++;
 else {assert(a==PAYLOAD_END);guard_writes++;}
 memcpy(State.ram+a-RAM,&v,4);
}
'''


def semantic_step(source):
    # Decoder restricted to the exact production shape. The state operations
    # below are extracted GNU bodies, not a second implementation of the ISA.
    cases = [
        ('p[0]==0xf8&&p[1]==0xfe', 'OP_F8FE00', 3, 'unsigned IMM8=p[2];'),
        ('p[0]==0x42||p[0]==0x46', 'OP_4200', 2, 'unsigned DM1=(p[0]-0x42)/4,D8=p[1];'),
        ('p[0]==0x43', 'OP_4300', 2, 'unsigned AM1=0,D8=p[1];'),
        ('p[0]==0xf2&&p[1]==0xe4', 'OP_F2E4', 2, 'unsigned DN0=0;'),
        ('p[0]==0xf2&&p[1]==0xf3', 'OP_F2F3', 2, 'unsigned DM1=0;'),
        ('p[0]==0xfc&&p[1]==0xdc', 'OP_FCDC0000', 6,
         'unsigned AN0=0,IMM32A=p[2],IMM32B=p[3],IMM32C=p[4],IMM32D=p[5];'),
        ('p[0]==0x2d', 'OP_2C0000', 3, 'unsigned DN0=1,IMM16A=p[1],IMM16B=p[2];'),
        ('p[0]==0', 'OP_0', 1, 'unsigned DN1=0;'),
        ('p[0]==0x60', 'OP_60', 1, 'unsigned AN0=0,DM1=0;'),
        ('p[0]==0x50', 'OP_50', 1, 'unsigned AN0=0;'),
        ('p[0]==0x29', 'OP_2800', 2, 'unsigned DN0=1,IMM8=p[1];'),
        ('p[0]==0xc9', 'OP_C900', 2, 'unsigned D8=p[1];'),
        ('p[0]==0x58||p[0]==0x59', 'OP_5800', 2, 'unsigned DN0=p[0]-0x58,D8=p[1];'),
        ('p[0]==0x5c', 'OP_5C00', 2, 'unsigned AN0=0,D8=p[1];'),
        ('p[0]==0xfc&&p[1]==0xa4', 'OP_FCA40000', 6,
         'unsigned DN0=0,IMM32A=p[2],IMM32B=p[3],IMM32C=p[4],IMM32D=p[5];'),
        ('p[0]==0xdc', 'OP_DC000000', 5, 'unsigned D32A=p[1],D32B=p[2],D32C=p[3],D32D=p[4];'),
    ]
    result = ['static void step(const unsigned char *p) { uint32_t cia=PC,nia=0;']
    for condition, marker, length, fields in cases:
        result += [f'if({condition}) {{nia=cia+{length};{fields}', body(source, marker),
                   'PC=nia;return;}']
    result += ['assert(!"unreviewed opcode");}']
    return '\n'.join(result), [x[1] for x in cases]


DRIVER = r'''
static struct machine initial;
static void reset(uint32_t psw) {
 memset(&State,0xa5,sizeof State);
 for(unsigned i=0;i<32;i++)State.regs[i]=0x11000000u+0x010101u*i;
 State.regs[REG_SP]=ENTRY_SP;PC=CODE;PSW=psw;
 uint32_t value=0x61234568u;memcpy(State.ram+REPLAY_SOURCE-RAM,&value,4);
 writes=payload_writes=stack_writes=guard_writes=0;initial=State;
}
static void run(int broken) {
 unsigned char code[sizeof production_code];memcpy(code,production_code,sizeof code);
 if(broken==2)code[0x14]=1; /* 4096 -> 4097 words: expose guard overwrite. */
 unsigned count=0;
 while(PC!=RESUME) {
  assert(++count<17000&&PC>=CODE&&PC<CODE+sizeof code);
  unsigned offset=PC-CODE;
  if(broken==1&&offset==0x1f){PC+=2;continue;} /* Omit PSW restore. */
  if(broken==3&&offset==0x2a){PC+=6;continue;} /* Omit original MOV replay. */
  step(code+offset);
 }
}
static void check_success(void) {
 struct machine expected=initial;
 expected.regs[0]=load_word(REPLAY_SOURCE);expected.regs[REG_PC]=RESUME;
 assert(memcmp(expected.regs,State.regs,sizeof expected.regs)==0);
 assert(writes==4100&&payload_writes==4096&&stack_writes==4&&guard_writes==0);
 for(unsigned i=0;i<sizeof State.ram;i++) {
  uint32_t a=RAM+i;
  if(a>=PAYLOAD&&a<PAYLOAD_END)assert(State.ram[i]==0);
  else if(a<ENTRY_SP-16||a>=ENTRY_SP)assert(State.ram[i]==initial.ram[i]);
 }
 assert(load_word(ENTRY_SP-16)==initial.regs[0]);
 assert(load_word(ENTRY_SP-12)==initial.regs[1]);
 assert(load_word(ENTRY_SP-8)==initial.regs[4]);
 assert(load_word(ENTRY_SP-4)==initial.regs[11]);
}
int main(void) {
 const uint32_t patterns[]={0x750fu,0x8000u};
 for(unsigned i=0;i<2;i++){reset(patterns[i]);run(0);check_success();}
 reset(0x750f);run(1);assert(PSW!=initial.regs[11]);
 reset(0x750f);run(2);assert(payload_writes==4096&&guard_writes==1&&load_word(PAYLOAD_END)==0);
 reset(0x750f);run(3);assert(State.regs[0]==initial.regs[0]&&State.regs[0]!=load_word(REPLAY_SOURCE));
 puts("{\"positive_state_checks\":2,\"negative_controls\":3,\"payload_word_writes_each\":4096,\"stack_word_writes_each\":4}");
 return 0;
}
'''


def inspect(reference, op_utils, prefix):
    step, markers = semantic_step(reference.read_text())
    helpers = re.findall(r'genericAdd\(unsigned32 source, unsigned32 destReg\)\s*(\{.*?\n\})',
                         op_utils.read_text(), re.S)
    if len(helpers) != 1:
        raise ValueError('GNU genericAdd body missing/ambiguous')
    with tempfile.TemporaryDirectory(prefix='ep7-cold-clear-') as temp:
        out = Path(temp)
        obj = out/'cold.o'
        subprocess.run([prefix+'as', '-o', str(obj), str(ROOT/SOURCE)], check=True)
        subprocess.run([prefix+'objcopy', '-O', 'binary', '-j', '.text.ep7_cold_clear',
                        str(obj), str(out/'object.bin')], check=True)
        expected = bytes.fromhex('f8fef0420046044308f2e4420cfcdc000000002d001000605029ffc900'
                                 '580cf2f3580059045c08f8fe10fca400000000dc00000000')
        if (out/'object.bin').read_bytes() != expected:
            raise ValueError('production cold-clear instruction shape changed')
        relocations = subprocess.check_output([prefix+'objdump', '-r', str(obj)], text=True)
        found = re.findall(r'^([0-9a-f]+)\s+(R_MN10300_\w+)\s+(\S+)$', relocations, re.M)
        wanted = [(0xf, 'R_MN10300_32', '__ep7_private_uncached_start'),
                  (0x1c, 'R_MN10300_PCREL8', '.Lzero+0x00000001'),
                  (0x2c, 'R_MN10300_32', 'ep7_stock_boot_next_copy_end_unresolved'),
                  (0x31, 'R_MN10300_PCREL32', 'ep7_stock_boot_after_clear_unresolved+0x00000001')]
        if sorted((int(a, 16), kind, symbol) for a, kind, symbol in found) != wanted:
            raise ValueError('production cold-clear relocations changed: '+str(found))
        subprocess.run([prefix+'ld', '--no-relax', '-Ttext=0x19010000', '-e', 'ep7_native_cold_clear',
                        '--defsym=__ep7_private_uncached_start=0x18021000',
                        '--defsym=ep7_stock_boot_next_copy_end_unresolved=0x18027000',
                        '--defsym=ep7_stock_boot_after_clear_unresolved=0x18010000', str(obj),
                        '-o', str(out/'fixture.elf')], check=True)
        subprocess.run([prefix+'objcopy', '-O', 'binary', '-j', '.text',
                        str(out/'fixture.elf'), str(out/'fixture.bin')], check=True)
        code = (out/'fixture.bin').read_bytes()
        linked = bytearray(expected)
        linked[0xf:0x13] = (0x18021000).to_bytes(4, 'little')
        linked[0x1c] = 0xfc
        linked[0x2c:0x30] = (0x18027000).to_bytes(4, 'little')
        linked[0x31:0x35] = (0x18010000-0x19010030).to_bytes(4, 'little', signed=True)
        if code != linked:
            raise ValueError('linked fixture altered shape or resolved a wrong address')
        sizes = subprocess.check_output([prefix+'size', str(obj)], text=True).splitlines()[-1].split()
        if list(map(int, sizes[:3])) != [53, 0, 0]:
            raise ValueError('cold-clear object acquired unexpected storage')
        harness = PRELUDE+'\nstatic void genericAdd(unsigned32 source,unsigned32 destReg)'+helpers[0]
        harness += '\n'+step+'\nstatic const unsigned char production_code[]={'+','.join(map(str, code))+'};\n'+DRIVER
        (out/'semantic.c').write_text(harness)
        subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                        str(out/'semantic.c'), '-o', str(out/'semantic')], check=True)
        checks = json.loads(subprocess.check_output([str(out/'semantic')], text=True))
    return dict(scope=__doc__, source=SOURCE, text_data_bss=[53, 0, 0],
        instruction_count=21, transient_stack_bytes=16, zeroed_payload_bytes=16384,
        gnu_references=[REFERENCE, GNU_BASE+'/op_utils.c', GNU_BASE+'/mn10300_sim.h'],
        reused_gnu_instruction_bodies=markers, reused_gnu_helpers=['genericAdd'],
        reference_bytes=reference.stat().st_size, helper_reference_bytes=op_utils.stat().st_size,
        exact_object_and_relocation_shape_checked=True, synthetic_link_relaxation_disabled=True,
        all_registers_match_original_mov_then_resume=True, memory_outside_payload_and_stack_unchanged=True,
        **checks, unresolved_production_bindings=[row[2] for row in wanted if not row[2].startswith('.L')],
        production_object_assembled=True, synthetic_fixture_linked=True, gnu_libsim_full_engine_run=False,
        firmware_input_used=False, firmware_modified=False, firmware_built=False,
        camera_executed=False, hash_checks_performed=False,
        limits=['Restricted decoder and reused GNU C bodies, not full libsim or proprietary hardware execution.',
                'Aligned synthetic RAM/stack only; no cache, interrupts, secondary CPU or DMA model.',
                'Placement, exclusive reservation and cold-only execution are prerequisites, not established here.',
                'No firmware rewrite, runtime bootstrap, hook installer or publication is performed.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--op-utils', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.reference, args.op_utils, args.tool_prefix), indent=2))
