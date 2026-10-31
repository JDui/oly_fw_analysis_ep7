/* Owned terminal hold for an inconsistent live cleanup. D0 carries the reason.
 * Disable maskable interrupts on this core, then remain in a no-call loop.
 * No extra stack, BREAK/diagnostic entry, return, native reset/free/ACK or retry.
 * This intentionally stops local task progress and retains owned resources.
 * NMI, watchdog/reset and other-core behavior remain hardware responsibilities. */
.text
.global _ep7_gcc_quarantine
.type _ep7_gcc_quarantine,@function
_ep7_gcc_quarantine:
 and 0xf7ff,psw
.Lquarantined:
 bra .Lquarantined
.size _ep7_gcc_quarantine,.-_ep7_gcc_quarantine
