#!/usr/bin/env python3
"""Host-only actual routing integration; native admission is mocked."""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CORE=ROOT/'prototypes/ep7_volatile_hl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
    sources=[HERE/'test_integration.c',CORE/'ui_native/bridge.c',CORE/'ep7p_ui_raw.c',CORE/'ep7p_ui.c',CORE/'ep7p.c',CORE/'ep7p_decode.c',CORE/'ep7p_lifecycle.c',CORE/'text_viewer/text.c']
    headers=[CORE/n for n in ['ui_native/bridge.h','ep7p_ui_raw.h','ep7p_ui.h','ep7p.h','ep7p_decode.h','ep7p_lifecycle.h','ep7p_direct.h','ep7_ui_adapter_contract.h']]
    headers.append(CORE/'text_viewer/text.h')
    results={}
    with tempfile.TemporaryDirectory(prefix='ep7-ui-actual-host-') as tmp:
        for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=Path(tmp)/name
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',*extra,'-I'+str(CORE),'-I'+str(CORE/'ui_native'),'-I'+str(CORE/'text_viewer'),*[str(p) for p in sources],'-o',str(exe)],check=True,timeout=60)
            result=subprocess.run([str(exe)],check=True,text=True,capture_output=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
            results[name]=dict(passed=True,stdout=result.stdout.strip())
    return dict(scope='Actual C router/raw/UI/core/text/capture/direct-lifecycle host integration; mocked native admission and renderer readiness, not native rendering',sources={str(p.relative_to(ROOT)):sha(p) for p in sources+headers+[HERE/'check.py']},runs=results,raw_dispatch_stubbed=False,text_setter_mocked=True,native_admission_mocked=True,lifecycle_native_callbacks_mocked=True,real_decoder_operation_slots_exercised=16,renderer_implemented=False,ui_serialization='single host thread',lsan_disabled_due_ptrace=True,current_task_queries=0,target_executed=False,camera_accessed=False,flash_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
