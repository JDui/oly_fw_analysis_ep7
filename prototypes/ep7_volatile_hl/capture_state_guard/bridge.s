/* Self-authored, native CALL [d2,d3,a2,a3],32 at BOTH reviewed sites only.
 * Incoming saved registers occupy SP+16..28; do not use those as locals.
 * No installer/global service detour/caller stack arguments. */
.text
.global ep7_native_state_service_bridge
.type ep7_native_state_service_bridge,@function
ep7_native_state_service_bridge:
 call ep7_stock_state_service_unresolved,[d2,d3,a2,a3],32
 add -32,sp
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov mdr,d2
 mov d2,(28,sp)
 call _ep7_gcc_state_transition_observer,[],0
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 mov (28,sp),d2
 mov d2,mdr
 add 32,sp
 ret [d2,d3,a2,a3],32
.size ep7_native_state_service_bridge,.-ep7_native_state_service_bridge
