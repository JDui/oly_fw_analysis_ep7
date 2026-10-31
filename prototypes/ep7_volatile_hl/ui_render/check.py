#!/usr/bin/env python3
"""Joined MVC/content/model, published runtime/core and owner text lifecycle; native calls mocked."""
import json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;CORE=HERE.parent
SOURCES=['ui_render/viewer.c','ui_render/test_viewer.c','ui_model/model.c',
        'ui_mvc/lifetime.c','ui_mvc/cohort.c','target/far_call.c','ui_content/content.c','ui_owner/owner.c','ui_owner/cohort.c',
        'text_lifecycle/native_lifecycle.c','text_lifecycle/lifecycle.c','text_rollback/native_context.c',
        'text_rollback/rollback.c','text_viewer/text.c','ep7p_ui.c','ep7p.c','ep7p_decode.c',
        'runtime/runtime.c','runtime/queue_context.c','poll_lock_provider/ep7_sem_provider.c',
        'poll_lock_provider/bootstrap/bootstrap.c','snapshot_transport/transport.c','snapshot_transport/wire.c']
def check():
    sources=SOURCES
    runs={}
    with tempfile.TemporaryDirectory(prefix='ep7-ui-viewer-') as temp:
        for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=Path(temp)/name
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
                '-fno-pie','-no-pie',*extra,'-I'+str(CORE),*[str(CORE/p) for p in sources],
                '-o',str(exe)],check=True,timeout=60)
            subprocess.run([str(exe)],check=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
            runs[name]=dict(passed=True)
    return dict(scope=__doc__,runs=runs,join_scenario_groups=7,reused_mvc_and_content_groups=12,
        real_portable_core_bootstrap_runtime_session_and_native_lifecycle_C_used=True,
        independent_ui_serial_checked=True,captured_snapshot_unchanged_after_ui_edit=True,
        async_owner_ordering_modeled_at_boundaries=True,native_task_allocator_property_queue_calls_mocked=True,
        quarantine_modeled_with_longjmp=True,hl_mask_enable_fixture_only=True,
        native_input_provider_bound=False,target_executed=False,installed=False,lcd_acceptance=False,
        firmware_built=False,hash_checks_performed=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
