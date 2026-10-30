/* Self-authored logical event adapter. No global delta reads/native calls. */
#include "ep7p_ui_raw.h"
int ep7p_ui_raw_dispatch(ep7p_ui *ui,struct ep7_ui_session session,
                         const struct ep7p_ui_raw_event *input)
{
    struct ep7_ui_frame frame;
    struct ep7p_ui_raw_event event;
    enum ep7_ui_event normalized;
    int32_t delta;
    uint16_t repeat;
    if(!input) return EP7_UI_REJECTED;
    event=*input; /* Caller already owns and synchronizes this copied input. */
    /* Preserve category navigation, OK/internal commit and long-hold semantics;
       unknown events likewise remain unclaimed, not fabricated H/L bindings. */
    if(event.local_event!=0x9031u && event.local_event!=0x9032u &&
       event.local_event!=0x9014u) return EP7P_UI_RAW_DELEGATE;
    /* Existing interface verifies live generation, category4/5 and COLOR mode.
       UI serialization must span this read and subsequent normalized callback. */
    if(ep7p_ui_ops.frame(ui,session,&frame)==EP7_UI_REJECTED)
        return EP7_UI_REJECTED;
    if(event.local_event==0x9014u)
        return ep7p_ui_ops.event(ui,session,EP7_UI_TOGGLE_ALL,1);
    delta=event.copied_full_delta;
    /* Reject before negation: includes -32768 and every unbounded input. */
    if(delta < -64 || delta > 64) return EP7_UI_REJECTED;
    if(delta==0) return EP7_UI_UNCHANGED;
    repeat=(uint16_t)(delta<0 ? -delta : delta);
    /* Direction names below are explicit new-H/L policy. The static evidence
       proves native child-event lanes, not physical knob orientation. */
    if(event.local_event==0x9032u)
        normalized=delta>0 ? EP7_UI_VALUE_INCREASE : EP7_UI_VALUE_DECREASE;
    else
        normalized=delta>0 ? EP7_UI_SECTOR_NEXT : EP7_UI_SECTOR_PREVIOUS;
    return ep7p_ui_ops.event(ui,session,normalized,repeat);
}
