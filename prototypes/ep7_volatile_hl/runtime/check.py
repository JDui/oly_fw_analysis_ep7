#!/usr/bin/env python3
"""Focused runtime host checks with mocked native facts; no hashes or target execution."""
import json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
CORE=HERE.parent

def check():
    targets={'queue_view':[HERE/'test_queue_context.c',HERE/'queue_context.c'],
        'runtime':[HERE/n for n in ['test_runtime.c','runtime.c','contexts.c','queue_context.c']]+[
            CORE/n for n in ['ep7p.c','ep7p_decode.c','poll_lock_provider/ep7_sem_provider.c',
                'poll_lock_provider/bootstrap/bootstrap.c','snapshot_transport/transport.c',
                'snapshot_transport/job.c','snapshot_transport/consumer.c','snapshot_transport/wire.c']]}
    runs={}
    with tempfile.TemporaryDirectory(prefix='ep7-runtime-') as tmp:
        for target,sources in targets.items():
            runs[target]={}
            for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-pie','-no-pie'])]:
                exe=Path(tmp)/(target+'-'+name)
                subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',*extra,'-I'+str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True,timeout=60)
                result=subprocess.run([str(exe)],check=True,text=True,capture_output=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
                runs[target][name]=dict(passed=True,stdout=result.stdout.strip())
    return dict(scope=__doc__,runs=runs,kernel_reads_mocked=True,queue_lifetime_lease_proved=False,
        hash_checks_performed=False,target_executed=False,firmware_built=False,camera_accessed=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
