/* Self-authored callable bridges. No stock instructions copied/installed.
 * Outer call603f2722 already owns native[a2,a3],56. Additional owned80 bytes:
 * GCC scratch0..11, spare12..15, saved native inputs16..31, scope32..79.
 * The nested original job call adds56: total extra live stack136 bytes. */
.text
.global ep7_native_worker_scope_bridge
.type ep7_native_worker_scope_bridge,@function
ep7_native_worker_scope_bridge:
 add -80,sp
 mov d0,(16,sp)
 mov d1,(20,sp)
 mov a0,(24,sp)
 mov a1,(28,sp)
 mov sp,a0
 mov a0,d1
 add 32,a0
 mov a0,d0
 call _ep7q_worker_scope_entry,[],0
 mov (16,sp),d0
 mov (20,sp),d1
 mov (24,sp),a0
 mov (28,sp),a1
 call ep7_stock_worker_job_unresolved,[a2,a3],56
.global _ep7_worker_native_return
_ep7_worker_native_return:
 add 80,sp
 ret [a2,a3],56
.size ep7_native_worker_scope_bridge,.-ep7_native_worker_scope_bridge

/* Exact constructor allocation call603537f3: native[],4; input size d0,
 * returned allocation a0. Keep original W for qualification, then reserve16
 * for the GCC outgoing area without touching the native return at W+4. */
.global ep7_native_worker_allocate_bridge
.type ep7_native_worker_allocate_bridge,@function
ep7_native_worker_allocate_bridge:
 mov sp,a0
 mov a0,d1
 add -16,sp
 call _ep7q_worker_allocate_entry,[],0
 add 16,sp
 ret [],4
.size ep7_native_worker_allocate_bridge,.-ep7_native_worker_allocate_bridge

/* GCC unsigned size -> native60022700. BOTH pointer result ABIs use a0;
 * a GCC pointer result must not be inferred from the integer result d0. */
.global _ep7_gcc_job_allocate
.type _ep7_gcc_job_allocate,@function
_ep7_gcc_job_allocate:
 movm [a2],(sp)
 add -12,sp
 call ep7_stock_job_allocate_unresolved,[],4
 ret [a2],16
.size _ep7_gcc_job_allocate,.-_ep7_gcc_job_allocate

/* Preserve all four native input registers and original native24-byte frame.
 * Own16 + old scratch0..11 give saved input slots12..27; original saves12..23
 * and RA24 are untouched. C observer returns before tail delegation. */
.global ep7_native_worker_process_bridge
.type ep7_native_worker_process_bridge,@function
ep7_native_worker_process_bridge:
 add -16,sp
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov a0,d0
 mov sp,a0
 add 16,a0
 mov a0,d1
 call _ep7q_worker_process_entry,[],0
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 add 16,sp
 jmp ep7_stock_worker_process_unresolved
.size ep7_native_worker_process_bridge,.-ep7_native_worker_process_bridge

.global ep7_native_worker_cleanup_bridge
.type ep7_native_worker_cleanup_bridge,@function
ep7_native_worker_cleanup_bridge:
 add -16,sp
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov a0,d0
 mov sp,a0
 add 16,a0
 mov a0,d1
 call _ep7q_worker_cleanup_entry,[],0
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 add 16,sp
 jmp ep7_stock_worker_cleanup_unresolved
.size ep7_native_worker_cleanup_bridge,.-ep7_native_worker_cleanup_bridge
