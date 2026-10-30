#ifndef EP7P_H
#define EP7P_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define EP7P_CAP 8
#define EP7P_DEPTH 8
#define EP7P_STOCK 15488u
#define EP7P_EXTENT 15512u
#define EP7P_OUTPUT 976u
/* All capacities are prototype choices, not native firmware facts.
 * Trusted adapter API: pointers/lengths must denote real, live C objects.
 * Input/output buffers and token outputs must not alias this runtime or each
 * other where copied. A claimed extent is NOT validated allocation provenance.
 * lock/current/unlock callbacks must not reenter this runtime. current must
 * remain callable under the chosen lock; a native interrupt/dispatch-disabling
 * lock may make get_tid reject and is not qualified by host tests.
 */
typedef struct { uint16_t tid; uint64_t epoch; } ep7p_task;
typedef struct {
    void *ctx;
    bool (*lock)(void *);
    void (*unlock)(void *);
    int (*current)(void *, ep7p_task *); /* independent task-instance lease */
} ep7p_ops;
typedef struct { uint8_t profile; int8_t hl[24]; } ep7p_snapshot;
typedef struct {
    uintptr_t job, request, operation, request_operation, operation_job, operation_request;
    uint32_t callback, stage_callback;
    unsigned stage, type, raw_mode, raw_selector;
    uintptr_t owner, mutation_callback;
} ep7p_observation;
typedef struct { uint64_t token; unsigned char *base; size_t extent; uint8_t profile; } ep7p_job;
typedef struct { uint64_t token, job; ep7p_observation shape; } ep7p_frame;
typedef struct { bool live; ep7p_task who; unsigned depth; ep7p_frame frames[EP7P_DEPTH]; } ep7p_task_slot;
typedef struct {
    ep7p_ops ops; bool ready; uint64_t serial;
    int8_t profiles[4][24]; /* volatile session settings: no NVM persistence */
    ep7p_job jobs[EP7P_CAP]; ep7p_task_slot tasks[EP7P_CAP];
} ep7p;
bool ep7p_init(ep7p *, ep7p_ops); /* once, before sharing; never reset live state */
bool ep7p_edit(ep7p *, unsigned profile, const int8_t hl[24]);
/* axis 0=H / 1=L; sector 0..11 or 255=ALL; reset ignores delta.
   Atomic profile-local adjustment, clamps to [-7,+7]. ALL uses one common
   limited delta, preserving sector differences; reset explicitly zeros them. */
bool ep7p_axis_read(ep7p *, unsigned profile, unsigned axis, int8_t out[12]);
bool ep7p_axis_adjust(ep7p *, unsigned profile, unsigned axis, unsigned sector,
                      int delta, bool reset);
/* Returns changed status in the same critical section as the committed edit.
   On false, no edit is committed and *changed is untouched. */
bool ep7p_axis_adjust_result(ep7p *, unsigned profile, unsigned axis, unsigned sector,
                             int delta, bool reset, bool *changed);
bool ep7p_capture(ep7p *, unsigned raw_mode, unsigned selector, ep7p_snapshot *);
/* Trusted allocation adapter supplies genuinely writable extent and fresh lifetime.
   Geometry/magic cannot qualify this call. Caller must release BEFORE freeing. */
bool ep7p_register_job(ep7p *, void *base, size_t extent, const ep7p_snapshot *, uint64_t *);
bool ep7p_release_job(ep7p *, uint64_t);
bool ep7p_register_task(ep7p *, ep7p_task);
bool ep7p_release_task(ep7p *, ep7p_task); /* trusted lifecycle adapter */
bool ep7p_enter(ep7p *, uint64_t job, const ep7p_observation *, uint64_t *scope);
bool ep7p_unwind(ep7p *, uint64_t scope); /* revokes frame and descendants */
bool ep7p_apply(ep7p *, uint64_t scope, uint64_t job, const ep7p_observation *,
                unsigned char *native_output, size_t length);
#endif
