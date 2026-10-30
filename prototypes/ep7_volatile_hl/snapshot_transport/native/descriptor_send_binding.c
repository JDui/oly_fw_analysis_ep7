#include "descriptor_send.h"
#include "queue.h"
_Static_assert(sizeof(uintptr_t)==4,"target-only descriptor send binding");
static int send_local(void *ctx,unsigned handle,const void *buffer,unsigned bytes,int timeout)
{ (void)ctx;return ep7_gcc_queue_send_local(handle,buffer,bytes,timeout); }
int ep7q_descriptor_send_entry(const ep7q_send_input *in,uint32_t wrapper_sp)
{
    ep7q_send_context context={0};ep7q_send_args args;
    if(!in || !ep7q_descriptor_send_context_unresolved(in->handle,wrapper_sp,&context) ||
       context.stack.bytes!=(const unsigned char *)(uintptr_t)context.stack.low ||
       !ep7q_descriptor_send_layout(&context.stack,wrapper_sp,in,&args))return EP7Q_DELEGATE_SEND;
    context.forward.queue.receive=NULL;context.forward.queue.send=send_local;
    return ep7q_forward_send(&context.forward,in->handle,args.timeout,
        (unsigned char *)(uintptr_t)args.descriptor,EP7W_MAX);
}
