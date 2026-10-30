#include "worker.h"
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
