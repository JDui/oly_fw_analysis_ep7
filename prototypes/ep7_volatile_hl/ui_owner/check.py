#!/usr/bin/env python3
"""Owner switch/retire with actual cohort/lifecycle/rollback C; native methods mocked."""
import json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;CORE=HERE.parent

def check():
    sources=[HERE/p for p in ['owner.c','cohort.c','test_owner.c']]+[
        CORE/'text_lifecycle'/p for p in ['native_lifecycle.c','lifecycle.c']]+[
        CORE/'text_rollback'/p for p in ['native_context.c','rollback.c']]
    runs={}
    with tempfile.TemporaryDirectory(prefix='ep7-ui-owner-') as temp:
        for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=Path(temp)/name
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
                '-fno-pie','-no-pie',*extra,'-I'+str(CORE),*[str(p) for p in sources],'-o',str(exe)],
                check=True,timeout=60)
            subprocess.run([str(exe)],check=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
            runs[name]=dict(passed=True)
    return dict(scope=__doc__,runs=runs,scenarios=12,host_fixture_static_addresses_fit_native32=True,
        actual_cohort_checks_used=True,actual_native_text_lifecycle_and_rollback_C_used=True,
        resource_constructor_and_native_leaf_calls_mocked=True,manager_execution_modeled_at_boundaries=True,
        quarantine_modeled_with_longjmp=True,hardware_exception_behavior_tested=False,
        renderer_ready=False,installed=False,target_executed=False,firmware_built=False,hash_checks_performed=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
