/* E-P7 axis text, using an existing native text child's font.
 * Native owner creation60d7ab4f..5b initializes58 child pointers at+792.
 * Save the incoming origin/clip before recursive child painting. Only the
 * 36-byte geometry prefix is kept across recursion, not the large context.
 * Layer1 owns a compact native translucent backdrop, layer2 the lettering.
 * No widget allocation or retained owner pointer. */
.text
.global ep7h_paint
ep7h_paint:
 movm [d2,d3,a2,a3],(sp)
 add -60,sp
 mov a0,a2
 mov a1,(20,sp)
 cmp 0,a1
 beq .Lstock_only
 mov (8,a1),a0
 cmp 0,a0
 beq .Lstock_only
 mov sp,a1
 add 24,a1
 mov 9,d1
.Lgeometry_save:
 mov (a0),d0
 mov d0,(a1)
 inc4 a0
 inc4 a1
 add -1,d1
 bne .Lgeometry_save
 mov a2,a0
 mov (20,sp),a1
 call ep7_stock_h_paint_unresolved,[],0
 mov (20,sp),a1
 add -732,sp
 mov a1,(20,sp)
 mov d0,(16,sp)
 call _ep7h_visible,[],0
 cmp 0,d0
 beq .Ldone
 mov (20,sp),a0
 cmp 0,a0
 beq .Ldone
 movhu (4,a0),d0
 sub 1,d0
 cmp 2,d0
 bcc .Ldone
 mov d0,(28,sp)
 mov (8,a0),a0
 cmp 0,a0
 beq .Ldone
 /* E-P7 child20, Color heading: left456/496; wheel center480/520. */
 mov (872,a2),a1
 cmp 0,a1
 beq .Ldone
 movhu (8,a1),d0
 add 24,d0
 mov d0,(24,sp)
 /* Prefer the Color heading if it is a native text. Otherwise use one
  * of the owner's bounded58 native child entries. Text constructor60d4be23
  * sets type0x8010; its resource binding owns font+128. */
 movhu (4,a1),d0
 and 8191,d0
 cmp 16,d0
 beq .Lfont_child
 mov a2,a0
 add 792,a0
 mov 58,d1
.Lfind_text:
 mov (a0),a1
 cmp 0,a1
 beq .Lfind_next
 movhu (4,a1),d0
 and 8191,d0
 cmp 16,d0
 beq .Lfont_child
.Lfind_next:
 inc4 a0
 add -1,d1
 bne .Lfind_text
 bra .Ldone
.Lfont_child:
 movhu (128,a1),d0
 mov d0,(36,sp)
 /* The first native text child uses foreground0, which is transparent in the
  * shooting text CLUT (resource54). Borrow its font, not that invisible ink.
  * Entry4 is opaque white; entry16 is opaque black for outline and shadow. */
 mov 4,d0
 mov d0,(732,sp)
 mov 16,d0
 mov d0,(736,sp)
 mov d0,(740,sp)
 /* Center this independent label without widget margins. */
 mov 257,d0
 movhu d0,(744,sp)
 clr d0
 movhu d0,(746,sp)
 mov d0,(748,sp)
 mov d0,(752,sp)
 mov (20,sp),a0
 mov (8,a0),a0
 mov sp,a3
 add 48,a3
 mov a3,a1
 mov 171,d1
.Lcopy:
 mov (a0),d0
 mov d0,(a1)
 inc4 a0
 inc4 a1
 add -1,d1
 bne .Lcopy
 /* Child painting may leave a different local clip/origin. Use the incoming
  * container geometry for our global title rectangle. */
 mov sp,a0
 add 756,a0
 mov a3,a1
 mov 9,d1
.Lgeometry_restore:
 mov (a0),d0
 mov d0,(a1)
 inc4 a0
 inc4 a1
 add -1,d1
 bne .Lgeometry_restore
 mov (24,sp),d0
 add -48,d0
 movhu d0,(40,sp)
 add 95,d0
 movhu d0,(44,sp)
 mov (28,sp),d0
 cmp 0,d0
 bne .Ltext
 mov 12,d0
 movhu d0,(42,sp)
 mov 51,d0
 movhu d0,(46,sp)
 mov a3,a0
 mov -1,d0
 call ep7_stock_h_pen_unresolved,[d2,d3,a2,a3],16
 mov a3,a0
 mov -2,d0
 mov -1,d1
 /* Native OSD CLUT resources5/53 map entry1 to0x88000000 (entry2:0xcc000000). */
 mov 1,a1
 call ep7_stock_h_brush_unresolved,[d2,d3,a2],16
 mov a3,a0
 mov sp,a1
 add 40,a1
 call ep7_stock_h_rectangle_unresolved,[d2,a2,a3],52
 bra .Ldone
.Ltext:
 mov a3,a0
 mov (36,sp),d0
 call ep7_stock_h_font_unresolved,[a2],8
 cmp 0,a0
 beq .Ldone
 mov a0,(32,sp)
 mov 2,d0
 movhu d0,(52,a3)
 mov 16,d0
 movhu d0,(42,sp)
 mov 47,d0
 movhu d0,(46,sp)
 mov (_ep7h_axis),d0
 mov .Lsaturation,d1
 cmp 1,d0
 bne .Lnot_hue
 mov .Lhue,d1
 bra .Ltitle
.Lnot_hue:
 cmp 2,d0
 bne .Ltitle
 mov .Llightness,d1
.Ltitle:
 mov a3,a0
 mov sp,a1
 add 40,a1
 mov a1,d0
 add 692,d0
 call ep7_stock_h_text_unresolved,[d2,d3,a2,a3],252
 mov (32,sp),a0
 call ep7_stock_h_font_release_unresolved,[],4
.Ldone:
 mov (16,sp),d0
 add 792,sp
 ret [d2,d3,a2,a3],16
.Lstock_only:
 mov a2,a0
 mov (20,sp),a1
 call ep7_stock_h_paint_unresolved,[],0
 add 60,sp
 ret [d2,d3,a2,a3],16
.balign 4
.Lsaturation:
 .short 'S','a','t',0
.Lhue:
 .short 'H','u','e',0
.Llightness:
 .short 'L','u','m',0
