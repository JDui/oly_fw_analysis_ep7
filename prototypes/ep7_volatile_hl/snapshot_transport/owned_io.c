#include "owned_io.h"
#include <string.h>
static ep7q_result rejected(void)
{ ep7q_result r={false,0,-1,EP7W_REJECT,{0,0}};return r; }
static int normalize(int raw)
{ return raw>=0?0:(raw==-50?-2:-1); }
static unsigned descriptor_max(unsigned handle)
{
    if(handle==0x4c || handle==0xab || handle==0x4f)return EP7W_MAX;
    if(handle==0x4d)return EP7W_DESCRIPTOR; /* unchanged alternate queue */
    return 0;
}
static bool qualify(const ep7q_ops *ops,unsigned handle,unsigned maximum,bool receive)
{
    return ops && ops->qualify && maximum &&
        (receive?ops->receive!=NULL:ops->send!=NULL) && ops->qualify(ops->ctx,handle,maximum);
}
ep7q_result ep7q_command_receive(const ep7q_ops *ops,unsigned handle,int timeout,
    unsigned char *command,size_t command_extent,unsigned char *descriptor,size_t descriptor_extent)
{
    unsigned char scratch[148];ep7q_result r=rejected();
    if(!command || command_extent<EP7W_COMMAND || !descriptor || descriptor_extent<EP7W_MAX)return r;
    memset(descriptor+EP7W_DESCRIPTOR,0,EP7W_TRAILER);
    if(handle!=0x4b || !qualify(ops,handle,sizeof scratch,true))return r;
    r.called=true;r.raw_result=ops->receive(ops->ctx,handle,scratch,timeout);
    r.status=normalize(r.raw_result);
    if(r.raw_result<0)return r;
    r.wire_status=ep7w_decode(EP7W_COMMAND,scratch,(size_t)r.raw_result,command,command_extent,&r.ticket);
    if(r.wire_status==EP7W_REJECT){r.status=-1;return r;}
    (void)ep7w_write_trailer(descriptor+EP7W_DESCRIPTOR,r.ticket);
    return r;
}
ep7q_result ep7q_descriptor_receive(const ep7q_ops *ops,unsigned handle,int timeout,
    unsigned char *descriptor,size_t extent)
{
    unsigned maximum=descriptor_max(handle);ep7q_result r=rejected();
    if(!descriptor || extent<EP7W_MAX)return r;
    memset(descriptor+EP7W_DESCRIPTOR,0,EP7W_TRAILER);
    if(!qualify(ops,handle,maximum,true))return r;
    r.called=true;r.raw_result=ops->receive(ops->ctx,handle,descriptor,timeout);
    r.status=normalize(r.raw_result);
    if(r.raw_result>=0 && (unsigned)r.raw_result<=maximum)
        r.wire_status=ep7w_ticket(EP7W_DESCRIPTOR,descriptor,(size_t)r.raw_result,&r.ticket);
    if(r.wire_status!=EP7W_TAGGED)memset(descriptor+EP7W_DESCRIPTOR,0,EP7W_TRAILER);
    if(r.raw_result>=0 && r.wire_status==EP7W_REJECT)r.status=-1;
    return r;
}
ep7q_result ep7q_descriptor_send(const ep7q_ops *ops,unsigned handle,int timeout,
    unsigned char *descriptor,size_t extent)
{
    unsigned char scratch[EP7W_MAX];unsigned maximum=descriptor_max(handle);size_t bytes;
    ep7q_result r=rejected();ep7t_ticket carried;
    if(!descriptor || extent<EP7W_MAX)return r;
    r.wire_status=ep7w_ticket(EP7W_DESCRIPTOR,descriptor,EP7W_MAX,&carried);
    (void)ep7w_retirement_ticket(descriptor,&r.ticket);
    if(maximum!=EP7W_MAX)carried=(ep7t_ticket){0,0};
    memset(descriptor+EP7W_DESCRIPTOR,0,EP7W_TRAILER);
    if(!qualify(ops,handle,maximum,false))return r;
    if(!ep7w_encode(EP7W_DESCRIPTOR,descriptor,carried,scratch,sizeof scratch,&bytes))return r;
    r.called=true;r.raw_result=ops->send(ops->ctx,handle,scratch,(unsigned)bytes,timeout);
    r.status=normalize(r.raw_result);return r;
}
