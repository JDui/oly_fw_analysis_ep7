/* New startup integration only. Each process has genuinely fresh production
 * storage; longjmp observes terminal failure solely inside this host fixture. */
#include "cold_bootstrap.c"
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>

static unsigned scenario,creates,deletes,checks,queries,reason;
static jmp_buf escape;
ep7c ep7_controller_sidecar_unresolved;
static int get_tid(void *ctx,uint16_t *out)
{ (void)ctx;*out=0x2d;return 0; }
static int create(void *ctx,const ep7b_sem_spec *spec)
{
    (void)ctx;assert(!spec->attributes&&spec->initial==1&&spec->maximum==1);
    creates++;return scenario==6?-33:1;
}
static int drop(void *ctx,unsigned handle)
{ (void)ctx;assert(handle==1);deletes++;return scenario==9?-42:0; }
static int poll(void *ctx,uint16_t handle)
{ (void)ctx;assert(handle==1);return 0; }
static int signal_sem(void *ctx,uint16_t handle)
{ (void)ctx;assert(handle==1);return 0; }
ep7b_native ep7b_unresolved_native(void)
{ return (ep7b_native){NULL,create,drop,{NULL,get_tid,poll,signal_sem}}; }
bool ep7n_native_current_task(uint32_t anchor,ep7n_task *out)
{
    *out=(ep7n_task){0x2d,0,0x1000,0x601912fb,anchor&~0x7ffu,2048};
    if(scenario==2){out->domain=2;out->tid=0x202d;}
    if(scenario==3)out->entry=0x60191b74;
    if(scenario==4)out->stack_bytes=512;
    if(scenario==10)out->tid=0x2e;
    return scenario!=1;
}
bool ep7r_native_early_cohort_present(void)
{ checks++;return scenario!=5 && !(scenario==7 && checks==2); }
bool ep7cn_native_cohort_present(void){return scenario!=11;}
bool ep7q_native_cohort_present(void){return true;}
bool ep7n_postbuilder_cohort_present(void){return true;}
static bool task(void *ctx,uint32_t anchor,ep7n_task *out)
{ (void)ctx;return ep7n_native_current_task(anchor,out); }
static bool queue(void *ctx,unsigned handle,ep7n_queue *out)
{
    (void)ctx;queries++;
    unsigned maximum=handle==0x4b?148:(handle==0x4d?300:312);
    unsigned ring=handle==0x4b?4864:(handle==0x4d?9728:10112);
    *out=(ep7n_queue){(uint16_t)handle,0,0x1000,0x2000,0x3000+64*handle,
                     128,maximum,ring,0x100000+0x4000*handle};
    if((scenario==8 || scenario==9) && handle==0x4c)out->maximum=300;
    return true;
}
static int delay(void *ctx){(void)ctx;assert(!"startup must not wait for later Usr tasks");return -1;}
_Noreturn void ep7_gcc_quarantine(unsigned why){reason=why;longjmp(escape,1);}
static void quarantine(void *ctx,unsigned why){(void)ctx;ep7_gcc_quarantine(why);}
ep7r_environment ep7r_native_environment(void *ctx,bool (*ready)(void *))
{ return (ep7r_environment){ctx,ready,task,queue,delay,quarantine}; }
int main(int argc,char **argv)
{
    assert(argc==2);scenario=(unsigned)strtoul(argv[1],NULL,10);assert(scenario<=14);
    ep7_controller_sidecar_unresolved.initialized=scenario!=12;
    ep7_controller_sidecar_unresolved.poison=scenario==13;
    ep7_controller_sidecar_unresolved.serial=scenario==14;
    assert(!ep7r_get(&ep7_native_runtime_slot));
    if(!setjmp(escape)){
        ep7r_bootstrap_initialize();assert(scenario==0);
        assert(creates==1 && deletes==0 && checks==2 && queries==5);
        ep7r *r=ep7r_get(&ep7_native_runtime_slot);
        assert(r==&storage.runtime && r->boot==&storage.boot && r->boot->core==&storage.core);
        assert(ep7r_accepting(r) && storage.boot.state==EP7B_PUBLISHED);
        for(unsigned p=0;p<4;p++)for(unsigned i=0;i<24;i++)assert(!storage.core.profiles[p][i]);
        ep7r_bootstrap_initialize();assert(!"second cold initialization returned");
    }
    if(scenario==0){assert(reason==0xf01 && creates==1 && deletes==0);assert(ep7r_get(&ep7_native_runtime_slot));}
    else{
        assert(!ep7r_get(&ep7_native_runtime_slot));
        if(scenario==1 || scenario==2 || scenario==3 || scenario==4 || scenario==10)
            assert(reason==0xf02 && creates==0 && deletes==0 && checks==0);
        if(scenario==5 || scenario==11 || scenario>=12)assert(reason==0xf03 && creates==0 && deletes==0);
        if(scenario==6)assert(reason==0xf04 && creates==1 && deletes==0 && storage.boot.state==EP7B_FAILED);
        if(scenario==7 || scenario==8)assert(reason==0xf05 && creates==1 && deletes==1 && storage.boot.state==EP7B_CLOSED);
        if(scenario==9)assert(reason==0xf05 && creates==1 && deletes==1 &&
            storage.boot.state==EP7B_QUARANTINED && storage.boot.owned_handle==1);
    }
    printf("{\"scenario\":%u,\"creates\":%u,\"deletes\":%u,\"terminal_reason\":%u}\n",scenario,creates,deletes,reason);
    return 0;
}
