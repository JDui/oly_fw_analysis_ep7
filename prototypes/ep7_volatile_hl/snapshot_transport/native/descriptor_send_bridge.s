/* Exact call603dfaa1 to stock wrapper603eeba4: [d2,d3,a2],36.
 * W+12..23 saves d0/a0/a1; original d1 is statically300. Native saves24..35,
 * returnW+36, timeoutW+40 and traceW+44 remain untouched. Unknown paths use
 * stock300-byte send at unchanged W. They never read an unproved trailer. */
.text
.global ep7_native_descriptor_send_bridge
.type ep7_native_descriptor_send_bridge,@function
ep7_native_descriptor_send_bridge:
 mov d0,(12,sp)
 mov a0,(16,sp)
 mov a1,(20,sp)
 mov sp,a0
 add 12,a0
 mov a0,d0
 mov sp,a1
 mov a1,d1
 call _ep7q_descriptor_send_entry,[],0
 cmp 256,d0
 bne .Lsent
 mov (12,sp),d0
 mov 300,d1
 mov (16,sp),a0
 mov (20,sp),a1
 jmp ep7_stock_send_wrapper_unresolved
.Lsent:
 ret [d2,d3,a2],36
.size ep7_native_descriptor_send_bridge,.-ep7_native_descriptor_send_bridge
