#include "content.h"
#include "stock.h"
#include "../ui_gate/gate.h"
/* Reuse the actual MVC/cohort fixture and its six existing lifetime regressions. */
#define main mvc_lifetime_regressions
#include "../ui_mvc/test_lifetime.c"
#undef main

volatile uint16_t ep7_stock_selector_remembered_unresolved;
const unsigned char ep7_content_vtable[72]={0};
static struct ep7c_child allocation;
static uint8_t stock_content[240]; /* Largest reused native creator extent. */
static unsigned allocations,initializations,stock_calls,stock_frees,private_frees,fail_alloc,reenter;
static unsigned free_count_at_allocate;
static void *getpointer(const uint8_t *p)
{ uint32_t n=0;for (unsigned i=0;i<4;i++) n|=(uint32_t)p[i]<<(8*i);return (void *)(uintptr_t)n; }
void *ep7_gcc_mvc_scalar_new(uint32_t bytes)
{
    assert(bytes==sizeof allocation&&ep7_native_mvc.busy);allocations++;free_count_at_allocate=stock_frees;
    assert(getpointer(parent+80)==stock_content);
    if (reenter==1) ep7m_before_parent_destroy(parent);
    if (reenter==2) ep7m_before_viewer_destroy(viewer);
    if (reenter==3) ep7c_rebuild(parent);
    return fail_alloc?NULL:&allocation;
}
void ep7_gcc_mvc_base_init(void *p)
{
    assert(p==&allocation&&ep7_native_mvc.busy&&stock_frees==free_count_at_allocate);initializations++;
    for (unsigned i=0;i<sizeof allocation;i++) assert(((uint8_t *)p)[i]==0);
    /* Native leaf itself is checked against stock, not executed here. */
}
void ep7_gcc_mvc_dispose(void *p)
{
    if (p==stock_content) { assert(ep7_native_mvc.busy);stock_frees++; }
    else {
        assert(p==&allocation);ep7c_before_destroy(p);assert(!ep7_native_content.child);
        memset(p,0xcd,sizeof allocation);private_frees++;
    }
}
void ep7_gcc_mvc_stock_rebuild(void *p)
{
    stock_calls++;
    if (p!=parent) return; /* Native boundary fixture, no arbitrary pointer reads. */
    void *old=getpointer(parent+80);
    if (old) ep7_gcc_mvc_dispose(old);
    pointer(parent+80,stock_content); /* Original allocation success boundary. */
}
#ifndef EP7_UI_GATE_INTEGRATION
/* Earlier isolated checks retain their explicit gate/stock boundary fixtures.
 * ui_gate/check.py links the real gate and allocation-before-free adapter. */
