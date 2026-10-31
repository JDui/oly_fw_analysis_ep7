/* Original factory dispatch entry60d337b2 uses CALL[b0],24. Reuse it rather
 * than rebuilding the native allocation/constructor/resource-init sequence.
 * Own frame40: return W0, service W4, saved bytes W8/9, owner W12, resource W16,
 * result W20, saved four GCC registers W24..39, GCC return S=W40.
 * Third GCC argument is at S12 = W52. All nested native frames are below W.
 * Normal-return only, with stable live service and exclusive GUI context. */
.text
.global _ep7_gcc_text_factory
.type _ep7_gcc_text_factory,@function
_ep7_gcc_text_factory:
 movm [d2,d3,a2,a3],(sp)
 add -24,sp
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov (52,sp),d0
 mov d0,(20,sp)
 call ep7_stock_ui_service_unresolved,[],0
 mov a0,(4,sp)
 mov sp,a1
 add 8,a1
 mov a1,d0
 add 1,d0
 call ep7_stock_ui_context_get_unresolved,[],0
 mov (12,sp),d1
 mov (16,sp),a1
 mov 32784,d0
 call ep7_stock_widget_factory_unresolved,[d2,a2,a3],24
 cmp 0,a0
 bne .Ltext_allocated
 clr d0
.Ltext_allocated:
 mov (20,sp),a1
 mov a0,(a1)
 mov d0,(4,a1)
 mov (4,sp),a0
 movbu (8,sp),d0
 movbu (9,sp),d1
 call ep7_stock_ui_context_set_unresolved,[],0
 ret [d2,d3,a2,a3],40
.size _ep7_gcc_text_factory,.-_ep7_gcc_text_factory
