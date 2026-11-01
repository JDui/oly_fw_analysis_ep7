/* Historical candidate001..004 implementation, excluded from sources.txt.
 * Candidate005 uses image-initialized state and leaves600201fe unchanged.
 * Candidate at600201fe, entered by JMP with the original startup SP.
 * Linker must bind an aligned, exclusively reserved16KiB uncached payload.
 * No C, RTOS, allocator, CALL/MDR, loop-register or existing BSS dependency.
 * Preserve register/PSW state, replay original MOV, resume60020204.
 * This object does not authorize placement or install the startup rewrite. */
.section .text.ep7_cold_clear,"ax"
.global ep7_native_cold_clear
.type ep7_native_cold_clear,@function
ep7_native_cold_clear:
 add -16,sp
 mov d0,(sp)
 mov d1,(4,sp)
 mov a0,(8,sp)
 mov psw,d0
 mov d0,(12,sp)
 mov __ep7_private_uncached_start,a0
 mov 4096,d1
 clr d0
.Lzero:
 mov d0,(a0)
 inc4 a0
 add -1,d1
 bne .Lzero
 mov (12,sp),d0
 mov d0,psw
 mov (sp),d0
 mov (4,sp),d1
 mov (8,sp),a0
 add 16,sp
 mov (ep7_stock_boot_next_copy_end_unresolved),d0
 jmp ep7_stock_boot_after_clear_unresolved
.size ep7_native_cold_clear,.-ep7_native_cold_clear
