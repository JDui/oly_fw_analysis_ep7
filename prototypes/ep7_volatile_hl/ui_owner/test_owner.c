#include "owner.h"
#include "../text_rollback/native_context.h"
#include "../text_viewer/text.h"
#include <assert.h>
#include <setjmp.h>
#include <string.h>

volatile uint32_t ep7_stock_ui_service_vtable_unresolved[197];
volatile uint32_t ep7_stock_ui_display_vtable_unresolved[109];
const unsigned char ep7_native_ui_screen_bridge[1]={1};
const unsigned char ep7_native_ui_owner_cleanup_bridge[1]={2};
const unsigned char ep7_native_ui_owner_bulk_bridge[1]={3};
const unsigned char ep7_native_ui_owner_destructor_bridge[1]={4};
static uint8_t service[2880],owners[2][1360],children[2][180];
static struct {
    unsigned queries,fail_query,creates,fresh_frees,parent_frees,sets,quarantines;
    unsigned member[2],allocated[2],partial,reject_set,reenter_set,domain,task_changed;
    void *child_owner[2];
    jmp_buf fatal;
} f;
static void put16(uint8_t *p,uint16_t n) { p[0]=(uint8_t)n;p[1]=(uint8_t)(n>>8); }
static void put32(uint8_t *p,uint32_t n)
{ for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(n>>(8*i)); }
static void pointer(uint8_t *p,const void *v)
{ assert((uintptr_t)v<=UINT32_MAX);put32(p,(uint32_t)(uintptr_t)v); }
bool ep7n_native_current_task(uint32_t anchor,ep7n_task *task)
{
    (void)anchor;f.queries++;
    *task=(ep7n_task){0x101,(uint16_t)f.domain,0x1000+f.task_changed,0x60dd5067,0x2000,16384};
    return f.queries!=f.fail_query;
}
void *ep7_gcc_ui_service(void) { return service; }
uint16_t ep7_gcc_ui_context_exchange(void *p,uint16_t value)
{
    assert(p==service);uint16_t prior=(uint16_t)(service[28]|((uint16_t)service[29]<<8));
    put16(service+28,value);return prior;
}
void ep7_gcc_ui_context_select(void *p,uint16_t value)
{ (void)ep7_gcc_ui_context_exchange(p,value); }
_Noreturn void ep7_gcc_quarantine(unsigned reason)
{ assert(reason>=0x701&&reason<=0x70b);f.quarantines++;longjmp(f.fatal,1); }
/* Resource construction is the separately target-checked native32 primitive.
 * Host test supplies its owned descriptor result, not its target execution. */
