#!/usr/bin/env python3
"""Targeted selector storage/failure tests; native initializer, allocator and task mocked."""
import json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def check():
    runs={}
    with tempfile.TemporaryDirectory(prefix='ep7-ui-selector-') as temp:
        for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=Path(temp)/name
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
                '-fno-pie','-no-pie',*extra,'-I'+str(HERE.parent),str(HERE/'selector.c'),str(HERE/'test_selector.c'),
                '-o',str(exe)],check=True,timeout=60)
            subprocess.run([str(exe)],check=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
            runs[name]=dict(passed=True)
    return dict(scope=__doc__,runs=runs,scenarios=4,actual_storage_upgrade_C_used=True,
        new_allocation_failure_preserves_entire_stock_object=True,stock_masks_preserved=True,
        additional_categories_disabled=True,native_navigation_executed=False,
        native_original_allocation_failure_handled=False,renderer_ready=False,installed=False,
        target_executed=False,firmware_built=False,hash_checks_performed=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
