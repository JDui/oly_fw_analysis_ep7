/* Pre-cache seam at 603ae830. Preserve the selector ABI and replay the
 * complete five displaced bytes before the native gamma builder continues. */
.am33_2
.text
.macro preserve
 movm [d2,d3,a2,a3,other],(sp)
 mov psw,d2
 add -16,sp
 mov d2,(16,sp)
.endm
.macro restore
 mov (16,sp),d2
 add 16,sp
 mov d2,psw
 movm (sp),[d2,d3,a2,a3,other]
.endm

.global ep7dr_gamma_bridge
ep7dr_gamma_bridge:
 preserve
 cmp 1,d0
 bne .Lgamma_resume
 mov (104,sp),d0               /* native SP+40 = request */
 mov sp,a0
 mov a0,d1
 add 132,d1                    /* native SP+68 = three RGB pointers */
 call _ep7dr_gamma_apply,[],0
.Lgamma_resume:
 restore
 movbu d0,(60,sp)
 mov (36,sp),a0
 jmp ep7dr_stock_gamma_resume_unresolved

/* The native worker keeps the request in A3. Reset the per-attempt proof
 * before configuration, then require it before installing an ISP slot. */
.global ep7dr_gamma_config_bridge
ep7dr_gamma_config_bridge:
 preserve
 mov a3,d0
 call _ep7dr_gamma_config_begin,[],0
 restore
 call ep7dr_stock_gamma_config,[d2,a2],72
.Lafter_gamma_config:
 preserve
 mov (28,sp),d1
 cmp .Lafter_gamma_config,d1
 bne .Lgamma_config_mdr_saved
 mov ep7dr_stock_gamma_config_resume,d1
 mov d1,(28,sp)
.Lgamma_config_mdr_saved:
 exthu d0
 cmp 0,d0
 bne .Lgamma_config_continue
 mov a3,d0
 call _ep7dr_gamma_config_missing,[],0
 cmp 0,d0
 bne .Lgamma_config_reject
.Lgamma_config_continue:
 restore
 jmp ep7dr_stock_gamma_config_resume

/* Native 60334dda..e0 checks a variant that bypasses configuration. */
.global ep7dr_gamma_bypass_bridge
ep7dr_gamma_bypass_bridge:
 mov (192,sp),d0
 btst 32768,d0
 beq .Lgamma_config_enter
 preserve
 mov a3,d0
 call _ep7dr_gamma_bypass_pending,[],0
 cmp 0,d0
 bne .Lgamma_config_reject
 restore
 jmp ep7dr_stock_gamma_bypass
.Lgamma_config_enter:
 jmp ep7dr_stock_gamma_config_enter

.Lgamma_config_reject:
 restore
 mov 0x9e02,d2
 jmp ep7dr_stock_gamma_config_cleanup

/* No stage-2 route can advance the stock scheduler without a proof. */
.global ep7dr_gamma_stage_bridge
ep7dr_gamma_stage_bridge:
 preserve
 exthu d0
 cmp 0,d0
 bne .Lgamma_stage_resume
 mov (60,sp),d0              /* native D2 is the scheduler's job */
 call _ep7dr_gamma_stage_missing,[],0
 cmp 0,d0
 bne .Lgamma_stage_reject
.Lgamma_stage_resume:
 restore
 bra .Lgamma_stage_result
.Lgamma_stage_reject:
 restore
 mov 0x9e02,d0
.Lgamma_stage_result:
 mov (8,sp),a0
 movhu d0,(a0)
 exthu d0
 jmp ep7dr_stock_gamma_stage_resume

/* Kind19 turns native cancellation into success on one route. Require the
 * same job's proof before success postprocessing, while A3 still owns it. */
.global ep7dr_gamma_output_bridge
ep7dr_gamma_output_bridge:
 movhu (12,sp),d0
 cmp 0,d0
 bne .Lgamma_output_resume
 preserve
 mov a3,d0
 call _ep7dr_gamma_output_missing,[],0
 cmp 0,d0
 bne .Lgamma_output_reject
 restore
.Lgamma_output_resume:
 jmp ep7dr_stock_gamma_output_resume
.Lgamma_output_reject:
 restore
 mov 0x9e02,d0
 movhu d0,(12,sp)
 cmp 0,d0
 jmp ep7dr_stock_gamma_output_resume
