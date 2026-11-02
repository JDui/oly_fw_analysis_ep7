#include "worker.h"
bool ep7q_worker_legacy_cleanup_layout(const ep7q_stack *s,uint32_t w,
                                      uint32_t actual_descriptor)
{
    uint32_t pc,saved,original;const unsigned char *descriptor;unsigned i;
    /* task603f26a1 ->603ede1f(frame44) ->603f2800(frame56)
     * ->cleanup(frame24). This route never entered the H/L scope bridge.
     * 603ede1f saves code0x2002 at its+24, temporarily changes it to0x2001,
     * and retains the descriptor pointer at its+12. */
    if(!s || !s->expanded_group_ready || (w&3u) ||
       !ep7q_stack_word(s,w,24,&pc) || pc!=0x603f28c7u ||
       !ep7q_stack_word(s,w,80,&pc) || pc!=0x603edeb8u ||
       !ep7q_stack_word(s,w,124,&pc) || pc!=0x603f271fu ||
       !ep7q_stack_word(s,w,92,&saved) || saved!=actual_descriptor ||
       !ep7q_stack_word(s,w,104,&original) || (original&0xffffu)!=0x2002u ||
       !(descriptor=ep7q_stack_span(s,w,128,EP7W_MAX)) ||
       actual_descriptor!=w+128 || descriptor[194]!=1 || descriptor[195]!=0x20)return false;
    /* Receive clears non-0x2001 trailers. Never bypass cleanup for a tagged
     * or consumed descriptor, even if its surrounding return PCs look stock. */
    for(i=EP7W_DESCRIPTOR;i<EP7W_MAX;i++)if(descriptor[i])return false;
    return true;
}
bool ep7q_worker_layout(const ep7q_stack *s,uint32_t w,unsigned stage,
                       uint32_t actual_descriptor,uint32_t native_return,ep7q_worker_args *out)
{
    uint32_t pc,saved;unsigned scope,descriptor,owner,original,saved_descriptor;
    if(!out)return false;
    *out=(ep7q_worker_args){0,0};
    if(!s || !s->expanded_group_ready)return false;
    if(stage==EP7Q_WORKER_ENTER){
        scope=32;descriptor=140;original=136;saved_descriptor=24;
    }else{
        if(!native_return)return false;
        if(stage==EP7Q_WORKER_ALLOCATE){
            if(!ep7q_stack_word(s,w,4,&pc) || pc!=0x603537fau ||
               !ep7q_stack_word(s,w,48,&pc) || pc!=0x603f2845u)return false;
            owner=104;scope=136;descriptor=244;original=240;saved_descriptor=128;
        }else if(stage==EP7Q_WORKER_PROCESS || stage==EP7Q_WORKER_CLEANUP){
            if(!ep7q_stack_word(s,w,24,&pc) ||
               pc!=(stage==EP7Q_WORKER_PROCESS?0x603f2897u:0x603f28c7u))return false;
            owner=80;scope=112;descriptor=220;original=216;saved_descriptor=104;
        }else return false;
        if(!ep7q_stack_word(s,w,owner,&pc) || pc!=native_return)return false;
    }
    if(!ep7q_stack_word(s,w,original,&pc) || pc!=0x603f2727u ||
       !ep7q_stack_span(s,w,scope,48) || !ep7q_stack_span(s,w,descriptor,EP7W_MAX) ||
       !ep7q_stack_word(s,w,saved_descriptor,&saved) || saved!=w+descriptor ||
       (stage!=EP7Q_WORKER_ALLOCATE && actual_descriptor!=saved))return false;
    *out=(ep7q_worker_args){saved,w+scope};return true;
}
