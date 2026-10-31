#include "stock.h"
extern const uint32_t ep7_stock_mvc_category_keys_unresolved[32];
extern volatile uint32_t ep7_stock_ui_input_gate_unresolved,ep7_stock_ui_active_content_unresolved;
extern volatile uint16_t ep7_stock_selector_remembered_unresolved;
extern _Noreturn void ep7_gcc_quarantine(unsigned reason);
static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static void put32(uint8_t *p,uint32_t n)
{ for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(n>>(8*i)); }
static int key(unsigned category,uint32_t mode,uint32_t *out)
{
    if (category==0) { *out=111;return 1; }
    if (category==3) { *out=383;return 1; }
    if (category!=1&&category!=2) return 0;
    const uint32_t *rows=ep7_stock_mvc_category_keys_unresolved+(category-1)*16;
    for (unsigned i=0;i<8;i++) if (rows[2*i]==mode) { *out=rows[2*i+1];return 1; }
    return 0; /* Do not invent the original unknown-mode factory key0. */
}
int ep7c_stock_supported(unsigned category,uint32_t mode)
{ uint32_t unused;return key(category,mode,&unused); }
void ep7c_stop_transition(struct ep7m_lifetime *m)
{
    if (m!=&ep7_native_mvc||!m->busy||ep7m_current()!=m) ep7_gcc_quarantine(0x908);
    ep7_gcc_mvc_transition_timers(); /* Stock stop535 and cancel537/572. */
    uint8_t *p=m->parent;put32(p+16,0);put32(p+20,0);put32(p+44,0);put32(p+84,0);
}
int ep7c_to_stock_held(struct ep7m_lifetime *m,unsigned category,uint32_t mode)
{
    uint32_t args[2]={0,mode};
    if (m!=&ep7_native_mvc||!m->busy||ep7m_current()!=m||m->category<4) ep7_gcc_quarantine(0x906);
    ep7c_require_owned(m);
    if (!key(category,mode,&args[0])) return 0;
    ep7c_stop_transition(m);
    /* Reproduce generic factory preparation, but restore the two globals on
     * NULL instead of following its unconditional (32,A0) write. */
    uint32_t active=ep7_stock_ui_active_content_unresolved,gate=ep7_stock_ui_input_gate_unresolved;
    ep7_stock_ui_active_content_unresolved=ep7_stock_ui_input_gate_unresolved=0;
    uint8_t *next=ep7_gcc_mvc_stock_create(category,args);
    if (!next) {
        ep7_stock_ui_active_content_unresolved=active;ep7_stock_ui_input_gate_unresolved=gate;
        uint8_t *selector=m->selector;selector[86]=(uint8_t)m->category;selector[87]=0;
        ep7_stock_selector_remembered_unresolved=(uint16_t)m->category;return 0;
    }
    static const uint32_t vtables[4]={0x61155a7c,0x61187534,0x61187534,0x61159ea8};
    if (word(next)!=vtables[category]) ep7_gcc_quarantine(0x907);
    /* Same three post-creator fields as60dd51bf/c2/c5, only after non-NULL. */
    put32(next+32,0);next[36]=next[37]=next[38]=next[39]=0;
    ep7_gcc_mvc_dispose(m->content);
    put32((uint8_t *)m->parent+80,(uint32_t)(uintptr_t)next);
    m->content=next;m->category=category;
    uint8_t *selector=m->selector;selector[86]=(uint8_t)category;selector[87]=0;
    ep7_stock_selector_remembered_unresolved=(uint16_t)category;
    if (category==0) ep7_gcc_mvc_stock_selected(m->parent);
    return 1;
}
