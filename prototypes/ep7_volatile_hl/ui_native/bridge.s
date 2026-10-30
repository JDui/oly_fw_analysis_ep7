/* Self-authored callable native virtual0 -> GCC router bridge. Compile only.
 * Entry is native CALLS with d0=event,d1=parameter,a0=parent. Not a midfunction
 * patch. The original full parent implementation has its own prologue.
 * Stack at entry S: RA[S]; MOVM saves four registers in S-16..S-4;
 * reserve32 gives S-48. GCC outgoing0..8; input12..23; savedregs32..47.
 */
.text
.global ep7_native_ui_event_bridge
.type ep7_native_ui_event_bridge,@function
ep7_native_ui_event_bridge:
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov sp,a0
 add 12,a0
 mov a0,d0
 call _ep7_gcc_ui_route,[],0
 cmp 256,d0
 bne .Ldone
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov ep7_stock_ui_event_unresolved,a1
 calls (a1)
.Ldone:
 ret [d2,d3,a2,a3],48
.size ep7_native_ui_event_bridge,.-ep7_native_ui_event_bridge
