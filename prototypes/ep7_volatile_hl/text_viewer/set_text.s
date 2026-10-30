/* Self-authored GCC(d0 widget,d1 text) -> exact native CALL frame.
 * Compile-only; original native entry has no self-prologue, and owns RET24.
 * GCC return at entrySP=S. Reserve12 for separate native return slot;
 * CALL saves four native callee registers and reserves24 => deepestS-36.
 * Native RET restores SP=S-12; final RET[],12 returns via original[S].
 */
.text
.global _ep7_gcc_set_text_unresolved_binding
.type _ep7_gcc_set_text_unresolved_binding,@function
_ep7_gcc_set_text_unresolved_binding:
 add -12,sp
 mov d0,a0
 mov d1,a1
 call ep7_stock_text_setter_unresolved,[d2,d3,a2,a3],24
 ret [],12
.size _ep7_gcc_set_text_unresolved_binding,.-_ep7_gcc_set_text_unresolved_binding
