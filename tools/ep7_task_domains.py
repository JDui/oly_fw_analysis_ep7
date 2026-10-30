#!/usr/bin/env python3
"""Bounded GUI task birth / kind19 worker configuration evidence, read-only."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ep7_private_semaphore as base
WINDOWS=[(0x60cfceba,0x60cfcf0a),(0x60dd5067,0x60dd5083),(0x607a7968,0x607a799c),(0x60779102,0x60779167),(0x607791cd,0x6077920a),(0x6077925e,0x60779263),(0x6077a4ab,0x6077a4e8),(0x6077a542,0x6077a648),(0x60051d66,0x60051d82),(0x60051e3a,0x60051e6c),(0x60051f29,0x60051f67),(0x60030619,0x6003071e),(0x60034e3f,0x60034f31),(0x6005b42d,0x6005b453),(0x6005b52a,0x6005b543)]
W={0x60cfcec4:('mov','1625116775,d0'),0x60cfceca:('mov','d0,(12,sp)'),0x60cfcecc:('mov','1,d2'),0x60cfcece:('mov','d2,(16,sp)'),0x60cfced0:('mov','16384,d0'),0x60cfced3:('mov','d0,(20,sp)'),0x60cfced5:('clr','d0'),0x60cfced6:('mov','d0,(24,sp)'),0x60cfceda:('mov','1626947848,a1'),0x60cfcee3:('add','12,d1'),0x60cfcee5:('call','0x607a791e,[d2,d3,a2,a3],36'),0x60dd5079:('call','0x60cfd311,[d2,d3,a2,a3],16'),0x607a7968:('call','0x60779102,[],4'),0x607a796f:('mov','a3,(4,sp)'),0x607a7973:('mov','(a0),a2'),0x607a7976:('mov','(4,a2),a2'),0x607a7979:('calls','(a2)'),0x6077913c:('call','0x607791cd,[a2],8'),0x60779143:('mov','d0,(0x61fa8f90)'),0x60779159:('mov','(0x61fa8f90),a0'),0x6077915f:('call','0x6077925e,[],0'),0x607791ec:('mov','16,a0'),0x607791ee:('add','a2,a0'),0x607791f0:('call','0x6077a4ab,[a2],8'),0x6077925e:('add','16,a0'),0x6077a4ac:('mov','1621623120,d0'),0x6077a4b2:('mov','d0,(a2)'),0x6077a553:('mov','(80,sp),a2'),0x6077a5ab:('mov','(4,a2),d0'),0x6077a5ae:('mov','55,d1'),0x6077a5c9:('mov','(12,a2),d0'),0x6077a5d4:('mov','(a2),d0'),0x6077a5d5:('mov','d0,(44,sp)'),0x6077a5d7:('movhu','d1,(48,sp)'),0x6077a5ee:('movhu','(48,sp),d0'),0x6077a5f3:('mov','(44,sp),a1'),0x6077a600:('clr','d0'),0x6077a601:('call','0x60051d66,[d2,d3,a2,a3],56'),0x60051d67:('movbu','d0,(12,sp)'),0x60051d78:('mov','(0x8050),d3'),0x60051e3a:('clr','d0'),0x60051e3b:('movbu','d0,(16,sp)'),0x60051e40:('mov','a2,(24,sp)'),0x60051e4b:('add','16,a0'),0x60051e53:('call','0x60030619,[d2,a2,a3],20'),0x60051f29:('movbu','(12,sp),d3'),0x60051f2c:('cmp','2,d3'),0x60051f31:('call','0x6003071f,[d2,d3,a2],16'),0x60030695:('call','0x60034e3f,[d2,d3,a2,a3],24'),0x600306a3:('movhu','d0,(16,a0)'),0x60034ee3:('mov','(0x8050),d3'),0x60034ee8:('asl','12,d3'),0x60034eeb:('or','d3,d1'),0x60034f27:('movhu','d1,(16,a1)'),0x6005b437:('mov','1610844624,a2'),0x6005b447:('movhu','(a2),d0'),0x6005b44c:('call','0x60034ae3,[d2,a2,a3],16'),0x6005b52d:('udfu01','28,d0'),0x6005b532:('add','1610844624,a2')}
def inspect(raw,od):
 oldw,oldwindows=base.W,base.WINDOWS
 try:
  base.W,base.WINDOWS=W,WINDOWS;r=base.inspect(raw,od)
 finally:base.W,base.WINDOWS=oldw,oldwindows
 main=base.parse(raw)[0].payload
 row=struct.unpack_from('<7I',main,0x600395a0-base.BASE)
 if row!=(0x6c,0,0,0x603f26a1,26,8192,0):raise ValueError('worker row mismatch')
 if struct.unpack_from('<I',main,0x60a80154-base.BASE)[0]!=0x6077a542:raise ValueError('GUI task creator slot mismatch')
 return dict(source_sha256=r['source_sha256'],windows=r['windows'],witness_count=len(W),gui_task_entry='0x60dd5067',gui_task_loop_entry='0x60cfd311',gui_dynamic_task_domain_inherits_creator=True,gui_creator_domain_proven=False,worker_config=dict(address='0x600395a0',configured_id='0x006c',entry='0x603f26a1',priority=26,stack_bytes=8192,row_sha256=hashlib.sha256(main[0x600395a0-base.BASE:0x600395bc-base.BASE]).hexdigest()),worker_loader_domain_binding_proven=False,gui_and_worker_same_domain_proven=False,capture_snapshot_producer_domain_proven=False,separate_domain_value_copy_design_possible_but_unimplemented=True,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True);a=p.parse_args();print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
