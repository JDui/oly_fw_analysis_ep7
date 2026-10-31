#include "owner.h"
#include "../text_rollback/native_context.h"
#include "../text_viewer/text.h"
#include "../ui_render/viewer.h"
#include <stddef.h>

struct ep7u_owner ep7_native_ui_owner;
extern _Noreturn void ep7_gcc_quarantine(unsigned reason);
#if UINTPTR_MAX==UINT32_MAX
_Static_assert(sizeof(struct ep7u_screen_call)==16,"screen bridge input extent");
_Static_assert(offsetof(struct ep7u_screen_call,admitted)==12,"screen bridge token");
#endif

static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static uint16_t half(const uint8_t *p)
{ return (uint16_t)(p[0]|((uint16_t)p[1]<<8)); }
static int same_task(const ep7n_task *a,const ep7n_task *b)
{
    return a->tid==b->tid&&a->domain==b->domain&&a->tcb==b->tcb&&a->entry==b->entry&&
        a->stack_low==b->stack_low&&a->stack_bytes==b->stack_bytes;
}
static int gui(ep7n_task *t)
{
    return ep7n_native_current_task((uint32_t)(uintptr_t)t,t)&&
        t->domain==0&&t->entry==UINT32_C(0x60dd5067);
}
static _Noreturn void inconsistent(unsigned reason)
{ ep7_gcc_quarantine(0x700u+reason); }
static void require_live_call(struct ep7u_owner *s)
{
    ep7n_task t;
    if (!gui(&t)||!same_task(&s->task,&t)) inconsistent(1);
    if (!ep7u_native_cohort_present()) inconsistent(2);
    if (ep7_gcc_ui_service()!=s->service) inconsistent(3);
}
static void suspend(struct ep7u_owner *s)
{
    ep7v_invalidate();
    s->active=0;
    if (s->generation==UINT32_MAX) s->stopped=1;
    else s->generation++;
}
static int service_shape(const uint8_t *p)
{
    return p&&word(p)==UINT32_C(0x60faaab4)&&half(p+4)==0x0101&&
        half(p+80)==2&&half(p+82)<2;
}
static void *current_owner(const uint8_t *service)
{ return (void *)(uintptr_t)word(service+416); }

void ep7u_screen_enter(struct ep7u_screen_call *call)
{
    struct ep7u_owner *s=&ep7_native_ui_owner;
    ep7n_task t;
    call->admitted=0;
    int started=atomic_load_explicit(&s->started,memory_order_acquire);
    if (!ep7u_native_cohort_present()||!gui(&t)) {
        if (started) inconsistent(4);
        return;
    }
    /* Only after actual native service identity is established. The original
     * method's live service argument supplies extent/lifetime in this scope. */
    if (ep7_gcc_ui_service()!=call->service||!service_shape(call->service)) {
        if (started) inconsistent(5);
        return;
    }
    if (started) {
        if (!same_task(&s->task,&t)||s->service!=call->service) inconsistent(6);
    } else {
        s->task=t;s->service=call->service;
        atomic_store_explicit(&s->started,true,memory_order_release);
    }
    if (s->opening||s->text.busy||s->depth==UINT32_MAX) inconsistent(7);
    suspend(s);
    call->admitted=++s->depth;
}

static int qualify(void *context,const void *owner,size_t bytes,const void *resource,size_t n)
{
    struct ep7u_owner *s=context;
    ep7n_task t;
    if (!s->opening||s->depth||s->stopped||s->owner!=owner||bytes!=1360||
        resource!=s->resource.descriptor||n!=94||!gui(&t)||!same_task(&s->task,&t)||
        !ep7u_native_cohort_present()||ep7_gcc_ui_service()!=s->service) return 0;
    const uint8_t *service=s->service;
    /* owner was obtained only from the completed request278 publication chain,
     * not by a vtable scan or an unqualified external pointer lookup. */
    return service_shape(service)&&service[2032]==0&&current_owner(service)==owner;
}

void ep7u_screen_leave(struct ep7u_screen_call *call)
{
    struct ep7u_owner *s=&ep7_native_ui_owner;
    if (!call->admitted) return;
    require_live_call(s);
    if (call->service!=s->service||call->admitted!=s->depth) inconsistent(8);
    --s->depth;
    if (s->depth) return; /* Inner busy rejection cannot publish an outer owner. */
    const uint8_t *service=s->service;
    if (!service_shape(service)||service[2032]) return;
    if (call->result!=1) {
        /* Native failed before replacement: retain the parent-owned text; only
         * this new generation can become eligible again. No fresh pointer bind. */
        if (!s->stopped&&s->display_ready&&call->result==0&&s->owner&&current_owner(service)==s->owner&&
            s->text.attached.child&&s->text.attached.bound) { s->active=1;ep7v_refresh(); }
        return;
    }
    if (s->text.fresh.child&&!s->owner) (void)ep7_text_native_retry_rollback(&s->text);
    if (s->stopped||call->request!=278||s->owner||s->text.fresh.child||
        s->text.attached.child) return; /* Never evict an outstanding owner. */
    uint8_t *owner=current_owner(service);
    if (!owner) return;
    /* The source call allocated1360, constructed and bound this exact owner.
     * Header checks reject unsupported final state; they do not prove a lease. */
    if (word(owner)!=UINT32_C(0x61032f10)||half(owner+4)!=0x6111||half(owner+6)!=0x0112||
        word(owner+20)!=(uint32_t)(uintptr_t)service||owner[28]!=6||owner[29]>1||
        service[1378+owner[29]]!=1||word(owner+92)!=UINT32_C(0x60f94aa0)) return;
    s->owner=owner;
    ep7_text_resource_prepare(&s->resource);
    const uint16_t empty[EP7_TEXT_UNITS]={0};
    s->opening=1;
    int result=ep7_text_native_open(&s->text,owner,s->resource.descriptor,empty,qualify,s);
    s->opening=0;
    s->display_ready=s->active=result==EP7_TEXT_ATTACHED_READY;
    ep7v_refresh(); /* Request278 may complete after the MVC draw/entry returned. */
    /* Failed and retained creation stays associated until native retirement.
     * No retry allocates a duplicate child under the same owner. */
}

