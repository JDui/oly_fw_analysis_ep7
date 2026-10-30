#include "producer.h"
#include <string.h>
static uint32_t get32(const unsigned char *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
void ep7q_capture_scope_init(ep7q_capture_scope *scope,uint32_t capture_id,const ep7p_snapshot *snapshot)
{
    if(!scope)return;
    memset(scope,0,sizeof *scope);scope->capture_id=capture_id;
    if(snapshot){scope->snapshot=*snapshot;scope->state=EP7Q_SCOPE_AVAILABLE;}
}
int ep7q_producer_send(const ep7q_producer_ops *ops,ep7q_capture_scope *scope,
    unsigned handle,int timeout,const unsigned char *command,size_t extent)
{
    unsigned char wire[EP7W_COMMAND+EP7W_TRAILER];size_t bytes;ep7t_ticket ticket;int raw;
    if(!scope || scope->state!=EP7Q_SCOPE_AVAILABLE)return EP7Q_DELEGATE_SEND;
    scope->state=EP7Q_SCOPE_CONSUMED;
    if(!ops || !ops->transport || !ops->forward.retire_owned || !ops->forward.queue.qualify ||
       !ops->forward.queue.send || !command || extent<EP7W_COMMAND || handle!=0x4b ||
       get32(command+8)!=19 || !ops->forward.queue.qualify(ops->forward.queue.ctx,handle,148))
        return EP7Q_DELEGATE_SEND;
    if(!ep7t_prepare(ops->transport,get32(command+12),&scope->snapshot,&ticket))return EP7Q_DELEGATE_SEND;
    if(!ep7w_encode(EP7W_COMMAND,command,ticket,wire,sizeof wire,&bytes) || !ep7t_publish(ops->transport,ticket)){
        ops->forward.retire_owned(ops->forward.retirement_context,ticket);return EP7Q_DELEGATE_SEND;
    }
    raw=ops->forward.queue.send(ops->forward.queue.ctx,handle,wire,(unsigned)bytes,timeout);
    if(raw<0)ops->forward.retire_owned(ops->forward.retirement_context,ticket);
    return raw>=0?0:(raw==-50?-2:-1);
}
