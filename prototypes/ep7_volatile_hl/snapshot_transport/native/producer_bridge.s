/* Exact native producer call602ac3de,[d2,a2,a3],32 only.
 * Additional64-byte scope frame S: outgoing0..15, original ID16, associated20,
 * scope24..55. Native metadata producer gets a separate32-byte incoming frame;
 * its send48 entry W=S-80 can reach this owned scope at W+104. */
.text
.global ep7_native_capture_scope_bridge
.type ep7_native_capture_scope_bridge,@function
ep7_native_capture_scope_bridge:
 add -64,sp
 mov d0,(16,sp)
 mov a2,d1
 mov d1,(20,sp)
 mov sp,a0
 add 24,a0
 mov a0,(12,sp)
 call _ep7q_capture_scope_entry,[],0
 mov (16,sp),d0
 call ep7_stock_kind19_metadata_producer_unresolved,[d2,a2,a3],32
.global _ep7_capture_scope_native_return
_ep7_capture_scope_native_return:
 add 64,sp
 ret [d2,a2,a3],32
.size ep7_native_capture_scope_bridge,.-ep7_native_capture_scope_bridge

/* Exact metadata command call602ac869,[d2,d3],48 only. Preserve all four native
 * inputs at W+12..27; original captureID d2 is saved by native CALL at W+44.
 * Unknown/alternate producers tail-delegate original16-byte command at same W. */
.global ep7_native_producer_send_bridge
.type ep7_native_producer_send_bridge,@function
ep7_native_producer_send_bridge:
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov sp,a0
 add 12,a0
 mov a0,d0
 mov sp,a1
 mov a1,d1
 call _ep7q_producer_entry,[],0
 cmp 256,d0
 bne .Lproduced
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 jmp ep7_stock_command_send_unresolved
.Lproduced:
 ret [d2,d3],48
.size ep7_native_producer_send_bridge,.-ep7_native_producer_send_bridge
