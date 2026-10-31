#include "lifetime.h"
#include "../ui_selector/selector.h"
#include "../ui_model/model.h"
#include "../ui_render/viewer.h"
#include <stddef.h>

struct ep7m_lifetime ep7_native_mvc;
extern volatile uint32_t ep7_stock_color_container_unresolved;
extern _Noreturn void ep7_gcc_quarantine(unsigned reason);
static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static uint16_t half(const uint8_t *p)
{ return (uint16_t)(p[0]|((uint16_t)p[1]<<8)); }
static void *pointer(const uint8_t *p) { return (void *)(uintptr_t)word(p); }
static int same_task(const ep7n_task *a,const ep7n_task *b)
{
    return a->tid==b->tid&&a->domain==b->domain&&a->tcb==b->tcb&&a->entry==b->entry&&
        a->stack_low==b->stack_low&&a->stack_bytes==b->stack_bytes;
}
static int gui(ep7n_task *t)
{
    return ep7n_native_current_task((uint32_t)(uintptr_t)t,t)&&t->domain==0&&
        t->entry==UINT32_C(0x60dd5067);
}
static _Noreturn void inconsistent(unsigned reason) { ep7_gcc_quarantine(0x800u+reason); }
static void require_live(struct ep7m_lifetime *s)
{
    ep7n_task t;
    if (!gui(&t)||!same_task(&t,&s->task)) inconsistent(1);
    if (!ep7m_native_cohort_present()) inconsistent(2);
}
static void forget(struct ep7m_lifetime *s)
{
    /* Keep old graph identity and block matching reentry through text callbacks
     * until its label is cleared; then drop the graph before original free. */
    s->busy=1;ep7cm_revoke();ep7v_clear();
    s->container=NULL;s->parent=NULL;s->viewer=NULL;s->selector=NULL;s->masks=NULL;
    s->selector_count=0;s->invalidated=0;
    s->content=NULL;s->category=0;s->busy=0;
    /* generation and pinned task never reset; address reuse is a new capture. */
}
static int selector_shape(const uint8_t *p)
{
    unsigned n=half(p+84);
    uint32_t values=word(p+92);
    return word(p)==UINT32_C(0x6114f7e4)&&word(p+80)==193&&word(p+88)&&
        ((n==4&&values==UINT32_C(0x6114e050))||
         (n==6&&values==(uint32_t)(uintptr_t)ep7s_categories))&&half(p+86)<n;
}

void ep7m_gui_begin(void)
{
    struct ep7m_lifetime *s=&ep7_native_mvc;
    ep7n_task t;int started=atomic_load_explicit(&s->started,memory_order_acquire);
    if (!ep7m_native_cohort_present()||!gui(&t)) {
        if (started) inconsistent(3);
        return;
    }
    if (started&&!same_task(&t,&s->task)) inconsistent(1);
    if (s->constructing||s->container||s->busy) inconsistent(4); /* Before original allocation. */
    if (!started) {
        s->task=t;atomic_store_explicit(&s->started,true,memory_order_release);
    }
    s->constructing=1;
}
void ep7m_gui_complete(void *original_result)
{
    struct ep7m_lifetime *s=&ep7_native_mvc;
    if (!atomic_load_explicit(&s->started,memory_order_acquire)) return;
    require_live(s);
    if (!s->constructing) return;
    s->constructing=0;
    if (s->stopped||!original_result||
        ep7_stock_color_container_unresolved!=(uint32_t)(uintptr_t)original_result) return;
    uint8_t *container=original_result;
    /* Only from the just-completed GUI041d group8/key463 creation chain:
     * container228 -> parent100/selector124 and viewer408. Not pointer discovery. */
    if (word(container+8)!=0x34||word(container+12)!=0x84) return;
    uint8_t *parent=pointer(container),*viewer=pointer(container+4);
    if (!parent||!viewer||word(parent)!=UINT32_C(0x6118957c)||
        word(viewer)!=UINT32_C(0x61189ba8)||pointer(viewer+384)!=parent) return;
    uint8_t *selector=pointer(parent+76);
    if (!selector||!selector_shape(selector)) return;
    if (s->generation==UINT32_MAX) { s->stopped=1;return; }
    ++s->generation;s->container=container;s->parent=parent;s->viewer=viewer;
    s->selector=selector;s->masks=pointer(selector+88);s->selector_count=half(selector+84);
    s->content=pointer(parent+80);s->category=half(selector+86);
    ep7v_refresh();
}
void ep7m_before_gui_exit(void)
{
    struct ep7m_lifetime *s=&ep7_native_mvc;
    if (!atomic_load_explicit(&s->started,memory_order_acquire)) return;
    require_live(s);
    if (s->constructing||s->busy) inconsistent(5);
    if (s->container&&ep7_stock_color_container_unresolved!=(uint32_t)(uintptr_t)s->container)
        inconsistent(6);
    forget(s); /* Before parent, viewer, argument block or container can be freed. */
}
static void retire(void *object,int is_viewer)
{
    struct ep7m_lifetime *s=&ep7_native_mvc;
    if (!atomic_load_explicit(&s->started,memory_order_acquire)) return;
    require_live(s);
    if (!object||(is_viewer?s->viewer:s->parent)!=object) return;
    if (s->constructing||s->busy) inconsistent(7);
    forget(s);
}
void ep7m_before_parent_destroy(void *p) { retire(p,0); }
void ep7m_before_viewer_destroy(void *p) { retire(p,1); }
const struct ep7m_lifetime *ep7m_current(void)
{
    struct ep7m_lifetime *s=&ep7_native_mvc;
    if (!atomic_load_explicit(&s->started,memory_order_acquire)) return NULL;
    require_live(s);
    if (s->constructing||s->stopped||s->invalidated||!s->container) return NULL;
    if (ep7_stock_color_container_unresolved!=(uint32_t)(uintptr_t)s->container) {
        s->invalidated=1;return NULL;
    }
    const uint8_t *p=s->parent,*v=s->viewer,*list=s->selector,*c=s->container;
    if (pointer(c)!=p||pointer(c+4)!=v||word(c+8)!=0x34||word(c+12)!=0x84||
        word(p)!=UINT32_C(0x6118957c)||word(v)!=UINT32_C(0x61189ba8)||
        pointer(v+384)!=p||pointer(p+76)!=list||pointer(p+80)!=s->content) {
        s->invalidated=1;return NULL;
    }
    if (!selector_shape(list)||half(list+84)!=s->selector_count||pointer(list+88)!=s->masks) {
        s->invalidated=1;return NULL; /* Never follow a substituted mask array. */
    }
    return s;
}
void ep7m_require_context(void)
{
    struct ep7m_lifetime *s=&ep7_native_mvc;
    if (!atomic_load_explicit(&s->started,memory_order_acquire)) inconsistent(8);
    require_live(s);
}
struct ep7m_lifetime *ep7m_hold_content(void *parent)
{
    const struct ep7m_lifetime *view=ep7m_current();
    struct ep7m_lifetime *s=&ep7_native_mvc;
    if (!view||view->parent!=parent) {
        if (atomic_load_explicit(&s->started,memory_order_acquire)&&s->parent==parent&&parent)
            inconsistent(9); /* Never delegate an invalidated owned graph. */
        return NULL;
    }
    if (s->busy) inconsistent(10);
    s->busy=1;ep7v_invalidate();return s;
}
void ep7m_release_content(struct ep7m_lifetime *s)
{
    if (s!=&ep7_native_mvc||!s->busy||ep7m_current()!=s||
        half((const uint8_t *)s->selector+86)!=s->category) inconsistent(11);
    s->busy=0;
}
