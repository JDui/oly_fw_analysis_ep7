#include "worker.h"
#include <string.h>
_Static_assert(sizeof(uintptr_t)==4,"target-only worker binding");
_Static_assert(sizeof(ep7j_scope)==48 && offsetof(ep7j_scope,allocation)==32 &&
               offsetof(ep7j_scope,extent)==36 && offsetof(ep7j_scope,job)==40,"owned worker scope layout");
extern const unsigned char ep7_worker_native_return[];
static bool admit(unsigned stage,uint32_t w,uint32_t descriptor,
                  ep7q_worker_context *context,ep7q_worker_args *args)
{
    return ep7q_worker_context_unresolved(stage,w,context) &&
        context->stack.bytes==(const unsigned char *)(uintptr_t)context->stack.low &&
        ep7q_worker_layout(&context->stack,w,stage,descriptor,
            (uint32_t)(uintptr_t)ep7_worker_native_return,args);
}
void ep7q_worker_scope_entry(ep7j_scope *scope,uint32_t s)
{
    ep7q_worker_context context={0};ep7q_worker_args args;uint32_t descriptor;
    /* Scope was allocated by this bridge, irrespective of runtime admission. */
    memset(scope,0,sizeof *scope);
    if(ep7q_worker_context_unresolved(EP7Q_WORKER_ENTER,s,&context) &&
       context.stack.bytes==(const unsigned char *)(uintptr_t)context.stack.low &&
       ep7q_stack_word(&context.stack,s,24,&descriptor) &&
       ep7q_worker_layout(&context.stack,s,EP7Q_WORKER_ENTER,descriptor,0,&args) &&
       args.scope==(uint32_t)(uintptr_t)scope)
        ep7j_begin(scope,context.transport,(unsigned char *)(uintptr_t)args.descriptor,EP7W_MAX);
}
static void *native_allocate(void *ctx,unsigned size)
{ (void)ctx;return ep7_gcc_job_allocate(size); }
void *ep7q_worker_allocate_entry(unsigned requested,uint32_t w)
{
    ep7q_worker_context context={0};ep7q_worker_args args;ep7j_scope *scope=NULL;
    if(admit(EP7Q_WORKER_ALLOCATE,w,0,&context,&args))scope=(ep7j_scope *)(uintptr_t)args.scope;
    return ep7j_allocate(scope,requested,native_allocate,NULL);
}
void ep7q_worker_process_entry(uint32_t descriptor,uint32_t w)
{
    ep7q_worker_context context={0};ep7q_worker_args args;uint32_t job;
    if(admit(EP7Q_WORKER_PROCESS,w,descriptor,&context,&args) && context.wait_cleanup &&
       ep7q_stack_word(&context.stack,descriptor,36,&job))
        (void)ep7j_register((ep7j_scope *)(uintptr_t)args.scope,context.core,(void *)(uintptr_t)job);
}
void ep7q_worker_cleanup_entry(uint32_t descriptor,uint32_t w)
{
    ep7q_worker_context context={0};ep7q_worker_args args;
    if(!admit(EP7Q_WORKER_CLEANUP,w,descriptor,&context,&args))return;
    while(!ep7j_revoke((ep7j_scope *)(uintptr_t)args.scope,context.core)){
        /* Registration required a stable wait callback. If that contract is
         * violated, do not free a still-registered job; retain this frame. */
        if(context.wait_cleanup)context.wait_cleanup(context.wait_context);
    }
}
