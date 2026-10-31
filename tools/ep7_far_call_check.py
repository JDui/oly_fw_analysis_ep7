#!/usr/bin/env python3
"""Check one far-CALL veneer against reused GNU instruction bodies, on synthetic state only."""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REFERENCE='https://gnu.googlesource.com/binutils-gdb/+/cbe950e9fe8a56f788bcf985cc51733f18abb45b/sim/mn10300/mn10300.igen'
MIRROR='https://raw.githubusercontent.com/RTEMS/sourceware-mirror-binutils-gdb/cbe950e9fe8a56f788bcf985cc51733f18abb45b/sim/mn10300/mn10300.igen'


def body(source, marker):
    matches=list(re.finditer(r'/\*\s*'+re.escape(marker)+r'\s*\(\);\s*\*/',source))
    if len(matches)!=1:
        raise ValueError('GNU instruction marker missing/ambiguous: '+marker)
    start=source.rfind('\n{',0,matches[0].start())+1
    if start<1:
        raise ValueError('instruction body opening missing')
    depth=0
    for end in range(start,len(source)):
        if source[end]=='{':depth+=1
        elif source[end]=='}':
            depth-=1
            if depth==0:return source[start:end+1]
    raise ValueError('unterminated GNU instruction body')


def capture_rows():
    cohort=(ROOT/'prototypes/ep7_volatile_hl/controller_sidecar/cohort.c').read_text()
    symbols=dict(re.findall(r'extern const unsigned char (\w+)\[\] __asm__\("(\w+)"\);',cohort))
    sites=re.findall(r'\{(0x[0-9a-f]+),(\w+),2,(0x[0-9a-f]+|0),(\d+)\}',cohort)
    expected=[(int(pc,16),symbols[name],int(mask,0),int(frame)) for pc,name,mask,frame in sites]
    source=(ROOT/'prototypes/ep7_volatile_hl/controller_sidecar/far_calls.s').read_text()
    rows=re.findall(r'^EP7_FAR_CALL ep7_capture_far_([0-9a-f]+),(\w+),(0x[0-9a-f]+),(0x[0-9a-f]+),(\d+)$',source,re.M)
    actual=[]
    for pc,target,resume,mask,frame in rows:
        if int(resume,16)!=int(pc,16)+5:raise ValueError('capture veneer has wrong resume')
        actual.append((int(pc,16),target,int(mask,0),int(frame)))
    if len(expected)!=18 or actual!=expected:
        raise ValueError('capture veneer order differs from the real cohort')
    return expected


def validate_capture_object(obj,prefix):
    return validate_object(obj,prefix,capture_rows(),'.text.ep7_capture_far_calls')


def validate_object(obj,prefix,rows,section):
    binary=obj.with_suffix('.veneer.bin')
    subprocess.run([prefix+'objcopy','-O','binary','-j',section,str(obj),str(binary)],check=True)
    data=binary.read_bytes()
    if len(data)!=30*len(rows):raise ValueError('production veneer size changed')
    relocs=subprocess.check_output([prefix+'objdump','-r',str(obj)],text=True)
    found=re.findall(r'^([0-9a-f]+)\s+R_MN10300_PCREL32\s+(\w+)\+0x0*1$',relocs,re.M)
    if [(int(offset,16),target) for offset,target in found]!=[(30*i+26,row[1]) for i,row in enumerate(rows)]:
        raise ValueError('production veneer adapter relocations differ')
    for i,(pc,_,mask,frame) in enumerate(rows):
        expected=bytes([0xcd,5,0,mask,frame,0xf8,0xfe,0xfc,0x42,0,0xfc,0xcc])+\
            (pc+5).to_bytes(4,'little')+bytes([0x42,frame+4,0xf2,0xf2,0x58,0,0xf8,0xfe,4,0xdc])
        if data[30*i:30*i+26]!=expected:raise ValueError('production veneer exact prefix differs')
    return dict(checked_veneer_rows=len(rows),veneer_bytes=len(data),extra_transient_stack_bytes=4,
                actual_cohort_order_and_resume_checked=True,actual_adapter_relocations_checked=True)


