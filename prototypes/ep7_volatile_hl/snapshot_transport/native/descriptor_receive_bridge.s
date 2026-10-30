/* Five exact CALL sites, all [d2,d3,a2,a3],44:
 * dual relay603ef8b5/8d2/8fd/91a and shared helper603dfa04.
 * W+12..27 stores the four original arguments; saved native registers start28.
 * Unsupported nonexpanded queues tail-delegate at unchanged W with ALL four
 * arguments restored, preserving original timeout/trace words W+48/+52.
 * Expanded4c/ab/4f never take that fallback unless their layout was admitted. */
.text
.global ep7_native_descriptor_receive_bridge
.type ep7_native_descriptor_receive_bridge,@function
ep7_native_descriptor_receive_bridge:
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov sp,a0
 add 12,a0
 mov a0,d0
 mov sp,a1
 mov a1,d1
 call _ep7q_descriptor_receive_entry,[],0
 cmp 256,d0
 bne .Lreceived
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 jmp ep7_stock_receive_wrapper_unresolved
.Lreceived:
 ret [d2,d3,a2,a3],44
.size ep7_native_descriptor_receive_bridge,.-ep7_native_descriptor_receive_bridge
