/* Qualified live display owner61032f10 only. Native +436 has a self-prologue
 * of24 and uses owner+92's SHARED iterator at list+16. Preserve that cursor
 * around the lookup, including the absent-ID path. This is not a lifetime lock
 * or a defense against list membership changes/reentrant UI mutation. */
.text
.global _ep7_gcc_ui_find_child
.type _ep7_gcc_ui_find_child,@function
_ep7_gcc_ui_find_child:
 add -12,sp
 mov d0,a0
 mov a0,(4,sp)
 mov (108,a0),d0
 mov d0,(8,sp)
 mov d1,d0
 call ep7_stock_ui_find_child_unresolved,[],0
 mov (4,sp),a1
 mov (8,sp),d0
 mov d0,(108,a1)
 mov a0,d0
 ret [],12
.size _ep7_gcc_ui_find_child,.-_ep7_gcc_ui_find_child
