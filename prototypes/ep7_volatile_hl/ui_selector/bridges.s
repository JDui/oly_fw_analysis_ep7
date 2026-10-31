/* Full ID193 initializer (self12) followed by a private C post-boundary.
 * Own56: outgoing0..11,selector12,id16,original a0/d0/d1/a1 at20..35,
 * saved f0 at40..55. The native caller still receives all original results. */
.text
.global ep7_native_selector_init_bridge
.type ep7_native_selector_init_bridge,@function
ep7_native_selector_init_bridge:
 movm [d2,d3,a2,a3],(sp)
 add -40,sp
 mov a0,(12,sp)
 mov d0,(16,sp)
 call ep7_stock_selector_init_unresolved,[],0
 mov a0,(20,sp)
 mov d0,(24,sp)
 mov d1,(28,sp)
 mov a1,(32,sp)
 mov (12,sp),d0
 mov (16,sp),d1
 call _ep7s_expand_after_init,[],0
 mov (20,sp),a0
 mov (24,sp),d0
 mov (28,sp),d1
 mov (32,sp),a1
 ret [d2,d3,a2,a3],56
.size ep7_native_selector_init_bridge,.-ep7_native_selector_init_bridge

/* Same array new/delete pair used by native list mask loader/destructor.
 * These original entries require caller-provided4-byte frames. */
.global _ep7_gcc_mvc_array_new
.type _ep7_gcc_mvc_array_new,@function
_ep7_gcc_mvc_array_new:
 add -4,sp
 call ep7_stock_mvc_array_new_unresolved,[],4
 mov a0,d0
 ret [],4
.size _ep7_gcc_mvc_array_new,.-_ep7_gcc_mvc_array_new
.global _ep7_gcc_mvc_array_delete
.type _ep7_gcc_mvc_array_delete,@function
_ep7_gcc_mvc_array_delete:
 add -4,sp
 mov d0,a0
 call ep7_stock_mvc_array_delete_unresolved,[],4
 ret [],4
.size _ep7_gcc_mvc_array_delete,.-_ep7_gcc_mvc_array_delete
