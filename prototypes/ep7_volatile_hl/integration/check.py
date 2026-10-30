#!/usr/bin/env python3
"""Host-only actual routing integration; native admission is mocked."""
import argparse,hashlib,json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CORE=ROOT/'prototypes/ep7_volatile_hl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(record_hashes=True):
    sources=[HERE/'test_integration.c',CORE/'ui_native/bridge.c',CORE/'ep7p_ui_raw.c',CORE/'ep7p_ui.c',CORE/'ep7p.c',CORE/'ep7p_decode.c',CORE/'ep7p_lifecycle.c',CORE/'text_viewer/text.c']
    headers=[CORE/n for n in ['ui_native/bridge.h','ep7p_ui_raw.h','ep7p_ui.h','ep7p.h','ep7p_decode.h','ep7p_lifecycle.h','ep7p_direct.h','ep7_ui_adapter_contract.h']]
    headers.append(CORE/'text_viewer/text.h')
    sources.append(CORE/'controller_sidecar/sidecar.c')
    headers.append(CORE/'controller_sidecar/sidecar.h')
    sources.append(CORE/'snapshot_transport/transport.c')
    headers.append(CORE/'snapshot_transport/transport.h')
    sources.append(CORE/'snapshot_transport/wire.c')
    headers.append(CORE/'snapshot_transport/wire.h')
    sources.append(CORE/'snapshot_transport/owned_io.c')
    headers.append(CORE/'snapshot_transport/owned_io.h')
    sources.append(CORE/'snapshot_transport/native/materializer_layout.c')
    headers.append(CORE/'snapshot_transport/native/materializer.h')
    sources.extend(CORE/'snapshot_transport/native'/n for n in ['stack.c','descriptor_receive_layout.c'])
    headers.extend(CORE/'snapshot_transport/native'/n for n in ['stack.h','descriptor_receive.h'])
    results={}
    with tempfile.TemporaryDirectory(prefix='ep7-ui-actual-host-') as tmp:
        for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=Path(tmp)/name
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',*extra,'-I'+str(CORE),'-I'+str(CORE/'ui_native'),'-I'+str(CORE/'text_viewer'),*[str(p) for p in sources],'-o',str(exe)],check=True,timeout=60)
            result=subprocess.run([str(exe)],check=True,text=True,capture_output=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
            results[name]=dict(passed=True,stdout=result.stdout.strip())
    return dict(scope='Actual C router/raw/UI/core/text/sidecar/direct-lifecycle host integration; owned snapshot handoff fixture, not native metadata transport',sources={str(p.relative_to(ROOT)):sha(p) if record_hashes else None for p in sources+headers+[HERE/'check.py']},hashes_recorded=record_hashes,runs=results,raw_dispatch_stubbed=False,text_setter_mocked=True,native_admission_mocked=True,lifecycle_native_callbacks_mocked=True,native_snapshot_transport_mocked=True,sidecar_executed=True,node_retired_before_job=True,early_publication_neutral=True,real_decoder_operation_slots_exercised=16,renderer_implemented=False,ui_serialization='single host thread',lsan_disabled_due_ptrace=True,current_task_queries=0,target_executed=False,camera_accessed=False,flash_ready=False)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-hash',action='store_true',help='omit optional source hash recording')
    args=parser.parse_args()
    print(json.dumps(check(record_hashes=not args.no_hash),indent=2))