unsigned ep7g_reconcile_held(struct ep7m_lifetime *m,uint32_t *mode)
{ assert(m->busy);*mode=54;return EP7G_AVAILABLE; }
int ep7g_before_event(void *p)
{ const struct ep7m_lifetime *m=ep7m_current();return m&&m->parent==p?(int)m->category:-1; }
void ep7c_stop_transition(struct ep7m_lifetime *m) { assert(m->busy); }
int ep7c_to_stock_held(struct ep7m_lifetime *m,unsigned category,uint32_t mode)
{
    (void)mode;ep7_gcc_mvc_stock_rebuild(m->parent);m->content=stock_content;m->category=category;return 1;
}
#endif
static void begin_case(void)
{
    reset();memset(&ep7_native_content,0,sizeof ep7_native_content);
    memset(&allocation,0,sizeof allocation);memset(masks,0,sizeof masks);
    allocations=initializations=stock_calls=stock_frees=private_frees=fail_alloc=reenter=0;
    ep7m_gui_begin();publish(6);pointer(parent+80,stock_content);
    put16(masks+8,1);put16(masks+10,1);ep7m_gui_complete(container);
    ep7_stock_selector_remembered_unresolved=2;
}
static void select_category(unsigned category)
{ put16(selector+86,(uint16_t)category);ep7_stock_selector_remembered_unresolved=(uint16_t)category; }
static void enable_fixture_hl(void)
{
    /* Models a later admitted renderer. Production code does not enable these
     * masks; host scenarios do not prove native COLOR/render/input admission. */
    put16(masks+8,0);put16(masks+10,0);
}
#ifndef EP7_CONTENT_TEST_MAIN
#define EP7_CONTENT_TEST_MAIN main
#endif
int EP7_CONTENT_TEST_MAIN(void)
{
    assert(!mvc_lifetime_regressions());
    /*1 Disabled category and malloc failure preserve exact old object+indices. */
    begin_case();select_category(4);ep7c_rebuild(parent);
    assert(!allocations&&!stock_calls&&!stock_frees&&getpointer(parent+80)==stock_content);
    assert(selector[86]==2&&ep7_stock_selector_remembered_unresolved==2&&!ep7_native_mvc.busy);
    enable_fixture_hl();fail_alloc=1;select_category(5);ep7c_rebuild(parent);
    assert(allocations==1&&!initializations&&!stock_frees&&!ep7_native_content.child);
    assert(selector[86]==2&&ep7_stock_selector_remembered_unresolved==2&&ep7m_current());
    /*2 Success constructs before old destruction; H/L reuse same owned extent. */
    begin_case();enable_fixture_hl();select_category(4);ep7c_rebuild(parent);
    assert(allocations==1&&initializations==1&&stock_frees==1&&!stock_calls);
    assert(getpointer(parent+80)==&allocation&&ep7_native_content.child==&allocation);
    assert(allocation.generation==1&&allocation.category==4&&ep7m_current());
    assert(getpointer(allocation.native)==ep7_content_vtable);
    select_category(5);ep7c_rebuild(parent);
    assert(allocations==1&&allocation.category==5&&ep7_native_mvc.category==5);
    /*3 Return to stock: private revoke precedes free; exact original rebuild. */
    select_category(1);ep7c_rebuild(parent);
    assert(private_frees==1&&!ep7_native_content.child&&stock_calls==1);
    assert(ep7_native_mvc.content==stock_content&&ep7_native_mvc.category==1&&ep7m_current());
    /*4 Parent retirement forgets graph; private destruction is still task-bound. */
    begin_case();enable_fixture_hl();select_category(4);ep7c_rebuild(parent);
    ep7m_before_parent_destroy(parent);memset(parent,0xcc,sizeof parent);
    ep7_gcc_mvc_dispose(&allocation);assert(private_frees==1&&!ep7_native_content.child);
    if (!setjmp(fatal)) { ep7c_before_destroy(&allocation);assert(!"duplicate destructor"); }
    assert(quarantines==1);
    /*5 Native allocation callbacks cannot free or recursively rebuild held graph. */
    for (volatile unsigned i=1;i<=3;i++) {
        begin_case();enable_fixture_hl();select_category(4);reenter=i;
        if (!setjmp(fatal)) { ep7c_rebuild(parent);assert(!"reentry returned"); }
        assert(quarantines==1&&ep7_native_mvc.busy&&!stock_frees&&!initializations);
    }
    /*6 Mutated graph/cohort stops before following foreign content or allocation. */
    begin_case();pointer(parent+80,(void *)1);assert(!ep7m_current());
    pointer(parent+80,stock_content);
    if (!setjmp(fatal)) { ep7c_rebuild(parent);assert(!"invalid graph delegated"); }
    assert(quarantines==1&&!stock_calls&&!allocations);
    begin_case();ep7_stock_mvc_rebuild_touch_call_unresolved[4]=24;
    if (!setjmp(fatal)) { ep7c_rebuild(parent);assert(!"wrong CALL frame admitted"); }
    assert(quarantines==1&&!stock_calls&&!allocations);
    begin_case();ep7c_rebuild((void *)1);assert(stock_calls==1&&!allocations&&ep7m_current());
    reset();ep7_stock_gui_color_exit_unresolved=0;ep7c_rebuild((void *)1);
    assert(stock_calls==2&&!queries); /* Cold native delegation. */
    return 0;
}
