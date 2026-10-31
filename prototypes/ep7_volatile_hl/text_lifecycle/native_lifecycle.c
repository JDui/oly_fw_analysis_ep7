#include "native_lifecycle.h"
#include "../text_rollback/native_context.h"
#include "../text_viewer/text.h"
#include "../runtime/task_context.h"

static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static uint16_t half(const uint8_t *p)
{ return (uint16_t)(p[0]|((uint16_t)p[1]<<8)); }
static int gui(void)
{
    ep7n_task task;
    return ep7n_native_current_task((uint32_t)(uintptr_t)&task,&task)&&
        task.domain==0&&task.entry==UINT32_C(0x60dd5067);
}
static int fresh(void *opaque,const void *child,size_t bytes)
{
    const struct ep7_text_native *s=opaque;
    return s->busy&&bytes==180&&s->fresh.child==child&&!s->attached.child;
}
static void *create(void *opaque,void *owner,const void *resource)
{
    struct ep7_text_native *s=opaque;
    ep7_gcc_text_factory(owner,resource,&s->fresh);
    if (!s->fresh.child) s->fresh.initialized=0;
    return s->fresh.child;
}
static int initialized(void *opaque,void *child)
{
    const struct ep7_text_native *s=opaque;
    return s->fresh.child==child&&s->fresh.initialized==1;
}
static void destroy(void *opaque,void *child)
{
    struct ep7_text_native *s=opaque;
    if (ep7_text_rollback_native(child,fresh,s)==1)
        s->fresh=(struct ep7_text_factory_result){0};
    /* Rejection retains the original allocation and its provenance. */
}
static int attach(void *opaque,void *owner,void *child)
{
    struct ep7_text_native *s=opaque;
    int transferred=ep7_gcc_ui_attach(owner,child);
    if (transferred==1) s->fresh=(struct ep7_text_factory_result){0};
    return transferred;
}
static int bind(void *opaque,void *child,void *owner)
{
    (void)opaque;
    int event_status=ep7_gcc_text_bind(child,owner);
    /* Exact owner61032f10 handles event6144 with its default -1. The parent
     * pointer was already written; this is not a normalized success boolean. */
    return event_status==-1&&word((const uint8_t *)child+20)==(uint32_t)(uintptr_t)owner;
}
static int set(void *opaque,void *child,const uint16_t *text)
{ (void)opaque;return ep7_gcc_set_text_unresolved_binding(child,text); }

int ep7_text_native_open(struct ep7_text_native *s,void *owner,const void *resource,
    const uint16_t *text,
    int (*qualify)(void *,const void *,size_t,const void *,size_t),void *context)
{
    const uint8_t *o=owner,*r=resource,*service;
    uint16_t prior;size_t units;int result;
    if (!s||!owner||!resource||!text||!qualify||s->busy||s->owner||s->fresh.child||
        s->attached.child||s->attached.owner||s->attached.bound) return EP7_TEXT_CREATE_REJECTED;
    for (units=0;units<EP7_TEXT_UNITS&&text[units];units++) {}
    if (units==EP7_TEXT_UNITS||!gui()||qualify(context,owner,1360,resource,94)!=1)
        return EP7_TEXT_CREATE_REJECTED;
    service=ep7_gcc_ui_service();
    if (!service||word(service)!=UINT32_C(0x60faaab4)||half(service+4)!=0x0101||
        half(service+80)!=2||half(service+82)>1||word(o)!=UINT32_C(0x61032f10)||
        half(r)!=0x8010||r[68]!=0||r[84]!=0) return EP7_TEXT_CREATE_REJECTED;
    const struct ep7_text_lifecycle_ops ops={s,create,initialized,destroy,attach,bind,set};
    s->busy=1;s->owner=owner;
    prior=ep7_gcc_ui_context_exchange((void *)service,half(o+28));
    result=ep7_text_create_attach(&s->attached,&ops,owner,resource,text,1);
    ep7_gcc_ui_context_select((void *)service,prior);
    s->busy=0;
    if (s->fresh.child) return EP7_TEXT_NATIVE_RETAINED;
    if (!s->attached.child) s->owner=NULL;
    return result;
}
int ep7_text_native_retry_rollback(struct ep7_text_native *s)
{
    if (!s||s->busy||s->attached.child||!s->fresh.child) return 0;
    s->busy=1;destroy(s,s->fresh.child);s->busy=0;
    if (s->fresh.child) return 0;
    s->owner=NULL;return 1;
}
int ep7_text_native_revoke(struct ep7_text_native *s)
{
    if (!s||s->busy||s->fresh.child) return 0;
    ep7_text_revoke(&s->attached);s->owner=NULL;return 1;
}
