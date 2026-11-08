/* Interpose only the six known 015 CALLs to its GCC snapshot helpers.
 * Preserve their arguments and tail-transfer to the original implementation. */
.text
.macro observer name
.global ep7dr_\name\()_bridge
ep7dr_\name\()_bridge:
 movm [d2,d3,a2,a3,other],(sp)
 mov psw,d2
 add -16,sp
 mov d2,(16,sp)
 call _ep7dr_highlight_\name,[],0
 mov (16,sp),d2
 add 16,sp
 mov d2,psw
 movm (sp),[d2,d3,a2,a3,other]
 jmp ep7dr_015_\name
.endm
observer capture_sample
observer capture_clone
observer capture_to_job
observer live_sample
observer live_to_job
