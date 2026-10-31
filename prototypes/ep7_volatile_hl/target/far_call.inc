/* A five-byte JMP at a native short-CALL site can reach this30-byte veneer.
 * Real CALL creates the original save/frame tuple. Repair BOTH stack return
 * and MDR before entering the actual adapter. ADD immediate,SP changes no PSW.
 * One extra4-byte scratch word below the native frame is live during repair.
 * No site/placement is authorized by including this macro; each runtime cohort
 * must explicitly validate its own site and known veneer before admission.
 */
.macro EP7_FAR_CALL name,target,resume,mask,frame
 .if ((\mask) < 0) || ((\mask) > 240) || ((\mask) & 15)
  .error "far call supports only d2/d3/a2/a3 save bits"
 .endif
 .if ((\frame) < 0) || ((\frame) > 248) || ((\frame) & 3)
  .error "far call frame must be aligned and fit the repair SP displacement"
 .endif
 .if (\frame) < (4*((((\mask)>>7)&1)+(((\mask)>>6)&1)+(((\mask)>>5)&1)+(((\mask)>>4)&1)))
  .error "far call frame overlaps its saved registers"
 .endif
 .global \name
 .type \name,@function
\name:
 /* An actual CD CALL to the next instruction; keep its exact five bytes. */
 .byte 0xcd
 .short 5
 .byte \mask,\frame
 add -4,sp
 mov d0,(sp)
 mov \resume,d0
 mov d0,(\frame+4,sp)
 mov d0,mdr
 mov (sp),d0
 add 4,sp
 jmp \target
 .size \name,.-\name
.endm
