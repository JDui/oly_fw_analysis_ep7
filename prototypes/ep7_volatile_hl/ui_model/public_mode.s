/* Existing property service ABI: getter caller frame4; virtual+8 writes uint32
 * to A1, D0=id111. Independent local initialized0; null getter rejects as mode0. */
.text
.global _ep7_gcc_ui_public_mode
.type _ep7_gcc_ui_public_mode,@function
_ep7_gcc_ui_public_mode:
 movm [a2],(sp)
 add -16,sp
 clr d0
 mov d0,(12,sp)
 call ep7_stock_property_service_unresolved,[],4
 cmp 0,a0
 beq .Lmode_done
 mov (a0),a2
 mov (8,a2),a2
 mov sp,a1
 add 12,a1
 mov 111,d0
 calls (a2)
.Lmode_done:
 mov (12,sp),d0
 ret [a2],20
.size _ep7_gcc_ui_public_mode,.-_ep7_gcc_ui_public_mode
