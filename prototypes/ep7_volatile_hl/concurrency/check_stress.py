#!/usr/bin/env python3
"""Run self-authored host pthread tests only. No target build/execution or firmware."""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CORE=ROOT/'prototypes/ep7_volatile_hl'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 sources=[HERE/'stress.c',CORE/'ep7p.c',CORE/'ep7p_decode.c']
 flags=['-std=c11','-O2','-Wall','-Wextra','-Werror','-pedantic','-pthread','-I'+str(CORE)]
 results=[]
 with tempfile.TemporaryDirectory(prefix='ep7-pthread-host-') as tmp:
  for kind,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']),('tsan',['-fsanitize=thread','-fno-sanitize-recover=all','-fno-omit-frame-pointer'])]:
   exe=Path(tmp)/kind
   compile_result=subprocess.run(['cc',*flags,*extra,*map(str,sources),'-o',str(exe)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
   if compile_result.returncode:
    if kind!='tsan': raise RuntimeError(compile_result.stderr)
    results.append(dict(configuration=kind,compiled=False,passed=False,diagnostic=compile_result.stderr));continue
   env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=0';env['TSAN_OPTIONS']='halt_on_error=1'
   r=subprocess.run([str(exe)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=60)
   if r.returncode:raise RuntimeError(kind+' runtime failed: '+r.stderr)
   results.append(dict(configuration=kind,compiled=True,passed=r.returncode==0,exit_code=r.returncode,stdout=r.stdout.strip(),stderr=r.stderr.strip()))
 return dict(source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources+[CORE/'ep7p.h',CORE/'ep7p_direct.h',CORE/'ep7p_decode.h']},compiler=subprocess.check_output(['cc','--version'],text=True).splitlines()[0],results=results,host_multithread_stress_tested=True,host_pthread_adapter_only=True,native_RTOS_qualified=False,leak_sanitizer_enabled=False,firmware_input_used=False,target_executed=False,camera_accessed=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
