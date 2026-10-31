#!/usr/bin/env python3
"""Reuse object sizes and check target type sizes against the actual cold runtime storage."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'prototypes/ep7_volatile_hl'
REPORTS=['research/ep7/pipeline-far-call-target.json','research/ep7/ui-far-call-target.json',
         'research/ep7/pipeline-installation-cohort.json','research/ep7/cold-bootstrap.json']
COLD_REPORT='research/ep7/cold-clear-semantics.json'
# These compiler-call probes verify ABI; they are not runtime implementation.
PROBES={'prototypes/ep7_volatile_hl/snapshot_transport/native/worker_caller.c',
        'prototypes/ep7_volatile_hl/text_lifecycle/factory_caller.c'}
SOURCE='''#include "runtime/runtime.h"
struct cold_storage { ep7p core; ep7b boot; ep7r runtime; };
unsigned char ep7_size_core[sizeof(ep7p)];
unsigned char ep7_size_boot[sizeof(ep7b)];
unsigned char ep7_size_runtime[sizeof(ep7r)];
unsigned char ep7_size_cold_storage[sizeof(struct cold_storage)];
unsigned char ep7_align_cold_storage[_Alignof(struct cold_storage)];
'''


def inspect(prefix):
    objects={}
    for relative in REPORTS:
        report=json.loads((ROOT/relative).read_text(encoding='utf-8-sig'))
        for row in report['objects'].values():
            source=row['source']
            if source in PROBES:
                continue
            if not (ROOT/source).is_file():
                raise ValueError('missing implementation source '+source)
            sizes=[int(x) for x in row['size_output'][:3]]
            if source in objects and objects[source]['text_data_bss']!=sizes:
                raise ValueError('conflicting historical size measurements for '+source)
            objects.setdefault(source,dict(text_data_bss=sizes,reports=[]))['reports'].append(relative)
    cold=json.loads((ROOT/COLD_REPORT).read_text(encoding='utf-8-sig'))
    if not (ROOT/cold['source']).is_file() or cold['source'] in objects:
        raise ValueError('missing or duplicate cold-clear implementation source')
    objects[cold['source']]=dict(text_data_bss=cold['text_data_bss'],reports=[COLD_REPORT])
    gcc=prefix+'gcc'
    include=subprocess.check_output([gcc,'-print-file-name=include'],text=True).strip()
    version=subprocess.check_output([gcc,'--version'],text=True).splitlines()[0]
    flags=['-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin',
           '-mno-setlb','-mno-liw','-nostdinc','-I'+str(CORE/'target/include'),
           '-I'+include,'-I'+str(CORE)]
    sizes={}
    with tempfile.TemporaryDirectory(prefix='ep7-budget-') as temp:
        obj=Path(temp)/'storage-sizes.o'
        subprocess.run([gcc,*flags,'-x','c','-c','-','-o',str(obj)],input=SOURCE,text=True,check=True)
        symbols=subprocess.check_output([prefix+'nm','-S','--defined-only',str(obj)],text=True)
        for line in symbols.splitlines():
            _,size,kind,name=line.split()
            if kind.upper()!='B' or not name.startswith('_ep7_'):
                raise ValueError('unexpected size-probe symbol: '+line)
            sizes[name.removeprefix('_ep7_')]=int(size,16)
    expected={'size_core','size_boot','size_runtime','size_cold_storage','align_cold_storage'}
    if set(sizes)!=expected:
        raise ValueError('incomplete target type size measurements')
    totals=[sum(row['text_data_bss'][i] for row in objects.values()) for i in range(3)]
    startup=json.loads((ROOT/'research/ep7/cold-bootstrap.json').read_text(encoding='utf-8-sig'))
    if startup['production_runtime_storage_bytes']!=sizes['size_cold_storage']:
        raise ValueError('production cold storage differs from current header types')
    # The runtime instance now exists in cold_bootstrap.c BSS. Do not add its
    # former forecast5704 bytes a second time on top of the measured object.
    required=totals[1]+totals[2]
    return dict(scope=__doc__,compiler=version,
        prior_object_reports=REPORTS+[COLD_REPORT],prior_measurements_recompiled=False,
        implementation_sources=len(objects),excluded_abi_probe_sources=sorted(PROBES),
        prior_unlinked_text_data_bss=totals,prior_object_sizes=objects,
        current_target_type_sizes=sizes,new_objects_compiled=1,
        production_runtime_storage_already_in_bss=True,additional_forecast_runtime_storage_bytes=0,
        rough_static_storage_bytes=required,reservation_payload_bytes=16384,
        rough_remaining_storage_bytes=16384-required,
        storage_budget_fits_before_link_alignment=required<=16384,
        limits=['Historical object sizes are reused, not revalidated against every current source.',
                'Only the current header type sizes are freshly compiled; no target code is executed.',
                'No linker layout, alignment, installer storage, native queue growth or full stack is included.',
                'Production cold storage is included once via its object; this probe reserves no target memory.'],
        target_linked=False,target_executed=False,firmware_built=False,hash_checks_performed=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-prefix',required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.tool_prefix),indent=2))
