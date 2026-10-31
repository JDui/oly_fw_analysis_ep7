#!/usr/bin/env python3
"""Owned H/L content with actual MVC/cohort C; native allocation and destruction mocked."""
import json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
def check():
    runs={}
    with tempfile.TemporaryDirectory(prefix='ep7-ui-content-') as temp:
        for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=Path(temp)/name
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
                '-fno-pie','-no-pie',*extra,'-I'+str(HERE.parent),
                *[str(HERE/p) for p in ['content.c','../ui_mvc/lifetime.c','../ui_mvc/cohort.c','test_content.c']],
                '-o',str(exe)],check=True,timeout=60)
            subprocess.run([str(exe)],check=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
            runs[name]=dict(passed=True)
    return dict(scope=__doc__,runs=runs,content_scenario_groups=6,reused_mvc_scenario_groups=6,
        actual_content_lifetime_and_cohort_C_used=True,quarantine_modeled_with_longjmp=True,
        enabled_masks_are_fixture_only=True,hl_malloc_failure_preserves_old_content=True,
        stock_factory_failure_unchanged=True,ui_session_and_renderer_join_implemented=False,
        input_provider_implemented=False,target_executed=False,installed=False,firmware_built=False,
        hash_checks_performed=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
