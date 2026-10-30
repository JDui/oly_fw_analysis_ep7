#include "bridge.h"
#include <assert.h>
static int admission, normalized, admissions, dispatches;
static int32_t expected_delta;
int ep7_ui_native_admit_unresolved(const struct ep7_native_ui_input *in, struct ep7_ui_admission *a) {
    assert(in->parent==0x12340000u); ++admissions;
    a->ui=0; a->session=(struct ep7_ui_session){0};
    a->synchronized_full_delta=expected_delta; return admission;
}
int ep7p_ui_raw_dispatch(ep7p_ui *ui,struct ep7_ui_session session,const struct ep7p_ui_raw_event *e) {
    (void)ui;(void)session;assert(e->copied_full_delta==expected_delta);++dispatches;return normalized;
}
int main(void) {
    struct ep7_native_ui_input in={0x9032u,1u,0x12340000u};
    assert(ep7_gcc_ui_route(0)==0);
    admission=EP7_NATIVE_STOCK;assert(ep7_gcc_ui_route(&in)==256u);assert(!dispatches);
    admission=EP7_NATIVE_REJECT;assert(ep7_gcc_ui_route(&in)==0);assert(!dispatches);
    admission=77;assert(ep7_gcc_ui_route(&in)==0);assert(!dispatches);
    admission=EP7_NATIVE_OWNED;expected_delta=-7;normalized=EP7_UI_CHANGED;
    assert(ep7_gcc_ui_route(&in)==1); /* delta is provider -7, NOT packet +1 */
    normalized=EP7_UI_UNCHANGED;assert(ep7_gcc_ui_route(&in)==0);
    normalized=EP7_UI_REJECTED;assert(ep7_gcc_ui_route(&in)==0);
    normalized=EP7P_UI_RAW_DELEGATE;assert(ep7_gcc_ui_route(&in)==256u);
    normalized=4;assert(ep7_gcc_ui_route(&in)==0);
    in.event=0x9014u;normalized=EP7_UI_CHANGED;assert(ep7_gcc_ui_route(&in)==1);
    in.event=0x9031u;assert(ep7_gcc_ui_route(&in)==1);
    int old=admissions;in.event=0x900cu;assert(ep7_gcc_ui_route(&in)==256u);assert(admissions==old);
    in.event=0x9016u;assert(ep7_gcc_ui_route(&in)==256u);assert(admissions==old);
    return 0;
}
