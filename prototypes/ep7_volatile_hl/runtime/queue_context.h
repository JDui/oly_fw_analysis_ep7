#ifndef EP7_NATIVE_QUEUE_CONTEXT_H
#define EP7_NATIVE_QUEUE_CONTEXT_H
#include "task_context.h"

typedef struct {
    uint16_t handle,domain;
    uint32_t root,table,object,attributes,maximum,ring_bytes,backing;
} ep7n_queue;
/* Read-only local-kernel queue view, using the same access vocabulary as TCB
 * queries. The two matching reads detect changes, NOT an ABA generation or a
 * lifetime lease. Caller must independently exclude delete/recreate and config
 * changes through subsequent raw I/O. No backing bytes are dereferenced here. */
bool ep7n_query_queue(const ep7n_task_ops *,unsigned handle,ep7n_queue *);
bool ep7n_same_queue(const ep7n_queue *,const ep7n_queue *);
bool ep7n_native_queue(unsigned handle,ep7n_queue *);
#endif
