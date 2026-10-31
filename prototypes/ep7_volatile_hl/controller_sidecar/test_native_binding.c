#define _GNU_SOURCE
#include "native.h"
#include "sidecar.h"
#include "../runtime/runtime.h"
#include "../snapshot_transport/native/producer.h"
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>
/* These labels are address-only native bridge surrogates. No MN103 code runs. */
__asm__(".globl ep7_native_capture_fresh\n.set ep7_native_capture_fresh,0x602a6000\n"
        ".globl ep7_native_capture_sample\n.set ep7_native_capture_sample,0x602a6020\n"
        ".globl ep7_native_capture_finish\n.set ep7_native_capture_finish,0x602a6040\n"
        ".globl ep7_native_capture_node_free\n.set ep7_native_capture_node_free,0x602a6060\n"
        ".globl ep7_native_capture_pool_release\n.set ep7_native_capture_pool_release,0x602a6080\n"
        ".globl ep7_native_capture_prewrite\n.set ep7_native_capture_prewrite,0x602a60a0\n"
        ".globl ep7_native_capture_postwrite\n.set ep7_native_capture_postwrite,0x602a60c0\n"
        ".globl ep7_native_associated_recycle\n.set ep7_native_associated_recycle,0x602a60e0\n"
        ".globl ep7_native_associated_reset\n.set ep7_native_associated_reset,0x6029e000\n"
        ".globl ep7_native_state_service_bridge\n.set ep7_native_state_service_bridge,0x6028b000\n");
static const uint32_t calls[][5]={
    {0x602973bc,0x602a60e0,4,0,8},{0x6029c692,0x6029e000,2,0xf0,28},
    {0x602a7ea0,0x602a60a0,4,0,24},{0x602a8dca,0x602a60c0,4,0,24},
    {0x602a31c7,0x602a6000,2,0xa0,28},{0x602a440a,0x602a6000,2,0xa0,28},{0x602a4480,0x602a6000,2,0xa0,28},
    {0x602a31ea,0x602a6020,2,0xf0,20},{0x602a442c,0x602a6020,2,0xf0,20},{0x602a44a3,0x602a6020,2,0xf0,20},
    {0x602a31f7,0x602a6040,2,0xf0,48},{0x602a443e,0x602a6040,2,0xf0,48},{0x602a44b5,0x602a6040,2,0xf0,48},
    {0x60289c5e,0x6028b000,2,0xf0,32},{0x60289d02,0x6028b000,2,0xf0,32},
    {0x6029be5d,0x602a6080,4,0,4},
    {0x602a31b1,0x602a6060,4,0,4},{0x602a4461,0x602a6060,4,0,4},
    {0x6029f1c2,0x602a6060,4,0,4},{0x602a4220,0x602a6060,4,0,4},
    {0x6029f6ba,0x602a6060,4,0,4},{0x602a29ab,0x602a6060,4,0,4},
    {0x602a2a00,0x602a6060,4,0,4},{0x602a2a48,0x602a6060,4,0,4},
    {0x602a2ab5,0x602a6060,4,0,4},{0x602a427d,0x602a6060,4,0,4},
    {0x602a44d8,0x602a6060,4,0,4},{0x602a2cb9,0x602a6060,4,0,4},
    {0x602a2d0d,0x602a6060,4,0,4}};
