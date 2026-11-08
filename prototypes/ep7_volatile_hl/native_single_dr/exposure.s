/* Exact native caller frames for the ordinary E-P7 build1100 STILL path.
 * The calculation ticket lives on this invocation's stack. */
.text

.macro save_observer
 movm [d2,d3,a2,a3,other],(sp)
 mov psw,d2
 add -16,sp
 mov d2,(16,sp)
.endm

.macro restore_observer
 mov (16,sp),d2
 add 16,sp
 mov d2,psw
 movm (sp),[d2,d3,a2,a3,other]
.endm

.macro reject_ticket
 save_observer
 mov (92,sp),d0
 mov (96,sp),d1
 call _ep7dr_reject_plan,[],0
 restore_observer
.endm

/* 6029d68e CALL [d2,d3,a2],32. */
.global ep7dr_exposure_freeze_bridge
ep7dr_exposure_freeze_bridge:
 save_observer
 mov (0x6223d414),d0
 mov a0,d1
 call _ep7dr_freeze_plan,[],0
 restore_observer
 jmp ep7dr_stock_engine_dispatch

/* 601429cc CALL [d2,d3,a2,a3],56. The first 40 frame bytes are local;
 * outer caller's saved registers start at byte 40. GCC home slots 0..8
 * are separate from the saved arguments, identity, ticket and outcome. */
.global ep7dr_exposure_scope_bridge
ep7dr_exposure_scope_bridge:
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 /* Authenticate each stock frame before consulting its caller. The
  * transition path's temporary selector 7 returns to 6014ddc2 instead
  * and its final selector 4 subsequently programs gain again. */
 mov (56,sp),d0
 cmp 0x601429d3,d0
 bne .Lstock_calc_tail
 mov (84,sp),d0
 cmp 0x6013cce5,d0
 bne .Lstock_calc_tail
 mov (92,sp),d0
 cmp 0x601420ad,d0
 bne .Lstock_calc_tail
 mov (128,sp),d0
 cmp 0x6014e5f8,d0
 bne .Lstock_calc_tail
 mov (164,sp),d0
 cmp 0x6014e783,d0
 bne .Lstock_calc_tail
 mov (180,sp),d0
 cmp 0x6014de09,d0
 bne .Lstock_calc_tail
 mov a0,d0
 mov a3,d1
 call _ep7dr_exposure_metadata,[],0
 cmp 0,d0
 beq .Lstock_calc_tail
 mov d0,(28,sp)
 call _ep7dr_plan_for_metadata,[],0
 cmp 0,d0
 beq .Lstock_calc_tail
 mov d0,(32,sp)
 clr d0
 mov d0,(36,sp)
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 call ep7dr_stock_exposure_calculate,[d2,d3,a2,a3],56
.Lcalc_done:
 mov (36,sp),d1
 cmp 0,d1
 beq .Lno_gain_change
 exthu d0
 cmp 0,d0
 bne .Lrerun_stock
 mov (20,sp),a0
 lsr 16,d1
 mov (56,a0),d0
 cmp d1,d0
 bne .Lrerun_stock
 mov (60,a0),d0
 cmp d1,d0
 bne .Lrerun_stock
 mov (48,a0),d0
 cmp 1,d0
 bne .Lrerun_stock
 mov (44,a0),d0
 cmp 65536,d0
 bne .Lrerun_stock
 save_observer
 mov (92,sp),d0
 mov (96,sp),d1
 call _ep7dr_record_applied,[],0
 cmp 1,d0
 bne .Lpublish_rejected
 restore_observer
 clr d0
 ret [d2,d3,a2,a3],56
.Lno_gain_change:
 reject_ticket
 ret [d2,d3,a2,a3],56
.Lpublish_rejected:
 restore_observer
.Lrerun_stock:
 reject_ticket
.Lstock_calc_tail:
 /* Re-evaluate entirely stock if the packed gain differs. No TG_GAIN
  * payload has yet been built at 6013cd94. The tail transfer has no ticket. */
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 jmp ep7dr_stock_exposure_calculate

/* JMP at 6012e6ef, replacing MOV a3,a0 and the native f788 CALL. This is
 * inside e654's 16-byte frame, which is inside e2fc's 56-byte frame.
 * After the observer's 64 bytes the two return PCs are +80 and +136. */
.global ep7dr_exposure_gain_bridge
ep7dr_exposure_gain_bridge:
 save_observer
 mov (80,sp),d0
 cmp 0x6012e393,d0
 bne .Lstock_gain
 mov (136,sp),d0
 cmp .Lcalc_done,d0
 bne .Lstock_gain
 mov (156,sp),a0
 cmp a3,a0
 bne .Lstock_gain
 mov (20,a3),a0
 movhu (8,a0),d0
 movhu (46,a2),d1
 cmp d0,d1
 bne .Lstock_gain
 mov (168,sp),d1
 call _ep7dr_exposure_target,[],0
 cmp 0,d0
 beq .Lstock_gain
 mov d0,(172,sp)
 movhu d0,(46,a2)
.Lstock_gain:
 restore_observer
 mov a3,a0
 call ep7dr_stock_gain_table,[a2,a3],12
 jmp ep7dr_stock_gain_resume

.global _ep7dr_stock_exp2_q12
_ep7dr_stock_exp2_q12:
 add -4,sp
 call ep7dr_stock_exp2,[d2],4
 ret [],4
