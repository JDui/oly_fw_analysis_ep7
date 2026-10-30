#include "queue.h"
int ep7q_send_local_preserving(void *ctx,unsigned handle,const void *buffer,unsigned bytes,int timeout)
{
    int status;(void)ctx;
    status=ep7_gcc_queue_send_preserving_hooks(handle,buffer,bytes,timeout);
    return status==-2?-50:status;
}
