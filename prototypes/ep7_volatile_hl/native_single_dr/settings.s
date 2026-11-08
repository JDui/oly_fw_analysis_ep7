/* Typed property getter for the same core and part as stock 602a7ea0. */
.text
.global _ep7dr_stock_key
_ep7dr_stock_key:
 add -4,sp
 mov 0,a0
 clr d1
 call ep7dr_stock_key_get_unresolved,[d2,d3],12
 ret [],4

.macro save_capture_key_context
 movm [d2,d3,a2,a3,other],(sp)
 mov psw,d2
 add -20,sp
 mov d2,(16,sp)
 mov d0,d1
.endm

/* Exact 602a7ea0 typed property calls, each CALL [d2,d3],12.
 * D3 is the populated capture and D0 is the requested part-0 key. */
.global ep7dr_capture_key_bridge
ep7dr_capture_key_bridge:
 save_capture_key_context
 mov d3,d0
 bra .Lcapture_key_lookup

/* 6061f118, CALL [d2,d3],12. The captured format/size helper keeps its
 * image pointer in A2 and the raw key 52b1 arrives in D0. */
.global ep7dr_capture_format_key_bridge
ep7dr_capture_format_key_bridge:
 save_capture_key_context
 mov a2,d0

.Lcapture_key_lookup:
 call _ep7dr_capture_key,[],0
 cmp -1,d0
 beq .Lcapture_key_stock
 /* Put the result in the original CALL frame's scratch word. */
 mov d0,(68,sp)
 mov (16,sp),d2
 add 20,sp
 mov d2,psw
 movm (sp),[d2,d3,a2,a3,other]
 mov (0,sp),d0
 ret [d2,d3],12
.Lcapture_key_stock:
 mov (16,sp),d2
 add 20,sp
 mov d2,psw
 movm (sp),[d2,d3,a2,a3,other]
 jmp ep7dr_stock_key_get_unresolved

/* Epoch changes are per core. Only the short observer update masks
 * interrupts. The original bank transaction runs with its original PSW. */
.macro bank_observer helper
 movm [d2,d3,a2,a3,other],(sp)
 mov psw,d2
 add -20,sp
 mov d2,(16,sp)
 and 0xf7ff,psw
 call \helper,[],0
 mov (16,sp),d2
 add 20,sp
 mov d2,psw
 movm (sp),[d2,d3,a2,a3,other]
.endm

.global ep7dr_bank_session_enter_bridge
ep7dr_bank_session_enter_bridge:
 bank_observer _ep7dr_bank_begin
 call .Lstock_bank_session_enter,[d2,d3,a2,a3],32
 bank_observer _ep7dr_bank_end
 ret [d2,d3,a2,a3],32
.Lstock_bank_session_enter:
 mov d1,d3
 movbu (0x622484fa),d1
 jmp ep7dr_stock_bank_session_enter_resume

.global ep7dr_bank_session_leave_bridge
ep7dr_bank_session_leave_bridge:
 bank_observer _ep7dr_bank_begin
 call .Lstock_bank_session_leave,[],4
 bank_observer _ep7dr_bank_end
 ret [],4
.Lstock_bank_session_leave:
 clr d0
 movbu d0,(0x622484fa)
 jmp ep7dr_stock_bank_session_leave_resume

.global ep7dr_bank_mode_bridge
ep7dr_bank_mode_bridge:
 bank_observer _ep7dr_bank_begin
 /* Stock reads the first stack argument at new SP+32. */
 mov (32,sp),d2
 mov d2,(4,sp)
 call .Lstock_bank_mode,[d2,d3,a2,a3],28
 bank_observer _ep7dr_bank_end
 ret [d2,d3,a2,a3],28
.Lstock_bank_mode:
 mov a0,d2
 movbu d2,(5,sp)
 jmp ep7dr_stock_bank_mode_resume

