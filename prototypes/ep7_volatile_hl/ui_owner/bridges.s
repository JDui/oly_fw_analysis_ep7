/* Native full-method entries. No midfunction displacement or startup writes.
 * Screen wrapper: own64 (saved f0 at48..63), GCC outgoing0..11,
 * call record12..27, incoming d1/a1 at28/32, original a0/d1/a1 at36/40/44.
 * Retire wrappers: own48, saved f0 at32..47, arguments at12..27. */
.text
.global ep7_native_ui_screen_bridge
.type ep7_native_ui_screen_bridge,@function
ep7_native_ui_screen_bridge:
 movm [d2,d3,a2,a3],(sp)
 add -48,sp
 mov a0,(12,sp)
 mov d0,(16,sp)
 mov d1,(28,sp)
 mov a1,(32,sp)
 mov sp,a0
 add 12,a0
 mov a0,d0
 call _ep7u_screen_enter,[],0
 mov (12,sp),a0
 mov (16,sp),d0
 mov (28,sp),d1
 mov (32,sp),a1
 call ep7_stock_screen_manager_unresolved,[],0
 mov d0,(20,sp)
 mov a0,(36,sp)
 mov d1,(40,sp)
 mov a1,(44,sp)
 mov sp,a0
 add 12,a0
 mov a0,d0
 call _ep7u_screen_leave,[],0
 mov (20,sp),d0
 mov (36,sp),a0
 mov (40,sp),d1
 mov (44,sp),a1
 ret [d2,d3,a2,a3],64
.size ep7_native_ui_screen_bridge,.-ep7_native_ui_screen_bridge

.macro retire_bridge name,target,stage
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
 mov \stage,d1
 call _ep7u_before_retire,[],0
 mov (12,sp),a0
 mov (16,sp),d0
 mov (20,sp),d1
 mov (24,sp),a1
 call \target,[],0
 ret [d2,d3,a2,a3],48
.size \name,.-\name
.endm
retire_bridge ep7_native_ui_owner_cleanup_bridge,ep7_stock_ui_owner_cleanup_unresolved,1
retire_bridge ep7_native_ui_owner_bulk_bridge,ep7_stock_ui_owner_bulk_unresolved,2
retire_bridge ep7_native_ui_owner_destructor_bridge,ep7_stock_ui_owner_destructor_unresolved,3
