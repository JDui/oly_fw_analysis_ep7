#ifndef EP7_PIPELINE_RUNTIME_H
#define EP7_PIPELINE_RUNTIME_H
#include "../poll_lock_provider/bootstrap/bootstrap.h"
#include "../snapshot_transport/transport.h"
#include "queue_context.h"

enum { EP7R_COLD,EP7R_PREPARED,EP7R_PUBLISHED };
enum { EP7R_FAULT_LOCK=1,EP7R_FAULT_DELAY,EP7R_FAULT_CONTEXT,
       EP7R_FAULT_QUEUE,EP7R_FAULT_OWNED_LAYOUT,EP7R_FAULT_TICKET };
#define EP7R_QUEUES 5u
typedef struct {
    void *ctx;
    /* G6 installer evidence, not a configurable enable switch: all frame/hook
     * edits, stable task/queue/private-lock lifetimes and native ordering must
     * already be established, before any hooked caller can execute. */
    bool (*installation_ready)(void *);
    bool (*task)(void *,uint32_t anchor,ep7n_task *);
    bool (*queue)(void *,unsigned handle,ep7n_queue *);
    int (*delay_one)(void *);
    /* Must not return, ACK, free, reset, delete or reuse any owned state. */
    void (*quarantine)(void *,unsigned reason);
} ep7r_environment;
typedef struct {
    unsigned state;
    ep7b *boot;
    ep7t transport;
    ep7r_environment env;
    ep7n_queue queues[EP7R_QUEUES];
    atomic_bool stopped;
    atomic_uint fault;
} ep7r;
typedef struct { _Atomic(ep7r *) published; } ep7r_slot;

/* Fresh zeroed objects, serialized startup, no moves or users before publish.
 * Reuses a PREPARED bootstrap; does not create a second lock or core. After
 * publication all objects/callbacks are permanent, with no live reset/unpublish.
 * Single-domain candidate only. C atomics are not hardware visibility evidence. */
bool ep7r_prepare(ep7r *,ep7b *,ep7r_environment);
bool ep7r_publish(ep7r_slot *,ep7r *);
ep7r *ep7r_get(const ep7r_slot *);
bool ep7r_accepting(const ep7r *);
/* Rejects subsequent admission checks. Already-admitted producers can finish;
 * this is NOT quiescence, queue teardown permission or revocation of old work. */
void ep7r_stop(ep7r *);
bool ep7r_task(ep7r *,uint32_t anchor,ep7n_task *);
bool ep7r_qualify_queue(void *,unsigned handle,unsigned maximum);
void ep7r_retire(void *,ep7t_ticket); /* Synchronous by-value cleanup owner. */
void ep7r_progress(void *); /* No lock held, one native timed-delay unit. */
_Noreturn void ep7r_fault(ep7r *,unsigned reason);

/* Defined storage becomes meaningful only after safe G6 placement/startup.
 * Merely linking this symbol never publishes a runtime or installs any hook. */
extern ep7r_slot ep7_native_runtime_slot;
ep7r_environment ep7r_native_environment(void *,bool (*installation_ready)(void *));
#endif
