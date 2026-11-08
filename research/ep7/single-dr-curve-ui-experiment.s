/* Native CPU probe payload. No camera addresses for code or storage placement. */
.text
.set hdr_owner, 0x18f00000
.set hdr_level, 0x18f00004
.set constructing_curve, 0x18f00008

/* A0 is the child. Leave it and D1 intact. D0/A1 are scratch. The prototype
 * handles the exact COLOR1 scope used by the event fixture. */
is_current_curve:
 mov (0x61fb2564),a1
 cmp 0,a1
 beq .Lnot_curve
 movbu (a1),d0
 cmp 4,d0
 bne .Lnot_curve
 movbu (1,a1),d0
 cmp 29,d0
 bne .Lnot_curve
 mov (0x61fc436c),a1
 cmp 0,a1
 beq .Lnot_curve
 mov (a1),a1
 cmp 0,a1
 beq .Lnot_curve
 mov (a1),d0
 cmp 0x6118957c,d0
 bne .Lnot_curve
 mov (76,a1),d0
 mov (80,a1),a1
 cmp a0,a1
 bne .Lnot_curve
 cmp 0,d0
 beq .Lnot_curve
 mov d0,a1
 movhu (86,a1),d0
 cmp 3,d0
 bne .Lnot_curve
 mov (a0),d0
 cmp 0x61159ea8,d0
 bne .Lnot_curve
 movhu (236,a0),d0
 cmp 383,d0
 bne .Lnot_curve
 movhu (220,a0),d0
 cmp 2,d0
 bne .Lnot_curve
 mov (216,a0),d0
 cmp 0x611595e0,d0
 bne .Lnot_curve
 mov 1,d0
 retf [],0
.Lnot_curve:
 clr d0
 retf [],0

/* Call only after the caller has established the native event/viewer context. */
is_hdr_page:
 add -4,sp
 cmp 0,a0
 beq .Lnot_hdr
 mov (hdr_owner),a1
 cmp a0,a1
 bne .Lnot_hdr
 call is_current_curve,[],0
 cmp 0,d0
 beq .Lnot_hdr
 movhu (222,a0),d0
 cmp 1,d0
 bne .Lnot_hdr
 ret [],4
.Lnot_hdr:
 clr d0
 ret [],4

.global experiment_info
experiment_info:
 mov (16,sp),a0
 call is_current_curve,[],0
 cmp 1,d0
 bne .Lstock_info
 movhu (222,a0),d0
 cmp 1,d0
 bne .Lstock_info
 mov (hdr_owner),a1
 cmp a0,a1
 beq .Lexit_hdr
 mov a0,(hdr_owner)
 jmp stock_child_redraw
.Lexit_hdr:
 clr d0
 mov d0,(hdr_owner)
.Lstock_info:
 jmp stock_info

.macro wheel name, original, backwards
.global \name
\name:
 movm [d2,a2],(sp)
 add -4,sp
 mov a1,a2
 mov d0,d2
 call is_hdr_page,[],0
 cmp 1,d0
 bne .Lstock_wheel\@
 .if \backwards
 not d1
 inc d1
 .endif
 mov (hdr_level),d0
 cmp 0,d1
 beq .Lno_change\@
 blt .Ldecrease\@
 cmp 2,d0
 bge .Lno_change\@
 inc d0
 bra .Lstore\@
.Ldecrease\@:
 cmp 0,d0
 beq .Lno_change\@
 add -1,d0
.Lstore\@:
 mov d0,(hdr_level)
 mov 1,d0
 ret [d2,a2],12
.Lno_change\@:
 clr d0
 ret [d2,a2],12
.Lstock_wheel\@:
 mov d2,d0
 mov a2,a1
 add 4,sp
 movm (sp),[d2,a2]
 jmp \original
.endm
wheel experiment_dial_9031,stock_dial_9031,0
wheel experiment_dial_9032,stock_dial_9032,1

.global experiment_reset
experiment_reset:
 mov (16,sp),a0
 call is_hdr_page,[],0
 cmp 1,d0
 bne .Lstock_reset
 clr d0
 mov d0,(hdr_level)
 jmp stock_child_redraw
.Lstock_reset:
 jmp stock_reset

.global experiment_touch
experiment_touch:
 mov (16,sp),a0
 call is_hdr_page,[],0
 cmp 1,d0
 bne .Lstock_touch
 jmp stock_child_return
.Lstock_touch:
 jmp stock_touch

.global experiment_draw
experiment_draw:
 mov (392,a3),a0
 call is_hdr_page,[],0
 cmp 1,d0
 bne .Lstock_draw
 /* Keep the native descriptor type. Skip just its curve-specific fields,
  * which the viewer already cleared. Actual display output is a boundary. */
 mov 13,d0
 mov d0,(340,a3)
 jmp stock_viewer_publish
.Lstock_draw:
 mov a3,a0
 mov a3,a1
 call stock_curve_draw,[d2,d3,a2,a3],52
 jmp stock_viewer_publish

.global experiment_content_factory
experiment_content_factory:
 clr d1
 mov d1,(hdr_owner)
 cmp 14,d0
 bne .Lstock_content
 mov 1,d1
 mov d1,(constructing_curve)
 call stock_factory,[d2,d3,a2],16
 clr d1
 mov d1,(constructing_curve)
 ret [d2,d3,a2],16
.Lstock_content:
 jmp stock_factory

.global experiment_restore_page
experiment_restore_page:
 mov (constructing_curve),d0
 cmp 1,d0
 beq .Lreset_page
 mov (24,sp),d0
 cmp 3200,d0
 beq .Lreset_page
 jmp stock_ctor_restore
.Lreset_page:
 jmp stock_ctor_first_page
