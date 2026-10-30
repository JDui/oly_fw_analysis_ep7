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
 ret [a2],16
.size _ep7_gcc_queue_send_local,.-_ep7_gcc_queue_send_local
