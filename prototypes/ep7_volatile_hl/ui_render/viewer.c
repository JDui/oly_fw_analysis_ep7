#include "viewer.h"
#include "../ui_model/model.h"
#include "../ui_owner/owner.h"
#include "../ui_gate/gate.h"
#include "../text_viewer/text.h"
#include <stddef.h>
struct ep7v_receipt ep7_native_ui_receipt;
void ep7v_invalidate(void) { ep7_native_ui_receipt.ready=0; }
extern _Noreturn void ep7_gcc_quarantine(unsigned reason);
static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static unsigned half(const uint8_t *p) { return p[0]|((unsigned)p[1]<<8); }
void ep7v_clear(void)
{
    const uint16_t empty[EP7_TEXT_UNITS]={0};
    ep7_native_ui_receipt.ready=0;
    (void)ep7u_present(empty,NULL);
}
void ep7v_refresh_held(struct ep7m_lifetime *m,unsigned flags)
{
    struct ep7v_receipt *receipt=&ep7_native_ui_receipt;
    receipt->ready=0;
    if (m!=&ep7_native_mvc||!m->busy||ep7m_current()!=m) ep7_gcc_quarantine(0xb03);
    if (flags&EP7G_REBUILT) ep7_gcc_ui_draw_original(m->viewer);
    const uint8_t *v=m->viewer;
    /* Full original draw supplies these values. Owner completion alone does not
     * prove this MVC has finished drawing its current content/category. */
    if (m->category<4) { ep7cm_revoke();ep7v_clear(); }
    else if (!(flags&EP7G_AVAILABLE)||word(v+388)!=(uint32_t)(uintptr_t)m->selector||
        word(v+392)!=(uint32_t)(uintptr_t)m->content||half(v+396)!=m->category) ep7v_clear();
    else {
        struct ep7_ui_frame frame;uint16_t text[EP7_TEXT_UNITS];uint32_t generation;
        if (ep7cm_frame_held(m,&frame)&&frame.public_mode==word(v+400)&&
            ep7_text_format(&frame,text,EP7_TEXT_UNITS)&&ep7u_present(text,&generation)) {
            *receipt=(struct ep7v_receipt){m->viewer,m->content,m->generation,
                ep7_native_ui_model.session.generation,generation,frame.public_mode,frame.category,1};
        } else ep7v_clear();
    }
    /* Clearing an old label can also fail while still on stock or before the
     * first matching draw. Revoke masks after any observed setter failure.
     * No second restoration attempt if this boundary was already unavailable. */
    if ((flags&EP7G_AVAILABLE)&&!ep7_native_ui_owner.display_ready) {
        uint32_t mode;unsigned after=ep7g_reconcile_held(m,&mode);
        if (after&EP7G_REBUILT) ep7_gcc_ui_draw_original(m->viewer);
    }
}
void ep7v_refresh(void)
{
    ep7_native_ui_receipt.ready=0;
    const struct ep7m_lifetime *view=ep7m_current();
    if (!view||view->busy) return;
    struct ep7m_lifetime *m=ep7m_hold_content(view->parent);
    if (!m) return;
    uint32_t mode;unsigned flags=ep7g_reconcile_held(m,&mode);
    ep7v_refresh_held(m,flags);
    ep7m_release_content(m);
}
unsigned ep7v_draw_begin(void *viewer)
{
    const struct ep7m_lifetime *m=ep7m_current();
    if (!m||m->viewer!=viewer) {
        if (viewer&&ep7_native_mvc.viewer==viewer) ep7_gcc_quarantine(0xb02);
        return 0; /* Initial draw precedes MVC publication; invalid owned draws never delegate. */
    }
    ep7_native_ui_receipt.ready=0;
    struct ep7m_lifetime *held=ep7m_hold_content(m->parent);
    uint32_t mode;unsigned flags=ep7g_reconcile_held(held,&mode);
    return 1u|(flags<<1);
}
void ep7v_draw_end(void *viewer,unsigned held)
{
    if (!held) return;
    if (!(held&1)||held>7||ep7_native_mvc.viewer!=viewer) ep7_gcc_quarantine(0xb01);
    /* The enclosing bridge has already drawn the reconciled content. */
    ep7v_refresh_held(&ep7_native_mvc,(held>>1)&~EP7G_REBUILT);
    ep7m_release_content(&ep7_native_mvc);
}
