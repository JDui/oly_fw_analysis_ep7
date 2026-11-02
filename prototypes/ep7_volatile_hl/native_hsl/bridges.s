/* Exact build1100 native frames. GCC helpers use D0/D1 and stack arguments;
 * native methods retain CALL/CALLS framing, as in the PEN-F editor adapter. */
.text

.global _ep7h_active_get
_ep7h_active_get:
 add -4,sp
 mov 1,d1
 call ep7_stock_h_active_get_unresolved,[d2],8
 ret [],4
.global _ep7h_active_set
_ep7h_active_set:
 add -4,sp
 mov d1,a0
 mov 1,d1
 call ep7_stock_h_active_set_unresolved,[d2],8
 ret [],4
.global _ep7h_stock_value
_ep7h_stock_value:
 add -4,sp
 call ep7_stock_h_raw_get_unresolved,[],4
 ret [],4

/* Existing GUI setter's inner manager CALL, e0/16 at607fa355. */
.global ep7h_set_bridge
ep7h_set_bridge:
 mov d0,d2
 mov d1,d3
 mov a0,a2
 add -16,sp
 call _ep7h_property,[],0
 cmp 0,d0
 blt .Lset_stock
 mov (_ep7h_axis),d0
 sub 1,d0
 cmp 2,d0
 bcc .Lset_stock
 mov d2,d0
 mov d3,d1
 call _ep7h_set,[],0
 add 16,sp
 cmp 1,d0
 bne .Lset_reject
 /* This is the original manager's notifications/finish, after its S write. */
 jmp ep7_stock_h_manager_finish_unresolved
.Lset_reject:
 clr d0
 ret [d2,d3,a2],16
.Lset_stock:
 add 16,sp
 mov d2,d0
 mov d3,d1
 mov a2,a0
 jmp ep7_stock_h_manager_unresolved

/* Property-service vtable CALLS entry. Preserve stock inputs for delegation. */
.macro h_getter name,stock,isdefault
.global \name
\name:
 movm [d2,d3,a2,a3],(sp)
 add -16,sp
 mov d0,d2
 mov d1,d3
 mov a0,a2
 mov a1,a3
 exthu d0
 call _ep7h_property,[],0
 cmp 0,d0
 blt .Lstock\@
 cmp 0,a3
 beq .Lstock\@
 mov (_ep7h_axis),d1
 sub 1,d1
 cmp 2,d1
 bcc .Lstock\@
 .if \isdefault
 clr d0
 .else
 inc d1
 mov d2,d0
 exthu d0
 call _ep7h_value,[],0
 .endif
 mov d0,(a3)
 clr d0
 ret [d2,d3,a2,a3],32
.Lstock\@:
 mov d2,d0
 mov d3,d1
 mov a2,a0
 mov a3,a1
 add 16,sp
 movm (sp),[d2,d3,a2,a3]
 jmp \stock
.endm
h_getter ep7h_get_bridge,ep7_stock_h_get_unresolved,0
h_getter ep7h_default_bridge,ep7_stock_h_default_unresolved,1

/* Common FSM body after original input saves; works for CALL and CALLS. */
.global ep7h_dispatch_bridge
ep7h_dispatch_bridge:
 mov (16,sp),d0
 cmp 0x9016,d0
 bne .Ldispatch_stock
 add -16,sp
 mov (24,sp),d0
 call _ep7h_cycle,[],0
 add 16,sp
 cmp 0,d0
 beq .Ldispatch_stock
 clr d0
 ret [d2,d3,a2,a3],48
.Ldispatch_stock:
 mov (8,sp),a0
 call ep7_stock_h_descriptor_unresolved,[],0
 jmp ep7_stock_h_dispatch_resume_unresolved

.global _ep7h_redraw
_ep7h_redraw:
 add -12,sp
 mov d0,a0
 call ep7_stock_h_viewer_unresolved,[],0
 /* Axis lives outside the original viewer model. Updating its unchanged
  * S-only fields does not dirty the owner/layer cache. Resolve the current
  * native root each time and ask its full entry for whole-root damage. */
 call ep7_stock_h_gui_root_unresolved,[],0
 cmp 0,a0
 beq .Lredraw_request
 mov 0,a1
 mov 1,d0
 call ep7_stock_h_root_invalidate_unresolved,[],0
.Lredraw_request:
 /* Stock request278 uses FFE4 and this 44-byte descriptor. Explicitly send it
  * even when the selected number is unchanged (e.g. three all-zero axes). */
 mov 2,d0
 mov d0,(4,sp)
 mov 0x62473fe8,d0
 mov d0,(8,sp)
 mov 65508,d0
 clr d1
 mov 0,a0
 mov 0,a1
 call ep7_stock_h_draw_unresolved,[d2,d3,a2,a3],36
 ret [],12

.global _ep7h_refresh
_ep7h_refresh:
 add -4,sp
 asl2 d0
 mov .Lrefresh_table,a0
 mov (d0,a0),a0
 calls (a0)
 ret [],4
.balign 4
.Lrefresh_table:
 .long 0x602b5e91,0x602b5eaa,0x602b5ec3,0x602b5edc

/* The sole four-profile wheel loop, table60b40c4c; cursor getter stays stock.
 * Replaces its seven-byte raw-get CALL with the same []/4 frame. */
.global ep7h_wheel_bridge
ep7h_wheel_bridge:
 mov (_ep7h_axis),d1
 cmp 0,d1
 beq .Lwheel_stock
 call _ep7h_value,[],0
 ret [],4
.Lwheel_stock:
 jmp ep7_stock_h_raw_get_unresolved

/* Both screen observer updates still run their complete native body. */
.global ep7h_initial_bridge,ep7h_changed_bridge
ep7h_initial_bridge:
 call ep7h_update,[d2,d3,a2,a3],36
 jmp ep7_stock_h_initial_resume_unresolved
ep7h_changed_bridge:
 call ep7h_update,[d2,d3,a2,a3],36
 jmp ep7_stock_h_changed_resume_unresolved
ep7h_update:
 mov a0,a3
 call ep7_stock_h_update_unresolved,[a2],8
 mov d0,(16,sp)
 /* Native owner bounds do not include our title above the wheel. Dirty the
  * whole native root too, including when a category change hides the title.
  * The 36-byte frame reserves20 locals in addition to16 saved registers. */
 mov a3,a0
 mov 0,a1
 mov 1,d0
 call ep7_stock_h_invalidate_unresolved,[],0
 call ep7_stock_h_gui_root_unresolved,[],0
 cmp 0,a0
 beq .Lupdate_return
 mov 0,a1
 mov 1,d0
 call ep7_stock_h_root_invalidate_unresolved,[],0
.Lupdate_return:
 mov (16,sp),d0
 ret [d2,d3,a2,a3],36
