.am33_2
.text
.global ep7dr_gamma_bridge
ep7dr_gamma_bridge:
 movm [d2,d3,a2,a3,other],(sp)
 mov psw,d2
 add -16,sp
 mov d2,(16,sp)
 /* GCC's third argument is at caller SP+12 (two register argument homes).
  * Observe selector bypasses too,
  * instead of leaving a stale successful V/P code from an earlier frame. */
 mov d0,(12,sp)
 mov (104,sp),d0
 mov sp,a0
 mov a0,d1
 add 132,d1
 call _ep7dr_gamma_apply,[],0
 mov (16,sp),d2
 add 16,sp
 mov d2,psw
 movm (sp),[d2,d3,a2,a3,other]
 movbu d0,(60,sp)
 mov (36,sp),a0
 jmp ep7dr_stock_gamma_resume_unresolved
