#include "gate.h"
#include "../ui_selector/selector.h"
#include "../ui_model/model.h"
#include "../ui_owner/owner.h"
#include "../ui_render/viewer.h"
#include "../ui_native/input.h"
#include "../ui_content/stock.h"
struct ep7g_state ep7_native_ui_gate;
extern volatile uint32_t ep7_stock_selector_initializer_unresolved;
extern const unsigned char initializer[] __asm__("ep7_native_selector_init_bridge");
extern volatile uint16_t ep7_stock_selector_remembered_unresolved;
extern _Noreturn void ep7_gcc_quarantine(unsigned reason);
static unsigned half(const uint8_t *p) { return p[0]|((unsigned)p[1]<<8); }
static int enabled(const struct ep7m_lifetime *m,unsigned category,uint32_t mode)
{ return category<4&&!half((const uint8_t *)m->masks+2*category)&&ep7c_stock_supported(category,mode); }
unsigned ep7g_reconcile_held(struct ep7m_lifetime *m,uint32_t *mode)
{
    struct ep7g_state *g=&ep7_native_ui_gate;
    if (m!=&ep7_native_mvc||!m->busy||ep7m_current()!=m||!mode) ep7_gcc_quarantine(0xd01);
    *mode=ep7_gcc_ui_public_mode();
    if (g->generation!=m->generation) { g->generation=m->generation;g->last_stock=m->category; }
    if (m->category<4) g->last_stock=m->category;
    unsigned target=half((const uint8_t *)m->selector+86);
    if (!enabled(m,target,*mode)) target=g->last_stock;
    if (!enabled(m,target,*mode)) {
        for (target=0;target<4&&!enabled(m,target,*mode);target++) {}
    }
    g->available=0;
    if (m->selector_count==6&&target<4&&
        ep7_stock_selector_initializer_unresolved==(uint32_t)(uintptr_t)initializer&&
        ep7i_native_cohort_present()&&ep7cm_available_held(m,*mode)) {
        uint32_t owner_generation=ep7_native_ui_owner.generation;
        if (ep7u_hold_ready(owner_generation)) {
            g->available=1;ep7u_release_ready(owner_generation);
        }
    }
    if (m->selector_count==6) {
        uint8_t *mask=m->masks;mask[8]=mask[10]=(uint8_t)!g->available;mask[9]=mask[11]=0;
    }
    if (g->available) return EP7G_AVAILABLE;
    ep7cm_revoke();
    if (m->category>=4) {
        ep7v_clear();
        /* All stock masks disabled or allocation failure retains a noneditable
         * owned H/L object; never invent a stock mask or publish NULL content. */
        if (target<4) {
            if (ep7c_to_stock_held(m,target,*mode)) { g->last_stock=target;return EP7G_REBUILT; }
        } else ep7c_stop_transition(m);
        uint8_t *selector=m->selector;selector[86]=(uint8_t)m->category;selector[87]=0;
        ep7_stock_selector_remembered_unresolved=(uint16_t)m->category;
    }
    return 0;
}
int ep7g_before_event(void *parent)
{
    const struct ep7m_lifetime *view=ep7m_current();
    if (!view||view->parent!=parent) {
        if (parent&&ep7_native_mvc.parent==parent) ep7_gcc_quarantine(0xd02);
        return -1;
    }
    int category=(int)view->category;
    struct ep7m_lifetime *m=ep7m_hold_content(parent);uint32_t mode;
    unsigned flags=ep7g_reconcile_held(m,&mode);
    ep7v_refresh_held(m,flags);
    ep7m_release_content(m);
    return category;
}
