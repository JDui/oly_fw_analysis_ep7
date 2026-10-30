#include "producer.h"
#include "queue.h"
_Static_assert(sizeof(uintptr_t)==4,"target-only capture producer binding");
extern const unsigned char ep7_capture_scope_native_return[];
void ep7q_capture_scope_entry(uint32_t capture_id,uint32_t associated,ep7q_capture_scope *scope)
{
    ep7p_snapshot snapshot;
    ep7q_capture_scope_init(scope,capture_id,NULL);
    if(ep7q_capture_snapshot_unresolved(capture_id,associated,&snapshot))
        ep7q_capture_scope_init(scope,capture_id,&snapshot);
}
int ep7q_producer_entry(const ep7q_producer_input *in,uint32_t wrapper_sp)
{
    ep7q_producer_context context={0};ep7q_producer_args args;
    if(!in || !ep7q_producer_context_unresolved(in->handle,wrapper_sp,&context) ||
       context.stack.bytes!=(const unsigned char *)(uintptr_t)context.stack.low ||
       !ep7q_producer_layout(&context.stack,wrapper_sp,in,
           (uint32_t)(uintptr_t)ep7_capture_scope_native_return,&args))return EP7Q_DELEGATE_SEND;
    context.producer.forward.queue.receive=NULL;context.producer.forward.queue.send=ep7q_send_local_preserving;
    return ep7q_producer_send(&context.producer,(ep7q_capture_scope *)(uintptr_t)args.scope,
        in->handle,args.timeout,(const unsigned char *)(uintptr_t)args.command,EP7W_COMMAND);
}
