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
        ".globl ep7_native_wait_enqueue\n.set ep7_native_wait_enqueue,0x602aca00\n"
        ".globl ep7_native_wait_pop\n.set ep7_native_wait_pop,0x602aca20\n"
        ".globl ep7_native_wait_reset\n.set ep7_native_wait_reset,0x602aca40\n"
        ".globl ep7_native_wait_scope\n.set ep7_native_wait_scope,0x602aca60\n"
        ".globl ep7_wait_scope_native_return\n.set ep7_wait_scope_native_return,0x602aca80\n"
        ".globl ep7_native_engine_configure\n.set ep7_native_engine_configure,0x602a6100\n"
        ".globl ep7_native_engine_pool\n.set ep7_native_engine_pool,0x602a4000\n"
        ".globl ep7_native_state_service_bridge\n.set ep7_native_state_service_bridge,0x6028b000\n");
static const uint32_t calls[][5]={
    {0x6029ef4c,0x602a6100,2,0x20,8},{0x602a27e4,0x602a6100,2,0x20,8},
    {0x6029ce9d,0x602a4000,2,0xc0,16},
    {0x602ac3f6,0x602aca00,4,0,8},{0x602ac5e8,0x602aca20,4,0,24},
    {0x602ac8f8,0x602aca20,4,0,24},{0x602abe96,0x602aca40,4,0x80,4},
    {0x602ac4fd,0x602aca60,2,0x80,8},{0x602ac5a6,0x602aca60,2,0x80,8},{0x602ac66c,0x602aca60,2,0x80,8},
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
static void (*list_callback)(void);
static _Alignas(4) unsigned char wait_stack[164];
static unsigned list_bad_result;
static jmp_buf fatal;
static uint32_t addr(const void *p) { assert((uintptr_t)p<=UINT32_MAX);return (uint32_t)(uintptr_t)p; }
static void put32(uint8_t *p,uint32_t v) { for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(v>>(8*i)); }
static uint16_t *list_half(unsigned offset) { return (uint16_t *)(uintptr_t)(0x6223e7e0u+offset); }
static uint32_t *list_slot(unsigned index) { assert(index<25);return (uint32_t *)(uintptr_t)(0x6223e7f4u+4u*index); }
static void list_before(void)
{ if(list_callback) { void (*cb)(void)=list_callback;list_callback=NULL;cb(); } }
uint32_t ep7_gcc_wait_enqueue(uint32_t queue,uint32_t associated_value)
{
    assert(queue==0x6223e7e0u);list_before();
    if(*list_half(12)==25)return 0;
    unsigned tail=*list_half(14);*list_slot(tail)=associated_value;
    ++*list_half(12);*list_half(14)=(uint16_t)((tail+1u)%25u);
    return list_bad_result?0u:4u;
}
uint32_t ep7_gcc_wait_pop(uint32_t queue)
{
    assert(queue==0x6223e7e0u);list_before();
    if(!*list_half(12))return 0;
    unsigned head=*list_half(16);uint32_t result=*list_slot(head);
    --*list_half(12);*list_half(16)=(uint16_t)((head+1u)%25u);
    return list_bad_result?0u:result;
}
static void list_initialize(void)
{
    put32((uint8_t *)(uintptr_t)0x6223e7dc,0x6223e7e0);
    put32((uint8_t *)(uintptr_t)0x6223e7e0,182);
    *list_half(4)=25;*list_half(6)=4;
    put32((uint8_t *)(uintptr_t)0x6223e7e8,0x6223e7f4);
    *list_half(12)=*list_half(14)=*list_half(16)=0;
}
static void engine_initialize(void)
{
    const uint32_t callbacks[17]={0x602a2d43,0x602a2ec7,0x602a2ef7,0x602a2f57,
        0x602a2f62,0x602a2f91,0x602a2f6d,0x602a2f73,0x602a2f70,0x602a2f7e,0,
        0x602a301b,0x602a2f81,0x602a3042,0x60000,0x602a2edd,0x70000};
    put32((uint8_t *)(uintptr_t)0x6223d0d8,0xf000f);
    for(unsigned i=0;i<17;i++)put32((uint8_t *)(uintptr_t)(0x6223d134u+4u*i),callbacks[i]);
}
static void wait_layout(void)
{
    memset(wait_stack,0,sizeof wait_stack);
    put32(wait_stack+80,0x602ac5ef);put32(wait_stack+88,0x602aca80);put32(wait_stack+160,0x602ac502);
}
static ep7q_capture_scope *wait_output(void) { return (ep7q_capture_scope *)(void *)(wait_stack+112); }
static void enqueue(unsigned i) { assert(ep7cn_wait_enqueue(0x6223e7e0,addr(associated[i]))==4); }
static void pop_one(unsigned i) { assert(ep7cn_wait_pop(0x6223e7e0,addr(wait_stack+56))==addr(associated[i])); }
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
    void *p=mmap((void *)(uintptr_t)0x60289000,0x25000,PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(p==(void *)(uintptr_t)0x60289000);
    p=mmap((void *)(uintptr_t)0x62234000,4096,PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(p==(void *)(uintptr_t)0x62234000);
    p=mmap((void *)(uintptr_t)0x6223e000,4096,PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(p==(void *)(uintptr_t)0x6223e000);
    p=mmap((void *)(uintptr_t)0x6223d000,4096,PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(p==(void *)(uintptr_t)0x6223d000);
    put32((uint8_t *)(uintptr_t)0x6223e0d8,0x6223e0dc);
    put32((uint8_t *)(uintptr_t)0x6223e0e4,(4u<<16)|25u);
    put32((uint8_t *)(uintptr_t)0x6223e0e8,0x6223e0fc);
    put32((uint8_t *)(uintptr_t)0x6223e0f4,16);
    put32((uint8_t *)(uintptr_t)0x6223e0f8,0x6223e160);
    list_initialize();wait_layout();engine_initialize();
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
static void try_enqueue(void) { (void)ep7cn_wait_enqueue(0x6223e7e0,addr(associated[0]));native_resumed=1; }
static void try_pop(void) { (void)ep7cn_wait_pop(0x6223e7e0,addr(wait_stack+56));native_resumed=1; }
static void try_engine(void) { ep7cn_engine_epoch();native_resumed=1; }
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
    case 31: { /* Actual C enqueue owns a value before node retirement/UI edits. */
        edit(5);seal(0);enqueue(0);edit(-6);seal(1);enqueue(1);
        ep7cn_free(addr(nodes[0]));ep7cn_free(addr(nodes[1]));edit(2);
        pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_AVAILABLE&&wait_output()->snapshot.hl[0]==5);
        ep7q_capture_scope frozen=*wait_output();pop_one(1);
        assert(wait_output()->state==EP7Q_SCOPE_AVAILABLE&&wait_output()->snapshot.hl[0]==-6&&frozen.snapshot.hl[0]==5);
        assert(!copy(0,&out)&&!copy(1,&out));break;
    }
    case 32: /* Reused associated address cannot replace an older queued value. */
        edit(3);seal(0);enqueue(0);try_recycle();put32(associated[0]-4,1);
        edit(-4);seal(0);enqueue(0);pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_EMPTY);
        pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_AVAILABLE&&wait_output()->snapshot.hl[0]==-4);break;
    case 33:
        seal(0);seal(1);enqueue(0);enqueue(1);ep7cn_prewrite(addr(captures[0]),0);
        ep7cn_release_capture(addr(registry[1]));pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_EMPTY);
        pop_one(1);assert(wait_output()->state==EP7Q_SCOPE_EMPTY);break;
    case 34:
        seal(0);enqueue(0);ep7_sidecar_transition_unresolved(33,255);pop_one(0);
        assert(wait_output()->state==EP7Q_SCOPE_AVAILABLE);enqueue(0);
        ep7_sidecar_transition_unresolved(33,33);pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_EMPTY);break;
    case 35: /* List reset and entries predating tracking never recover a value. */
        seal(0);enqueue(0);ep7cn_wait_reset();list_initialize();
        assert(ep7_gcc_wait_enqueue(0x6223e7e0,addr(associated[0]))==4);
        pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_EMPTY);enqueue(0);pop_one(0);
        assert(wait_output()->state==EP7Q_SCOPE_AVAILABLE);break;
    case 36:
        seal(0);enqueue(0);ep7cn_associated_reset();pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_EMPTY);
        seal(0);enqueue(0);put32(associated[0]-4,0);assert(!copy(0,&out));put32(associated[0]-4,1);
        pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_EMPTY);break;
    case 37: /* Native full/empty results, FIFO wrap, and stopped cleanup. */
        seal(0);for(unsigned i=0;i<25;i++)enqueue(0);
        assert(ep7cn_wait_enqueue(0x6223e7e0,addr(associated[1]))==0);
        for(unsigned i=0;i<25;i++) { pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_AVAILABLE); }
        assert(ep7cn_wait_pop(0x6223e7e0,addr(wait_stack+56))==0&&wait_output()->state==EP7Q_SCOPE_EMPTY);
        enqueue(0);ep7r_stop(&runtime);pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_EMPTY);break;
    case 38: /* Cancellation consumes its ledger slot without writing a scope. */
        seal(0);enqueue(0);put32(wait_stack+80,0x602ac8ff);pop_one(0);
        assert(wait_output()->state==EP7Q_SCOPE_EMPTY);wait_layout();enqueue(0);pop_one(0);
        assert(wait_output()->state==EP7Q_SCOPE_AVAILABLE);break;
    case 39:
        seal(0);enqueue(0);wrong_task=4;expect_fault(try_pop,0xe03);break;
    case 40: /* Capture guard covers the native list call, not just helper entry. */
        seal(0);list_callback=try_recycle;expect_fault(try_enqueue,0xe05);break;
    case 41:
        seal(0);list_bad_result=1;expect_fault(try_enqueue,0xe09);break;
    case 42: /* A changed head slot cannot silently bind another image. */
        seal(0);enqueue(0);*list_slot(0)=addr(associated[1]);expect_fault(try_pop,0xe09);break;
    case 43: {
        uint32_t scoped;ep7q_producer_args args;
        ep7q_stack s={wait_stack,0x1000,sizeof wait_stack,true};
        ep7q_producer_input in={0x4b,16,0x1034,UINT32_MAX};
        const uint32_t returns[]={0x602ac502,0x602ac5ab,0x602ac671};
        for(unsigned i=0;i<3;i++) {
            put32(wait_stack+160,returns[i]);put32(wait_stack+80,0x602ac5ef);
            assert(ep7q_wait_pop_layout(&s,0x1038,0x602aca80,&scoped)&&scoped==0x1070);
            put32(wait_stack+80,0x602ac613);put32(wait_stack+48,0x602ac870);
            put32(wait_stack+44,1);put32(wait_stack+112,1);
            assert(ep7q_wait_producer_layout(&s,0x1000,&in,0x602aca80,&args)&&args.scope==0x1070&&args.timeout==-1);
        }
        --s.extent;assert(!ep7q_wait_producer_layout(&s,0x1000,&in,0x602aca80,&args));++s.extent;
        put32(wait_stack+112,2);assert(!ep7q_wait_producer_layout(&s,0x1000,&in,0x602aca80,&args));
        put32(wait_stack+80,0x602ac5ef);put32(wait_stack+88,0x602aca81);
        assert(!ep7q_wait_pop_layout(&s,0x1038,0x602aca80,&scoped));
        expect_fault(try_pop,0xe0a);break;
    }
    case 44: /* Permanent closure clears a previous rejected pop's owned scope. */
        seal(0);enqueue(0);enqueue(0);pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_AVAILABLE);
        wrong_task=4;assert(!copy(0,&out));wrong_task=0;pop_one(0);
        assert(wait_output()->state==EP7Q_SCOPE_EMPTY);break;
    case 45: {
        ep7p_snapshot frozen;edit(5);seal(0);assert(copy(0,&frozen));enqueue(0);
        uint64_t generation=ep7_controller_sidecar_unresolved.generation;
        uint64_t serial=ep7_controller_sidecar_unresolved.serial;
        ep7cn_engine_epoch();assert(ep7_controller_sidecar_unresolved.generation==generation+1);
        assert(ep7_controller_sidecar_unresolved.serial==serial&&!copy(0,&out));
        pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_EMPTY&&frozen.hl[0]==5);
        edit(-4);seal(0);assert(copy(0,&out)&&out.hl[0]==-4);
        assert(ep7_controller_sidecar_unresolved.serial>serial);break;
    }
    case 46: { /* Table restoration cannot resurrect an observed invalid epoch. */
        const uint32_t fields[]={0x6223d134,0x6223d16c,0x6223d0d8};
        for(unsigned i=0;i<3;i++) {
            seal(0);enqueue(0);uint32_t *field=(uint32_t *)(uintptr_t)fields[i],old=*field;
            *field=0;assert(!copy(0,&out));*field=old;assert(!copy(0,&out));
            pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_EMPTY);
        }
        seal(0);assert(copy(0,&out));break;
    }
    case 47:
        ep7cn_fresh(addr(nodes[0]));lookup_callback=try_engine;expect_fault(population,0xe05);break;
    case 48:
        seal(0);wrong_task=4;expect_fault(try_engine,0xe03);break;
    case 49:
        seal(0);enqueue(0);ep7r_stop(&runtime);ep7cn_engine_epoch();
        assert(!ep7c_resolve_live(&ep7_controller_sidecar_unresolved,33,addr(nodes[0]),&token));
        pop_one(0);assert(wait_output()->state==EP7Q_SCOPE_EMPTY);break;
    default:assert(!"unknown case");
    }
}
int main(void)
{
    /* Each fork is a fresh simulated boot; production state exposes no reset. */
    for (unsigned i=0;i<50;i++) {
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
