#!/usr/bin/env python3
"""COLOR availability and allocation-before-free stock restoration joined to real UI/core C."""
import json,os,runpy,subprocess,tempfile
from pathlib import Path
CORE=Path(__file__).resolve().parent.parent
def check():
    sources=[p for p in runpy.run_path(str(CORE/'ui_render/check.py'))['SOURCES'] if p!='ui_render/test_viewer.c']
    sources+=['ui_gate/test_gate.c','ui_gate/gate.c','ui_content/stock.c',
        'ui_native/bridge.c','ui_native/input.c','ui_native/cohort.c','ep7p_ui_raw.c']
    runs={}
    with tempfile.TemporaryDirectory(prefix='ep7-ui-gate-') as temp:
        for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=Path(temp)/name
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
                '-fno-pie','-no-pie',*extra,'-I'+str(CORE),*[str(CORE/p) for p in sources],'-o',str(exe)],check=True,timeout=60)
            subprocess.run([str(exe)],check=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
            runs[name]=dict(passed=True)
    return dict(scope=__doc__,runs=runs,scenario_groups=8,real_hl_mask_admission=True,
        all_four_stock_category_routes_checked=True,stock_masks_preserved=True,
        allocation_failure_keeps_owned_child=True,same_event_stock_replay_suppressed=True,
        native_creators_timers_task_draw_and_text_calls_mocked=True,
        no_sha_checks=True,installed=False,target_executed=False,firmware_built=False,lcd_acceptance=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
