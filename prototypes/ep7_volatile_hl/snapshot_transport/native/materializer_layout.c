#include "materializer.h"
#include <string.h>
_Static_assert(sizeof(int)==4,"native timeout is a 32-bit int");
bool ep7q_materializer_layout(const ep7q_stack *s,uint32_t w,unsigned handle,
                            ep7q_materializer_args *out)
{
    uint32_t pc,parent,descriptor,timeout;unsigned offset,origin;
    if(!out)return false;
    *out=(ep7q_materializer_args){0};
    if(!s || !s->expanded_group_ready || handle!=0x4b || (w&3u) || !ep7q_stack_span(s,w,0,44))return false;
    if(!ep7q_stack_word(s,w,44,&pc) || pc!=UINT32_C(0x603dfca2))return false;
    /* Materializer owns424 locals plus its16-byte native incoming CALL frame. */
    if(!ep7q_stack_word(s,w,484,&parent))return false;
    if(parent==UINT32_C(0x603dfb7d)){
        /* Read the additional parent only after identifying the normal router. */
        if(!ep7q_stack_word(s,w,532,&pc) || pc!=UINT32_C(0x603df8c0))return false;
        offset=552;origin=EP7Q_NORMAL;
    }else if(parent==UINT32_C(0x603e0594)){
        offset=496;origin=EP7Q_DRAIN_FIRST;
    }else if(parent==UINT32_C(0x603e05d2)){
        offset=496;origin=EP7Q_DRAIN_NEXT;
    }else return false;
    if(!ep7q_stack_span(s,w,offset,EP7W_MAX) || !ep7q_stack_span(s,w,196,EP7W_COMMAND) ||
       !ep7q_stack_word(s,w,56,&descriptor) || descriptor!=w+offset || !ep7q_stack_word(s,w,48,&timeout))return false;
    out->command=w+196;out->descriptor=descriptor;out->origin=origin;
    memcpy(&out->timeout,&timeout,4);
    return true;
}
