/* Callable substitute for three qualified calls to603df97d, native[a2,a3],32.
 * Own16 bytes plus original unused scratch preserve d0,d1,a0,a1 at12..27.
 * Original native savesW24..31/returnW32 are untouched. Qualification/retirement
 * finishes before tail delegation at original W; no stock ACK is synthesized. */
.text
.global ep7_native_ack_bridge
.type ep7_native_ack_bridge,@function
ep7_native_ack_bridge:
 add -16,sp
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov a0,d0
 mov sp,a0
 add 16,a0
 mov a0,d1
 call _ep7q_ack_entry,[],0
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 add 16,sp
 jmp ep7_stock_ack_unresolved
.size ep7_native_ack_bridge,.-ep7_native_ack_bridge
