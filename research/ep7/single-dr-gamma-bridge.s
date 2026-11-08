/* Strict-runner fixture only. R+1884 is a test-owned byte appended to each
 * synthetic request. It has no allocation or writer in stock/015. */
.am33_2
.text
.global single_dr_gamma_bridge
single_dr_gamma_bridge:
 movm [d2,d3,a2,a3,other],(sp)
 mov psw,d2
 add -16,sp
 mov d2,(16,sp)

 cmp 1,d0                       /* original selector's successful result */
 bne .Lresume
 mov (104,sp),a0                /* native SP+40 is the current request */
 movbu (1884,a0),d1
 cmp 1,d1
 bcs .Lresume
 cmp 3,d1
 bcc .Lresume

 mov (132,sp),d0                /* native SP+68, +72 and +76 */
 mov (136,sp),d2
 cmp d0,d2
 bne .Lresume
 mov (140,sp),d2
 cmp d0,d2
 bne .Lresume
 mov .Ltables,a1
 mov 3,d3
.Lfind:
 mov (a1),d2
 cmp d0,d2
 beq .Lreplace
 add 12,a1
 add -1,d3
 bne .Lfind
 bra .Lresume
.Lreplace:
 asl2 d1
 mov (d1,a1),a1
 mov a1,(132,sp)
 mov a1,(136,sp)
 mov a1,(140,sp)

.Lresume:
 mov (16,sp),d2
 add 16,sp
 mov d2,psw
 movm (sp),[d2,d3,a2,a3,other]
 movbu d0,(60,sp)               /* displaced 603ae830 */
 mov (36,sp),a0                 /* displaced 603ae833 */
 jmp fixture_gamma_resume

.balign 4
.Ltables:
 .long 0x604ede78, fixture_gamma_luts,      fixture_gamma_luts+512
 .long 0x604ee078, fixture_gamma_luts+1024, fixture_gamma_luts+1536
 .long 0x604f3e78, fixture_gamma_luts+2048, fixture_gamma_luts+2560
