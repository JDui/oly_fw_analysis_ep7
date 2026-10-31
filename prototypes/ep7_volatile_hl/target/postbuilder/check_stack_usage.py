#!/usr/bin/env python3
"""Compile-only GCC per-function stack estimates, not camera stack headroom."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 manifest=json.loads((ROOT/'prototypes/ep7_volatile_hl/target/build-manifest.json').read_text())
 for p,h in manifest['tools'].items():
  if sha(ROOT/p)!=h:raise ValueError('tool hash mismatch')
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc'
 sources=[HERE/'native_observer.c',ROOT/'prototypes/ep7_volatile_hl/runtime/runtime.c',ROOT/'prototypes/ep7_volatile_hl/ep7p.c',ROOT/'prototypes/ep7_volatile_hl/ep7p_decode.c',ROOT/'prototypes/ep7_volatile_hl/target/memory.c'];functions={};inputs={}
 with tempfile.TemporaryDirectory(prefix='ep7-stack-estimate-') as tmp:
  for p in sources:
   asm=Path(tmp)/(p.stem+'.s')
   subprocess.run([str(gcc),'-B'+str(gcc.parent)+'/','-std=c11','-O2','-ffreestanding','-fno-builtin','-fno-tree-loop-distribute-patterns','-mno-setlb','-mno-liw','-fstack-usage','-I'+str(ROOT/'prototypes/ep7_volatile_hl'),'-I'+str(ROOT/'prototypes/ep7_volatile_hl/target/include'),'-S',str(p),'-o',str(asm)],check=True)
   inputs[str(p.relative_to(ROOT))]=sha(p)
   usages={}
   for line in asm.with_suffix('.su').read_text().splitlines():
    label,size,kind=line.split('\t');usages[label.rsplit(':',1)[1]]=(int(size),kind)
   text=asm.read_text()
   for name,(size,kind) in usages.items():
    marker='_'+name+':';start=text.find(marker)
    end=text.find('\n\t.size\t_'+name+',',start)
    body=text[start:end] if start>=0 and end>=0 else ''
    calls=re.findall(r'^\t(call|calls)\s+([^\n]+)',body,re.M)
    functions[name]=dict(frame_bytes=size,kind=kind,emitted_calls=[f'{op} {arg}' for op,arg in calls])
 return dict(source_hashes=inputs,compiler_reported_functions=functions,native_wrapper_nested_builder_extra_bytes=96,observer_frame_excludes_callee_frames=True,unknown_lock_unlock_callback_depth=True,interrupt_stack_margin_unknown=True,actual_task_stack_capacity_unknown=True,target_executed=False,target_linked=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
