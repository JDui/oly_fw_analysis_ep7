/* Replaces all four caller-framed CALL f0,28 targets, not the original entry.
 * This 12-byte entry MUST be in signed16 CALL range of all four callers.
 * Inherited frame: outgoing0..11, saved f0 at12..27; no additional frame. */
.section .text.ep7_content_rebuild,"ax"
.global ep7_native_content_rebuild_bridge
.type ep7_native_content_rebuild_bridge,@function
ep7_native_content_rebuild_bridge:
 mov a0,d0
 call _ep7c_rebuild,[],0
 ret [d2,d3,a2,a3],28
.size ep7_native_content_rebuild_bridge,.-ep7_native_content_rebuild_bridge

.text
.global _ep7_gcc_mvc_stock_rebuild
.type _ep7_gcc_mvc_stock_rebuild,@function
_ep7_gcc_mvc_stock_rebuild:
 add -4,sp
 mov d0,a0
 call ep7_stock_mvc_rebuild_unresolved,[d2,d3,a2,a3],28
 ret [],4
.size _ep7_gcc_mvc_stock_rebuild,.-_ep7_gcc_mvc_stock_rebuild

.global _ep7_gcc_mvc_scalar_new
.type _ep7_gcc_mvc_scalar_new,@function
_ep7_gcc_mvc_scalar_new:
 add -4,sp
 call ep7_stock_mvc_scalar_new_unresolved,[],4
 mov a0,d0
 ret [],4
.size _ep7_gcc_mvc_scalar_new,.-_ep7_gcc_mvc_scalar_new

.global _ep7_gcc_mvc_base_init
.type _ep7_gcc_mvc_base_init,@function
_ep7_gcc_mvc_base_init:
 add -4,sp
 mov d0,a0
 call ep7_stock_mvc_base_init_unresolved,[],0
 ret [],4
.size _ep7_gcc_mvc_base_init,.-_ep7_gcc_mvc_base_init

/* Virtual+40 performs destruction; returned A0 is an optional deallocator. */
.global _ep7_gcc_mvc_dispose
.type _ep7_gcc_mvc_dispose,@function
_ep7_gcc_mvc_dispose:
 movm [a2],(sp)
 add -4,sp
 mov d0,a2
 mov a2,a0
 mov (a0),a1
 mov (40,a1),a1
 calls (a1)
 mov a0,a1
 cmp 0,a0
 beq .Lscalar_delete
 mov a2,a0
 calls (a1)
 ret [a2],8
.Lscalar_delete:
 mov a2,a0
 call ep7_stock_mvc_scalar_delete_unresolved,[],4
 ret [a2],8
.size _ep7_gcc_mvc_dispose,.-_ep7_gcc_mvc_dispose

.global ep7_native_content_destroy_bridge
.type ep7_native_content_destroy_bridge,@function
ep7_native_content_destroy_bridge:
 movm [d2,d3,a2,a3],(sp)
 add -16,sp
 mov a0,(12,sp)
 mov a0,d0
 call _ep7c_before_destroy,[],0
 mov (12,sp),a0
 call ep7_stock_mvc_base_destroy_unresolved,[],0
 ret [d2,d3,a2,a3],32
.size ep7_native_content_destroy_bridge,.-ep7_native_content_destroy_bridge

/* Private content never dispatches an unqualified event to an S callback. */
.global ep7_native_content_zero
.type ep7_native_content_zero,@function
ep7_native_content_zero:
 clr d0
 retf [],0
.size ep7_native_content_zero,.-ep7_native_content_zero
.global ep7_native_content_null
.type ep7_native_content_null,@function
ep7_native_content_null:
 mov 0,a0
 retf [],0
.size ep7_native_content_null,.-ep7_native_content_null

.section .rodata
.balign 4
.global ep7_native_content_vtable
.type ep7_native_content_vtable,@object
ep7_native_content_vtable:
 .long ep7_native_content_zero,ep7_native_content_zero,ep7_native_content_zero
 .long ep7_native_content_zero,ep7_native_content_zero,ep7_native_content_zero
 .long ep7_native_content_zero,ep7_native_content_null,ep7_native_content_zero
 .long ep7_native_content_zero,ep7_native_content_destroy_bridge,ep7_native_content_zero
 .long ep7_native_content_zero,ep7_native_content_zero,ep7_native_content_zero
 .long ep7_native_content_zero,ep7_native_content_zero,ep7_native_content_zero
.size ep7_native_content_vtable,.-ep7_native_content_vtable
