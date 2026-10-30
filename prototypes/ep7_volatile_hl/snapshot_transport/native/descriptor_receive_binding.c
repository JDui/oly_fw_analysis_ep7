#include "descriptor_receive.h"
#include "queue.h"
_Static_assert(sizeof(uintptr_t)==4,"target-only descriptor receive binding");
static int receive_local(void *ctx,unsigned handle,void *buffer,int timeout)
{ (void)ctx;return ep7_gcc_queue_receive_local(handle,buffer,timeout); }
int ep7q_descriptor_receive_entry(const ep7q_receive_input *in,uint32_t wrapper_sp)
{
    ep7q_materializer_context context={0};ep7q_receive_args args;ep7q_ops ops;
    ep7q_result result;
    if(!in)return -1;
    if(!ep7q_descriptor_receive_context_unresolved(in->handle,wrapper_sp,&context) ||
       context.stack.bytes!=(const unsigned char *)(uintptr_t)context.stack.low ||
       !ep7q_descriptor_receive_layout(&context.stack,wrapper_sp,in,&args))
        return ep7q_receive_rejection(in->handle);
    ops=(ep7q_ops){context.queue_context,context.qualify_queue,receive_local,NULL};
    result=ep7q_descriptor_receive(&ops,in->handle,args.timeout,
        (unsigned char *)(uintptr_t)args.descriptor,EP7W_MAX);
    return result.status;
}
