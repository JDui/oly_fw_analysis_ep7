/* Self-authored, compile/assemble only. No install address or linked firmware.
 * Native entry CALL [d2,d3,a2,a3],96 at the reviewed COLOR builder site ONLY.
 * Original native builder receives unchanged d0,d1,a0,a1; restores setup in a2.
 * Outer frame upper80..92 holds original callee registers; RA is at+96.
 */
.text
.global ep7_native_postbuilder_bridge
.type ep7_native_postbuilder_bridge,@function
ep7_native_postbuilder_bridge:
 call ep7_stock_color_builder_unresolved,[d2,d3,a2,a3],96
 /* Preserve post-builder volatile registers without touching upper saved frame.
  * [0..8] is reserved for GCC one-argument return/argument-flush area.
  * Flags need not survive: exact continuation overwrites d0 then BTST.
  */
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov mdr,d2
 mov d2,(28,sp)
 mov a2,d0
 call _ep7_gcc_postbuilder_observer,[],0
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 mov (28,sp),d2
 mov d2,mdr
 ret [d2,d3,a2,a3],96
.size ep7_native_postbuilder_bridge,.-ep7_native_postbuilder_bridge