void ep7u_before_retire(void *owner,unsigned stage)
{
    struct ep7u_owner *s=&ep7_native_ui_owner;
    if (!atomic_load_explicit(&s->started,memory_order_acquire)) return;
    require_live_call(s);
    if (s->owner!=owner) return;
    if (s->opening||s->text.busy) inconsistent(9);
    /* A bare owner destructor frees list nodes, not children. If no cleanup
     * boundary revoked our attached child, do not silently lose that ownership. */
    if (stage<EP7U_CLEANUP||stage>EP7U_DESTRUCTOR||
        (stage==EP7U_DESTRUCTOR&&s->text.attached.child)) inconsistent(11);
    suspend(s);
    s->display_ready=0;
    if (s->text.fresh.child) (void)ep7_text_native_retry_rollback(&s->text);
    if (!s->text.fresh.child) {
        if (!ep7_text_native_revoke(&s->text)) inconsistent(10);
    }
    /* A rejected fresh rollback has no parent membership. Keep its full record
     * and permanent resource storage even when this native owner is freed. */
    s->owner=NULL;
}
int ep7u_hold_ready(uint32_t generation)
{
    struct ep7u_owner *s=&ep7_native_ui_owner;
    if (!atomic_load_explicit(&s->started,memory_order_acquire)) return 0;
    require_live_call(s);
    if (!generation||s->generation!=generation||s->stopped||s->depth||s->opening||s->text.busy||!s->active||!s->display_ready||
        !s->owner||!s->text.attached.child||!s->text.attached.bound) return 0;
    const uint8_t *service=s->service,*owner=s->owner;
    if (!service_shape(service)||service[2032]||current_owner(service)!=owner) {
        s->active=s->display_ready=0;return 0; /* No substituted owner dereference. */
    }
    if (word(owner)!=UINT32_C(0x61032f10)||half(owner+4)!=0x6111||half(owner+6)!=0x0112||
        word(owner+20)!=(uint32_t)(uintptr_t)service||owner[28]!=6||owner[29]>1||
        service[1378+owner[29]]!=1||word(owner+92)!=UINT32_C(0x60f94aa0)||
        s->text.owner!=owner||s->text.attached.owner!=owner) {
        s->active=s->display_ready=0;return 0;
    }
    s->text.busy=1;
    const uint8_t *child=s->text.attached.child;
    if (ep7_gcc_ui_find_child((void *)owner,EP7_HL_TEXT_WIDGET_ID)==child&&
        word(child)==UINT32_C(0x60faec7c)&&half(child+4)==0x8010&&
        half(child+6)==EP7_HL_TEXT_WIDGET_ID&&word(child+20)==(uint32_t)(uintptr_t)owner&&
        half(child+28)==half(owner+28)) return 1;
    s->text.busy=0;s->active=s->display_ready=0;return 0;
}
void ep7u_release_ready(uint32_t generation)
{
    struct ep7u_owner *s=&ep7_native_ui_owner;
    require_live_call(s);
    if (!s->text.busy||s->generation!=generation||current_owner(s->service)!=s->owner) inconsistent(12);
    s->text.busy=0;
}
int ep7u_present(const uint16_t *text,uint32_t *generation)
{
    struct ep7u_owner *s=&ep7_native_ui_owner;size_t n;
    if (!text) return 0;
    for (n=0;n<EP7_TEXT_UNITS&&text[n];n++) {}
    if (n==EP7_TEXT_UNITS||!ep7u_hold_ready(s->generation)) return 0;
    uint32_t held=s->generation;
    uint16_t prior=ep7_gcc_ui_context_exchange(s->service,half((const uint8_t *)s->owner+28));
    int result=ep7_gcc_set_text_unresolved_binding(s->text.attached.child,text);
    ep7_gcc_ui_context_select(s->service,prior);
    ep7u_release_ready(held);
    if (result!=1) { s->active=s->display_ready=0;return 0; }
    if (generation) *generation=s->generation;
    return 1;
}