PRELUDE=r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
enum {REG_D0=0,REG_A0=4,REG_SP=8,REG_PC=9,REG_MDR=10,REG_LIR=12,REG_LAR=13,REG_E0=16};
typedef uint32_t unsigned32;
typedef int32_t signed32;
struct machine { uint32_t regs[32];unsigned char ram[512]; } State;
struct architecture { int mach; } arch={0};
#define bfd_mach_am33 33
#define bfd_mach_am33_2 34
#define STATE_ARCHITECTURE(sd) (&arch)
#define PC State.regs[REG_PC]
#define PSW State.regs[11]
#define FETCH16(a,b) ((uint32_t)(a)|((uint32_t)(b)<<8))
#define FETCH32(a,b,c,d) (FETCH16(a,b)|(FETCH16(c,d)<<16))
#define EXTEND8(x) ((int32_t)(int8_t)(x))
#define EXTEND16(x) ((int32_t)(int16_t)(x))
#define RAM 0x18020000u
#define ENTRY_SP (RAM+384u)
#define SITE 0x18010000u
#define DEST 0x18011000u
#define VENEERS 0x19010000u
static unsigned writes;
static uint32_t lowest;
static uint32_t load_word(uint32_t a) {
 uint32_t value;assert(!(a&3u)&&a>=RAM&&a<=RAM+508u);
 memcpy(&value,State.ram+a-RAM,4);return value;
}
static void store_word(uint32_t a,uint32_t value) {
 assert(!(a&3u)&&a>=RAM&&a<=RAM+508u);writes++;if(a<lowest)lowest=a;
 memcpy(State.ram+a-RAM,&value,4);
}
'''


def semantic_step(source):
    # Only the opcodes emitted by this macro and the two return controls.
    # Their state transformations are extracted, not rewritten in this harness.
    cases=[
        ('0xcd','OP_CD000000',5,'uint32_t D16A=p[1],D16B=p[2],REGS=p[3],IMM8=p[4];'),
        ('0xdc','OP_DC000000',5,'uint32_t D32A=p[1],D32B=p[2],D32C=p[3],D32D=p[4];'),
        ('0xdf','OP_DF0000',3,'uint32_t REGS=p[1],IMM8=p[2];'),
        ('0xde','OP_DE0000',3,'uint32_t REGS=p[1],IMM8=p[2];'),
        ('0xf8','OP_F8FE00',3,'assert(p[1]==0xfe);uint32_t IMM8=p[2];'),
        ('0x42','OP_4200',2,'uint32_t DM1=0,D8=p[1];'),
        ('0x58','OP_5800',2,'uint32_t DN0=0,D8=p[1];'),
        ('0xfc','OP_FCCC0000',6,'assert(p[1]==0xcc);uint32_t DN0=0,IMM32A=p[2],IMM32B=p[3],IMM32C=p[4],IMM32D=p[5];'),
        ('0xf2','OP_F2F2',2,'assert(p[1]==0xf2);uint32_t DM1=0;'),
    ]
    result=['static void step(const unsigned char *p) { uint32_t cia=PC,nia=0; switch(p[0]) {']
    for opcode,marker,length,fields in cases:
        result += [f'case {opcode}: {{nia=cia+{length};{fields}',body(source,marker),'break;}']
    result += ['default: assert(!"unreviewed opcode");}', 'PC=nia;}']
    return '\n'.join(result),[x[1] for x in cases]


DRIVER=r'''
static void reset(void) {
 memset(&State,0xa5,sizeof State);
 for(unsigned i=0;i<32;i++)State.regs[i]=0x11000000u+0x010101u*i;
 State.regs[REG_SP]=ENTRY_SP;PC=SITE;PSW=0x750fu;writes=0;lowest=UINT32_MAX;
}
static void jump_to(uint32_t target) {
 unsigned char jump[5]={0xdc};uint32_t delta=target-PC;
 memcpy(jump+1,&delta,4);step(jump);
}
static void run_veneer(const unsigned char *code,uint32_t start,int broken) {
 jump_to(start);
 for(unsigned i=0;i<12&&PC!=DEST;i++) {
  assert(PC>=start&&PC<start+30);
  unsigned offset=PC-start;
  if((broken==1&&offset==18)||(broken==2&&offset==16)){PC+=2;continue;}
  step(code+offset);
 }
 assert(PC==DEST);
}
int main(void) {
 unsigned pass=0;
 for(unsigned n=0;n<sizeof shapes/sizeof shapes[0];n++) {
  unsigned mask=shapes[n][0],frame=shapes[n][1];
  unsigned char direct[5]={0xcd,0x00,0x10,mask,frame};
  uint32_t start=VENEERS+30*n,low=ENTRY_SP-frame;
  struct machine baseline,actual;
  reset();step(direct);baseline=State;
  reset();run_veneer(veneer_code+30*n,start,0);actual=State;
  assert(memcmp(baseline.regs,actual.regs,sizeof baseline.regs)==0);
  for(unsigned i=0;i<512;i++)if(i<low-RAM-4||i>=low-RAM)
   assert(baseline.ram[i]==actual.ram[i]);
  assert(lowest==low-4);assert(load_word(ENTRY_SP)==SITE+5);
  /* Exercise both native return paths, including caller-save restoration. */
  for(unsigned fast=0;fast<2;fast++) {
   unsigned char ret[3]={fast?0xde:0xdf,mask,frame};
   State=baseline;
   State.regs[2]^=0x55555555u;State.regs[3]^=0x66666666u;
   State.regs[6]^=0x77777777u;State.regs[7]^=0x88888888u;
   step(ret);struct machine expected=State;
   State=actual;
   State.regs[2]^=0x55555555u;State.regs[3]^=0x66666666u;
   State.regs[6]^=0x77777777u;State.regs[7]^=0x88888888u;
   step(ret);
   assert(memcmp(expected.regs,State.regs,sizeof expected.regs)==0);
   assert(PC==SITE+5&&State.regs[REG_SP]==ENTRY_SP);pass++;
  }
  reset();run_veneer(veneer_code+30*n,start,1);
  assert(State.regs[REG_MDR]!=SITE+5&&load_word(ENTRY_SP)==SITE+5);
  reset();run_veneer(veneer_code+30*n,start,2);
  assert(State.regs[REG_MDR]==SITE+5&&load_word(ENTRY_SP)!=SITE+5);
 }
 printf("{\"return_path_checks\":%u,\"negative_controls\":%zu}\n",pass,sizeof shapes/sizeof shapes[0]*2);
 return 0;
}
'''


def inspect(reference,prefix,additional_shapes=()):
    source=reference.read_text()
    step_source,markers=semantic_step(source)
    rows=capture_rows()
    shapes=sorted({(mask,frame) for _,_,mask,frame in rows}|{(0,0),(0xf0,96)}|set(additional_shapes))
    macro=ROOT/'prototypes/ep7_volatile_hl/target/far_call.inc'
    asm='.text\n.include "'+str(macro)+'"\n'
    for i,(mask,frame) in enumerate(shapes):
        asm+=f'EP7_FAR_CALL ep7_test_veneer_{i},ep7_test_destination,0x18010005,{mask},{frame}\n'
    with tempfile.TemporaryDirectory(prefix='ep7-far-call-') as temp:
        out=Path(temp);(out/'fixture.s').write_text(asm)
        subprocess.run([prefix+'as','-o',str(out/'fixture.o'),str(out/'fixture.s')],check=True)
        subprocess.run([prefix+'ld','-Ttext=0x19010000','-e','ep7_test_veneer_0',
                        '--defsym=ep7_test_destination=0x18011000',str(out/'fixture.o'),
                        '-o',str(out/'fixture.elf')],check=True)
        subprocess.run([prefix+'objcopy','-j','.text','-O','binary',str(out/'fixture.elf'),
                        str(out/'fixture.bin')],check=True)
        code=(out/'fixture.bin').read_bytes()
        if len(code)!=30*len(shapes):raise ValueError('veneer width changed')
        for i,(mask,frame) in enumerate(shapes):
            b=code[30*i:30*(i+1)]
            expected=bytes([0xcd,5,0,mask,frame,0xf8,0xfe,0xfc,0x42,0,0xfc,0xcc])+\
                (0x18010005).to_bytes(4,'little')+bytes([0x42,frame+4,0xf2,0xf2,0x58,0,0xf8,0xfe,4,0xdc])
            if b[:26]!=expected:raise ValueError('assembled veneer shape changed')
            if 0x19010000+30*i+25+int.from_bytes(b[26:],'little',signed=True)!=0x18011000:
                raise ValueError('far final jump did not resolve exactly')
        host=PRELUDE+'\n'+step_source+'\n'
        host+='static const unsigned char veneer_code[]={'+','.join(map(str,code))+'};\n'
        host+='static const unsigned shapes[][2]={'+','.join('{%d,%d}'%x for x in shapes)+'};\n'+DRIVER
        (out/'semantic.c').write_text(host)
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(out/'semantic.c'),
                        '-o',str(out/'semantic')],check=True)
        result=json.loads(subprocess.check_output([str(out/'semantic')],text=True))
        target=ROOT/'prototypes/ep7_volatile_hl/target'
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(target/'far_call.c'),
                        str(target/'test_far_call.c'),'-o',str(out/'cohort-test')],check=True)
        subprocess.run([str(out/'cohort-test')],check=True)
    return dict(scope=__doc__,gnu_reference=REFERENCE,download_mirror=MIRROR,
        reference_bytes=reference.stat().st_size,reused_gnu_instruction_bodies=markers,
        tested_save_frame_tuples=[dict(mask=hex(mask),frame=frame) for mask,frame in shapes],
        synthetic_veneer_bytes_each=30,extra_transient_stack_bytes=4,
        callee_entry_registers_stack_return_mdr_psw_equal=True,
        native_frame_bytes_unchanged=True,**result,
        self_authored_fixture_assembled_and_linked=True,gnu_libsim_full_engine_run=False,
        firmware_input_used=False,firmware_modified=False,firmware_built=False,
        capture_veneer_rows=len(rows),capture_runtime_cohort_conversion_implemented=True,
        cohort_positive_checks=1,cohort_negative_checks=6,
        camera_executed=False,hash_checks_performed=False,
        limits=['GNU instruction C bodies run in a small host semantic harness, not the full libsim decoder.',
                'Synthetic aligned stack and base MN103 register masks only; no UDF/MMIO/interrupts.',
                'Actual hook rewrites, cohort recognition, executable placement, cache and total stack remain separate.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True,help='explicit local GNU mn10300.igen; no download or hash')
    parser.add_argument('--tool-prefix',required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.reference,args.tool_prefix),indent=2))
