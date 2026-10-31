#!/usr/bin/env python3
"""Actual C creation/attach/rollback composition with mocked native leaves/task facts."""
import json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;CORE=HERE.parent
def check():
    sources=[HERE/p for p in ['native_lifecycle.c','lifecycle.c','test_native_lifecycle.c']]+[
        CORE/'text_rollback'/p for p in ['rollback.c','native_context.c']]
    runs={}
    with tempfile.TemporaryDirectory(prefix='ep7-text-lifecycle-') as tmp:
        for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-pie','-no-pie'])]:
            exe=Path(tmp)/name
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',*extra,
                '-I'+str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True,timeout=60)
            subprocess.run([str(exe)],check=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
            runs[name]=dict(passed=True)
    return dict(scope=__doc__,runs=runs,scenarios=16,actual_native_context_and_rollback_C_used=True,
        live_id_collision_rejected_before_allocation=True,child_lookup_native_leaf_mocked=True,
        retained_cleanup_rejection_exercised=True,normal_bind_event_minus_one_exercised=True,
        target_executed=False,concrete_gui_owner_entry_qualified=False,resource_semantics_fully_qualified=False,
        hash_checks_performed=False,firmware_built=False,renderer_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
