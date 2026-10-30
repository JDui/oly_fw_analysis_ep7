#ifndef EP7_NATIVE_TASK_CONTEXT_H
#define EP7_NATIVE_TASK_CONTEXT_H
#include "ep7p.h"
typedef struct {
    uint16_t tid,domain;
    uint32_t tcb,entry,stack_low,stack_bytes;
} ep7n_task;
/* Read-only kernel access vocabulary. Reads return false without output writes
 * when unavailable. Production backend trusts the same live kernel objects as
 * native get_tid; this is not a validator for arbitrary corrupt kernel pointers.
 * Call only in a normally returning current task, with no migration/cancellation.
 * Do not retain this view as a task lease or proof of ID/address nonreuse. */
typedef struct {
    void *ctx;
    int (*get_tid)(void *,uint16_t *);
    bool (*read32)(void *,uint32_t,uint32_t *);
    bool (*read16)(void *,uint32_t,uint16_t *);
} ep7n_task_ops;
/* Verifies current identity before/after, domain, current-TCB chain and actual
 * TCB stack allocation bounds containing anchor. Output clears on every failure.
 * Does not set any hook-installation flag or create a runtime/task-generation. */
bool ep7n_query_task(const ep7n_task_ops *,uint32_t anchor,ep7n_task *);
bool ep7n_native_current_task(uint32_t anchor,ep7n_task *);
#endif
