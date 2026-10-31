#!/usr/bin/env python3
"""Original text factory preserves init D0 alongside child A0; no hash guards run."""
import argparse,ast,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
ROOT=Path(__file__).resolve().parents[1]
WINDOWS=[(0x60d337b2,0x60d3381e),(0x60d33b02,0x60d33b3b),
    (0x60d37b4b,0x60d37b53),(0x60d4bfee,0x60d4c000),
    (0x60d4c068,0x60d4c097),(0x60d04928,0x60d0493a),(0x60cfe04f,0x60cfe06f),
    (0x60cfe0c8,0x60cfe0cd)]

def witnesses():
    # Reuse exact native witnesses without importing legacy SHA-checking probes.
    tree=ast.parse((ROOT/'tools/ep7_text_creation.py').read_text())
    old=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='WITNESSES' for t in node.targets))
    w={address:row for address,row in old.items() if any(a<=address<b for a,b in WINDOWS)}
    w.update({0x60d33819:('mov','(4,a0),a0'),0x60d3381c:('jmp','(a0)'),
        0x60d37b4b:('mov','a3,a0'),0x60d37b4c:('bra','0x60d37b50'),
        0x60d37b4e:('mov','0,a0'),0x60d37b50:('ret','[d2,a2,a3],24'),
        0x60d4bfee:('mov','a1,a2'),0x60d4bfef:('mov','a0,a3'),
        0x60d4bff0:('call','0x60d04928,[],4'),0x60d4bff7:('exth','d0'),
        0x60d4bff8:('cmp','0,d0'),0x60d4bffa:('bne','0x60d4c000'),
        0x60d4bffc:('clr','d0'),0x60d4bffd:('ret','[a2,a3],12'),
        0x60d4c092:('mov','1,d0'),0x60d4c094:('ret','[a2,a3],12'),
        0x60d04928:('call','0x60cfdff1,[d2,d3,a2,a3],32'),
        0x60d0492d:('exth','d0'),0x60d0492e:('cmp','0,d0'),0x60d04930:('bne','0x60d04935'),
        0x60d04932:('clr','d0'),0x60d04933:('bra','0x60d04937'),
        0x60d04935:('mov','1,d0'),0x60d04937:('ret','[],4'),
        0x60cfe06c:('clr','d0'),0x60cfe06d:('bra','0x60cfe0ca'),
        0x60cfe0c8:('mov','1,d0'),0x60cfe0ca:('ret','[d2,d3,a2,a3],32')})
    return w

def inspect(stock,objdump):
    e=inspect_windows(stock,objdump,WINDOWS,witnesses(),[(0x60fa8e84,'<2I',(0x8010,0x60d33b02))])
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],factory_entry='0x60d337b2',
        native_factory_save=['d2','a2','a3'],native_factory_frame=24,
        type_register='d0',owner_register='d1',resource_register='a1',
        allocated_child_result='a0',text_initializer_status='d0',
        initializer_result_on_nonnull_child=[0,1],generic_factory_does_not_check_result=True,
        factory_changes_global_allocator_selection=True,veneer_restores_prior_selection=True,
        allocation_failure_status_native_unspecified=True,allocation_failure_status_veneer=0,
        nonnull_failed_init_requires_unattached_rollback=True,
        resource_and_parent_lifetime_proved=False,hash_checks_performed=False,
        firmware_modified=False,target_executed=False,renderer_ready=False,flash_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
