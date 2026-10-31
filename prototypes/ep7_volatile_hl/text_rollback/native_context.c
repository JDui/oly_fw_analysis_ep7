#include "native_context.h"
#include "../runtime/task_context.h"

struct rollback_context {
    int (*qualify)(void *,const void *,size_t);
    void *caller,*service;
    ep7n_task owner;
};
static uint32_t read32(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static int gui_task(ep7n_task *t)
{
    return ep7n_native_current_task((uint32_t)(uintptr_t)t,t)&&
        t->domain==0&&t->entry==UINT32_C(0x60dd5067);
}
static int qualify(void *opaque,const void *object,size_t extent)
{
    struct rollback_context *c=opaque;
    const uint8_t *service;
    if (!gui_task(&c->owner)||c->qualify(c->caller,object,extent)!=1) return 0;
    /* Live service storage comes from the admitted GUI operation, not from the
     * table comparison. Do not use this as an arbitrary pointer validator. */
    service=ep7_gcc_ui_service();
    if (!service||read32(service)!=UINT32_C(0x60faaab4)||
        service[4]!=1||service[5]!=1) return 0;
    c->service=(void *)service;
    return 1;
}
static int enter(void *opaque,uint8_t first,uint8_t second,uintptr_t *prior)
{
    struct rollback_context *c=opaque;
    ep7n_task now;
    if (!gui_task(&now)||now.tid!=c->owner.tid||now.tcb!=c->owner.tcb||
        now.stack_low!=c->owner.stack_low||now.stack_bytes!=c->owner.stack_bytes||
        ep7_gcc_ui_service()!=c->service) return 0;
    *prior=ep7_gcc_ui_context_exchange(c->service,
        (uint16_t)((uint16_t)first|((uint16_t)second<<8)));
    return 1;
}
static void restore(void *opaque,uintptr_t prior)
{
    struct rollback_context *c=opaque;
    /* Same pinned live service; no new admission or potentially failing query
     * after object destruction. Nothing in this function reads the child. */
    ep7_gcc_ui_context_select(c->service,(uint16_t)prior);
}
int ep7_text_rollback_native(void *object,
    int (*admit)(void *,const void *,size_t),void *caller)
{
    struct rollback_context c={0};
    const struct ep7_text_rollback_ops ops={&c,qualify,enter,restore};
    if (!admit) return 0;
    c.qualify=admit;c.caller=caller;
    return ep7_text_rollback(object,&ops);
}
