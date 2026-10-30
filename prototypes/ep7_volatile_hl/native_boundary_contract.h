#ifndef EP7_NATIVE_BOUNDARY_CONTRACT_H
#define EP7_NATIVE_BOUNDARY_CONTRACT_H
#include <stdint.h>
/* Host-only boundary vocabulary, not a camera RAM structure or compiler ABI.
 * All capabilities below are issued by future instrumented admission, not
 * reconstructed by reading a candidate trailer/magic or trusting a task ID. */
struct ep7_capture_cap {
    uint32_t capture_id;
    uint64_t capture_generation;
    uint64_t settings_generation; /* Proposed H/L publication only; not atomic stock S. */
};
struct ep7_fresh_job_cap {
    uintptr_t job;
    uint32_t allocated_bytes;
    uint64_t allocation_generation;
    struct ep7_capture_cap capture;
};
struct ep7_scope_cap {
    uint16_t task_id;
    uint64_t task_instance_generation; /* Not supplied by get_tid. */
    uint32_t depth;
    uint64_t invocation_generation;
};
/* Proposed PORT callbacks. No native implementation is claimed.
 * A failed call must leave no published admission and no partially attached
 * values. Snapshot acquire must select the ORIGINAL capture generation, never
 * the current GUI settings. Unsupported paths retain stock S and neutral H/L. */
struct ep7_native_port_contract {
    int (*capture_snapshot_acquire)(struct ep7_capture_cap capture,
                                   void *owned_snapshot, uint32_t size);
    int (*fresh_job_attach)(struct ep7_fresh_job_cap job,
                            const void *owned_snapshot, uint32_t size);
    int (*scope_enter)(struct ep7_fresh_job_cap job,
                       struct ep7_scope_cap *out);
    int (*cpu_read_copy)(struct ep7_scope_cap scope, uintptr_t request,
                         void *hl_copy, uint32_t size);
    int (*scope_leave)(struct ep7_scope_cap exact_token);
    void (*invalidate_before_free)(struct ep7_fresh_job_cap job);
};
#endif
