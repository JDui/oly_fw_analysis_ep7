/* Epoch observers BEFORE the original engine writes. Both bridges tail-transfer
 * with the complete original argument/register/stack state. No substituted
 * engine configuration, callback, or workrecord allocation is performed here. */
.text
.macro engine_save
 add -40,sp
 mov d0,(12,sp)
 mov d1,(16,sp)
 mov a0,(20,sp)
 mov a1,(24,sp)
 mov d2,(32,sp)
 mov mdr,d2
 mov d2,(28,sp)
.endm
.macro engine_restore
 mov (28,sp),d2
 mov d2,mdr
 mov (32,sp),d2
 mov (12,sp),d0
 mov (16,sp),d1
 mov (20,sp),a0
 mov (24,sp),a1
 add 40,sp
.endm
.global ep7_native_engine_configure
.type ep7_native_engine_configure,@function
ep7_native_engine_configure:
 engine_save
 call _ep7cn_engine_epoch,[],0
 engine_restore
 jmp ep7_stock_engine_configure_unresolved
.size ep7_native_engine_configure,.-ep7_native_engine_configure
.global ep7_native_engine_pool
.type ep7_native_engine_pool,@function
ep7_native_engine_pool:
 engine_save
 call _ep7cn_engine_epoch,[],0
 engine_restore
 jmp ep7_stock_engine_pool_unresolved
.size ep7_native_engine_pool,.-ep7_native_engine_pool
