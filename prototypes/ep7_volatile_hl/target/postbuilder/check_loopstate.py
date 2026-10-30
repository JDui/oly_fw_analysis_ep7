#!/usr/bin/env python3
"""Compile-only loop-register use audit of current self-authored C objects."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 manifest=json.loads((ROOT/'prototypes/ep7_volatile_hl/target/build-manifest.json').read_text())
 for p,h in manifest['tools'].items():
  if sha(ROOT/p)!=h:raise ValueError('tool hash mismatch')
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 sources=[HERE/'native_observer.c']+[ROOT/'prototypes/ep7_volatile_hl'/name for name in ['ep7p.c','ep7p_ui.c','ep7p_decode.c','target/memory.c']]
 forbidden={'setlb','leq','lne','lgt','lge','lle','llt','lhi','lcc','lls','lcs','lra'};reports={}
 flags=['-std=c11','-O2','-ffreestanding','-fno-builtin','-fno-tree-loop-distribute-patterns','-mno-setlb','-mno-liw']
 with tempfile.TemporaryDirectory(prefix='ep7-loopstate-audit-') as tmp:
  for p in sources:
   asm=Path(tmp)/(p.stem+'.s');obj=Path(tmp)/(p.stem+'.o')
   subprocess.run([str(gcc),'-B'+str(gcc.parent)+'/',*flags,'-I'+str(ROOT/'prototypes/ep7_volatile_hl/target/include'),'-I'+str(ROOT/'prototypes/ep7_volatile_hl'),'-S',str(p),'-o',str(asm)],check=True)
   subprocess.run([str(gas),'-o',str(obj),str(asm)],check=True)
   dis=subprocess.check_output([str(od),'-dr','--insn-width=16',str(obj)],text=True)
   ops=set(re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s',dis,re.M))
   if ops&forbidden or re.search(r'\b(?:lir|lar|epsw|mdrq|mcrh|mcrl|mcvf|e[0-7]|fs[0-9]+)\b',asm.read_text()):raise ValueError('loop/extended state used')
   reports[str(p.relative_to(ROOT))]=dict(source_sha256=sha(p),object_sha256=sha(obj),mnemonics=sorted(ops),loop_register_use_found=False,extended_register_use_found=False)
 return dict(compile_flags=flags,objects=reports,transitive_unknown_callees_qualified=False,target_executed=False,target_linked=False,firmware_executed=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
