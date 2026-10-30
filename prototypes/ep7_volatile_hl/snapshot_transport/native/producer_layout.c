#include "producer.h"
#include <string.h>
_Static_assert(sizeof(int)==4,"native timeout is a 32-bit int");
bool ep7q_producer_layout(const ep7q_stack *s,uint32_t w,const ep7q_producer_input *in,
    uint32_t expected_scope_return,ep7q_producer_args *out)
{
    uint32_t pc,capture_id,original_id,scope_id;
    if(!out)return false;
    *out=(ep7q_producer_args){0};
    if(!s || !s->expanded_group_ready || !in || !expected_scope_return || (w&3u) ||
       in->handle!=0x4b || in->nominal_bytes!=16 || !ep7q_stack_span(s,w,0,48) ||
       !ep7q_stack_word(s,w,48,&pc) || pc!=UINT32_C(0x602ac870) ||
       !ep7q_stack_word(s,w,80,&pc) || pc!=expected_scope_return ||
       !ep7q_stack_word(s,w,176,&pc) || pc!=UINT32_C(0x602ac3e3))return false;
    if(!ep7q_stack_span(s,w,52,EP7W_COMMAND) || in->command!=w+52 ||
       !ep7q_stack_span(s,w,104,sizeof(ep7q_capture_scope)) ||
       !ep7q_stack_word(s,w,44,&capture_id) || !ep7q_stack_word(s,w,96,&original_id) ||
       !ep7q_stack_word(s,w,104,&scope_id) || capture_id!=original_id || capture_id!=scope_id)return false;
    out->command=in->command;out->scope=w+104;memcpy(&out->timeout,&in->timeout,4);
    return true;
}
