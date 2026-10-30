#!/usr/bin/env python3
"""Bounded read-only CPU semaphore result/ACK join; no API invocation."""
import argparse,json
from pathlib import Path
import ep7_private_semaphore as base
WINDOWS=[(0x60053e48,0x60053f4f),(0x60053fb2,0x600540c5),(0x60054197,0x600541d0),(0x600544f0,0x60054566),(0x60037261,0x60037397),(0x60053c5e,0x60053cce)]
W={0x60053e5f:('cmp','7,d1'),0x60053e63:('jmp','0x60053eee'),0x60053e66:('cmp','8,d1'),0x60053e6a:('jmp','0x60053efb'),0x60053ef2:('call','0x60035b62,[d2,d3,a2],16'),0x60053f04:('call','0x600370af,[d2,d3,a2,a3],24'),0x60053f18:('mov','d0,(8,a2)'),0x60053f20:('mov','5,d0'),0x60053f22:('mov','d0,(48,a2)'),0x60053f25:('add','12,a2'),0x60053f27:('mov','(a2),d0'),
0x60053fb7:('call','0x600317ac,[a2],4'),0x60053fc4:('mov','d2,(a0)'),0x60053fce:('movhu','d0,(a0)'),0x60053fd5:('mov','3,d0'),0x60053fd7:('mov','d0,(48,a3)'),0x6005405e:('mov','16,a2'),0x60054060:('add','a3,a2'),0x60054062:('mov','(a2),d1'),0x60054063:('mov','1,a1'),0x60054065:('call','0x60037261,[d2,d3,a2,a3],32'),0x6005406d:('mov','d0,d2'),0x60054071:('call','0x60030a3f,[d2,d3,a2,a3],20'),0x6005407d:('cmp','0,d2'),0x6005407f:('beq','0x600540bf'),0x60054088:('call','0x60022694,[d2,a2],24'),0x600540bf:('mov','(8,a3),d0'),0x600540c2:('ret','[d2,d3,a2,a3],36'),
0x600541a0:('cmp','5,d0'),0x600541a2:('bne','0x600541c7'),0x600541a4:('mov','6,d0'),0x600541a6:('mov','d0,(a2)'),0x600541ad:('mov','(a3),d1'),0x600541af:('call','0x60038422,[d2,d3,a2,a3],20'),
0x60054513:('cmp','0,d0'),0x60054517:('mov','1,d0'),0x60054519:('mov','d0,(a0)'),0x6005451b:('asl','d2,d1'),0x6005451d:('mov','d1,(16,a2)'),0x60054537:('mov','0,a2'),0x60054542:('mov','a2,a0'),0x60054546:('retf','[],0'),0x60054551:('clr','d0'),0x60054552:('mov','52,d1'),0x60054555:('call','0x4700115e,[d2,a2],8'),
0x600372c8:('mov','-25,d0'),0x60037336:('and','d2,d0'),0x60037338:('beq','0x60037350'),0x60037376:('call','0x600343d7,[d2,a2,a3],20'),0x60037387:('mov','(a2),d0'),0x60037393:('clr','d0'),0x60037394:('ret','[d2,d3,a2,a3],32'),
0x60053c7b:('call','0x60053fb2,[d2,d3,a2,a3],36'),0x60053c80:('mov','d0,d2'),0x60053c82:('call','0x60054549,[a2],8'),0x60053c8e:('mov','d2,d0'),0x60053cb7:('call','0x60053fb2,[d2,d3,a2,a3],36'),0x60053cbc:('mov','d0,d2'),0x60053cbe:('call','0x60054549,[a2],8'),0x60053cca:('mov','d2,d0')}
def inspect(raw,od):
 oldw,oldwindows=base.W,base.WINDOWS
 try:
  base.W,base.WINDOWS=W,WINDOWS
  evidence=base.inspect(raw,od)
 finally:base.W,base.WINDOWS=oldw,oldwindows
 return dict(source_sha256=evidence['source_sha256'],windows=evidence['windows'],witness_count=len(W),normal_remote_result_before_completion_signal=True,wait_error_does_not_gate_record_result_load=True,record_released_after_submitter_returns=True,rejecting_positive_255_alone_qualifies_lock=False,error_reachability_on_camera_proven=False,cross_core_visibility_qualified=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path);a=p.parse_args();print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
