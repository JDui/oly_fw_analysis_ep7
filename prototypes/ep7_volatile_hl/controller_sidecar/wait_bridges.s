/* Fixed waiting-list seams only. GCC transactions hold the capture guard across
 * the original list operation. Native inputs/D2/MDR survive the C helper;
 * only native result D0 is replaced with the actual stock operation result. */
.text
.macro wait_save
 add -40,sp
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov d2,(32,sp)
 mov mdr,d2
 mov d2,(28,sp)
.endm
.macro wait_restore
 mov (28,sp),d2
 mov d2,mdr
 mov (32,sp),d2
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 add 40,sp
.endm
.global ep7_native_wait_enqueue
.type ep7_native_wait_enqueue,@function
ep7_native_wait_enqueue:
 wait_save
 mov d0,d1
 mov a0,d0
 call _ep7cn_wait_enqueue,[],0
 mov d0,(12,sp)
 wait_restore
 ret [],8
.size ep7_native_wait_enqueue,.-ep7_native_wait_enqueue
.global ep7_native_wait_pop
.type ep7_native_wait_pop,@function
ep7_native_wait_pop:
 wait_save
 mov a0,d0
 mov sp,a0
 add 40,a0
 mov a0,d1
 call _ep7cn_wait_pop,[],0
 mov d0,(12,sp)
 wait_restore
 ret [],24
.size ep7_native_wait_pop,.-ep7_native_wait_pop
.global ep7_native_wait_reset
.type ep7_native_wait_reset,@function
ep7_native_wait_reset:
 wait_save
 call _ep7cn_wait_reset,[],0
 wait_restore
 /* Initializer needs the original incoming SP+8 tag argument. */
 jmp ep7_stock_wait_initialize_unresolved
.size ep7_native_wait_reset,.-ep7_native_wait_reset

/* Three reviewed CALLs to602ac5d0,[d2],8. Its native input registers are unused.
 * S=entrySP-64: outgoing0..15; scope24..55. The inner8-byte frame and pop24
 * frame place this scope at popW+56; metadata32/send48 place it at sendW+112. */
.global ep7_native_wait_scope
.type ep7_native_wait_scope,@function
ep7_native_wait_scope:
 add -64,sp
 mov sp,a0
 add 24,a0
 mov a0,d0
 clr d1
 mov d1,(12,sp)
 call _ep7q_capture_scope_init,[],0
 call ep7_stock_wait_service_unresolved,[d2],8
.global _ep7_wait_scope_native_return
_ep7_wait_scope_native_return:
 add 64,sp
 ret [d2],8
.size ep7_native_wait_scope,.-ep7_native_wait_scope

.global _ep7_gcc_wait_enqueue
.type _ep7_gcc_wait_enqueue,@function
_ep7_gcc_wait_enqueue:
 movm [a2],(sp)
 add -12,sp
 mov d0,a0
 mov d1,d0
 call ep7_stock_associated_enqueue_unresolved,[],8
 ret [a2],16
.size _ep7_gcc_wait_enqueue,.-_ep7_gcc_wait_enqueue
.global _ep7_gcc_wait_pop
.type _ep7_gcc_wait_pop,@function
_ep7_gcc_wait_pop:
 movm [a2],(sp)
 add -12,sp
 mov d0,a0
 call ep7_stock_wait_pop_unresolved,[],24
 ret [a2],16
.size _ep7_gcc_wait_pop,.-_ep7_gcc_wait_pop
