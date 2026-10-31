/* Self-authored GCC13.4 MN10300 -> native local raw queue ABI.
 * Callable entry only. Exact-build planned bindings: receive60036c8e/send60036ede.
 * No target link/execution/install here; symbols deliberately unresolved.
 * GCC words1/2=d0/d1, word3 at entrySP+12, word4 at entrySP+16.
 * movm/add reserve16, so the extra arguments are now at SP+28/+32.
 * d0 result is retained verbatim, including receive's actual length. */
.text
.global _ep7_gcc_queue_receive_local
.type _ep7_gcc_queue_receive_local,@function
_ep7_gcc_queue_receive_local:
 movm [a2],(sp)
 add -12,sp
 mov d1,a0
 mov (28,sp),d1
 call ep7_stock_queue_receive_local_unresolved,[d2,d3,a2,a3],32
.global _ep7_queue_receive_native_return
_ep7_queue_receive_native_return:
 ret [a2],16
.size _ep7_gcc_queue_receive_local,.-_ep7_gcc_queue_receive_local
.global _ep7_gcc_queue_send_local
.type _ep7_gcc_queue_send_local,@function
_ep7_gcc_queue_send_local:
 movm [a2],(sp)
 add -12,sp
 mov d1,a0
 mov (28,sp),d1
 mov (32,sp),a1
 call ep7_stock_queue_send_local_unresolved,[d2,d3,a2,a3],40
.global _ep7_queue_raw_send_native_return
_ep7_queue_raw_send_native_return:
 ret [a2],16
.size _ep7_gcc_queue_send_local,.-_ep7_gcc_queue_send_local

/* Sending must retain600514b6 post-send notification60051078. Its native input
 * is a pointer/count pair at a0, timeout in d1, handle in d0; normalized result.
 * Own24-byte envelope: pair at12/16, saved a2 at20. Incoming GCC words3/4
 * therefore arrive at36/40. Named wrapper CALL frame48 preserves its hooks. */
.global _ep7_gcc_queue_send_preserving_hooks
.type _ep7_gcc_queue_send_preserving_hooks,@function
_ep7_gcc_queue_send_preserving_hooks:
 movm [a2],(sp)
 add -20,sp
 mov d1,(12,sp)
 mov (36,sp),d1
 mov d1,(16,sp)
 mov sp,a0
 add 12,a0
 mov (40,sp),d1
 call ep7_stock_queue_send_preserving_unresolved,[d2,d3,a2,a3],48
.global _ep7_queue_named_send_native_return
_ep7_queue_named_send_native_return:
 ret [a2],24
.size _ep7_gcc_queue_send_preserving_hooks,.-_ep7_gcc_queue_send_preserving_hooks
