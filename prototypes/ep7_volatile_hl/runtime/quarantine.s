/* Owned terminal hold for an inconsistent live cleanup. D0 carries the reason.
 * No native reset/free/ACK, no stock fall-through even if a debugger continues.
 * Actual exception-vector/debugger behavior remains a G6/device qualification.
 * Do not call the stock single BREAK at6003853d: its next byte is a different
 * context-switch routine, not a returning fatal-handler contract. */
.text
.global _ep7_gcc_quarantine
.type _ep7_gcc_quarantine,@function
_ep7_gcc_quarantine:
.Lquarantined:
 break
 bra .Lquarantined
.size _ep7_gcc_quarantine,.-_ep7_gcc_quarantine
