/* Exact CALL60cfd53a,b0,224: inherited frame224, saved b0 at212..223,
 * original return at224. Locals12..47; nested original owns another224.
 * D3 is not in b0 and is preserved independently. */
.text
.global ep7_native_ui_preprocess_bridge
.type ep7_native_ui_preprocess_bridge,@function
ep7_native_ui_preprocess_bridge:
 mov a0,(12,sp)
 mov d0,(16,sp)
 mov d1,(20,sp)
 mov a1,(24,sp)
 mov d3,(28,sp)
 mov a0,d0
 call _ep7i_prepare_begin,[],0
 mov (12,sp),a0
 mov (16,sp),d0
 mov (20,sp),d1
 mov (24,sp),a1
 mov (28,sp),d3
 call ep7_stock_ui_preprocess_unresolved,[d2,a2,a3],224
 mov a0,(32,sp)
 mov d0,(36,sp)
 mov d1,(40,sp)
 mov a1,(44,sp)
 mov d0,d1
 mov (12,sp),d0
 call _ep7i_prepare_end,[],0
 mov (32,sp),a0
 mov (36,sp),d0
 mov (40,sp),d1
 mov (44,sp),a1
 mov (28,sp),d3
 ret [d2,a2,a3],224
.size ep7_native_ui_preprocess_bridge,.-ep7_native_ui_preprocess_bridge

/* Exact CALL60cfd558,f0,48: extra20 makes total68; inherited saved f0 at52..67.
 * Native arguments are D0 event,A1 parameter,D1 extra,A0 machine; A3 packet.
 * Locals12..31 copy that shape; token32, original results36..51. */
.global ep7_native_ui_dispatch_bridge
.type ep7_native_ui_dispatch_bridge,@function
ep7_native_ui_dispatch_bridge:
 add -20,sp
 mov d0,(12,sp)
 mov a1,(16,sp)
 mov d1,(20,sp)
 mov a0,(24,sp)
 mov a3,(28,sp)
 mov sp,a0
 add 12,a0
 mov a0,d0
 call _ep7i_dispatch_begin,[],0
 mov d0,(32,sp)
 mov (12,sp),d0
 mov (16,sp),a1
 mov (20,sp),d1
 mov (24,sp),a0
 call ep7_stock_ui_dispatch_unresolved,[d2,d3,a2,a3],48
 mov d0,(36,sp)
 mov d1,(40,sp)
 mov a0,(44,sp)
 mov a1,(48,sp)
 mov (32,sp),d0
 call _ep7i_dispatch_end,[],0
 mov (36,sp),d0
 mov (40,sp),d1
 mov (44,sp),a0
 mov (48,sp),a1
 add 20,sp
 ret [d2,d3,a2,a3],48
.size ep7_native_ui_dispatch_bridge,.-ep7_native_ui_dispatch_bridge

.global _ep7_gcc_ui_drop_info
.type _ep7_gcc_ui_drop_info,@function
_ep7_gcc_ui_drop_info:
 add -4,sp
 mov 36884,d0
 call ep7_stock_ui_drop_event_unresolved,[d2,d3,a2],16
 ret [],4
.size _ep7_gcc_ui_drop_info,.-_ep7_gcc_ui_drop_info

/* Five CALL[],0 setters share this entry; signed16 placement is a G6 gate.
 * Preserve every data/address input plus original MDR; no incoming flags live
 * past the source's following CMP. Own64: sample12..31,saved D1/A0/A1/MDR32..47,
 * saved f0 at48..63, original return PC at64. */
.section .text.ep7_ui_wheel_sample,"ax"
.global ep7_native_ui_wheel_sample_bridge
.type ep7_native_ui_wheel_sample_bridge,@function
ep7_native_ui_wheel_sample_bridge:
 movm [d2,d3,a2,a3],(sp)
 add -48,sp
 mov a3,(12,sp)
 mov d0,(16,sp)
 mov (64,sp),d0
 mov d0,(20,sp)
 mov d2,(24,sp)
 mov a2,(28,sp)
 mov d1,(32,sp)
 mov a0,(36,sp)
 mov a1,(40,sp)
 mov mdr,d0
 mov d0,(44,sp)
 mov (16,sp),d0
 call ep7_stock_ui_wheel_set_unresolved,[],0
 mov sp,a0
 add 12,a0
 mov a0,d0
 call _ep7i_sample_wheel,[],0
 mov (44,sp),d0
 mov d0,mdr
 mov (16,sp),d0
 mov (32,sp),d1
 mov (36,sp),a0
 mov (40,sp),a1
 ret [d2,d3,a2,a3],64
.size ep7_native_ui_wheel_sample_bridge,.-ep7_native_ui_wheel_sample_bridge
