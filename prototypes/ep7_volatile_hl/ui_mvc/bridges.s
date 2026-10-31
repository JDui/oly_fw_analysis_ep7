/* Native full-method entry/retirement bridges. Entry owns48, outgoing0..11,
 * original arguments/results12..27, saved f0 at32..47. Entry inputs are kept
 * across begin; original result A0 is passed to complete after publication. */
.text
.global ep7_native_mvc_gui_entry_bridge
.type ep7_native_mvc_gui_entry_bridge,@function
ep7_native_mvc_gui_entry_bridge:
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 mov a0,(12,sp)
 mov d0,(16,sp)
 mov d1,(20,sp)
 mov a1,(24,sp)
 call _ep7m_gui_begin,[],0
 mov (12,sp),a0
 mov (16,sp),d0
 mov (20,sp),d1
 mov (24,sp),a1
 call ep7_stock_mvc_gui_entry_unresolved,[],0
 mov a0,(12,sp)
 mov d0,(16,sp)
 mov d1,(20,sp)
 mov a1,(24,sp)
 mov a0,d0
 call _ep7m_gui_complete,[],0
 mov (12,sp),a0
 mov (16,sp),d0
 mov (20,sp),d1
 mov (24,sp),a1
 ret [d2,d3,a2,a3],48
.size ep7_native_mvc_gui_entry_bridge,.-ep7_native_mvc_gui_entry_bridge

.macro retire name,callback,target
.global \name
.type \name,@function
\name:
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 mov a0,(12,sp)
 mov d0,(16,sp)
 mov d1,(20,sp)
 mov a1,(24,sp)
 mov a0,d0
 call \callback,[],0
 mov (12,sp),a0
 mov (16,sp),d0
 mov (20,sp),d1
 mov (24,sp),a1
 call \target,[],0
 ret [d2,d3,a2,a3],48
.size \name,.-\name
.endm
retire ep7_native_mvc_gui_exit_bridge,_ep7m_before_gui_exit,ep7_stock_mvc_gui_exit_unresolved
retire ep7_native_mvc_parent_destroy_bridge,_ep7m_before_parent_destroy,ep7_stock_mvc_parent_destroy_unresolved
retire ep7_native_mvc_viewer_destroy_bridge,_ep7m_before_viewer_destroy,ep7_stock_mvc_viewer_destroy_unresolved
