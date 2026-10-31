/* Same-width retarget of CALL60191371, original mask0/frame4.
 * Own40 is wholly below the original W. GCC outgoing/return area0..11 stays
 * separate from input d0/d1/a0/a1, d2, MDR and PSW at12..39. GCC preserves
 * d3/a2/a3. No active native SETLB loop precedes this seam in the reviewed
 * Usr3 prefix; this is not an arbitrary inline/interrupt entry.
 * On success tail-transfer with the original frame/RA/inputs intact. */
.text
.global ep7_native_cold_bootstrap_bridge
.type ep7_native_cold_bootstrap_bridge,@function
ep7_native_cold_bootstrap_bridge:
 add -40,sp
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov d2,(32,sp)
 mov mdr,d2
 mov d2,(28,sp)
 mov psw,d2
 mov d2,(36,sp)
 call _ep7r_bootstrap_initialize,[],0
 mov (36,sp),d2
 mov d2,psw
 mov (28,sp),d2
 mov d2,mdr
 mov (32,sp),d2
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 add 40,sp
 jmp ep7_stock_bootstrap_original_unresolved
.size ep7_native_cold_bootstrap_bridge,.-ep7_native_cold_bootstrap_bridge
