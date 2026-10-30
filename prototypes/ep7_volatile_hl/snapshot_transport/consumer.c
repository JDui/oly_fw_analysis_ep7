#include "consumer.h"
#include <string.h>
bool ep7q_claim_owned(ep7t *transport,unsigned char *descriptor,size_t extent,ep7p_snapshot *out)
{
    ep7t_ticket ticket;int status;
    if(!descriptor || extent<EP7W_MAX || !out)return false;
    status=ep7w_ticket(EP7W_DESCRIPTOR,descriptor,EP7W_MAX,&ticket);
    (void)ep7w_mark_consumed(descriptor+EP7W_DESCRIPTOR);
    return status==EP7W_TAGGED && ep7t_claim(transport,ticket,out);
}
bool ep7q_retire_owned(ep7t *transport,unsigned char *descriptor,size_t extent)
{
    ep7t_ticket ticket;
    if(!descriptor || extent<EP7W_MAX)return false;
    (void)ep7w_mark_consumed(descriptor+EP7W_DESCRIPTOR);
    if(ep7w_retirement_ticket(descriptor,&ticket) && !ep7t_retire_owned(transport,ticket))return false;
    memset(descriptor+EP7W_DESCRIPTOR,0,EP7W_TRAILER);return true;
}
