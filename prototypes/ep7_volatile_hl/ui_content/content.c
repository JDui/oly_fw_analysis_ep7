#include "content.h"
#include "../ui_model/model.h"
#include <stddef.h>
#include <string.h>
_Static_assert(sizeof(struct ep7c_child)==56,"owned MVC child extent");
struct ep7c_content ep7_native_content;
extern volatile uint16_t ep7_stock_selector_remembered_unresolved;
extern _Noreturn void ep7_gcc_quarantine(unsigned reason);
static uint16_t half(const uint8_t *p) { return (uint16_t)(p[0]|((uint16_t)p[1]<<8)); }
static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static void put16(uint8_t *p,unsigned n) { p[0]=(uint8_t)n;p[1]=(uint8_t)(n>>8); }
static void pointer(uint8_t *p,const void *v)
{ uint32_t n=(uint32_t)(uintptr_t)v;for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(n>>(8*i)); }
static _Noreturn void inconsistent(unsigned reason) { ep7_gcc_quarantine(0x900u+reason); }
static void restore_category(struct ep7m_lifetime *m)
{
    put16((uint8_t *)m->selector+86,m->category);
    ep7_stock_selector_remembered_unresolved=(uint16_t)m->category;
}
void ep7c_require_owned(const struct ep7m_lifetime *m)
{
    struct ep7c_content *s=&ep7_native_content;
    if (!s->child||m->content!=s->child||s->generation!=m->generation||
        s->child->generation!=m->generation||s->child->category!=m->category||
        word(s->child->native)!=(uint32_t)(uintptr_t)ep7_content_vtable) inconsistent(1);
}
void ep7c_rebuild(void *parent)
{
    struct ep7m_lifetime *m=ep7m_hold_content(parent);
    if (!m) { ep7_gcc_mvc_stock_rebuild(parent);return; }
    struct ep7c_content *s=&ep7_native_content;
    unsigned category=half((const uint8_t *)m->selector+86);
    if (m->category>=4) ep7c_require_owned(m);
    else if (s->child) inconsistent(2);
    if (category<4) {
        /* Original factories and semantics for stock categories, including the
         * original allocation-failure behavior; no S factory is used for H/L. */
        ep7_gcc_mvc_stock_rebuild(parent);
        if (s->child) inconsistent(3);
        m->content=(void *)(uintptr_t)word((uint8_t *)parent+80);m->category=category;
    } else if (m->selector_count!=6||half((const uint8_t *)m->masks+2*category)) {
        /* Default H/L masks stay disabled. Later native renderer admission owns
         * enabling them; this module never writes a mask or claims readiness. */
        restore_category(m);
    } else if (m->category>=4) {
        s->child->category=category;m->category=category; /* H <-> L retains extent. */
    } else {
        struct ep7c_child *next=ep7_gcc_mvc_scalar_new(sizeof *next);
        if (!next) restore_category(m);
        else {
            memset(next,0,sizeof *next);ep7_gcc_mvc_base_init(next);
            pointer(next->native,ep7_content_vtable);next->generation=m->generation;next->category=category;
            /* Native allocation/initialization completed before old ownership
             * changes. The held graph forbids matching teardown/rebuild reentry. */
            s->child=next;s->generation=m->generation;
            if (m->content) ep7_gcc_mvc_dispose(m->content);
            pointer((uint8_t *)parent+80,next);m->content=next;m->category=category;
        }
    }
    ep7m_release_content(m);
}
void ep7c_before_destroy(void *child)
{
    ep7m_require_context();
    struct ep7c_content *s=&ep7_native_content;
    if (!child||s->child!=child) inconsistent(4); /* Compare before dereference. */
    if (ep7_native_mvc.container&&!ep7_native_mvc.busy) inconsistent(5);
    /* Parent retirement has already forgotten the graph, or original rebuild
     * is under the hold. Revoke before base destruction and native deallocation. */
    ep7cm_revoke();s->child=NULL;s->generation=0;
}
