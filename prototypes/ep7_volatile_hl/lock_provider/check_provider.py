#!/usr/bin/env python3
"""Execute self-authored host tests; compile/assemble target only, no link."""
import hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CORE=ROOT/'prototypes/ep7_volatile_hl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 manifest=json.loads((CORE/'target/build-manifest.json').read_text())
 for p,d in manifest['tools'].items():
  if sha(ROOT/p)!=d:raise ValueError('untrusted tool '+p)
 cc=Path(shutil.which('cc'));gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 sources=[HERE/'ep7_sem_provider.c',HERE/'test_provider.c',CORE/'ep7p.c',CORE/'ep7p_decode.c']
 tests=[]
 with tempfile.TemporaryDirectory(prefix='ep7-provider-') as tmp:
  temp=Path(tmp)
  for name,flags in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
   exe=temp/name
   subprocess.run([str(cc),'-std=c11','-Wall','-Wextra','-Werror','-pedantic','-I'+str(CORE),*flags,*map(str,sources),'-o',str(exe)],check=True)
   env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=0'
   tests.append(dict(configuration=name,output=subprocess.check_output([str(exe)],text=True,env=env).strip(),passed=True))
  asm=temp/'provider.s';obj=temp/'provider.o'
  subprocess.run([str(gcc),'-B'+str(gcc.parent)+'/','-std=c11','-O2','-ffreestanding','-fno-builtin','-mno-setlb','-mno-liw','-Wall','-Wextra','-Werror','-I'+str(CORE/'target/include'),'-I'+str(CORE),'-S',str(HERE/'ep7_sem_provider.c'),'-o',str(asm)],check=True)
  subprocess.run([str(gas),'-o',str(obj),str(asm)],check=True)
  syms=subprocess.check_output([str(od),'-t',str(obj)],text=True)
  undef=sorted(x.split()[-1] for x in syms.splitlines() if '*UND*' in x)
  if undef!=['___atomic_compare_exchange_4']:raise ValueError('changed atomic backend dependencies '+repr(undef))
  digest=sha(obj)
 return dict(sources={str(p.relative_to(ROOT)):sha(p) for p in sources+[HERE/'ep7_sem_provider.h',CORE/'ep7p.h']},host_tests=tests,host_compiler_sha256=sha(cc),target_tool_hashes=manifest['tools'],target_undefined_symbols=undef,target_object_sha256=digest,target_linked=False,target_executed=False,firmware_input_used=False,native_atomic_backend_qualified=False,native_veneer_bound=False,flash_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
