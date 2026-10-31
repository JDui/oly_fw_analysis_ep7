#include "viewer.h"
#include "../ui_model/model.h"
#include "../ui_owner/owner.h"
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
void ep7v_refresh(void)
{
    struct ep7v_receipt *receipt=&ep7_native_ui_receipt;
    receipt->ready=0;
    const struct ep7m_lifetime *view=ep7m_current();
    if (!view||view->busy) return; /* Construction, drawing or a held text update. */
    const uint8_t *v=view->viewer;
    /* Full original draw supplies these values. Owner completion alone does not
     * prove this MVC has finished drawing its current content/category. */
    if (word(v+388)!=(uint32_t)(uintptr_t)view->selector||
        word(v+392)!=(uint32_t)(uintptr_t)view->content||half(v+396)!=view->category) return;
    struct ep7m_lifetime *m=ep7m_hold_content(view->parent);
    if (!m) return;
    if (m->category<4) { ep7cm_revoke();ep7v_clear(); }
    else {
        struct ep7_ui_frame frame;uint16_t text[EP7_TEXT_UNITS];uint32_t generation;
        if (ep7cm_frame_held(m,&frame)&&frame.public_mode==word(v+400)&&
            ep7_text_format(&frame,text,EP7_TEXT_UNITS)&&ep7u_present(text,&generation)) {
            *receipt=(struct ep7v_receipt){m->viewer,m->content,m->generation,
                ep7_native_ui_model.session.generation,generation,frame.public_mode,frame.category,1};
        } else ep7v_clear(); /* Do not leave a prior H/L label active on failed/unsupported refresh. */
    }
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
    return ep7m_hold_content(m->parent)!=NULL;
}
void ep7v_draw_end(void *viewer,unsigned held)
{
    if (!held) return;
    if (held!=1||ep7_native_mvc.viewer!=viewer) ep7_gcc_quarantine(0xb01);
    ep7m_release_content(&ep7_native_mvc);
    ep7v_refresh();
}
