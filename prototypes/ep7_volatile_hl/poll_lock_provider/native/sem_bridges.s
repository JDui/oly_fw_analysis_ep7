/* Self-authored GCC13.4 MN10300 -> native raw semaphore ABI candidates.
 * Compile/assemble only. No fixed addresses, linking, invocation or installation.
 * GCC handle d0 matches native; poll forces d1=0; status returns in d0.
 * Use callable-function ABI only, not arbitrary mid-instruction hooks. */
.text
.global _ep7_gcc_raw_sem_poll
.type _ep7_gcc_raw_sem_poll,@function
_ep7_gcc_raw_sem_poll:
 movm [a2],(sp)
 add -12,sp
 clr d1
 call ep7_stock_raw_sem_wait_unresolved,[d2,d3,a2,a3],24
 ret [a2],16
.size _ep7_gcc_raw_sem_poll,.-_ep7_gcc_raw_sem_poll
.global _ep7_gcc_raw_sem_signal
.type _ep7_gcc_raw_sem_signal,@function
_ep7_gcc_raw_sem_signal:
 movm [a2],(sp)
 add -12,sp
 call ep7_stock_raw_sem_signal_unresolved,[d2,d3,a2],16
 ret [a2],16
.size _ep7_gcc_raw_sem_signal,.-_ep7_gcc_raw_sem_signal
