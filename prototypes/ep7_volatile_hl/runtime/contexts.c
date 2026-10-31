#include "runtime.h"
#include "../snapshot_transport/native/producer.h"
#include "../snapshot_transport/native/descriptor_receive.h"
#include "../snapshot_transport/native/descriptor_send.h"
#include "../snapshot_transport/native/worker.h"
#include "../snapshot_transport/native/ack.h"
/* These providers construct target address views. Host fixtures may inspect
 * those values, but must never dereference their synthetic stack pointers. */
ep7r_slot ep7_native_runtime_slot={ATOMIC_VAR_INIT(NULL)};
static ep7q_stack mapped(const ep7n_task *t)
{
    ep7q_stack s={(const unsigned char *)(uintptr_t)t->stack_low,t->stack_low,t->stack_bytes,true};
    return s;
}
static bool current(ep7r *r,uint32_t w,ep7n_task *t,bool owns_cleanup)
{
    if(ep7r_task(r,w,t))return true;
    if(r && owns_cleanup)ep7r_fault(r,EP7R_FAULT_CONTEXT);
    return false;
}
static ep7q_forward_ops forward(ep7r *r)
{
    ep7q_forward_ops f={{r,ep7r_qualify_queue,NULL,NULL},r,ep7r_retire};return f;
}
bool ep7q_materializer_context_unresolved(unsigned handle,uint32_t w,ep7q_materializer_context *out)
{
    ep7r *r=ep7r_get(&ep7_native_runtime_slot);ep7n_task t;
    *out=(ep7q_materializer_context){0};
    if(handle!=0x4b || !current(r,w,&t,false) || t.entry!=0x603df803u)return false;
    out->stack=mapped(&t);out->queue_context=r;out->qualify_queue=ep7r_qualify_queue;return true;
}
bool ep7q_descriptor_receive_context_unresolved(unsigned handle,uint32_t w,ep7q_materializer_context *out)
{
    ep7r *r=ep7r_get(&ep7_native_runtime_slot);ep7n_task t;bool match;
    *out=(ep7q_materializer_context){0};
    if(!current(r,w,&t,false))return false;
    match=((handle==0x4c || handle==0x4d) && t.entry==0x603ef892u) ||
        (handle==0xab && t.entry==0x603ef94au) || (handle==0x4f && t.entry==0x603f26a1u);
    if(!match)return false;
    out->stack=mapped(&t);out->queue_context=r;out->qualify_queue=ep7r_qualify_queue;return true;
}
bool ep7q_descriptor_send_context_unresolved(unsigned handle,uint32_t w,ep7q_send_context *out)
{
    ep7r *r=ep7r_get(&ep7_native_runtime_slot);ep7n_task t;
    (void)handle;*out=(ep7q_send_context){0};
    /* Route changes may still carry an owned retirement ticket. Do not reject
     * them before the layout/forwarder has taken that cleanup obligation. */
    if(!current(r,w,&t,true) || (t.entry!=0x603df803u && t.entry!=0x603ef892u && t.entry!=0x603ef94au))return false;
    out->stack=mapped(&t);out->forward=forward(r);return true;
}
bool ep7q_producer_context_unresolved(unsigned handle,uint32_t w,ep7q_producer_context *out)
{
    ep7r *r=ep7r_get(&ep7_native_runtime_slot);ep7n_task t;
    *out=(ep7q_producer_context){0};
    if(handle!=0x4b || !ep7r_accepting(r) || !current(r,w,&t,false))return false;
    /* Producer scope/call chain separately proves the owned capture route. */
    out->stack=mapped(&t);out->producer.transport=&r->transport;out->producer.forward=forward(r);return true;
}
bool ep7q_worker_context_unresolved(unsigned stage,uint32_t w,ep7q_worker_context *out)
{
    ep7r *r=ep7r_get(&ep7_native_runtime_slot);ep7n_task t;
    *out=(ep7q_worker_context){0};
    if(stage<EP7Q_WORKER_ENTER || stage>EP7Q_WORKER_CLEANUP ||
       !current(r,w,&t,true) || t.entry!=0x603f26a1u)return false;
    out->stack=mapped(&t);out->transport=&r->transport;out->core=r->boot->core;
    out->wait_context=r;out->wait_cleanup=ep7r_progress;return true;
}
bool ep7q_ack_context_unresolved(uint32_t w,ep7q_ack_context *out)
{
    ep7r *r=ep7r_get(&ep7_native_runtime_slot);ep7n_task t;
    *out=(ep7q_ack_context){0};
    if(!current(r,w,&t,true) || (t.entry!=0x603df803u && t.entry!=0x603f26a1u))return false;
    out->stack=mapped(&t);out->transport=&r->transport;out->wait_context=r;out->wait_retirement=ep7r_progress;
    return true;
}
void ep7q_owned_context_lost(void)
{
    ep7r *r=ep7r_get(&ep7_native_runtime_slot);
    if(r)ep7r_fault(r,EP7R_FAULT_OWNED_LAYOUT);
}
