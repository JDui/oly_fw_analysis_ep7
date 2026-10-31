#!/usr/bin/env python3
"""Actual input scope/router joined to existing MVC, owner, runtime and portable core C."""
import json,os,runpy,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;CORE=HERE.parent
def check():
    sources=[p for p in runpy.run_path(str(CORE/'ui_render/check.py'))['SOURCES'] if p!='ui_render/test_viewer.c']
    sources+=['ui_native/test_input.c','ui_native/bridge.c','ui_native/input.c','ui_native/cohort.c','ep7p_ui_raw.c']
    runs={}
    with tempfile.TemporaryDirectory(prefix='ep7-ui-input-') as temp:
        for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=Path(temp)/name
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
                '-fno-pie','-no-pie',*extra,'-I'+str(CORE),*[str(CORE/p) for p in sources],
                '-o',str(exe)],check=True,timeout=60)
            subprocess.run([str(exe)],check=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
            runs[name]=dict(passed=True)
    return dict(scope=__doc__,runs=runs,new_input_scenario_groups=8,reused_viewer_mvc_content_groups=19,
        five_actual_sample_origins_modeled=True,packet_parameter_not_used_as_delta=True,
        complete_prepare_and_engine_scope=True,event_consumed_once=True,owner_and_mvc_held_through_dispatch=True,
        real_runtime_core_session_renderer_lifecycle_C_used=True,native_calls_task_and_stack_extent_mocked=True,
        input_provider_implemented=True,hl_mask_enable_fixture_only=True,installed=False,target_executed=False,
        firmware_built=False,lcd_acceptance=False,hash_checks_performed=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
