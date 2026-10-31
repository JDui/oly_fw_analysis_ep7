/* GCC two-pointer arguments -> actual native attach and text bind entries.
 * Exact display owner61032f10 and fresh/attached text60faec7c are prerequisites.
 * Attach owns native CALL[a2],8; bind owns a MOVM/add12 self-prologue. */
.text
.global _ep7_gcc_ui_attach
.type _ep7_gcc_ui_attach,@function
_ep7_gcc_ui_attach:
 add -4,sp
 mov d0,a0
 mov d1,a1
 call ep7_stock_ui_attach_unresolved,[a2],8
 ret [],4
.size _ep7_gcc_ui_attach,.-_ep7_gcc_ui_attach

.global _ep7_gcc_text_bind
.type _ep7_gcc_text_bind,@function
_ep7_gcc_text_bind:
 add -4,sp
 mov d0,a0
 mov d1,a1
 call ep7_stock_text_bind_unresolved,[],0
 ret [],4
.size _ep7_gcc_text_bind,.-_ep7_gcc_text_bind
