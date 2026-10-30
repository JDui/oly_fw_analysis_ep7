#include "forward.h"
int ep7q_forward_send(const ep7q_forward_ops *ops,unsigned handle,int timeout,
                     unsigned char *descriptor,size_t extent)
{
    ep7q_result r;
    if(!ops || !ops->retire_owned)return EP7Q_DELEGATE_SEND;
    r=ep7q_descriptor_send(&ops->queue,handle,timeout,descriptor,extent);
    if(r.ticket.serial && (!r.called || r.status!=0 || r.wire_status!=EP7W_TAGGED || handle==0x4d))
        ops->retire_owned(ops->retirement_context,r.ticket);
    return r.called?r.status:EP7Q_DELEGATE_SEND;
}
