#!/usr/bin/env python3
"""Bounded queue teardown and remote receive result evidence, no execution."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows

WINDOWS=[(0x603df93a,0x603df97d),(0x603eeb39,0x603eeb57),
         (0x60051372,0x600513e6),(0x60053ab0,0x60053b29),
         (0x60053e90,0x60053ea5),(0x60053f18,0x60053f25),
         (0x603ef998,0x603ef9bb),(0x603f2770,0x603f2799)]
W={
    0x603ef9a6:('movhu','(0x60040e32),d0'),
    0x603ef9ad:('call','0x603df93a,[d2,d3],20'),
    0x603f2783:('movhu','(0x60040d7a),d0'),
    0x603f2789:('mov','d2,d1'),
    0x603f278b:('call','0x603df93a,[d2,d3],20'),
    0x603df93a:('mov','d0,d3'),
    0x603df96b:('mov','d3,d0'),
    0x603df96c:('call','0x603eeb4d,[],4'),
    0x603df973:('call','0x603eeb39,[],4'),
    0x603eeb39:('call','0x60051a51,[],8'),
    0x603eeb4d:('call','0x60051372,[d2,d3,a2,a3],32'),
    0x60051379:('mov','d0,d3'),
    0x6005137a:('exth','d3'),
    0x6005137b:('mov','d3,d0'),
    0x6005137c:('call','0x60030fb7,[d2,d3,a2,a3],24'),
    0x60051383:('mov','1611084504,a0'),
    0x60051389:('call','0x6005378e,[d2],8'),
    0x600513e1:('mov','a3,d0'),
    0x60053ab0:('mov','d0,(4,sp)'),
    0x60053ab5:('mov','d1,d3'),
    0x60053ab6:('mov','a0,a3'),
    0x60053ab8:('call','0x600544f0,[d2,d3,a2,a3],24'),
    0x60053abd:('mov','a0,a2'),
    0x60053abe:('cmp','0,a2'),
    0x60053ac0:('beq','0x60053b20'),
    0x60053ac8:('mov','d0,(a1)'),
    0x60053ac9:('mov','a3,(4,a1)'),
    0x60053acc:('mov','d3,(8,a1)'),
    0x60053ad2:('mov','2,d0'),
    0x60053ad4:('mov','d0,(a2)'),
    0x60053b12:('call','0x60053fb2,[d2,d3,a2,a3],36'),
    0x60053b17:('mov','d0,d2'),
    0x60053b19:('call','0x60054549,[a2],8'),
    0x60053b20:('mov','255,d0'),
    0x60053b23:('bra','0x60053b26'),
    0x60053b25:('mov','d2,d0'),
    0x60053b26:('ret','[d2,d3,a2,a3],28'),
    0x60053e90:('mov','20,a1'),
    0x60053e92:('add','a0,a1'),
    0x60053e94:('mov','(a1),d0'),
    0x60053e95:('mov','(4,a1),a0'),
    0x60053e98:('mov','(8,a1),d1'),
    0x60053e9c:('call','0x60036c8e,[d2,d3,a2,a3],32'),
    0x60053f18:('mov','d0,(8,a2)'),
}

def inspect(stock,objdump):
    result=inspect_windows(stock,objdump,WINDOWS,W,[(0x600732d8,'<8s',(b'OlyQeDl\0',))])
    report={k:result[k] for k in ('objdump_version','input_structure','checked_instructions',
         'unknown_instruction_addresses','hash_checks_performed','firmware_executed','firmware_modified')}
    report.update(scope=__doc__,queue_teardown_calls=['0x603ef9ad','0x603f278b'],
        queue_teardown_wrapper='0x60051372',remote_receive='0x60053ab0',
        remote_allocation_failure_result=255,positive_result_alone_proves_received=False,
        raw_backend_receive='0x60036c8e',remote_completion_visibility_qualified=False,
        all_receive_sites_qualified=False,teardown_hook_installed=False,flash_ready=False)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True)
    parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.stock,args.objdump),indent=2))
