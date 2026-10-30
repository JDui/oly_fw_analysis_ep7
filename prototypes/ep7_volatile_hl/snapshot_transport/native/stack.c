#include "stack.h"
const unsigned char *ep7q_stack_span(const ep7q_stack *s,uint32_t w,unsigned offset,unsigned count)
{
    uint32_t address;size_t index;
    if(!s || !s->bytes || !count || offset>UINT32_MAX-w)return NULL;
    address=w+offset;
    if(count-1>UINT32_MAX-address || address<s->low)return NULL;
    index=(size_t)(address-s->low);
    if(index>s->extent || count>s->extent-index)return NULL;
    return s->bytes+index;
}
bool ep7q_stack_word(const ep7q_stack *s,uint32_t w,unsigned offset,uint32_t *out)
{
    const unsigned char *p=ep7q_stack_span(s,w,offset,4);
    if(!p || !out)return false;
    *out=(uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
    return true;
}
