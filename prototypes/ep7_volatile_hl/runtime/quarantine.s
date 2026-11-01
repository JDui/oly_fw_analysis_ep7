/* Owned terminal hold. Keep the first reason and make a best-effort AF signal
 * through the ORIGINAL E-P7 updater's channel0/250ms helper. This does not
 * resume cleanup, reset, acknowledge work or write firmware. Only domain0 and
 * a loaded section1 may call it. Reentry skips the helper and holds at once.
 * The native helper may itself stop if its clock/PWM service is unavailable;
 * absence of a signal therefore cannot exclude this terminal path.
 * NMI, watchdog/reset and other-core behavior remain hardware responsibilities. */
.bss
.balign 4
.global _ep7_terminal_reason
_ep7_terminal_reason:
 .space 4
.text
.global _ep7_gcc_quarantine
.type _ep7_gcc_quarantine,@function
_ep7_gcc_quarantine:
 mov (_ep7_terminal_reason),d1
 cmp 0,d1
 bne .Lhold
 mov d0,(_ep7_terminal_reason)
 mov (0x8050),d1
 cmp 0,d1
 bne .Lhold
 mov (0xa272e420),d1
 btst 1,d1
 beq .Lhold
 /* Same native CALL mask/frame as601e739f's original call. Do not alter the
  * caller's interrupt state until the helper has had a chance to configure
  * PWM using its normal service path. The helper's return value is irrelevant. */
 clr d0
 mov 250,d1
 call ep7_stock_terminal_af_unresolved,[d2,d3],28
.Lhold:
 and 0xf7ff,psw
.Lquarantined:
 bra .Lquarantined
.size _ep7_gcc_quarantine,.-_ep7_gcc_quarantine
