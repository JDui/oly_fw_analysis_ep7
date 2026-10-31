#!/usr/bin/env python3
"""Native queue critical-section gate seams and deletion wake/return path; no patching or hashes."""
import argparse,json,struct
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_producer_scope import W as PRODUCER_W
from ep7_prepare_input import BASE


def named_send_returns(data):
    """Derive return PCs from the actual native CALL32 bytes, not a copied list."""
    result=[]
    for site in (0x600514ec,0x60051550):
        if data[site-BASE:site-BASE+7]!=b'\xdd'+struct.pack('<i',0x60036ede-site)+b'\xf0\x28':
            raise ValueError('named send CALL32/target/frame changed')
        result.append(hex(site+7))
    return result

WINDOWS=[(0x6003103d,0x60031107),(0x600344b2,0x60034535),
    (0x60036d0c,0x60036e23),(0x60036f63,0x600370af),
    (0x600514ec,0x600514f3),(0x60051550,0x60051557),(0x600515d4,0x600515de)]
W={a:PRODUCER_W[a] for a in [0x600514ec,0x60051550,0x600515d4,0x600515db]}
W.update({
    0x60031040:('call','0x60038594,[],0'),0x60031048:('mov','(232,a0),a0'),
    0x60031066:('mov','(-4,a0),a3'),0x6003106b:('cmp','0,a3'),0x6003106d:('bne','0x60031072'),
    0x60031072:('mov','20,a0'),0x60031074:('add','a3,a0'),0x60031076:('movbu','(a0),d0'),
    0x60031078:('btst','128,d0'),0x6003107b:('beq','0x60031085'),
    0x6003107d:('mov','(12,a0),a0'),0x60031080:('call','0x60035ffa,[d2,a2,a3],12'),
    0x60031085:('mov','a3,a2'),0x60031086:('inc4','a2'),
    0x6003108e:('mov','-51,d0'),0x60031090:('call','0x600344b2,[a2,a3],12'),
    0x60031098:('bne','0x6003108c'),0x6003109a:('add','12,a3'),
    0x600310a3:('mov','-51,d0'),0x600310a5:('call','0x600344b2,[a2,a3],12'),
    0x600310ad:('bne','0x600310a1'),0x600310f5:('clr','d0'),0x600310f6:('movhu','d0,(a0)'),
    0x600310f8:('call','0x6003593f,[d2,a2,a3],16'),0x600310fe:('call','0x6003860b,[],0'),
    0x60031104:('ret','[d2,d3,a2,a3],24'),
    0x600344b2:('mov','d0,(64,a0)'),0x600344bf:('mov','(0x8050),d1'),
    0x600344c3:('bne','0x60034508'),0x600344de:('mov','a0,a3'),
    0x600344df:('mov','(a0),a2'),0x600344e1:('inc4','a3'),0x600344e2:('mov','(a3),a1'),
    0x600344e4:('mov','a1,(4,a2)'),0x600344e7:('mov','a2,(a1)'),
    0x60034501:('call','0x6003430d,[a2],4'),
    0x60036d0f:('call','0x60038594,[],0'),0x60036d17:('mov','(232,a0),a0'),
    0x60036d30:('mov','(-4,a0),a2'),0x60036d33:('cmp','0,a2'),0x60036d35:('bne','0x60036d3c'),
    0x60036d37:('mov','-42,d0'),0x60036d39:('jmp','0x60036e17'),
    0x60036d3c:('mov','(0x8050),d0'),0x60036d3f:('asl2','d0'),0x60036d40:('mov','-1880096764,a0'),
    0x60036d46:('mov','(d0,a0),a1'),0x60036d48:('mov','(96,a1),a1'),
    0x60036d5b:('call','0x60033ad9,[d2,d3,a2,a3],36'),
    0x60036d65:('call','0x60033ad9,[d2,d3,a2,a3],36'),
    0x60036e08:('call','0x600343d7,[d2,a2,a3],20'),
    0x60036e0d:('mov','64,a2'),0x60036e0f:('add','d3,a2'),0x60036e11:('mov','(a2),d0'),
    0x60036e12:('cmp','0,d0'),0x60036e14:('bne','0x60036e17'),0x60036e16:('mov','(a3),d0'),
    0x60036e17:('mov','d0,(12,sp)'),0x60036e19:('call','0x6003860b,[],0'),
    0x60036e1e:('mov','(12,sp),d0'),0x60036e20:('ret','[d2,d3,a2,a3],32'),
    0x60036f66:('call','0x60038594,[],0'),0x60036f6e:('mov','(232,a0),a0'),
    0x60036f87:('mov','(-4,a0),a2'),0x60036f8a:('cmp','0,a2'),0x60036f8c:('bne','0x60036f93'),
    0x60036f8e:('mov','-42,d0'),0x60036f90:('jmp','0x600370a3'),
    0x60036f93:('mov','(20,sp),d0'),0x60036f95:('mov','20,d3'),0x60036f97:('add','a2,d3'),
    0x60036f99:('mov','d3,a0'),0x60036f9b:('mov','(4,a0),d1'),0x60036f9e:('cmp','d0,d1'),
    0x60037095:('call','0x600343d7,[d2,a2,a3],20'),
    0x6003709a:('mov','64,a2'),0x6003709c:('add','d2,a2'),0x6003709e:('mov','(a2),d0'),
    0x6003709f:('cmp','0,d0'),0x600370a1:('beq','0x600370a5'),
    0x600370a3:('mov','d0,(8,sp)'),0x600370a5:('call','0x6003860b,[],0'),
    0x600370aa:('mov','(8,sp),d0'),0x600370ac:('ret','[d2,d3,a2,a3],40'),
})

def inspect(stock,objdump):
    returns=[]
    e=inspect_windows(stock,objdump,WINDOWS,W,observe_data=lambda data:returns.extend(named_send_returns(data)))
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],
        hooks=[dict(entry='0x60036d3c',replay_bytes=10,object_register='a2',continuation='0x60036d46',error='0x60036e17'),
               dict(entry='0x60036f93',replay_bytes=6,object_register='a2',continuation='0x60036f99',error='0x600370a3'),
               dict(entry='0x60031072',replay_bytes=6,object_register='a3',continuation='0x60031078')],
        gate_after_native_critical_entry_and_live_lookup=True,
        deleted_waiter_status=-51,waiter_removed_before_ready=True,
        negative_receive_wakeup_skips_length_and_copy=True,
        native_send_returns_wakeup_status=True,gate_rejection_status=-42,
        raw_frame_bytes=dict(receive=32,send=40,delete=24),named_send_frame_bytes=48,
        named_send_raw_return_sites=returns,named_returns_derived_from_call32_bytes=True,
        candidate_caller_return_offsets=dict(receive=32,raw_send=40,named_send=88),
        native_delete_and_notification_retained=True,live_reenable_supported=False,
        all_queue_callers_and_task_exits_qualified=False,atomic_installation_proved=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