void ep7_text_resource_prepare(struct ep7_text_resource *r)
{
    assert(!ep7_native_ui_owner.text.fresh.child&&!ep7_native_ui_owner.text.attached.child);
    memset(r,0,sizeof *r);put16(r->descriptor,0x8010);put16(r->descriptor+2,EP7_HL_TEXT_WIDGET_ID);
    pointer(r->descriptor+4,r->layouts);put32(r->descriptor+12,0x61030a5c);
    r->descriptor[8]=9;r->descriptor[48]=1;
}
void *ep7_gcc_ui_find_child(void *o,uint16_t id)
{
    assert(id==EP7_HL_TEXT_WIDGET_ID);
    for (unsigned i=0;i<2;i++) if (f.member[i]&&f.child_owner[i]==o) return children[i];
    return NULL;
}
void ep7_gcc_text_factory(void *o,const void *r,struct ep7_text_factory_result *out)
{
    unsigned i=f.creates++%2;
    assert(!f.allocated[i]&&r==ep7_native_ui_owner.resource.descriptor);
    assert(ep7_native_ui_owner.opening&&service[28]==6&&service[29]==((uint8_t *)o)[29]);
    memset(children[i],0,180);put32(children[i],0x60faec7c);put16(children[i]+4,0x8010);
    children[i][28]=6;children[i][29]=service[29];f.allocated[i]=1;f.child_owner[i]=o;
    *out=(struct ep7_text_factory_result){children[i],f.partial?0:1};
    if (f.partial) f.fail_query=f.queries+1; /* First rollback qualification fails. */
}
static unsigned child_index(void *p)
{ assert(p==children[0]||p==children[1]);return p==children[0]?0u:1u; }
int ep7_gcc_ui_attach(void *o,void *child)
{
    unsigned i=child_index(child);assert(f.allocated[i]&&!f.member[i]&&f.child_owner[i]==o);
    f.member[i]=1;return 1;
}
int ep7_gcc_text_bind(void *child,void *o)
{ assert(f.member[child_index(child)]);pointer((uint8_t *)child+20,o);return -1; }
int ep7_gcc_set_text_unresolved_binding(void *child,const uint16_t *text)
{
    assert(f.member[child_index(child)]&&text[0]==0);f.sets++;
    if (f.reenter_set) {
        struct ep7u_screen_call nested={service,278,0,0};ep7u_screen_enter(&nested);
        assert(!"screen replacement must not continue inside text creation");
    }
    return !f.reject_set;
}
void ep7_gcc_text_cleanup_destroy_unresolved(void *child)
{
    unsigned i=child_index(child);assert(f.allocated[i]&&!f.member[i]);
    assert(service[28]==6&&service[29]==children[i][29]);
    f.allocated[i]=0;f.fresh_frees++;memset(child,0xa5,180);
}
static void reset(void)
{
    memset(&f,0,sizeof f);memset(&ep7_native_ui_owner,0,sizeof ep7_native_ui_owner);
    atomic_init(&ep7_native_ui_owner.started,false);
    memset(service,0,sizeof service);memset(owners,0,sizeof owners);memset(children,0,sizeof children);
    put32(service,0x60faaab4);put16(service+4,0x0101);put16(service+80,2);
    service[28]=0x81;service[29]=0xfe;
    ep7_stock_ui_service_vtable_unresolved[784/4]=(uint32_t)(uintptr_t)ep7_native_ui_screen_bridge;
    ep7_stock_ui_display_vtable_unresolved[152/4]=(uint32_t)(uintptr_t)ep7_native_ui_owner_cleanup_bridge;
    ep7_stock_ui_display_vtable_unresolved[432/4]=(uint32_t)(uintptr_t)ep7_native_ui_owner_bulk_bridge;
    ep7_stock_ui_display_vtable_unresolved[0]=(uint32_t)(uintptr_t)ep7_native_ui_owner_destructor_bridge;
    assert(ep7u_native_cohort_present());
}
static void publish_owner(unsigned i)
{
    memset(owners[i],0,sizeof owners[i]);put32(owners[i],0x61032f10);
    put16(owners[i]+4,0x6111);put16(owners[i]+6,0x0112);pointer(owners[i]+20,service);
    owners[i][28]=6;owners[i][29]=(uint8_t)i;put32(owners[i]+92,0x60f94aa0);
    service[1378+i]=1;pointer(service+416,owners[i]);service[2032]=0;
}
static struct ep7u_screen_call enter(uint32_t request)
{
    struct ep7u_screen_call call={service,request,0,0};ep7u_screen_enter(&call);
    assert(call.admitted&&!ep7_native_ui_owner.active);return call;
}
static void create(unsigned i)
{
    struct ep7u_screen_call call=enter(278);publish_owner(i);call.result=1;ep7u_screen_leave(&call);
    assert(service[28]==0x81&&service[29]==0xfe);
}
static void retire(unsigned i,unsigned stage)
{
    ep7u_before_retire(owners[i],stage);
    for (unsigned j=0;j<2;j++) if (f.member[j]&&f.child_owner[j]==owners[i]) {
        assert(!ep7_native_ui_owner.text.attached.child);f.member[j]=0;f.allocated[j]=0;
        f.parent_frees++;memset(children[j],0xa5,180);
    }
    memset(owners[i],0xcc,sizeof owners[i]);
}

