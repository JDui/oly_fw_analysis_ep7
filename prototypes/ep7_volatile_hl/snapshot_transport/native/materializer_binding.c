#include "materializer.h"
#include "queue.h"
_Static_assert(sizeof(uintptr_t)==4,"target-only materializer binding");
static int receive_local(void *ctx,unsigned handle,void *buffer,int timeout)
{ (void)ctx;return ep7_gcc_queue_receive_local(handle,buffer,timeout); }
int ep7q_materializer_entry(unsigned handle,uint32_t wrapper_sp)
{
    ep7q_materializer_context context={0};ep7q_materializer_args args;
    ep7q_ops ops;ep7q_result result;
    if(!ep7q_materializer_context_unresolved(handle,wrapper_sp,&context) ||
       context.stack.bytes!=(const unsigned char *)(uintptr_t)context.stack.low ||
       !ep7q_materializer_layout(&context.stack,wrapper_sp,handle,&args))return -1;
    ops=(ep7q_ops){context.queue_context,context.qualify_queue,receive_local,NULL};
    result=ep7q_command_receive(&ops,handle,args.timeout,
        (unsigned char *)(uintptr_t)args.command,EP7W_COMMAND,
        (unsigned char *)(uintptr_t)args.descriptor,EP7W_MAX);
    /* Stock materializer retains its own return/error and ACK behavior. The
     * receive bridge neither claims nor retires a drain ticket prematurely. */
    return result.status;
}
