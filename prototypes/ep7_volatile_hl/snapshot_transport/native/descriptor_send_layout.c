#include "descriptor_send.h"
#include <string.h>
_Static_assert(sizeof(int)==4,"native timeout is a 32-bit int");
bool ep7q_descriptor_send_layout(const ep7q_stack *s,uint32_t w,
    const ep7q_send_input *in,ep7q_send_args *out)
{
    uint32_t pc,parent,timeout;unsigned offset,origin;
    if(!out)return false;
    *out=(ep7q_send_args){0};
    if(!s || !s->expanded_group_ready || !in || (w&3u) ||
       !ep7q_stack_span(s,w,0,36) || !ep7q_stack_word(s,w,36,&pc) ||
       pc!=UINT32_C(0x603dfaa8) || !ep7q_stack_word(s,w,56,&parent))return false;
    if(parent==UINT32_C(0x603dfc44)){
        if(!ep7q_stack_word(s,w,104,&pc) || pc!=UINT32_C(0x603df8c0))return false;
        offset=124;origin=EP7Q_NORMAL_SENDER;
    }else if(parent==UINT32_C(0x603ef93e)){
        offset=68;origin=EP7Q_DUAL_SENDER;
    }else if(parent==UINT32_C(0x603ef993)){
        offset=60;origin=EP7Q_KIND19_SENDER;
    }else return false;
    if(!ep7q_stack_span(s,w,offset,EP7W_MAX) || in->descriptor!=w+offset ||
       !ep7q_stack_word(s,w,40,&timeout))return false;
    out->descriptor=in->descriptor;out->origin=origin;memcpy(&out->timeout,&timeout,4);
    return true;
}
