#!/usr/bin/env python3
"""Existing rollback plus actual context adapter; native leaves/task facts mocked."""
import json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def check():
    runs={}
    with tempfile.TemporaryDirectory(prefix='ep7-ui-context-') as tmp:
        for target,files in [('rollback',['rollback.c','test_rollback.c']),
                ('native_context',['rollback.c','native_context.c','test_native_context.c'])]:
            runs[target]={}
            for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-pie','-no-pie'])]:
                exe=Path(tmp)/(target+'-'+name)
                subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',*extra,
                    '-I'+str(HERE.parent),*[str(HERE/p) for p in files],'-o',str(exe)],check=True,timeout=60)
                subprocess.run([str(exe)],check=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
                runs[target][name]=dict(passed=True)
    return dict(scope=__doc__,runs=runs,rollback_cases=9,native_context_cases=12,
        native_context_callbacks_implemented=True,exclusive_ui_ownership_proved=False,
        hash_checks_performed=False,target_executed=False,firmware_built=False,renderer_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
