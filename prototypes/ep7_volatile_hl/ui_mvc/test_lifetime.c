#include "lifetime.h"
#include "../ui_selector/selector.h"
#include <assert.h>
#include <setjmp.h>
#include <string.h>

volatile uint32_t ep7_stock_gui_color_entry_unresolved,ep7_stock_gui_color_exit_unresolved;
volatile uint32_t ep7_stock_color_container_unresolved;
volatile uint32_t ep7_stock_mvc_parent_vtable_unresolved[11],ep7_stock_mvc_viewer_vtable_unresolved[2];
const unsigned char ep7_native_mvc_gui_entry_bridge[1]={1},ep7_native_mvc_gui_exit_bridge[1]={2};
const unsigned char ep7_native_mvc_parent_destroy_bridge[1]={3},ep7_native_mvc_viewer_destroy_bridge[1]={4};
const unsigned char ep7_native_ui_viewer_bridge[1]={6};
#ifndef EP7_UI_RENDER_INTEGRATION
/* Viewer/model callbacks are boundary mocks in the earlier lifetime-only test. */
void ep7v_refresh(void) {}
void ep7v_clear(void) {}
void ep7v_invalidate(void) {}
void ep7cm_revoke(void) {}
#endif
/* Address-only native bridge marker: keep it in the same writable fixture area
 * as CALL bytes, including with sanitizer redzones; no host code runs here. */
volatile unsigned char ep7_fixture_rebuild_target[1];
extern const unsigned char ep7_native_content_rebuild_bridge[];
__asm__(".globl ep7_native_content_rebuild_bridge\n"
        ".set ep7_native_content_rebuild_bridge,ep7_fixture_rebuild_target");
volatile unsigned char ep7_stock_mvc_rebuild_initial_call_unresolved[5];
volatile unsigned char ep7_stock_mvc_rebuild_previous_call_unresolved[5];
volatile unsigned char ep7_stock_mvc_rebuild_next_call_unresolved[5];
volatile unsigned char ep7_stock_mvc_rebuild_touch_call_unresolved[5];
const uint16_t ep7s_categories[6]={0,1,2,3,4,5};
static uint8_t container[228],parent[100],selector[124],viewer[408],masks[12],other_masks[12];
static unsigned queries,wrong_task,quarantines;
static jmp_buf fatal;
static void put16(uint8_t *p,uint16_t n) { p[0]=(uint8_t)n;p[1]=(uint8_t)(n>>8); }
static void put32(uint8_t *p,uint32_t n)
{ for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(n>>(8*i)); }
static void pointer(uint8_t *p,const void *v)
{ assert((uintptr_t)v<=UINT32_MAX);put32(p,(uint32_t)(uintptr_t)v); }
bool ep7n_native_current_task(uint32_t anchor,ep7n_task *task)
{
    (void)anchor;queries++;*task=(ep7n_task){0x101,0,0x1000+wrong_task,0x60dd5067,0x2000,
#ifdef EP7_UI_INPUT_INTEGRATION
        0x1000000 /* Static native packet surrogate resides inside this fixture extent. */
#else
        16384
#endif
    };
    return true;
}
_Noreturn void ep7_gcc_quarantine(unsigned reason)
{ assert((reason>=0x701&&reason<=0x70c)||(reason>=0x801&&reason<=0x80b)||
    (reason>=0x901&&reason<=0x905)||(reason>=0xa01&&reason<=0xa02)||(reason>=0xb01&&reason<=0xb02)||
    (reason>=0xc01&&reason<=0xc0a));
  quarantines++;longjmp(fatal,1); }
static void call_patch(volatile unsigned char *p)
{
    intptr_t delta=(intptr_t)ep7_native_content_rebuild_bridge-(intptr_t)p;
    assert(delta>=INT16_MIN&&delta<=INT16_MAX);
    uint16_t d=(uint16_t)delta;
    p[0]=0xcd;p[1]=(uint8_t)d;p[2]=(uint8_t)(d>>8);p[3]=0xf0;p[4]=28;
}
static void reset(void)
{
    memset(&ep7_native_mvc,0,sizeof ep7_native_mvc);atomic_init(&ep7_native_mvc.started,false);
    queries=wrong_task=quarantines=0;ep7_stock_color_container_unresolved=0;
    ep7_stock_gui_color_entry_unresolved=(uint32_t)(uintptr_t)ep7_native_mvc_gui_entry_bridge;
    ep7_stock_gui_color_exit_unresolved=(uint32_t)(uintptr_t)ep7_native_mvc_gui_exit_bridge;
    ep7_stock_mvc_parent_vtable_unresolved[10]=(uint32_t)(uintptr_t)ep7_native_mvc_parent_destroy_bridge;
    ep7_stock_mvc_viewer_vtable_unresolved[1]=(uint32_t)(uintptr_t)ep7_native_mvc_viewer_destroy_bridge;
    ep7_stock_mvc_viewer_vtable_unresolved[0]=(uint32_t)(uintptr_t)ep7_native_ui_viewer_bridge;
    call_patch(ep7_stock_mvc_rebuild_initial_call_unresolved);
    call_patch(ep7_stock_mvc_rebuild_previous_call_unresolved);
    call_patch(ep7_stock_mvc_rebuild_next_call_unresolved);
    call_patch(ep7_stock_mvc_rebuild_touch_call_unresolved);
}
/* Boundary fixture: original native container creation, initial draw and global
 * publication are modeled, not executed. Exact object extents are ASan-visible. */
