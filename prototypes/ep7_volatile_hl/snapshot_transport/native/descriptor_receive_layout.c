#include "descriptor_receive.h"
#include <string.h>
_Static_assert(sizeof(int)==4,"native timeout is a 32-bit int");
int ep7q_receive_rejection(unsigned handle)
{ return handle==0x4c || handle==0xab || handle==0x4f?-1:EP7Q_DELEGATE_RECEIVE; }
bool ep7q_descriptor_receive_layout(const ep7q_stack *s,uint32_t w,
    const ep7q_receive_input *in,ep7q_receive_args *out)
{
    uint32_t pc,parent,timeout;unsigned handle,offset,origin;
    if(!out)return false;
    *out=(ep7q_receive_args){0};
    if(!s || !s->expanded_group_ready || !in || in->nominal_bytes!=300 ||
       (w&3u) || !ep7q_stack_span(s,w,0,44) || !ep7q_stack_word(s,w,44,&pc))return false;
    if(pc==UINT32_C(0x603ef8ba) || pc==UINT32_C(0x603ef902)){
        handle=0x4c;offset=56;origin=EP7Q_DUAL_RECEIVER;
    }else if(pc==UINT32_C(0x603ef8d7) || pc==UINT32_C(0x603ef91f)){
        handle=0x4d;offset=56;origin=EP7Q_DUAL_RECEIVER;
    }else if(pc==UINT32_C(0x603dfa0b)){
        if(!ep7q_stack_word(s,w,60,&parent))return false;
        if(parent==UINT32_C(0x603ef962)){handle=0xab;origin=EP7Q_KIND19_RELAY;}
        else if(parent==UINT32_C(0x603f26bb)){handle=0x4f;origin=EP7Q_KIND19_WORKER;}
        else return false;
        offset=64;
    }else return false;
    if(in->handle!=handle || !ep7q_stack_span(s,w,offset,EP7W_MAX) ||
       in->descriptor!=w+offset || !ep7q_stack_word(s,w,48,&timeout))return false;
    out->descriptor=in->descriptor;out->origin=origin;memcpy(&out->timeout,&timeout,4);
    return true;
}
