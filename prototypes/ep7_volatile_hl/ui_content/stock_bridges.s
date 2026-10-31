/* GCC D0 category,D1 pointer to two original stack words {key,mode}.
 * Creator14 reads THREE halfwords, including the low half of mode. */
.text
.global _ep7_gcc_mvc_stock_create
.type _ep7_gcc_mvc_stock_create,@function
_ep7_gcc_mvc_stock_create:
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 mov d1,a0
 cmp 0,d0
 beq .Lstock_create0
 cmp 3,d0
 beq .Lstock_create14
 call ep7_stock_mvc_creator7_unresolved,[],0
 bra .Lstock_created
.Lstock_create0:
 call ep7_stock_mvc_creator0_unresolved,[],0
 bra .Lstock_created
.Lstock_create14:
 call ep7_stock_mvc_creator14_unresolved,[],0
.Lstock_created:
 mov a0,d0
 ret [d2,d3,a2,a3],20
.size _ep7_gcc_mvc_stock_create,.-_ep7_gcc_mvc_stock_create

.global _ep7_gcc_mvc_stock_selected
.type _ep7_gcc_mvc_stock_selected,@function
_ep7_gcc_mvc_stock_selected:
 add -4,sp
 mov d0,a0
 call ep7_stock_mvc_stock_selected_unresolved,[a2],8
 ret [],4
.size _ep7_gcc_mvc_stock_selected,.-_ep7_gcc_mvc_stock_selected

.global _ep7_gcc_mvc_transition_timers
.type _ep7_gcc_mvc_transition_timers,@function
_ep7_gcc_mvc_transition_timers:
 add -4,sp
 call ep7_stock_mvc_stop535_unresolved,[],4
 mov 537,d0
 call ep7_stock_ui_timer_cancel_unresolved,[d2],8
 mov 572,d0
 call ep7_stock_ui_timer_cancel_unresolved,[d2],8
 ret [],4
.size _ep7_gcc_mvc_transition_timers,.-_ep7_gcc_mvc_transition_timers
