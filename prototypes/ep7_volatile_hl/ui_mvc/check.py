#!/usr/bin/env python3
"""GUI041d graph lifetime C and actual cohort checks; native boundaries/task are mocked."""
import json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def check():
    runs={}
    with tempfile.TemporaryDirectory(prefix='ep7-ui-mvc-') as temp:
        for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=Path(temp)/name
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
                '-fno-pie','-no-pie',*extra,'-I'+str(HERE.parent),
                *[str(HERE/p) for p in ['lifetime.c','cohort.c','test_lifetime.c']],'-o',str(exe)],
                check=True,timeout=60)
            subprocess.run([str(exe)],check=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
            runs[name]=dict(passed=True)
    return dict(scope=__doc__,runs=runs,scenario_groups=6,actual_cohort_C_used=True,
        original_constructor_draw_and_free_modeled_at_boundaries=True,quarantine_modeled_with_longjmp=True,
        hl_content_and_renderer_implemented=False,input_provider_implemented=False,
        target_executed=False,installed=False,firmware_built=False,hash_checks_performed=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
