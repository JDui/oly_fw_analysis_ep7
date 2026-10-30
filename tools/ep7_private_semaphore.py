#!/usr/bin/env python3
"""Pinned stock, read-only private-semaphore facility witnesses; not an adapter."""
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE
from ep7_request_ownership import require_instruction
from oly_container import parse
WINDOWS=[(0x6003057f,0x60030619),(0x60034f31,0x60035023),(0x60053c5e,0x60053cce),(0x60035b62,0x60035c3b),(0x600370af,0x60037201),(0x60051619,0x600517c7),(0x60051c62,0x60051d3a),(0x6005378e,0x600537b2),(0x6005393a,0x6005398a),(0x60c4fbb6,0x60c4fbdf)]
W={
0x6003057f:('mov','a0,a2'),0x60030580:('movbu','(a2),d0'),0x6003058a:('mov','-11,d2'),0x6003059b:('mov','(28,a0),a0'),0x600305b4:('movbu','(1,a1),d0'),0x600305bb:('mov','-25,d2'),0x600305c0:('inc4','a1'),0x600305c1:('mov','(a1),d0'),0x600305c6:('mov','65535,d1'),0x600305cf:('mov','8,a0'),0x600305dd:('bls','0x600305e3'),0x600305df:('mov','-17,d2'),0x600305ec:('call','0x60034f31,[d2,d3,a2,a3],24'),0x60030602:('setlb',''),0x60030608:('lne',''),0x60030616:('ret','[d2,a2],16'),
0x60035bc0:('ret','[d2,d3,a2],16'),0x60035bd1:('mov','-25,d0'),0x60035c06:('mov','-42,d0'),0x60035c11:('mov','(20,a1),d0'),0x60035c18:('mov','(a0),d1'),0x60035c1a:('bcs','0x60035c25'),0x60035c21:('mov','-43,d0'),0x60035c25:('mov','(a0),d0'),0x60035c26:('inc','d0'),0x60035c27:('mov','d0,(a0)'),0x60035c2d:('call','0x6003442c,[a2,a3],12'),0x60035c37:('clr','d0'),0x60035c38:('ret','[d2,d3,a2],16'),
0x60037165:('mov','(a0),d0'),0x60037166:('cmp','1,d0'),0x60037168:('bcs','0x60037172'),0x6003716c:('sub','d1,d0'),0x6003716e:('mov','d0,(a0)'),0x60037183:('mov','(4,sp),d0'),0x60037185:('cmp','0,d0'),0x60037187:('bne','0x60037193'),0x6003718e:('mov','-50,d0'),0x60037193:('cmp','-1,d0'),0x60037195:('beq','0x600371d7'),0x600371fe:('ret','[d2,d3,a2,a3],24'),
0x60051623:('call','0x60031107,[d2,d3,a2,a3],20'),0x6005168a:('ret','[d2,d3,a2,a3],32'),0x6005168d:('mov','d0,d3'),0x6005168e:('mov','d1,d2'),0x60051695:('call','0x6005393a,[d2,d3],16'),0x600516a1:('call','0x60053c92,[d2,d3,a2,a3],20'),0x600516b1:('call','0x600370af,[d2,d3,a2,a3],24'),0x600516ca:('mov','-2,a2'),0x600516d0:('cmp','-50,d0'),0x600516d7:('mov','-1,a2'),0x6005175f:('ret','[d2,d3,a2],40'),0x6005176e:('call','0x60053c5e,[d2,d3,a2],16'),0x6005177d:('call','0x60035b62,[d2,d3,a2],16'),0x600517aa:('mov','-1,d3'),0x600517c4:('ret','[d2,d3],36'),
0x60051c8e:('mov','a0,a3'),0x60051c8f:('mov','d1,a2'),0x60051c91:('mov','d0,d2'),0x60051ca9:('movbu','d0,(12,sp)'),0x60051cac:('mov','d2,(16,sp)'),0x60051cae:('mov','a2,(20,sp)'),0x60051cb3:('call','0x6003057f,[d2,a2],16'),0x60051cc7:('ble','0x60051d35'),0x60051cf7:('cmp','64,d2'),0x60051cf9:('bcc','0x60051d1d'),0x60051d0f:('movhu','d0,(16,a0)'),0x60051d1a:('exth','d0'),0x60051d35:('mov','-1,d0'),0x60051d37:('ret','[d2,d3,a2,a3],40'),
0x60c4fbc3:('mov','1,d0'),0x60c4fbc5:('mov','d0,d1'),0x60c4fbc6:('call','0x60051c8e,[d2,d3,a2,a3],40'),0x60c4fbce:('mov','d0,(a2)'),0x60c4fbd1:('bge','0x60c4fbdc')}
W.update({
0x60034f4a:('mov','(208,a1),d0'),0x60034fba:('mov','-34,d0'),0x60034fd6:('mov','(0x8050),d3'),0x60034fdb:('asl','12,d3'),0x60034fde:('or','d3,d1'),0x60035007:('mov','4095,d3'),0x6003501a:('movhu','d1,(a1)'),0x60035020:('retf','[d2,d3,a2,a3],24'),
0x60035b91:('mov','28672,d2'),0x60035b96:('asr','12,d2'),0x60035ba6:('mov','4095,d3'),
0x60053959:('call','0x600317ac,[a2],4'),0x60053960:('mov','32768,d3'),0x6005397a:('and','12288,d1'),0x6005397e:('and','12288,d2'),0x60053982:('cmp','d1,d2'),0x60053985:('mov','1,d0'),
0x60053c63:('call','0x600544f0,[d2,d3,a2,a3],24'),0x60053c69:('cmp','0,a2'),0x60053c6b:('beq','0x60053c89'),0x60053c70:('mov','7,d0'),0x60053c7b:('call','0x60053fb2,[d2,d3,a2,a3],36'),0x60053c89:('mov','255,d0'),0x60053c8f:('ret','[d2,d3,a2],16'),
0x60053c99:('call','0x600544f0,[d2,d3,a2,a3],24'),0x60053c9f:('cmp','0,a2'),0x60053ca1:('beq','0x60053cc5'),0x60053cac:('mov','8,d0'),0x60053cb7:('call','0x60053fb2,[d2,d3,a2,a3],36'),0x60053cc5:('mov','255,d0'),0x60053ccb:('ret','[d2,d3,a2,a3],20'),0x600516c5:('blt','0x600516ca'),0x60051790:('bge','0x600517c3')})
W.update({0x6005378e:('mov','d0,d2'),0x60053791:('bge','0x60053798'),0x60053798:('mov','d2,d0'),0x60053799:('ret','[d2],8'),0x6005379c:('mov','d0,d2'),0x6005379f:('bge','0x600537ae'),0x600537ae:('mov','d2,d0'),0x600537af:('ret','[d2],8'),0x6005168f:('mov','0,a2'),0x6005175d:('mov','a2,d0'),0x60051763:('clr','d3'),0x600517c3:('mov','d3,d0')})
OD_SHA='d6b4b56a93d7efa1eb62f6e6f4a3fbd2fc2eba0d2518ad45e52d287658994268'
def inspect(raw,od):
 identity=audit(raw) # full exact stock guard BEFORE decoding/disassembly
 if hashlib.sha256(od.read_bytes()).hexdigest()!=OD_SHA:raise ValueError('unrecognized objdump')
 main=parse(raw)[0].payload;windows=[]
 with tempfile.TemporaryDirectory(prefix='ep7-private-sem-') as tmp:
  path=Path(tmp)/'main.bin';path.write_bytes(main)
  for lo,hi in WINDOWS:
   asm=subprocess.check_output([str(od),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={lo:#x}',f'--stop-address={hi:#x}',str(path)],text=True)
   for addr,(op,args) in W.items():
    if lo<=addr<hi:require_instruction(asm,addr,op,args)
   windows.append(dict(start=hex(lo),end_exclusive=hex(hi),sha256=hashlib.sha256(main[lo-BASE:hi-BASE]).hexdigest()))
 return dict(source_sha256=identity['source_sha256'],windows=windows,witness_count=len(W),raw_create_struct=dict(attribute_byte=0,initial_u32=4,maximum_u32=8,size=12),binary_initial_maximum=[1,1],poll_timeout=0,raw_empty_poll_status=-50,wrapper_empty_poll_status=-2,raw_overrelease_status=-43,creation_wrapper_has_postallocation_metadata_capacity=64,encoded_handle_core_shift=12,encoded_handle_index_mask='0x0fff',wrapper_routing_mask='0x3000',cpu_transport_null_record_status=255,wrapper_nonnegative_false_success_branch=True,private_semaphore_created=False,adapter_implemented=False,timeout_units_proven=False,recursive_mutex_proven=False,priority_inheritance_proven=False,cross_domain_runtime_qualified=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path);a=p.parse_args();print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
