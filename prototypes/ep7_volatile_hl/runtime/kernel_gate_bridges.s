/* Inline candidates after native critical entry and non-null queue lookup.
 * Own40 below native W. Preserve d0/d1/a0/a1/d2/MDR; GCC preserves d3/a2/a3.
 * Saved bytes12..35 remain BELOW W even for delete's frame24/mask16.
 * GCC return/flush area0..11 is disjoint. No native API call inside the gates.
 * G6 must install all three with complete displaced instructions/relocations. */
.text
.macro save_gate
 add -40,sp
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov d2,(32,sp)
 mov mdr,d2
 mov d2,(28,sp)
.endm
.macro restore_gate
 mov (28,sp),d2
 mov d2,mdr
 mov (32,sp),d2
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 add 40,sp
.endm
.global ep7_native_queue_receive_gate
.type ep7_native_queue_receive_gate,@function
ep7_native_queue_receive_gate:
 save_gate
 mov sp,a0
 add 40,a0
 mov a0,d0
 mov a2,d1
 call _ep7r_native_receive_gate,[],0
 cmp 0,d0
 beq .Lreceive_rejected
 restore_gate
 /* Replay60036d3c..60036d46 exactly. */
 mov (0x8050),d0
 asl2 d0
 mov -1880096764,a0
 jmp ep7_stock_receive_gate_continue_unresolved
.Lreceive_rejected:
 restore_gate
 mov -42,d0
 jmp ep7_stock_receive_gate_error_unresolved
.size ep7_native_queue_receive_gate,.-ep7_native_queue_receive_gate
.global ep7_native_queue_send_gate
.type ep7_native_queue_send_gate,@function
ep7_native_queue_send_gate:
 save_gate
 mov sp,a0
 add 40,a0
 mov a0,d0
 mov a2,d1
 call _ep7r_native_send_gate,[],0
 cmp 0,d0
 beq .Lsend_rejected
 restore_gate
 /* Replay60036f93..60036f99 exactly. */
 mov (20,sp),d0
 mov 20,d3
 add a2,d3
 jmp ep7_stock_send_gate_continue_unresolved
.Lsend_rejected:
 restore_gate
 mov -42,d0
 jmp ep7_stock_send_gate_error_unresolved
.size ep7_native_queue_send_gate,.-ep7_native_queue_send_gate
.global ep7_native_queue_delete_observer
.type ep7_native_queue_delete_observer,@function
ep7_native_queue_delete_observer:
 save_gate
 mov a3,d0
 call _ep7r_native_delete_observer,[],0
 restore_gate
 /* Replay60031072..60031078 before backing free or waiter wakeups. */
 mov 20,a0
 add a3,a0
 movbu (a0),d0
 jmp ep7_stock_delete_gate_continue_unresolved
.size ep7_native_queue_delete_observer,.-ep7_native_queue_delete_observer
