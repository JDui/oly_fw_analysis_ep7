#include "model.h"
#include "../ui_content/content.h"
struct ep7cm_model ep7_native_ui_model;
extern _Noreturn void ep7_gcc_quarantine(unsigned reason);
void ep7cm_revoke(void)
{
    struct ep7cm_model *s=&ep7_native_ui_model;
    if (s->session.generation) ep7p_ui_ops.close(&s->ui,s->session);
    s->session=(struct ep7_ui_session){0};
}
int ep7cm_frame_held(struct ep7m_lifetime *m,struct ep7_ui_frame *out)
{
    struct ep7cm_model *s=&ep7_native_ui_model;
    if (m!=&ep7_native_mvc||!m->busy||ep7m_current()!=m) ep7_gcc_quarantine(0xa01);
    if (!out||m->category<4||m->category>5) { ep7cm_revoke();return 0; }
    ep7c_require_owned(m);
    ep7r *r=ep7r_get(&ep7_native_runtime_slot);
    if (s->runtime&&(s->runtime!=r||s->ui.core!=r->boot->core)) ep7_gcc_quarantine(0xa02);
    if (!ep7r_accepting(r)) { ep7cm_revoke();return 0; }
    if (!s->runtime) {
        s->runtime=r;ep7p_ui_init(&s->ui,r->boot->core); /* Same published worker/capture core. */
    }
    uint32_t mode=ep7_gcc_ui_public_mode();
    if (mode!=54&&mode!=55&&mode!=56&&mode!=64) { ep7cm_revoke();return 0; }
    if (!s->session.generation) {
        if (s->serial==UINT32_MAX) return 0; /* No live reset/wrap/reused UI token. */
        struct ep7_ui_session next={++s->serial,0};
        if (ep7p_ui_ops.open(&s->ui,next,(uint16_t)mode,(uint8_t)m->category)!=EP7_UI_CHANGED) return 0;
        s->session=next;
    } else if (ep7p_ui_ops.sync(&s->ui,s->session,(uint16_t)mode,(uint8_t)m->category)==EP7_UI_REJECTED)
        return 0;
    /* Transient poll contention does not erase the live session or its focus. */
    return ep7p_ui_ops.frame(&s->ui,s->session,out)!=EP7_UI_REJECTED;
}
