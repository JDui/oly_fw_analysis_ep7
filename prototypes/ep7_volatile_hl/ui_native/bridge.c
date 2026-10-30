/* Self-authored portable routing glue, native provider intentionally absent. */
#include "bridge.h"
_Static_assert(sizeof(struct ep7_native_ui_input)==12,"native input layout");
uint32_t ep7_gcc_ui_route(const struct ep7_native_ui_input *input)
{
    struct ep7_ui_admission a;
    struct ep7p_ui_raw_event event;
    int admission,result;
    if(!input) return 0;
    /* This seam deliberately leaves category navigation and all stock events
       with their original parent dispatcher. */
    if(input->event!=0x9031u && input->event!=0x9032u && input->event!=0x9014u)
        return EP7_NATIVE_CALL_STOCK;
    admission=ep7_ui_native_admit_unresolved(input,&a);
    if(admission==EP7_NATIVE_STOCK) return EP7_NATIVE_CALL_STOCK;
    if(admission!=EP7_NATIVE_OWNED) return 0;
    event.local_event=input->event;
    event.copied_full_delta=a.synchronized_full_delta;
    result=ep7p_ui_raw_dispatch(a.ui,a.session,&event);
    if(result==EP7P_UI_RAW_DELEGATE) return EP7_NATIVE_CALL_STOCK;
    /* Native parent return1 requests viewer virtual0; 2/3/4 are not synonymous
       with handled. Invalid, unchanged, and failed edits request no redraw. */
    return result==EP7_UI_CHANGED ? 1u : 0u;
}
