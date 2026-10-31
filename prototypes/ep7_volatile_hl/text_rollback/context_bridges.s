/* Self-authored GCC veneers. Native addresses are link-time bindings only.
 * service/get-selection/set-selection are exact leaves, not GCC virtual casts.
 * These functions do not acquire a lock or authorize service/object lifetime. */
.text
.global _ep7_gcc_ui_service
.type _ep7_gcc_ui_service,@function
_ep7_gcc_ui_service:
 add -4,sp
 call ep7_stock_ui_service_unresolved,[],0
 mov a0,d0
 ret [],4
.size _ep7_gcc_ui_service,.-_ep7_gcc_ui_service

.global _ep7_gcc_ui_context_exchange
.type _ep7_gcc_ui_context_exchange,@function
_ep7_gcc_ui_context_exchange:
 movm [a2],(sp)
 add -16,sp
 mov d0,a2
 mov d1,(12,sp)
 mov a2,a0
 mov sp,a1
 add 8,a1
 mov a1,d0
 add 1,d0
 /* Getter owns a MOVM[a2]/RETF4 self-prologue. Outputs at W+8 and W+9. */
 call ep7_stock_ui_context_get_unresolved,[],0
 mov a2,a0
 mov (12,sp),d0
 mov d0,d1
 lsr 8,d1
 call ep7_stock_ui_context_set_unresolved,[],0
 movbu (8,sp),d0
 movbu (9,sp),d1
 asl 8,d1
 or d1,d0
 ret [a2],20
.size _ep7_gcc_ui_context_exchange,.-_ep7_gcc_ui_context_exchange

.global _ep7_gcc_ui_context_select
.type _ep7_gcc_ui_context_select,@function
_ep7_gcc_ui_context_select:
 add -4,sp
 mov d0,a0
 mov d1,d0
 lsr 8,d1
 call ep7_stock_ui_context_set_unresolved,[],0
 ret [],4
.size _ep7_gcc_ui_context_select,.-_ep7_gcc_ui_context_select
