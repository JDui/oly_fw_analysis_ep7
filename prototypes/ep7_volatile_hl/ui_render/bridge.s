/* Full native viewer virtual0, original self-frame36. Own56: outgoing0..11,
 * original arguments/results12..27, held token28, viewer32, saved f0 at40..55. */
.text
.global ep7_native_ui_viewer_bridge
.type ep7_native_ui_viewer_bridge,@function
ep7_native_ui_viewer_bridge:
 movm [d2,d3,a2,a3],(sp)
 add -40,sp
 mov a0,(12,sp)
 mov d0,(16,sp)
 mov d1,(20,sp)
 mov a1,(24,sp)
 mov a0,(32,sp)
 mov a0,d0
 call _ep7v_draw_begin,[],0
 mov d0,(28,sp)
 mov (12,sp),a0
 mov (16,sp),d0
 mov (20,sp),d1
 mov (24,sp),a1
 call ep7_stock_mvc_viewer_draw_unresolved,[],0
 mov a0,(12,sp)
 mov d0,(16,sp)
 mov d1,(20,sp)
 mov a1,(24,sp)
 mov (32,sp),d0
 mov (28,sp),d1
 call _ep7v_draw_end,[],0
 mov (12,sp),a0
 mov (16,sp),d0
 mov (20,sp),d1
 mov (24,sp),a1
 ret [d2,d3,a2,a3],56
.size ep7_native_ui_viewer_bridge,.-ep7_native_ui_viewer_bridge
