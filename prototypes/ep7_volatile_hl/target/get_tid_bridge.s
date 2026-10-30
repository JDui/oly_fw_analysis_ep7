/* Self-authored GCC13.4 MN10300 -> audited native get_tid bridge.
 * Compile/assemble ONLY. Native target deliberately unresolved.
 * C declaration: int ep7_gcc_get_tid(unsigned short *out);
 * Valid writable aligned out is required; on failure do not consume *out.
 * Uses the exact generated probe_query nonleaf envelope, not native tail ABI.
 */
.text
.global _ep7_gcc_get_tid
.type _ep7_gcc_get_tid,@function
_ep7_gcc_get_tid:
 movm [a2],(sp)
 add -12,sp
 mov d0,a0
 call ep7_stock_get_tid_unresolved,[a2],4
 ret [a2],16
.size _ep7_gcc_get_tid,.-_ep7_gcc_get_tid
