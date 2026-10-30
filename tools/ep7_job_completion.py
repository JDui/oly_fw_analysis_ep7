#!/usr/bin/env python3
"""Exact E-P7 stock job/operation join witnesses; no firmware execution.

A successful static witness is NOT all-path completion or hardware qualification.
Supply a separately trusted MN10300 objdump; emits metadata only.
"""
import argparse,json,re,subprocess,tempfile
from pathlib import Path
from ep7_stock_audit import audit,BASE,require
from oly_container import parse,sha256
WINDOWS = {
    'operation_allocate_and_bind': (0x60354b8c, 0x60354cb9),
    'operation_membership': (0x60355f56, 0x60355f76),
    'iteration_gate': (0x603e16f1, 0x603e176c),
    'descriptor_iteration_release': (0x603e5f71, 0x603e5f94),
    'job_wrapper': (0x603e6d04, 0x603e6d98),
    'processing_and_join': (0x603e61b8, 0x603e62d1),
    'stage_runner': (0x60354214, 0x603542f3),
    'stage_join': (0x603544a6, 0x6035452f),
    'previous_operation_join': (0x60354930, 0x6035495d),
    'operation_wait_cleanup': (0x6035486d, 0x6035490d),
    'wait_wrapper': (0x60350c1a, 0x60350d0c),
    'wait_and_clear': (0x60350da1, 0x60350dbf),
    'callback': (0x60355fd4, 0x60356116),
    'callback_signal': (0x60350bfd, 0x60350c1a),
    'descriptor_cleanup': (0x603e6c8d, 0x603e6d04),
    'job_free': (0x60353cb7, 0x60353cf5),
}
WITNESSES = {
    0x60354b8f: ('mov', '14576,a1'),
    0x60354b96: ('udfu01', '56,d1'),
    0x60354ba1: ('mov', 'a2,(a0)'),
    0x60354ba8: ('cmp', '16,d2'),
    0x60354bb6: ('call', '0x60354b8c,[d2,a2],8'),
    0x60354be4: ('mov', 'a0,(4,a3)'),
    0x60354beb: ('mov', 'a3,(a2)'),
    0x60354bf3: ('add', '11364,a0'),
    0x60354bf7: ('mov', 'd3,(4,a0)'),
    0x60354bfc: ('mov', 'a0,(a2)'),
    0x60354c2e: ('add', '15472,a3'),
    0x60354c35: ('mov', '-8,d1'),
    0x60354c38: ('movhu', '(a1),d0'),
    0x60354c3c: ('movhu', 'd0,(a0)'),
    0x60354c43: ('mov', '16,d1'),
    0x60354c46: ('call', '0x4700115e,[d2,a2],8'),
    0x60355f58: ('add', '14576,a0'),
    0x60355f5e: ('udfu01', '56,d0'),
    0x60355f63: ('cmp', 'a1,d0'),
    0x60355f6e: ('cmp', '16,d1'),
    0x60355f71: ('mov', '0,a0'),

    0x603e1719: ('cmp', '4106,d0'),
    0x603e1721: ('mov', '(a2),d0'),
    0x603e173e: ('calls', '(a0)'),
    0x603e1740: ('movhu', '(4,a3),d1'),
    0x603e1743: ('movhu', '(6,a3),d0'),
    0x603e1747: ('cmp', 'd0,d1'),
    0x603e1748: ('ble', '0x603e174c'),
    0x603e174a: ('mov', '1,d2'),
    0x603e1768: ('mov', 'd2,d0'),
    0x603e5f71: ('mov', '(16,sp),a0'),
    0x603e5f74: ('mov', 'd0,(a0)'),
    0x603e5f78: ('call', '0x603e16f1,[d2,d3,a2,a3],24'),
    0x603e5f8f: ('call', '0x603edbd8,[],4'),
    0x603e6d3e: ('call', '0x603537eb,[d2,d3,a2,a3],44'),
    0x603e6d45: ('mov', 'd0,(36,a3)'),
    0x603e6d50: ('call', '0x603e62d1,[d2,d3,a2,a3],72'),
    0x603e6d84: ('call', '0x603e61b8,[d2,a2,a3],24'),
    0x603e6d8d: ('call', '0x603e6c8d,[a2,a3],24'),
    0x603e6247: ('mov', '65535,d1'),
    0x603e624d: ('call', '0x60354214,[d2,d3,a2,a3],32'),
    0x603e625c: ('call', '0x603544a6,[d2,a2,a3],16'),
    0x603e628f: ('call', '0x603544a6,[d2,a2,a3],16'),
    0x60354216: ('mov', '11312,a3'),
    0x60354237: ('mov', '10984,a2'),
    0x60354278: ('cmp', '16,d0'),
    0x6035428c: ('mov', '(d0,a2),a1'),
    0x6035428e: ('calls', '(a1)'),
    0x603542e6: ('movhu', 'd0,(a3)'),
    0x603544c5: ('mov', '11312,a2'),
    0x603544d4: ('add', '-1,d0'),
    0x603544ed: ('mov', '(8,a0),a0'),
    0x603544f5: ('call', '0x60354930,[a2],8'),
    0x603544fc: ('movhu', 'd0,(a0)'),
    0x60354930: ('mov', '11312,a1'),
    0x6035493b: ('add', '-1,d0'),
    0x60354943: ('mov', '10992,a2'),
    0x60354950: ('mov', '(a2),a0'),
    0x60354952: ('call', '0x6035486d,[d3,a2,a3],28'),
    0x60354958: ('mov', 'd1,(a2)'),
    0x60354872: ('mov', '(a2),d0'),
    0x60354880: ('mov', '1000,d0'),
    0x60354883: ('call', '0x60350da1,[d2,a2],12'),
    0x6035488b: ('mov', '32,a0'),
    0x60354899: ('call', '0x60350b6f,[d2,d3,a2],16'),
    0x60354900: ('call', '0x4700115e,[d2,a2],8'),
    0x60350c49: ('call', '0x6003883c,[d2,d3,a2,a3],40'),
    0x60350c82: ('call', '0x6003883c,[d2,d3,a2,a3],40'),
    0x60350cab: ('call', '0x6003883c,[d2,d3,a2,a3],40'),
    0x60350cb6: ('cmp', '-50,d0'),
    0x60350cba: ('mov', '40651,d0'),
    0x60350ce4: ('mov', '16,a1'),
    0x60350cfd: ('mov', '(24,a0),a1'),
    0x60350d03: ('call', '0x60350c1a,[d2,d3,a2,a3],48'),
    0x60350da2: ('call', '0x60350ce4,[d2,a2],16'),
    0x60350db6: ('call', '0x60350d71,[],4'),
    0x60355ff3: ('cmp', '10,d3'),
    0x60355ff5: ('beq', '0x60356049'),
    0x60356050: ('movhu', 'd1,(32,a1)'),
    0x603560e6: ('call', '0x60350bfd,[],4'),
    0x60350bfd: ('add', '16,a0'),
    0x60350c11: ('call', '0x60350ba8,[d2,d3],12'),
    0x603e6cce: ('call', '0x60353cb7,[d2,a2],12'),
    0x60353cdd: ('mov', '(13248,a2),a0'),
    0x60353ce9: ('call', '0x60022732,[],4'),
}

