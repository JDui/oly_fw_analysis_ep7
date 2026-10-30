/* Exact CALL at603dfc9b only: native[d2,d3,a2,a3],44, d0=queue4b.
 * W=entrySP. GCC outgoing return/flush area W+0..11 lies below native saves
 * W+28..43. Original return remains W+44. No extra stack allocation is needed
 * for two GCC arguments d0=handle,d1=W. Use RET, never nested-call MDR/RETF. */
.text
.global ep7_native_materializer_receive_bridge
.type ep7_native_materializer_receive_bridge,@function
ep7_native_materializer_receive_bridge:
 mov sp,a1
 mov a1,d1
 call _ep7q_materializer_entry,[],0
 ret [d2,d3,a2,a3],44
.size ep7_native_materializer_receive_bridge,.-ep7_native_materializer_receive_bridge
