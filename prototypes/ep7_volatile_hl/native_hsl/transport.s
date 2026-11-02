/* Exact build1100 native snapshot seams. Save original caller context around
 * the GCC observer, then replay the complete displaced native instructions. */
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

/* The last typed getter in native capture population. All COLOR/S fields have
 * already been stored. Preserve its return inD0 for the following MOVBU. */
.global ep7h_capture_sample_bridge
ep7h_capture_sample_bridge:
 call ep7_stock_h_capture_get_unresolved,[d2,d3],12
 preserve
 mov d3,d0
 call _ep7h_capture_sample,[],0
 restore
 ret [d2,d3],12

/* Native S copy has finished. Full64-byte observer frame sits below oldSP. */
.global ep7h_capture_to_job_bridge
ep7h_capture_to_job_bridge:
 preserve
 mov (84,sp),d0
 mov d3,d1
 call _ep7h_capture_to_job,[],0
 restore
 mov (20,sp),a0
 movbu (24086,a0),d0
 jmp ep7_stock_h_capture_copy_resume_unresolved

.global ep7h_alternate_to_job_bridge
ep7h_alternate_to_job_bridge:
 preserve
 mov (88,sp),d0
 mov (84,sp),d1
 call _ep7h_capture_to_job,[],0
 restore
 mov (24,sp),a0
 movbu (24086,a0),d0
 jmp ep7_stock_h_alternate_copy_resume_unresolved

/* The sole native temporary-clone copy; snapshot metadata before original copy.
 * Original arguments/frame remain intact for the tail-transfer to native memcpy. */
.global ep7h_capture_clone_bridge
ep7h_capture_clone_bridge:
 preserve
 mov a0,d0
 mov a1,d1
 call _ep7h_capture_clone,[],0
 restore
 jmp ep7_stock_h_capture_memcpy_unresolved

/* Retarget the existing short COLOR-builder CALL with its original f0/96 frame.
 * All native result registers and MDR survive the observer, as in PEN-F. */
.global ep7h_color_builder_bridge
ep7h_color_builder_bridge:
 call .Lcolor,[d2,d3,a2,a3],96
 jmp ep7_stock_h_color_resume_unresolved
.Lcolor:
 call ep7_stock_h_color_builder_unresolved,[d2,d3,a2,a3],96
 preserve
 mov a2,d0
 call _ep7h_transport_apply,[],0
 restore
 ret [d2,d3,a2,a3],96

/* Native borrowed-table packer has the same output fields, but its own80-byte
 * frame. Keep the native table immutable and apply H/L to this output only. */
.global ep7h_generic_color_bridge
ep7h_generic_color_bridge:
 call ep7_stock_h_generic_builder_unresolved,[d2,d3,a2,a3],80
.Lgeneric_return:
 preserve
 mov (28,sp),d1
 cmp .Lgeneric_return,d1
 bne .Lgeneric_mdr_saved
 mov ep7_stock_h_generic_resume_unresolved,d1
 mov d1,(28,sp)
.Lgeneric_mdr_saved:
 mov a2,d0
 call _ep7h_transport_apply,[],0
 restore
 jmp ep7_stock_h_generic_resume_unresolved
