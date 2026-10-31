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
static bool wait_caller(uint32_t pc)
{ return pc==0x602ac502u || pc==0x602ac5abu || pc==0x602ac671u; }
bool ep7q_wait_pop_layout(const ep7q_stack *s,uint32_t w,uint32_t label,uint32_t *scope)
{
    uint32_t pc;
    if(!scope)return false;
    *scope=0;
    if(!s || !s->expanded_group_ready || !label || (w&3u) ||
       !ep7q_stack_span(s,w,0,28) || !ep7q_stack_word(s,w,24,&pc))return false;
    if(pc==0x602ac8ffu)return true; /* Cancel drain owns no producer scope. */
    if(pc!=0x602ac5efu || !ep7q_stack_word(s,w,32,&pc) || pc!=label ||
       !ep7q_stack_word(s,w,104,&pc) || !wait_caller(pc) ||
       !ep7q_stack_span(s,w,56,sizeof(ep7q_capture_scope)))return false;
    *scope=w+56;return true;
}
bool ep7q_wait_producer_layout(const ep7q_stack *s,uint32_t w,const ep7q_producer_input *in,
    uint32_t label,ep7q_producer_args *out)
{
    uint32_t pc,id,scope_id;
    if(!out)return false;
    *out=(ep7q_producer_args){0};
    if(!s || !s->expanded_group_ready || !in || !label || (w&3u) ||
       in->handle!=0x4b || in->nominal_bytes!=16 ||
       !ep7q_stack_span(s,w,0,48) || !ep7q_stack_word(s,w,48,&pc) || pc!=0x602ac870u ||
       !ep7q_stack_word(s,w,80,&pc) || pc!=0x602ac613u ||
       !ep7q_stack_word(s,w,88,&pc) || pc!=label ||
       !ep7q_stack_word(s,w,160,&pc) || !wait_caller(pc) ||
       !ep7q_stack_span(s,w,52,EP7W_COMMAND) || in->command!=w+52 ||
       !ep7q_stack_span(s,w,112,sizeof(ep7q_capture_scope)) ||
       !ep7q_stack_word(s,w,44,&id) || !ep7q_stack_word(s,w,112,&scope_id) || id!=scope_id)return false;
    out->command=in->command;out->scope=w+112;memcpy(&out->timeout,&in->timeout,4);return true;
}
