#include "ack.h"
bool ep7q_ack_layout(const ep7q_stack *s,uint32_t w,uint32_t descriptor,ep7q_ack_args *out)
{
    uint32_t pc;unsigned offset,origin;
    if(!out)return false;
    *out=(ep7q_ack_args){0,0};
    if(!s || !s->expanded_group_ready || !ep7q_stack_word(s,w,32,&pc))return false;
    if(pc==0x603dfc6cu){
        if(!ep7q_stack_word(s,w,80,&pc) || pc!=0x603df8c0u)return false;
        offset=100;origin=EP7Q_ACK_NORMAL;
    }else if(pc==0x603e05cbu){offset=44;origin=EP7Q_ACK_DRAIN;}
    else if(pc==0x603f2770u){offset=36;origin=EP7Q_ACK_WORKER;}
    else return false;
    if(!ep7q_stack_span(s,w,offset,EP7W_MAX) || descriptor!=w+offset)return false;
    *out=(ep7q_ack_args){descriptor,origin};return true;
}
