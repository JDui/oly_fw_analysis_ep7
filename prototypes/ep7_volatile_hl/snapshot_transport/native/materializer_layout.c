#include "materializer.h"
#include <string.h>
_Static_assert(sizeof(int)==4,"native timeout is a 32-bit int");
static const unsigned char *span(const ep7q_stack *s,uint32_t w,unsigned offset,unsigned count)
{
    uint32_t address;size_t index;
    if(!s->bytes || !count || offset>UINT32_MAX-w)return NULL;
    address=w+offset;
    if(count-1>UINT32_MAX-address || address<s->low)return NULL;
    index=(size_t)(address-s->low);
    if(index>s->extent || count>s->extent-index)return NULL;
    return s->bytes+index;
}
static bool word(const ep7q_stack *s,uint32_t w,unsigned offset,uint32_t *out)
{
    const unsigned char *p=span(s,w,offset,4);
    if(!p)return false;
    *out=(uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
    return true;
}
bool ep7q_materializer_layout(const ep7q_stack *s,uint32_t w,unsigned handle,
                            ep7q_materializer_args *out)
{
    uint32_t pc,parent,descriptor,timeout;unsigned offset,origin;
    if(!out)return false;
    *out=(ep7q_materializer_args){0};
    if(!s || !s->expanded_group_ready || handle!=0x4b || (w&3u) || !span(s,w,0,44))return false;
    if(!word(s,w,44,&pc) || pc!=UINT32_C(0x603dfca2))return false;
    /* Materializer owns424 locals plus its16-byte native incoming CALL frame. */
    if(!word(s,w,484,&parent))return false;
    if(parent==UINT32_C(0x603dfb7d)){
        /* Read the additional parent only after identifying the normal router. */
        if(!word(s,w,532,&pc) || pc!=UINT32_C(0x603df8c0))return false;
        offset=552;origin=EP7Q_NORMAL;
    }else if(parent==UINT32_C(0x603e0594)){
        offset=496;origin=EP7Q_DRAIN_FIRST;
    }else if(parent==UINT32_C(0x603e05d2)){
        offset=496;origin=EP7Q_DRAIN_NEXT;
    }else return false;
    if(!span(s,w,offset,EP7W_MAX) || !span(s,w,196,EP7W_COMMAND) ||
       !word(s,w,56,&descriptor) || descriptor!=w+offset || !word(s,w,48,&timeout))return false;
    out->command=w+196;out->descriptor=descriptor;out->origin=origin;
    memcpy(&out->timeout,&timeout,4);
    return true;
}
