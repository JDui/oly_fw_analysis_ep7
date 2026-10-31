#include "ack.h"
_Static_assert(sizeof(uintptr_t)==4,"target-only ACK binding");
void ep7q_ack_entry(uint32_t descriptor,uint32_t w)
{
    ep7q_ack_context context={0};ep7q_ack_args args;
    if(!ep7q_ack_context_unresolved(w,&context) ||
       context.stack.bytes!=(const unsigned char *)(uintptr_t)context.stack.low ||
       !ep7q_ack_layout(&context.stack,w,descriptor,&args)){
        ep7q_owned_context_lost();return;
    }
    while(!ep7q_retire_owned(context.transport,(unsigned char *)(uintptr_t)args.descriptor,EP7W_MAX)){
        /* Do not notify original owner while an experimental cleanup obligation
         * remains. Missing progress policy retains this frame; never fake ACK. */
        if(context.wait_retirement)context.wait_retirement(context.wait_context);
    }
}
