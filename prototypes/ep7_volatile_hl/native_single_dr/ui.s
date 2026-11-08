/* Build1100 curve edges. Child hash branches inherit the stock frame. */
.text

.global ep7dr_ui_info_bridge
ep7dr_ui_info_bridge:
 mov (16,sp),d0
 call _ep7dr_ui_info,[],0
 cmp 0,d0
 beq .Lstock_info
 jmp ep7dr_stock_ui_child_redraw_unresolved
.Lstock_info:
 jmp ep7dr_stock_ui_info_unresolved

.global ep7dr_ui_reset_bridge
ep7dr_ui_reset_bridge:
 mov (16,sp),d0
 call _ep7dr_ui_reset,[],0
 cmp 0,d0
 beq .Lstock_reset
 cmp 2,d0
 beq .Lreset_redraw
 mov 0,a3
 jmp ep7dr_stock_ui_child_return_unresolved
.Lreset_redraw:
 jmp ep7dr_stock_ui_child_redraw_unresolved
.Lstock_reset:
 jmp ep7dr_stock_ui_reset_unresolved

.global ep7dr_ui_touch_bridge
ep7dr_ui_touch_bridge:
 mov (16,sp),d0
 call _ep7dr_ui_open,[],0
 cmp 0,d0
 beq .Lstock_touch
 mov 0,a3
 jmp ep7dr_stock_ui_child_return_unresolved
.Lstock_touch:
 jmp ep7dr_stock_ui_touch_unresolved

.macro ep7dr_ui_wheel name, original, backwards
.global \name
\name:
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 mov d0,d2
 mov d1,d3
 mov a0,a2
 mov a1,a3
 mov a0,d0
 .if \backwards
 not d1
 inc d1
 .endif
 call _ep7dr_ui_dial,[],0
 cmp 0,d0
 beq .Lstock_wheel\@
 cmp 2,d0
 beq .Lwheel_redraw\@
 clr d0
 ret [d2,d3,a2,a3],20
.Lwheel_redraw\@:
 mov 1,d0
 ret [d2,d3,a2,a3],20
.Lstock_wheel\@:
 mov d2,d0
 mov d3,d1
 mov a2,a0
 mov a3,a1
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 jmp \original
.endm
ep7dr_ui_wheel ep7dr_ui_dial_9031_bridge,ep7dr_stock_ui_dial_9031_unresolved,0
ep7dr_ui_wheel ep7dr_ui_dial_9032_bridge,ep7dr_stock_ui_dial_9032_unresolved,1

.global ep7dr_ui_draw_bridge
ep7dr_ui_draw_bridge:
 mov a3,d0
 call _ep7dr_ui_draw,[],0
 cmp 0,d0
 bne .Lpublish
 mov a3,a0
 mov a3,a1
 call ep7dr_stock_ui_curve_draw_unresolved,[d2,d3,a2,a3],52
.Lpublish:
 jmp ep7dr_stock_ui_viewer_publish_unresolved

.global ep7dr_ui_rebuild_bridge
ep7dr_ui_rebuild_bridge:
 /* Revoke the exact current child before stock releases or reuses it. */
 mov (80,a0),d1
 mov (_ep7dr_ui_child),d0
 cmp d1,d0
 bne .Lrebuild
 clr d0
 mov d0,(_ep7dr_ui_child)
.Lrebuild:
 mov a0,d3
 clr d0
 mov d0,(4,sp)
 jmp ep7dr_stock_ui_rebuild_resume_unresolved

.global ep7dr_ui_destroy_bridge
ep7dr_ui_destroy_bridge:
 mov (80,a0),d1
 mov (_ep7dr_ui_child),d0
 cmp d1,d0
 bne .Ldestroy
 clr d0
 mov d0,(_ep7dr_ui_child)
.Ldestroy:
 jmp ep7dr_stock_ui_destroy_unresolved

.global ep7dr_ui_factory_bridge
ep7dr_ui_factory_bridge:
 cmp 14,d0
 bne .Lstock_factory
 movhu (a0),d1
 cmp 383,d1
 bne .Lstock_factory
 mov 1,d1
 mov d1,(_ep7dr_ui_building_curve)
 call ep7dr_stock_ui_factory_unresolved,[d2,d3,a2],16
 clr d1
 mov d1,(_ep7dr_ui_building_curve)
 ret [d2,d3,a2],16
.Lstock_factory:
 jmp ep7dr_stock_ui_factory_unresolved

.global ep7dr_ui_restore_bridge
ep7dr_ui_restore_bridge:
 mov a3,d0
 call _ep7dr_ui_start_first_page,[],0
 cmp 0,d0
 bne .Lfirst_page
 mov (24,sp),d0
 cmp 3200,d0
 beq .Lfirst_page
 jmp ep7dr_stock_ui_ctor_restore_unresolved
.Lfirst_page:
 jmp ep7dr_stock_ui_ctor_first_page_unresolved