def require_instruction(assembly,address,mnemonic,operands):
 lines=[line for line in assembly.splitlines() if line.startswith(f'{address:x}:')]
 require(len(lines)==1 and re.search(r'\b'+re.escape(mnemonic)+r'\s+'+re.escape(operands)+r'\s*$',lines[0]),f'instruction mismatch at {address:#x}')
def inspect(raw,objdump):
 identity=audit(raw)
 main=parse(raw)[0].payload
 version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0]
 reports={}
 with tempfile.TemporaryDirectory(prefix='ep7-job-completion-') as tmp:
  image=Path(tmp)/'main.bin';image.write_bytes(main)
  for name,(start,stop) in WINDOWS.items():
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   witnesses=[a for a in WITNESSES if start<=a<stop]
   for a in witnesses:require_instruction(asm,a,*WITNESSES[a])
   reports[name]=dict(start=hex(start),stop_exclusive=hex(stop),sha256=sha256(main[start-BASE:stop-BASE]),witness_count=len(witnesses))
 return dict(scope='Static job-stage runner, operation join and callback signaling; not all-path async safety',
  source_sha256=identity['source_sha256'],objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),
  windows=reports,instruction_witness_count=len(WITNESSES),
  iteration_gate=dict(function='0x603e16f1',counter_halfword_offset=4,limit_halfword_offset=6,condition='counter > limit',direct_async_wait_identified=False),
  operation_shape=dict(records_job_offset=14576,record_stride_operand=56,record_count=16,embedded_request_job_offset=11364,occupied_job_tail_offset=15472,occupied_job_tail_bytes=16),
  stage_table=dict(job_offset=10984,row_stride_operand=12,max_rows=16,current_index_halfword_offset=11312,operation_pointer_in_row=8,status_halfword_offset=11316),
  operation_join=dict(function='0x6035486d',event_token_offset=16,result_halfword_offset=32,wait_argument=1000,timeout_units_qualified=False),
  callback=dict(function='0x60355fd4',numeric_event=10,result_write_offset=32,signal_wrapper='0x60350bfd'),
  limitations=['Iteration gate has a conditional indirect progress callback whose effects are not qualified.',
   'The 1000 wait argument is not converted to wall-clock units.',
   'Timeout/cancellation cleanup is not proof that all hardware readers are quiescent.',
   'Current stage callbacks and every error/alternate processing path are not exhaustively mapped.',
   'Descriptor completion flags and operation event tokens are separate contracts.',
   'No safe H/L extension memory or firmware patch is established.'],
  camera_accessed=False,firmware_executed=False,flash_ready=False)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path)
 a=p.parse_args();print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
