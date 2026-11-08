/* Observer frames use the same register and PSW preservation as 015 H/L. */
.text
.macro preserve
 movm [d2,d3,a2,a3,other],(sp)
 mov psw,d2
 add -16,sp
 mov d2,(16,sp)
.endm
.macro restore
 mov (16,sp),d2
 add 16,sp
 mov d2,psw
 movm (sp),[d2,d3,a2,a3,other]
.endm

/* All successful claims have set the native busy byte before this store. */
.global ep7dr_metadata_claim_bridge
ep7dr_metadata_claim_bridge:
 movbu d0,(0x6223e5d0)
 preserve
 mov a0,d0
 call _ep7dr_reset_metadata,[],0
 restore
 ret [a2],20

.global ep7dr_capture_claim_bridge
ep7dr_capture_claim_bridge:
 call ep7dr_stock_capture_pointer,[d2,d3,a2,a3],44
 preserve
 call _ep7dr_claim_capture,[],0
 restore
 ret [d2,d3,a2,a3],44

.global ep7dr_capture_release_bridge
ep7dr_capture_release_bridge:
 preserve
 mov (12,a2),d0
 call _ep7dr_release_capture,[],0
 restore
 jmp ep7dr_stock_capture_release

/* Event 0x4b. D2 is the selected node and A2 its controller command. */
.global ep7dr_selected_bridge
ep7dr_selected_bridge:
 call ep7dr_stock_selected_metadata,[d2,d3,a2,a3],64
 preserve
 mov (60,sp),d0
 mov a2,d1
 call _ep7dr_capture_result,[],0
 restore
 jmp ep7dr_stock_selected_resume

/* StlTake calls the same metadata writer with D0=0, A1=its command. */
.global ep7dr_still_result_bridge
ep7dr_still_result_bridge:
 mov a1,(12,sp)
 call ep7dr_stock_selected_metadata,[d2,d3,a2,a3],64
 preserve
 mov (76,sp),d0
 call _ep7dr_still_result,[],0
 restore
 ret [d2,d3,a2,a3],64

.global ep7dr_clone_bridge
ep7dr_clone_bridge:
 preserve
 mov a0,d0
 mov a1,d1
 call _ep7dr_capture_clone,[],0
 restore
 jmp ep7dr_015_clone_bridge

.global ep7dr_clone_release_bridge
ep7dr_clone_release_bridge:
 preserve
 call _ep7dr_release_clone,[],0
 restore
 call ep7dr_stock_clone_release,[d2],16
 jmp ep7dr_stock_clone_resume

/* 603f2800 keeps the descriptor in A3 across the native conversion. */
.global ep7dr_convert_bridge
ep7dr_convert_bridge:
 preserve
 mov a0,d0
 call _ep7dr_development_plan,[],0
 mov d0,(76,sp)               /* Original frame +12, outside callee homes. */
 restore
 call ep7dr_stock_still_convert,[d2,d3,a2,a3],72
 preserve
 exthu d0
 cmp 0,d0
 bne .Lconverted
 mov a3,d0
 mov (76,sp),d1
 call _ep7dr_bind_job,[],0
 cmp 0,d0
 beq .Lconverted
 restore
 mov 0x9e02,d0
 ret [d2,d3,a2,a3],72
.Lconverted:
 restore
 ret [d2,d3,a2,a3],72