static void publish(unsigned count)
{
    memset(container,0,sizeof container);memset(parent,0,sizeof parent);
    memset(viewer,0,sizeof viewer);memset(selector,0,sizeof selector);
    pointer(container,parent);pointer(container+4,viewer);put32(container+8,0x34);put32(container+12,0x84);
    put32(parent,0x6118957c);pointer(parent+76,selector);
    put32(viewer,0x61189ba8);pointer(viewer+384,parent);
    put32(selector,0x6114f7e4);put32(selector+80,193);put16(selector+84,(uint16_t)count);
    put16(selector+86,2);pointer(selector+88,masks);
    if (count==6) pointer(selector+92,ep7s_categories);else put32(selector+92,0x6114e050);
    ep7_stock_color_container_unresolved=(uint32_t)(uintptr_t)container;
}
static void enter(unsigned count)
{ ep7m_gui_begin();publish(count);ep7m_gui_complete(container); }
int main(void)
{
    struct ep7m_lifetime *s=&ep7_native_mvc;
    /*1 No installed cohort means no task query or arbitrary object access. */
    reset();ep7_stock_gui_color_exit_unresolved=0;ep7m_gui_begin();ep7m_gui_complete((void *)1);
    ep7m_before_parent_destroy((void *)1);assert(!ep7m_current()&&!queries);
    /*2 Capture exact returned/global relation; keep4 fallback as well as6. */
    reset();enter(6);assert(ep7m_current()==s&&s->generation==1&&s->selector_count==6);
    ep7m_before_gui_exit();assert(!ep7m_current());ep7_stock_color_container_unresolved=0;
    enter(4);assert(ep7m_current()==s&&s->generation==2&&s->selector_count==4);
    ep7m_before_gui_exit();ep7m_gui_begin();publish(6);ep7m_gui_complete((void *)1);
    assert(!ep7m_current()&&!s->container&&!s->constructing);
    /*3 Matching parent teardown invalidates viewer BEFORE parent storage dies. */
    reset();enter(6);ep7m_before_parent_destroy((void *)1);assert(ep7m_current()==s);
    ep7m_before_parent_destroy(parent);memset(parent,0xcc,sizeof parent);
    assert(!ep7m_current()&&!s->viewer&&!s->selector);
    ep7m_before_viewer_destroy(viewer);memset(viewer,0xcc,sizeof viewer);
    enter(6);assert(s->generation==2&&ep7m_current()==s);
    ep7m_before_viewer_destroy(viewer);assert(!ep7m_current());
    /*4 Changed global or mask is rejected without following substituted memory. */
    reset();enter(6);ep7_stock_color_container_unresolved=1;assert(!ep7m_current());
    if (!setjmp(fatal)) { ep7m_before_gui_exit();assert(!"mismatched global exit returned"); }
    assert(quarantines==1&&s->container==container);
    ep7_stock_color_container_unresolved=(uint32_t)(uintptr_t)container;
    assert(!ep7m_current()); /* Restoring pointer bits cannot revive this generation. */
    ep7m_before_gui_exit();enter(6);assert(s->generation==2&&ep7m_current()==s);
    pointer(selector+88,other_masks);assert(!ep7m_current());pointer(selector+88,masks);
    assert(!ep7m_current());ep7m_before_gui_exit();enter(6);assert(ep7m_current()==s);
    /*5 Wrong TCB, broken cohort and recursive/replacing entry stop before free/allocation. */
    reset();enter(6);wrong_task=4;
    if (!setjmp(fatal)) { ep7m_before_parent_destroy(parent);assert(!"wrong task returned"); }
    assert(quarantines==1&&s->parent==parent);wrong_task=0;
    ep7_stock_mvc_viewer_vtable_unresolved[1]=0;
    if (!setjmp(fatal)) { ep7m_before_viewer_destroy(viewer);assert(!"broken cohort returned"); }
    assert(quarantines==2&&s->viewer==viewer);
    reset();ep7m_gui_begin();ep7m_before_parent_destroy((void *)1); /* Unrecorded temporary cleanup. */
    if (!setjmp(fatal)) { ep7m_gui_begin();assert(!"nested entry returned"); }
    assert(quarantines==1&&s->constructing&&!s->container);
    reset();enter(6);
    if (!setjmp(fatal)) { ep7m_gui_begin();assert(!"active entry replaced"); }
    assert(quarantines==1&&s->parent==parent);
    /*6 Failed factory capture and generation exhaustion never publish. */
    reset();ep7m_gui_begin();ep7m_gui_complete(NULL);assert(!s->container&&!s->constructing);
    s->generation=UINT32_MAX;enter(6);assert(s->stopped&&!ep7m_current()&&!s->container);
    ep7m_before_gui_exit();enter(6);assert(s->stopped&&s->generation==UINT32_MAX&&!s->container);
    return 0;
}
