#ifndef EP7P_UI_RAW_H
#define EP7P_UI_RAW_H
#include "ep7p_ui.h"
/* These messages are local logical events, NOT physical front/rear dial IDs.
 * Caller must supply a stable copied FULL signed wheel delta associated with
 * THIS event under a separately qualified ordering/lifetime contract. Never
 * substitute native packet d1 or reread a shared global asynchronously.
 * Passing this struct does not establish freshness or native UI installation. */
struct ep7p_ui_raw_event {
    uint32_t local_event;
    int32_t copied_full_delta;
};
/* Separate from EP7_UI_CHANGED=1: the caller retains the original stock event.
 * Delegation does not call native code. Only invoke this adapter for independently
 * owned H/L sessions; stock categories0..3 remain outside the adapter. */
#define EP7P_UI_RAW_DELEGATE 2
int ep7p_ui_raw_dispatch(ep7p_ui *, struct ep7_ui_session,
                         const struct ep7p_ui_raw_event *);
#endif
