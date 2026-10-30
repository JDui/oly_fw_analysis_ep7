#ifndef EP7_NATIVE_WORKER_H
#define EP7_NATIVE_WORKER_H
#include "stack.h"
#include "../job.h"
enum { EP7Q_WORKER_ENTER=1,EP7Q_WORKER_ALLOCATE,EP7Q_WORKER_PROCESS,EP7Q_WORKER_CLEANUP };
typedef struct { uint32_t descriptor,scope; } ep7q_worker_args;
/* w is owned wrapper SP at ENTER, original native callee SP at other stages.
 * native_return is the linked self-authored wrapper label, not a stock address. */
bool ep7q_worker_layout(const ep7q_stack *,uint32_t w,unsigned stage,
                       uint32_t actual_descriptor,uint32_t native_return,ep7q_worker_args *);
typedef struct {
    ep7q_stack stack;
    ep7t *transport;
    ep7p *core;
    void *wait_context;
    /* Mandatory before registration. Must safely yield/progress in this live
     * worker context without releasing/reusing its scope/job/descriptor. No lock
     * is held across this callback. Must not reenter processing or claim. */
    void (*wait_cleanup)(void *);
} ep7q_worker_context;
/* Trusted provider proves the installed full group, actual live current stack,
 * local synchronous worker domain and immutable runtime bindings throughout the
 * entire wrapper. Once registered it must stay available through cleanup; losing
 * qualification cannot turn a registered job into an unknown stock invocation.
 * This stability/failure policy is still a G3/G6 obligation, not supplied here. */
bool ep7q_worker_context_unresolved(unsigned,uint32_t,ep7q_worker_context *);
void ep7q_worker_scope_entry(ep7j_scope *,uint32_t);
void *ep7q_worker_allocate_entry(unsigned,uint32_t);
void ep7q_worker_process_entry(uint32_t,uint32_t);
void ep7q_worker_cleanup_entry(uint32_t,uint32_t);
void *ep7_gcc_job_allocate(unsigned);
#endif
