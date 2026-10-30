/* GCC callable candidate for raw600313ef timed delay, native[d2,a2,a3],16.
 * Exactly one native time unit; unit duration/tick rounding not inferred.
 * Do not substitute tslp_tsk60036e23, which consumes pending wakeup count.
 * Ordinary wait-capable task only, no core lock held; result remains verbatim.
 * Callable object only: not a complete poison/recovery policy or installation. */
.text
.global _ep7_gcc_task_delay_one
.type _ep7_gcc_task_delay_one,@function
_ep7_gcc_task_delay_one:
 movm [a2],(sp)
 add -12,sp
 mov 1,d0
 call ep7_stock_task_delay_unresolved,[d2,a2,a3],16
 ret [a2],16
.size _ep7_gcc_task_delay_one,.-_ep7_gcc_task_delay_one
