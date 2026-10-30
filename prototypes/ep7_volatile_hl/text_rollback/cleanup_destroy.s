/* Self-authored GCC callable veneer for exact fresh qualified text subset.
 * Each native target has its OWN prologue and is entered using CALLS.
 * Entry S contains GCC return. Save four callee regs then reserve16;
 * child is at (12,sp)=S-20, separate from native call return at S-32.
 * Context selection/restoration is performed by serialized outer C callbacks.
 */
.text
.global _ep7_gcc_text_cleanup_destroy_unresolved
.type _ep7_gcc_text_cleanup_destroy_unresolved,@function
_ep7_gcc_text_cleanup_destroy_unresolved:
 movm [d2,d3,a2,a3],(sp)
 add -16,sp
 mov d0,(12,sp)
 mov d0,a0
 mov ep7_stock_text_cleanup_unresolved,a1
 calls (a1)
 mov (12,sp),a0
 mov ep7_stock_text_destructor_unresolved,a1
 calls (a1)
 mov a0,a1
 mov (12,sp),a0
 calls (a1)
 ret [d2,d3,a2,a3],32
.size _ep7_gcc_text_cleanup_destroy_unresolved,.-_ep7_gcc_text_cleanup_destroy_unresolved