.global ep7dr_bank_recall_bridge
ep7dr_bank_recall_bridge:
 bank_observer _ep7dr_bank_begin
 call .Lstock_bank_recall,[d2,d3,a2],20
 bank_observer _ep7dr_bank_end
 ret [d2,d3,a2],20
.Lstock_bank_recall:
 mov a0,d2
 movbu d2,(5,sp)
 jmp ep7dr_stock_bank_recall_resume

.global ep7dr_bank_reset_bridge
ep7dr_bank_reset_bridge:
 bank_observer _ep7dr_bank_begin
 call .Lstock_bank_reset,[d2,d3,a2],16
 bank_observer _ep7dr_bank_end
 ret [d2,d3,a2],16
.Lstock_bank_reset:
 mov d1,d3
 mov d0,d2
 mov 41,d0
 call ep7dr_stock_bank_property,[],4
 jmp ep7dr_stock_bank_reset_resume

.global ep7dr_bank_partial_reset_bridge
ep7dr_bank_partial_reset_bridge:
 bank_observer _ep7dr_bank_begin
 call .Lstock_bank_partial_reset,[d2,d3],12
 bank_observer _ep7dr_bank_end
 ret [d2,d3],12
.Lstock_bank_partial_reset:
 mov d1,d3
 mov d0,d2
 mov 1,d0
 call ep7dr_stock_bank_inhibit,[],0
 jmp ep7dr_stock_bank_partial_reset_resume

.global ep7dr_bank_clear_bridge
ep7dr_bank_clear_bridge:
 bank_observer _ep7dr_bank_begin
 call .Lstock_bank_clear,[d2],8
 bank_observer _ep7dr_bank_end
 ret [d2],8
.Lstock_bank_clear:
 mov d0,d2
 extbu d2
 cmp 8,d2
 bne .Lstock_bank_clear_other
 jmp ep7dr_stock_bank_clear_mode8
.Lstock_bank_clear_other:
 jmp ep7dr_stock_bank_clear_resume

.global ep7dr_bank_clear_recall_bridge
ep7dr_bank_clear_recall_bridge:
 bank_observer _ep7dr_bank_begin
 call .Lstock_bank_clear_recall,[d2,d3],12
 bank_observer _ep7dr_bank_end
 ret [d2,d3],12
.Lstock_bank_clear_recall:
 mov d1,d2
 mov d0,d3
 extbu d3
 mov d3,d0
 call ep7dr_bank_clear_bridge,[d2],8
 jmp ep7dr_stock_bank_clear_recall_resume

.global ep7dr_bank_defaults_bridge
ep7dr_bank_defaults_bridge:
 /* Cold initialization can precede settings readiness. Stock clears D3
  * at this entry, so the readiness check needs no extra frame. */
 mov (0xa272e420),d3
 btst 4,d3
 beq .Lstock_bank_defaults
 bank_observer _ep7dr_bank_begin
 call .Lstock_bank_defaults,[d2,d3,a2],16
 bank_observer _ep7dr_bank_end
 ret [d2,d3,a2],16
.Lstock_bank_defaults:
 clr d3
 mov d3,d0
 call ep7dr_stock_bank_default,[d2,d3,a2,a3],20
 jmp ep7dr_stock_bank_defaults_resume

.global ep7dr_bank_save_bridge
ep7dr_bank_save_bridge:
 bank_observer _ep7dr_bank_begin
 call .Lstock_bank_save,[d2,d3],12
 bank_observer _ep7dr_bank_end
 ret [d2,d3],12
.Lstock_bank_save:
 mov d0,d3
 clr d2
 extbu d3
 .byte 0xfb,0x03,0xd2,0x0d /* udf00 3538,d3 */
 jmp ep7dr_stock_bank_save_resume

.global _ep7dr_settings_irq_lock
_ep7dr_settings_irq_lock:
 mov psw,d0
 and 0xf7ff,psw
 rets

.global _ep7dr_settings_irq_unlock
_ep7dr_settings_irq_unlock:
 mov d0,psw
 nop
 nop
 rets
