/* Owned terminal hold. Keep the first reason and make a best-effort AF signal
 * through the ORIGINAL E-P7 updater's channel0 helper. Diagnostic 010 uses
 * only its supported modes: owner/text=255 (steady), input=100ms,
 * MVC/content/model/viewer/gate=50ms, all other reasons=250ms. This does not
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
 mov d0,d1
 and 0xffffff00,d1
 cmp 0x700,d1
 beq .Ldisplay
 cmp 0xc00,d1
 beq .Linput
 cmp 0x800,d1
 beq .Lpage
 cmp 0x900,d1
 beq .Lpage
 cmp 0xa00,d1
 beq .Lpage
 cmp 0xb00,d1
 beq .Lpage
 cmp 0xd00,d1
 beq .Lpage
 mov 250,d1
 bra .Lsignal
.Ldisplay:
 mov 255,d1
 bra .Lsignal
.Linput:
 mov 100,d1
 bra .Lsignal
.Lpage:
 mov 50,d1
.Lsignal:
 clr d0
 call ep7_stock_terminal_af_unresolved,[d2,d3],28
.Lhold:
 and 0xf7ff,psw
.Lquarantined:
 bra .Lquarantined
.size _ep7_gcc_quarantine,.-_ep7_gcc_quarantine