int main(void)
{
    struct ep7u_owner *s=&ep7_native_ui_owner;
    /* 1. Incomplete cohort: no task/owner/service reads, even invalid arguments. */
    reset();ep7_stock_ui_display_vtable_unresolved[432/4]=0;
    struct ep7u_screen_call invalid={(void *)(uintptr_t)1,278,1,0};
    ep7u_screen_enter(&invalid);ep7u_screen_leave(&invalid);ep7u_before_retire((void *)1,EP7U_BULK);
    assert(!invalid.admitted&&!f.queries&&!f.creates&&!atomic_load(&s->started));
    /* 2. Create; failed screen replacement resumes ownership under a NEW generation. */
    reset();create(0);assert(s->active&&s->owner==owners[0]&&f.creates==1);
    uint32_t generation=s->generation;void *child=s->text.attached.child;
    struct ep7u_screen_call failed=enter(9);ep7u_screen_leave(&failed);
    assert(s->active&&s->generation>generation&&s->text.attached.child==child&&f.creates==1);
    /* 3. Matched cleanup before old storage reuse; unrelated retirement cannot clear new owner. */
    struct ep7u_screen_call replace=enter(278);publish_owner(1);retire(0,EP7U_CLEANUP);
    assert(!s->owner&&!s->text.attached.child&&f.parent_frees==1);
    replace.result=1;ep7u_screen_leave(&replace);assert(s->active&&s->owner==owners[1]&&f.creates==2);
    ep7u_before_retire(owners[0],EP7U_DESTRUCTOR);assert(s->active&&s->owner==owners[1]);
    generation=s->generation;replace=enter(278);retire(1,EP7U_BULK);publish_owner(1);
    replace.result=1;ep7u_screen_leave(&replace);assert(s->active&&s->generation>generation&&f.creates==3);
    /* 4. Initial display failure is not promoted by a later failed screen switch. */
    reset();f.reject_set=1;create(0);assert(!s->active&&!s->display_ready&&s->text.attached.bound);
    failed=enter(4);ep7u_screen_leave(&failed);assert(!s->active&&f.creates==1);
    retire(0,EP7U_BULK);assert(!s->owner&&!s->text.attached.child&&f.parent_frees==1);
    /* 5. Fresh rollback can remain pending beyond owner retirement, then recover. */
    reset();f.partial=1;create(0);assert(s->text.fresh.child&&!s->active&&!f.fresh_frees);
    replace=enter(278);publish_owner(1);f.fail_query=f.queries+2;retire(0,EP7U_CLEANUP);
    assert(!s->owner&&s->text.fresh.child&&!f.fresh_frees&&!f.parent_frees);
    f.partial=0;replace.result=1;ep7u_screen_leave(&replace);
    assert(s->active&&s->owner==owners[1]&&!s->text.fresh.child&&f.fresh_frees==1&&f.creates==2);
    /* 6. Nested native busy rejection cannot publish an outer transition. */
    reset();create(0);struct ep7u_screen_call outer=enter(278);service[2032]=1;
    struct ep7u_screen_call inner=enter(278);ep7u_screen_leave(&inner);
    assert(!s->active&&s->depth==1&&f.creates==1);service[2032]=0;ep7u_screen_leave(&outer);
    assert(s->active&&!s->depth&&f.creates==1);
    /* 7. Full-manager success still rejects unsupported owner header/parent state. */
    reset();replace=enter(278);publish_owner(0);owners[0][6]++;
    replace.result=1;ep7u_screen_leave(&replace);assert(!s->owner&&!f.creates);
    /* 8. Bare destructor with an owned child must not lose it without cleanup. */
    reset();create(0);
    if (!setjmp(f.fatal)) { ep7u_before_retire(owners[0],EP7U_DESTRUCTOR);assert(!"bare destructor returned"); }
    assert(f.quarantines==1&&s->text.attached.child&&f.allocated[0]&&!f.parent_frees);
    /* 9. Wrong task and changed cohort stop BEFORE native destruction. */
    reset();create(0);f.domain=1;
    if (!setjmp(f.fatal)) { ep7u_before_retire(owners[0],EP7U_CLEANUP);assert(!"wrong task returned"); }
    assert(f.quarantines==1&&s->text.attached.child&&!f.parent_frees);
    f.domain=0;ep7_stock_ui_service_vtable_unresolved[784/4]=0;
    if (!setjmp(f.fatal)) { ep7u_before_retire(owners[0],EP7U_BULK);assert(!"lost cohort returned"); }
    assert(f.quarantines==2&&s->text.attached.child&&!f.parent_frees);
    /* 10. Reentrant screen change during text setup cannot free its owner. */
    reset();f.reenter_set=1;
    if (!setjmp(f.fatal)) { create(0);assert(!"reentrant replacement returned"); }
    assert(f.quarantines==1&&s->opening&&s->text.busy&&f.member[0]&&!f.parent_frees);
    /* 11. Generation exhaustion is sticky; cleanup responsibilities remain. */
    reset();create(0);s->generation=UINT32_MAX;failed=enter(9);ep7u_screen_leave(&failed);
    assert(s->stopped&&!s->active&&s->generation==UINT32_MAX);retire(0,EP7U_CLEANUP);
    create(1);assert(!s->active&&!s->owner&&f.creates==1&&f.parent_frees==1);
    /* 12. Reused task identity is rejected even when its entry remains GUI. */
    reset();create(0);f.task_changed=4;
    if (!setjmp(f.fatal)) { failed=enter(9);assert(!"changed TCB returned"); }
    assert(f.quarantines==1&&s->owner==owners[0]&&f.creates==1);
    return 0;
}
