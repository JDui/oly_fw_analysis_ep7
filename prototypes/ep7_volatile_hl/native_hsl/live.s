/* Native caller-owned source -> job transport, matching PEN-F's seams.
 * MOVM saves48B; the GCC observer's16B outgoing area makes64B total.
 * The otherwise blank MOVM word holds PSW. Saved MDR is at observer SP+28.
 */
.text
.macro live_preserve
 movm [d2,d3,a2,a3,other],(sp)
 mov psw,d2
 add -16,sp
 mov d2,(16,sp)
.endm
.macro live_restore
 mov (16,sp),d2
 add 16,sp
 mov d2,psw
 movm (sp),[d2,d3,a2,a3,other]
.endm

.global ep7h_live_sample_bridge
ep7h_live_sample_bridge:
 call ep7_stock_h_live_s_unresolved,[d2,d3,a2,a3],20
.Lafter_live_s:
 live_preserve
 mov (28,sp),d1
 cmp .Lafter_live_s,d1
 bne .Llive_s_mdr_saved
 mov ep7_stock_h_live_s_resume_unresolved,d1
 mov d1,(28,sp)
.Llive_s_mdr_saved:
 mov (76,sp),d0           /* native acquisition's frozen source at oldSP+12 */
 call _ep7h_live_sample,[],0
 live_restore
 jmp ep7_stock_h_live_s_resume_unresolved

.global ep7h_live_to_job_bridge
ep7h_live_to_job_bridge:
 call ep7_stock_h_live_setter_unresolved,[d2,d3,a2,a3],48
.Lafter_live_setter:
 live_preserve
 mov (28,sp),d1
 cmp .Lafter_live_setter,d1
 bne .Llive_job_mdr_saved
 mov ep7_stock_h_live_setter_resume_unresolved,d1
 mov d1,(28,sp)
.Llive_job_mdr_saved:
 mov d0,d1
 exthu d1
 cmp 0,d1
 bne .Llive_job_done
 mov (72,sp),d0           /* caller's source at oldSP+8 */
 mov (80,sp),d1           /* caller's job body at oldSP+16 */
 call _ep7h_live_to_job,[],0
.Llive_job_done:
 live_restore
 jmp ep7_stock_h_live_setter_resume_unresolved