static _Alignas(4) uint8_t nodes[2][56],captures[2][27332],registry[2][20];
static uint8_t *const associated[2]={(uint8_t *)(uintptr_t)0x6223e164,(uint8_t *)(uintptr_t)0x6223e174};
static volatile uint16_t *const native_state=(volatile uint16_t *)(uintptr_t)0x62234fc0;
static ep7p core;
static ep7b boot;
static ep7r runtime;
static unsigned wrong_task,native_resumed,quarantine_reason,sem_held;
static void (*lookup_callback)(void),(*poll_callback)(void);
static jmp_buf fatal;
static uint32_t addr(const void *p) { assert((uintptr_t)p<=UINT32_MAX);return (uint32_t)(uintptr_t)p; }
static void put32(uint8_t *p,uint32_t v) { for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(v>>(8*i)); }
_Noreturn void ep7_gcc_quarantine(unsigned reason) { quarantine_reason=reason;longjmp(fatal,1); }
void *ep7_gcc_capture_lookup(unsigned id)
{
    if (lookup_callback) { void (*cb)(void)=lookup_callback;lookup_callback=NULL;cb(); }
    return id>=1&&id<=2?captures[id-1]:NULL;
}
static int tid(void *ctx,uint16_t *out) { (void)ctx;*out=0x73;return 0; }
static int create(void *ctx,const ep7b_sem_spec *spec)
{ (void)ctx;assert(!spec->attributes&&spec->initial==1&&spec->maximum==1);return 1; }
static int destroy(void *ctx,unsigned id) { (void)ctx;assert(id==1);return 0; }
static int poll(void *ctx,uint16_t id)
{
    (void)ctx;assert(id==1&&!sem_held);
    if (poll_callback) { void (*cb)(void)=poll_callback;poll_callback=NULL;cb(); }
    sem_held=1;return 0;
}
static int signal_sem(void *ctx,uint16_t id) { (void)ctx;assert(id==1&&sem_held);sem_held=0;return 0; }
static bool ready(void *ctx) { (void)ctx;return true; }
static bool task(void *ctx,uint32_t anchor,ep7n_task *out)
{
    (void)ctx;(void)anchor;
    /* Only a task/stack boundary fixture. The real task query is tested elsewhere. */
    *out=(ep7n_task){0x73,0,0x1000+wrong_task,0x60289852,0x1000,0xffffe000};return true;
}
static bool queue(void *ctx,unsigned id,ep7n_queue *out)
{
    (void)ctx;unsigned maximum=id==0x4b?148:id==0x4d?300:312;
    unsigned ring=id==0x4b?4864:id==0x4d?9728:10112;
    *out=(ep7n_queue){(uint16_t)id,0,0x1000,0x2000,0x3000+id*32,128,maximum,ring,0x10000+id*0x10000};return true;
}
static int delay(void *ctx) { (void)ctx;assert(!"capture must not delay");return 0; }
static void runtime_fault(void *ctx,unsigned reason) { (void)ctx;ep7_gcc_quarantine(reason); }
static void setup(void)
{
    void *p=mmap((void *)(uintptr_t)0x60289000,0x20000,PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(p==(void *)(uintptr_t)0x60289000);
    p=mmap((void *)(uintptr_t)0x62234000,4096,PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(p==(void *)(uintptr_t)0x62234000);
    p=mmap((void *)(uintptr_t)0x6223e000,4096,PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(p==(void *)(uintptr_t)0x6223e000);
    put32((uint8_t *)(uintptr_t)0x6223e0d8,0x6223e0dc);
    put32((uint8_t *)(uintptr_t)0x6223e0e4,(4u<<16)|25u);
    put32((uint8_t *)(uintptr_t)0x6223e0e8,0x6223e0fc);
    put32((uint8_t *)(uintptr_t)0x6223e0f4,16);
    put32((uint8_t *)(uintptr_t)0x6223e0f8,0x6223e160);
    for (unsigned i=0;i<sizeof calls/sizeof calls[0];i++) {
        const uint32_t *c=calls[i];uint8_t *site=(uint8_t *)(uintptr_t)c[0];uint32_t delta=c[1]-c[0];
        if(c[2]==2) assert((int32_t)delta>=INT16_MIN&&(int32_t)delta<=INT16_MAX);
        site[0]=c[2]==2?0xcd:0xdd;
        for (unsigned j=0;j<c[2];j++) site[1+j]=(uint8_t)(delta>>(8*j));
        site[1+c[2]]=(uint8_t)c[3];site[2+c[2]]=(uint8_t)c[4];
    }
    assert(ep7cn_native_cohort_present());
    ep7b_native n={NULL,create,destroy,{NULL,tid,poll,signal_sem}};
    assert(ep7b_prepare(&boot,&core,n));
    ep7r_environment e={NULL,ready,task,queue,delay,runtime_fault};
    assert(ep7r_prepare(&runtime,&boot,e));
    ep7cn_initialize(0);*native_state=0;
    assert(ep7r_publish(&ep7_native_runtime_slot,&runtime));
    ep7_sidecar_transition_unresolved(0,33);*native_state=33;
    for (unsigned i=0;i<2;i++) {
        put32(nodes[i],i+1);put32(nodes[i]+8,addr(associated[i]));
        put32(associated[i],i+1);put32(associated[i]+8,addr(nodes[i]));
        put32(associated[i]-4,1);
        captures[i][24053]=11;captures[i][24083]=2;put32(registry[i]+12,addr(captures[i]));
    }
}
static void edit(int8_t value) { int8_t hl[24]={0};hl[0]=value;assert(ep7p_edit(&core,1,hl)); }
static bool copy(unsigned i,ep7p_snapshot *out) { return ep7q_capture_snapshot_unresolved(i+1,addr(associated[i]),out); }
static void run_population(unsigned i,unsigned post)
{ ep7cn_prewrite(addr(captures[i]),post);ep7cn_population(addr(nodes[i]),post); }
static void seal(unsigned i) { ep7cn_fresh(addr(nodes[i]));run_population(i,0);run_population(i,1); }
static void try_free(void) { ep7cn_free(addr(nodes[0]));native_resumed=1; }
static void try_pool(void) { ep7cn_release_capture(addr(registry[0]));native_resumed=1; }
static void try_state(void) { ep7_sidecar_transition_unresolved(33,34);native_resumed=1; }
static void try_init(void) { ep7cn_initialize(0);native_resumed=1; }
static void try_prewrite(void) { ep7cn_prewrite(addr(captures[0]),0);native_resumed=1; }
static void bad_prewrite(void) { ep7cn_prewrite(0,0);native_resumed=1; }
static void try_recycle(void)
{ put32(associated[0]-4,0);ep7cn_associated_recycle(0x6223e0dc,addr(associated[0]-4));native_resumed=1; }
static void live_recycle(void)
{ ep7cn_associated_recycle(0x6223e0dc,addr(associated[0]-4));native_resumed=1; }
static void bad_recycle(void) { ep7cn_associated_recycle(0x6223e0dc,4);native_resumed=1; }
static void try_reset(void) { ep7cn_associated_reset();native_resumed=1; }
static void bad_prefix(void) { ep7cn_fresh(4);native_resumed=1; }
static void population(void) { run_population(0,0); }
static void expect_fault(void (*fn)(void),unsigned reason)
{
    if (!setjmp(fatal)) { fn();assert(!"destructive callback returned"); }
    assert(quarantine_reason==reason&&!native_resumed);
}
static void scenario(unsigned which)
{
    setup();ep7p_snapshot out;uint64_t token;
    switch(which) {
    case 0: /* Real address reads, same published core, and frozen sample. */
        edit(5);ep7cn_fresh(addr(nodes[0]));run_population(0,0);edit(-3);
        run_population(0,1);assert(copy(0,&out)&&out.profile==1&&out.hl[0]==5);
        ep7r_stop(&runtime);assert(!copy(0,&out));try_free();
        assert(native_resumed&&!ep7c_resolve_live(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),&token));break;
    case 1: /* Early copy consumes the chance; no late resampling. */
        ep7cn_fresh(addr(nodes[0]));assert(!copy(0,&out));edit(7);
        run_population(0,0);run_population(0,1);assert(!copy(0,&out));break;
    case 2: /* Capture retirement and address reuse; other capture stays valid. */
        edit(4);seal(0);seal(1);assert(ep7c_resolve_live(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),&token));
        ep7cn_release_capture(addr(registry[0]));assert(!copy(0,&out)&&copy(1,&out));
        seal(0);assert(!ep7c_authorize(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),token));
        assert(copy(0,&out));break;
    case 3: /* Every CALL byte role participates; fail before touching a bogus node. */
        for(unsigned i=0;i<sizeof calls/sizeof calls[0];i++) {
            uint8_t *p=(uint8_t *)(uintptr_t)calls[i][0];p[1]^=1;
            assert(!ep7cn_native_cohort_present());p[1]^=1;assert(ep7cn_native_cohort_present());
        }
        *(uint8_t *)(uintptr_t)(0x602a440a+4)=24;expect_fault(bad_prefix,0xe04);break;
    case 4:case 5:case 6:case 7: /* Lookup and core poll callbacks cannot free held input. */
        ep7cn_fresh(addr(nodes[0]));
        if(which==7) poll_callback=try_free;
        else lookup_callback=which==4?try_free:which==5?try_pool:try_state;
        expect_fault(population,0xe05);
        assert(ep7c_resolve_live(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),&token));break;
    case 8: /* A mismatching context cannot resume the original destructive call. */
        seal(0);wrong_task=4;expect_fault(try_free,0xe03);break;
    case 9: /* Non-destructive foreign input closes admission permanently. */
        seal(0);wrong_task=4;assert(!copy(0,&out));wrong_task=0;assert(!copy(0,&out));break;
    case 10: /* Permanent runtime identity survives stopping; unpublication does not. */
        seal(0);atomic_store(&ep7_native_runtime_slot.published,NULL);expect_fault(try_pool,0xe02);break;
    case 11: /* No live reinitialization/reset can proceed through native state0 store. */
        seal(0);expect_fault(try_init,0xe01);
        assert(ep7c_resolve_live(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),&token));break;
    case 12: { /* Same ID/address/profile is a new population, BEFORE its writes. */
        ep7p_snapshot frozen;edit(5);seal(0);seal(1);assert(copy(0,&frozen));
        ep7cn_prewrite(addr(captures[0]),0);assert(!copy(0,&out)&&copy(1,&out));
        edit(-6);ep7cn_population(addr(nodes[0]),0);run_population(0,1);
        assert(!copy(0,&out)&&frozen.hl[0]==5);break;
    }
    case 13: /* Postpopulation alone may rewrite mode; revoke before first store. */
        seal(0);seal(1);ep7cn_prewrite(addr(captures[0]),1);
        assert(!copy(0,&out)&&copy(1,&out));ep7cn_population(addr(nodes[0]),1);
        assert(!copy(0,&out));break;
    case 14: /* Overlapping entry and reversed phases both burn a fresh chance. */
        ep7cn_fresh(addr(nodes[0]));ep7cn_prewrite(addr(captures[0]),0);
        run_population(0,0);run_population(0,1);assert(!copy(0,&out));
        ep7cn_fresh(addr(nodes[1]));ep7cn_prewrite(addr(captures[1]),1);
        run_population(1,0);run_population(1,1);assert(!copy(1,&out));break;
    case 15: /* Neither completion observer can substitute for prewrite entry. */
        ep7cn_fresh(addr(nodes[0]));ep7cn_population(addr(nodes[0]),0);
        run_population(0,1);assert(!copy(0,&out));
        ep7cn_fresh(addr(nodes[1]));run_population(1,0);
        ep7cn_population(addr(nodes[1]),1);assert(!copy(1,&out));break;
    case 16: /* Mutating another capture cannot authorize this node's sample. */
        ep7cn_fresh(addr(nodes[0]));ep7cn_fresh(addr(nodes[1]));
        ep7cn_prewrite(addr(captures[1]),0);ep7cn_population(addr(nodes[0]),0);
        run_population(0,1);assert(!copy(0,&out));
        run_population(1,0);run_population(1,1);assert(!copy(1,&out));break;
    case 17:
        seal(0);wrong_task=4;expect_fault(try_prewrite,0xe03);break;
    case 18:
        ep7cn_fresh(addr(nodes[0]));lookup_callback=try_prewrite;
        expect_fault(population,0xe05);break;
    case 19: { /* Stop does not suppress required revocation of existing images. */
        seal(0);ep7r_stop(&runtime);ep7cn_prewrite(addr(captures[0]),0);
        assert(ep7c_resolve_live(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),&token));
        ep7c_prefix v={addr(associated[0]),addr(captures[0]),1,11,2};
        assert(!ep7c_copyout(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),token,&v,&out));break;
    }
    case 20:
        seal(0);expect_fault(bad_prewrite,0xe07);break;
    case 21: { /* Associated can return to its pool while its node is still live. */
        ep7p_snapshot frozen;edit(4);seal(0);seal(1);assert(copy(0,&frozen));
        assert(ep7c_resolve_live(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),&token));
        try_recycle();assert(native_resumed&&!copy(0,&out)&&copy(1,&out));
        assert(!ep7c_authorize(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),token));
        /* Simulated subsequent free/fresh allocation reuses the same addresses. */
        ep7cn_free(addr(nodes[0]));put32(associated[0]-4,1);seal(0);
        assert(copy(0,&out)&&frozen.hl[0]==4);
        assert(!ep7c_authorize(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),token));break;
    }
    case 22: /* Generic allocator's other pools may belong to another task. */
        seal(0);wrong_task=4;ep7cn_associated_recycle(0x62236654,4);
        wrong_task=0;assert(copy(0,&out));break;
    case 23:
        seal(0);wrong_task=4;expect_fault(try_recycle,0xe03);break;
    case 24:
        ep7cn_fresh(addr(nodes[0]));lookup_callback=try_recycle;
        expect_fault(population,0xe05);break;
    case 25:
        seal(0);expect_fault(bad_recycle,0xe08);break;
    case 26:
        seal(0);expect_fault(live_recycle,0xe08);break;
    case 27: { /* Reset invalidates both sealed and pending without reusing tokens. */
        ep7p_snapshot frozen;seal(0);assert(copy(0,&frozen));
        assert(ep7c_resolve_live(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),&token));
        ep7cn_fresh(addr(nodes[1]));run_population(1,0);ep7cn_associated_reset();
        assert(!copy(0,&out)&&!copy(1,&out));run_population(1,1);assert(!copy(1,&out));
        seal(0);assert(copy(0,&out)&&frozen.profile==1);
        assert(!ep7c_authorize(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),token));break;
    }
    case 28:
        ep7cn_fresh(addr(nodes[0]));lookup_callback=try_reset;
        expect_fault(population,0xe05);break;
    case 29: { /* Fixed provenance before backlink access, including slot endpoints. */
        put32(nodes[0]+8,4);ep7cn_fresh(addr(nodes[0]));
        assert(!ep7c_resolve_live(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),&token));
        assert(!ep7q_capture_snapshot_unresolved(1,4,&out));
        put32(nodes[0]+8,addr(associated[0]));seal(0);put32(associated[0]-4,0);assert(!copy(0,&out));
        put32(associated[0]-4,1);seal(0);put32((uint8_t *)(uintptr_t)0x6223e0f4,20);
        assert(!copy(0,&out));put32((uint8_t *)(uintptr_t)0x6223e0f4,16);
        uint8_t *last=(uint8_t *)(uintptr_t)0x6223e2e4;
        put32(last-4,1);put32(last,2);put32(last+8,addr(nodes[1]));put32(nodes[1]+8,addr(last));
        ep7cn_fresh(addr(nodes[1]));run_population(1,0);run_population(1,1);
        assert(ep7q_capture_snapshot_unresolved(2,addr(last),&out));ep7cn_free(addr(nodes[1]));
        put32(nodes[1]+8,addr(last+16));ep7cn_fresh(addr(nodes[1]));
        assert(!ep7c_resolve_live(&ep7_controller_sidecar_unresolved,33,addr(nodes[1]),&token));break;
    }
    case 30:
        seal(0);ep7r_stop(&runtime);try_recycle();
        assert(!ep7c_resolve_live(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),&token));break;
    default:assert(!"unknown case");
    }
}
int main(void)
{
    /* Each fork is a fresh simulated boot; production state exposes no reset. */
    for (unsigned i=0;i<31;i++) {
        pid_t child=fork();assert(child>=0);
        if (!child) { scenario(i);_exit(0); }
        int status;assert(waitpid(child,&status,0)==child);
        if(!WIFEXITED(status)||WEXITSTATUS(status)!=0) {
            fprintf(stderr,"capture fixture scenario %u failed (wait status %d)\n",i,status);
            assert(!"capture fixture failed");
        }
    }
    return 0;
}
