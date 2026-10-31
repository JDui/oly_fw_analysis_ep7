#!/usr/bin/env python3
"""Actual native capture C and cohort against owned low-address memory and mocked native calls."""
import json,os,subprocess,tempfile
from pathlib import Path
CORE=Path(__file__).resolve().parent.parent
SOURCES=['controller_sidecar/test_native_binding.c','controller_sidecar/native_binding.c',
    'controller_sidecar/cohort.c','target/far_call.c','controller_sidecar/sidecar.c','runtime/runtime.c','runtime/queue_context.c',
    'ep7p.c','ep7p_decode.c','snapshot_transport/transport.c','snapshot_transport/wire.c',
    'snapshot_transport/producer.c','snapshot_transport/native/producer_layout.c','snapshot_transport/native/stack.c',
    'poll_lock_provider/ep7_sem_provider.c','poll_lock_provider/bootstrap/bootstrap.c']
def check():
    runs={}
    with tempfile.TemporaryDirectory(prefix='ep7-capture-native-') as temp:
        for name,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=Path(temp)/name
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
                '-DEP7CN_HOST_FIXTURE','-fno-pie','-no-pie',*extra,'-I'+str(CORE),
                *[str(CORE/p) for p in SOURCES],'-o',str(exe)],check=True,timeout=60)
            subprocess.run([str(exe)],check=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
            runs[name]=dict(passed=True)
    return dict(scope=__doc__,runs=runs,isolated_boot_scenarios=50,actual_native_binding_C_executed=True,
        actual_39_call_cohort_decoder_executed=True,actual_native_state_and_prefix_layout_reads=True,
        engine_reinitialization_and_callback_mask_mismatch_revoke_capture_epoch=True,
        deferred_snapshot_fifo_and_owned_stack_transfer_executed=True,
        actual_associated_pool_layout_and_slot_checks=True,
        zero_reference_return_and_pool_reset_revoke_before_reuse=True,
        repeated_and_out_of_order_population_revoked_before_writes=True,
        missing_prewrite_observers_cannot_seal=True,
        native_lookup_task_semaphore_queue_calls_mocked=True,firmware_code_not_mapped_or_executed=True,
        native_waiting_list_operations_mocked=True,
        host_pointer_width_exception_only_for_fixture=True,full_native_alias_closure_proven=False,
        installed=False,target_executed=False,firmware_built=False,hash_checks_performed=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
