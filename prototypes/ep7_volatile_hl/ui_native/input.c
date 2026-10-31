#include "input.h"
#include "../ui_model/model.h"
#include "../ui_render/viewer.h"
#include "../ui_owner/owner.h"
#include <stddef.h>
struct ep7i_scope ep7_native_ui_input_scope;
extern volatile uint32_t ep7_stock_gui_machine_unresolved;
extern volatile uint32_t ep7_stock_ui_input_gate_unresolved;
extern volatile uint32_t ep7_stock_ui_repeat_context_unresolved;
extern void ep7_gcc_ui_drop_info(void);
extern _Noreturn void ep7_gcc_quarantine(unsigned reason);
static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static unsigned half(const uint8_t *p) { return p[0]|((unsigned)p[1]<<8); }
static void put32(uint8_t *p,uint32_t n)
{ for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(n>>(8*i)); }
static int same_task(const ep7n_task *a,const ep7n_task *b)
{
    return a->tid==b->tid&&a->domain==b->domain&&a->tcb==b->tcb&&a->entry==b->entry&&
        a->stack_low==b->stack_low&&a->stack_bytes==b->stack_bytes;
}
static _Noreturn void fault(unsigned reason) { ep7_gcc_quarantine(0xc00u+reason); }
static void current_task(struct ep7i_scope *s)
{
    ep7n_task t;
    if (!ep7i_native_cohort_present()||!ep7n_native_current_task((uint32_t)(uintptr_t)&t,&t)||
        t.domain!=0||t.entry!=UINT32_C(0x60dd5067)) fault(1);
    if (atomic_load_explicit(&s->started,memory_order_acquire)) {
        if (!same_task(&s->task,&t)) fault(2);
    } else { s->task=t;atomic_store_explicit(&s->started,true,memory_order_release); }
}
void ep7i_prepare_begin(const void *packet)
{
    struct ep7i_scope *s=&ep7_native_ui_input_scope;
    current_task(s);
    if (s->phase==1||s->phase==3) fault(3);
    uintptr_t p=(uintptr_t)packet;
    if (p>UINT32_MAX||p<s->task.stack_low||s->task.stack_bytes<28||
        p-s->task.stack_low>s->task.stack_bytes-28) fault(4);
    s->phase=1;s->packet=packet;s->original_event=word(packet);
    s->samples=s->valid=s->consumed=0;s->delta=0;
}
void ep7i_sample_wheel(const struct ep7i_sample *sample)
{
    struct ep7i_scope *s=&ep7_native_ui_input_scope;
    current_task(s);
    /* Calls outside the registered complete preprocessor never publish input. */
    if (s->phase!=1) return;
    if (!sample||sample->packet!=(uint32_t)(uintptr_t)s->packet||s->samples) {
        s->valid=0;s->samples=2;return;
    }
    uint32_t source=0,event=0,status=sample->native_d2;
    switch (sample->return_pc) {
    case 0x60ea0075:source=0x9031;event=0x9031;break;
    case 0x60ea00fc:source=0x9032;event=0x9032;status=sample->native_a2;break;
    case 0x60ea0d75:source=0x904f;event=0x9031;break;
    case 0x60ea0df0:source=0x9051;event=0x9031;break;
    case 0x60ea0e6b:source=0x9050;event=0x9032;break;
    default:break;
    }
    s->samples=1;s->event=event;s->delta=(int32_t)sample->delta;
    s->valid=source&&source==s->original_event&&!status&&s->delta>=-64&&s->delta<=64;
}
void ep7i_prepare_end(const void *packet,uint32_t result)
{
    struct ep7i_scope *s=&ep7_native_ui_input_scope;
    current_task(s);
    if (s->phase!=1||packet!=s->packet) fault(5);
    s->phase=0;
    if (result!=0) return; /* Supported subset of native result !=1 delivery. */
    uint32_t event=word(s->packet),parameter=word(s->packet+12);
    if (event==0x9014&&s->original_event==event&&!s->samples) {
        s->event=event;s->delta=0;
    } else {
        int32_t normalized=s->delta>0?(s->event==0x9031&&s->delta>=2?2:1):-1;
        if (s->samples!=1||!s->valid||event!=s->event||parameter!=(uint32_t)normalized) return;
    }
    s->parameter=parameter;s->extra=word(s->packet+16);s->phase=2;
}
unsigned ep7i_dispatch_begin(const struct ep7i_dispatch *call)
{
    struct ep7i_scope *s=&ep7_native_ui_input_scope;
    current_task(s);
    if (s->phase==1||s->phase==3) fault(6);
    unsigned pending=s->phase==2;s->phase=0;
    if (!pending||!call||call->packet!=(uint32_t)(uintptr_t)s->packet||
        call->event!=s->event||call->parameter!=s->parameter||call->extra!=s->extra||
        !call->machine||call->machine!=ep7_stock_gui_machine_unresolved) return 0;
    const uint8_t *machine=(const uint8_t *)(uintptr_t)call->machine;
    if (machine[0]!=4||machine[1]!=29) return 0;
    s->machine=call->machine;s->consumed=0;s->phase=3;return 1;
}
void ep7i_dispatch_end(unsigned held)
{
    struct ep7i_scope *s=&ep7_native_ui_input_scope;
    current_task(s);
    if (!held) return;
    if (held!=1||s->phase!=3) fault(7);
    s->phase=0;s->packet=NULL;s->valid=0;
}
uint32_t ep7i_route(const struct ep7_native_ui_input *input)
{
    const struct ep7m_lifetime *view=ep7m_current();
    void *parent=(void *)(uintptr_t)input->parent;
    if (!view||view->parent!=parent) {
        if (parent&&ep7_native_mvc.parent==parent) fault(8);
        return EP7_NATIVE_CALL_STOCK;
    }
    if (view->category<4) return EP7_NATIVE_CALL_STOCK;
    struct ep7i_scope *s=&ep7_native_ui_input_scope;
    current_task(s);
    if (view->busy) fault(9);
    /* Reproduce the full parent entry's scalar bookkeeping on owned H/L. */
    uint8_t *p=parent;put32(p+24,input->event);put32(p+28,input->packet_parameter);
    if (ep7_stock_ui_repeat_context_unresolved) { p[36]=200;p[37]=0; }
    if (s->phase!=3||s->consumed||s->event!=input->event||s->parameter!=input->packet_parameter||
        input->caller_pc!=0x60e4d101||input->container!=(uint32_t)(uintptr_t)view->container)
        return 0;
    s->consumed=1; /* Even a failed owned attempt cannot replay this event. */
    if (s->machine!=ep7_stock_gui_machine_unresolved) return 0;
    const uint8_t *machine=(const uint8_t *)(uintptr_t)s->machine;
    if (machine[0]!=4||machine[1]!=29||half(machine+8)!=137||ep7_stock_ui_input_gate_unresolved)
        return 0;
    struct ep7v_receipt receipt=ep7_native_ui_receipt;
    struct ep7cm_model *model=&ep7_native_ui_model;
    if (!receipt.ready||receipt.viewer!=view->viewer||receipt.child!=view->content||
        receipt.mvc_generation!=view->generation||receipt.category!=view->category||
        receipt.session_generation!=model->session.generation||
        half((const uint8_t *)view->selector+86)!=view->category||
        half((const uint8_t *)view->masks+2*view->category)) return 0;
    struct ep7m_lifetime *m=ep7m_hold_content(parent);
    if (!m) fault(10);
    int result=EP7_UI_REJECTED;
    if (ep7u_hold_ready(receipt.owner_generation)) {
        struct ep7_ui_frame frame;
        const uint8_t *v=m->viewer;
        if (ep7cm_frame_held(m,&frame)&&frame.public_mode==receipt.mode&&
            frame.public_mode==word(v+400)&&frame.category==receipt.category&&
            word(v+388)==(uint32_t)(uintptr_t)m->selector&&
            word(v+392)==(uint32_t)(uintptr_t)m->content&&half(v+396)==m->category&&
            model->session.generation==receipt.session_generation) {
            if (input->event==0x9014) ep7_gcc_ui_drop_info();
            struct ep7p_ui_raw_event event={input->event,s->delta};
            result=ep7p_ui_raw_dispatch(&model->ui,model->session,&event);
        }
        ep7u_release_ready(receipt.owner_generation);
    }
    ep7m_release_content(m);
    /* Native changed=1 performs the full viewer draw. Otherwise refresh the
     * acknowledgement after releasing both holds; no pending input survives. */
    if (result!=EP7_UI_CHANGED) ep7v_refresh();
    return result==EP7_UI_CHANGED?1u:0u;
}
