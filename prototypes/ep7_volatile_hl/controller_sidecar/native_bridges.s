/* Exact candidates only. Own40 keeps saves below the original native W;
 * D3/A2/A3 are GCC-preserved; D2 and MDR explicitly saved as well. */
.text
.macro save_capture
 add -40,sp
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov d2,(32,sp)
 mov mdr,d2
 mov d2,(28,sp)
.endm
.macro restore_capture
 mov (28,sp),d2
 mov d2,mdr
 mov (32,sp),d2
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 add 40,sp
.endm
.global ep7_native_capture_initialize
.type ep7_native_capture_initialize,@function
ep7_native_capture_initialize:
 save_capture
 call _ep7cn_initialize,[],0
 restore_capture
 movhu d0,(0x62234fc0)
 jmp ep7_stock_capture_init_continue_unresolved
.size ep7_native_capture_initialize,.-ep7_native_capture_initialize
.global ep7_native_capture_fresh
.type ep7_native_capture_fresh,@function
ep7_native_capture_fresh:
 call ep7_stock_capture_fresh_unresolved,[d2,a2],28
 save_capture
 mov a0,d0
 call _ep7cn_fresh,[],0
 restore_capture
 ret [d2,a2],28
.size ep7_native_capture_fresh,.-ep7_native_capture_fresh
.global ep7_native_capture_sample
.type ep7_native_capture_sample,@function
ep7_native_capture_sample:
 call ep7_stock_capture_population_unresolved,[d2,d3,a2,a3],20
 save_capture
 mov a2,d0
 clr d1
 call _ep7cn_population,[],0
 restore_capture
 ret [d2,d3,a2,a3],20
.size ep7_native_capture_sample,.-ep7_native_capture_sample
.global ep7_native_capture_finish
.type ep7_native_capture_finish,@function
ep7_native_capture_finish:
 call ep7_stock_capture_postpopulation_unresolved,[d2,d3,a2,a3],48
 save_capture
 mov a2,d0
 mov 1,d1
 call _ep7cn_population,[],0
 restore_capture
 ret [d2,d3,a2,a3],48
.size ep7_native_capture_finish,.-ep7_native_capture_finish
.global ep7_native_capture_node_free
.type ep7_native_capture_node_free,@function
ep7_native_capture_node_free:
 save_capture
 mov a0,d0
 call _ep7cn_free,[],0
 restore_capture
 jmp ep7_stock_capture_node_free_unresolved
.size ep7_native_capture_node_free,.-ep7_native_capture_node_free
.global ep7_native_capture_pool_release
.type ep7_native_capture_pool_release,@function
ep7_native_capture_pool_release:
 save_capture
 mov a2,d0
 call _ep7cn_release_capture,[],0
 restore_capture
 jmp ep7_stock_capture_pool_release_unresolved
.size ep7_native_capture_pool_release,.-ep7_native_capture_pool_release
/* Replace the wide lookup CALL at7ea0 /8dca, not the lookup function itself.
 * D0 input ID goes unchanged to stock; preserve its complete result before C.
 * Both returns precede the first capture write in the containing function. */
.global ep7_native_capture_prewrite
.type ep7_native_capture_prewrite,@function
ep7_native_capture_prewrite:
 call ep7_stock_capture_lookup_unresolved,[],24
 save_capture
 mov a0,d0
 clr d1
 call _ep7cn_prewrite,[],0
 restore_capture
 ret [],24
.size ep7_native_capture_prewrite,.-ep7_native_capture_prewrite
.global ep7_native_capture_postwrite
.type ep7_native_capture_postwrite,@function
ep7_native_capture_postwrite:
 call ep7_stock_capture_lookup_unresolved,[],24
 save_capture
 mov a0,d0
 mov 1,d1
 call _ep7cn_prewrite,[],0
 restore_capture
 ret [],24
.size ep7_native_capture_postwrite,.-ep7_native_capture_postwrite
.global _ep7_gcc_capture_lookup
.type _ep7_gcc_capture_lookup,@function
_ep7_gcc_capture_lookup:
 movm [a2],(sp)
 add -12,sp
 call ep7_stock_capture_lookup_unresolved,[],24
 ret [a2],16
.size _ep7_gcc_capture_lookup,.-_ep7_gcc_capture_lookup
