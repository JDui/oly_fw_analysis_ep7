# Native UI event return contract — not a working H/L renderer

Exact firmware 1.1 evidence: `tools/ep7_ui_native_status.py` and
`research/ep7/ui-native-status-1100.json` check 167 instructions in 10 windows.

At the parent virtual-0/container seam, result **1** asks the existing viewer
virtual-0 to refresh (non-AF event, viewer present), then the container returns 0.
Parent results 2/3/4 instead become container results 1/2/3; handler 137 treats
result 1 as its distinct transition path. Wheel result 4 additionally clears timer
535. Thus portable DELEGATE enum 2 cannot be returned as a native result.

The compile-only [bridge](../../prototypes/ep7_volatile_hl/ui_native/) uses internal
256 to invoke the complete original parent with original event arguments. Owned
CHANGED maps to native 1; UNCHANGED/REJECTED to 0. Unknown events and native stock
categories delegate. Its 46-byte assembly preserves native saved registers and
uses the GCC ABI explicitly; neither it nor target C is linked or executed.

This is **not** generic handler-result translation. Native sector handler
`60e21efb` returns 1 even for zero; value handler `60e21cae` returns a child result;
INFO wrapper `60e20cdc` may schedule timer 500 on result 1. Interception bypasses
original event bookkeeping and modal gates, so an admission provider must qualify
context, current copied signed wheel count, parent/session lifetime and owned
renderer readiness. No inferred packet sign or last-event global is acceptable.

The [viewer study](VIEWER_DATA.md) shows that a refresh alone still reads S, not
H/L. Category 4/5 creation/disposal and the new viewer remain unbound. Keep
`renderer_ready` false. Host bridge tests stub admission/raw dispatch and only
prove routing policy; real core/raw-adapter tests are separate. No camera test,
firmware write or installable image is supplied.
