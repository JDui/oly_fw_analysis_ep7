/* GCC D0 viewer to full original native method, which owns its 36-byte frame. */
.text
.global _ep7_gcc_ui_draw_original
.type _ep7_gcc_ui_draw_original,@function
_ep7_gcc_ui_draw_original:
 add -4,sp
 mov d0,a0
 call ep7_stock_mvc_viewer_draw_unresolved,[],0
 ret [],4
.size _ep7_gcc_ui_draw_original,.-_ep7_gcc_ui_draw_original
