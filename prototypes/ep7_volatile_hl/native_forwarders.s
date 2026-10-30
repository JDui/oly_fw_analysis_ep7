/* Self-authored compile-only MN10300 native-frame forwarders.
 * NOT GCC C-callable functions. No installed hooks, addresses or firmware bytes.
 * Each caller MUST use the exact register-save/frame tuple documented below.
 * Tail jmp preserves argument registers, MDR, flags and SP at entry; target
 * owns its return ABI and clobbers. No portable callback is called here.
 */
.text
.global ep7_native_get_tid_frame
.type ep7_native_get_tid_frame,@function
/* call ep7_native_get_tid_frame,[a2],4 ; a0=&uint16_out ; d0=status */
ep7_native_get_tid_frame:
 jmp ep7_stock_get_tid_unresolved
.size ep7_native_get_tid_frame,.-ep7_native_get_tid_frame
.global ep7_native_constructor_frame
.type ep7_native_constructor_frame,@function
/* call ...,[d2,d3,a2,a3],44 ; a0=32-byte header; a1=&uint16_error;
 * d0=0 in the admitted caller; result d0=job. */
ep7_native_constructor_frame:
 jmp ep7_stock_constructor_unresolved
.size ep7_native_constructor_frame,.-ep7_native_constructor_frame
.global ep7_native_process_frame
.type ep7_native_process_frame,@function
/* call ...,[d2,a2,a3],24 ; a0=descriptor ; d0=status */
ep7_native_process_frame:
 jmp ep7_stock_process_unresolved
.size ep7_native_process_frame,.-ep7_native_process_frame
.global ep7_native_cleanup_frame
.type ep7_native_cleanup_frame,@function
/* call ...,[a2,a3],24 ; a0=descriptor ; return result not consumed */
ep7_native_cleanup_frame:
 jmp ep7_stock_cleanup_unresolved
.size ep7_native_cleanup_frame,.-ep7_native_cleanup_frame
