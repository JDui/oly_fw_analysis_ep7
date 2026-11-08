.text

/* D0 is the action and A1 is the shooting-view input packet. Intercept before
 * the stock HDR subapp disables releases until its own exit handler runs. */
.global ep7dr_rec_hdr_press_bridge
ep7dr_rec_hdr_press_bridge:
 cmp 14,d0
 bne .Lstock_key
 mov d1,(28,sp)
 mov a1,a2
 mov (a2),d0
 mov d0,(4,sp)
 mov (4,a2),d0
 mov d0,(8,sp)
 call ep7rec_native_normalize_key,[d2],4
 cmp 0x01000006,d0
 bcs .Lrestore_stock_key
 cmp 0x01000009,d0
 bhi .Lrestore_stock_key
 cmp 0x01000006,d0
 bne .Lkey_consumed
 mov 1,d0
 mov d0,(_ep7rec_status)
 mov 40,d0
 call ep7rec_native_subapp_active,[d2,d3],12
 cmp 0,d0
 bne .Lkey_consumed
 mov 24,d0
 call ep7rec_native_get,[],4
 cmp 3,d0
 bcs .Lkey_consumed
 cmp 6,d0
 bhi .Lkey_consumed
 call ep7rec_native_submit,[d2,a2,a3],60
.Lrec_submit_return:
.Lkey_consumed:
 jmp ep7rec_native_key_return
.Lrestore_stock_key:
 mov (28,sp),d1
 mov a2,a1
 mov 14,d0
.Lstock_key:
 mov a1,a2
 mov d0,d2
 mov sp,a0
 add 28,a0
 jmp ep7rec_native_key_continue

/* The native one-shot API is also used by the interval timer. The Rec caller
 * uses the same busy checks after excluding an active interval session. */
.global ep7dr_rec_hdr_sdk_guard_bridge
ep7dr_rec_hdr_sdk_guard_bridge:
 mov (68,sp),d0
 cmp .Lrec_submit_return,d0
 bne .Linterval_guard
 bra .Lrec_guard

.global ep7dr_rec_hdr_capture_guard_bridge
ep7dr_rec_hdr_capture_guard_bridge:
 mov (40,sp),d0
 cmp .Lrec_take_return,d0
 bne .Linterval_guard
.Lrec_guard:
 mov 478,d0
 call ep7rec_native_get_setting,[],4
 cmp 0,d0
 bne .Lguard_reject
 jmp ep7rec_native_busy_guard
.Lguard_reject:
 clr d0
 ret [],8
.Linterval_guard:
 jmp ep7rec_native_interval_guard

/* Use the actual event object for identity. All of its fields and virtual
 * methods keep the native one-shot ABI. No separate queue or key latch. */
.global ep7dr_rec_hdr_create_bridge
ep7dr_rec_hdr_create_bridge:
 mov (64,sp),d0
 cmp .Lrec_submit_return,d0
 bne .Lstock_event_create
 call ep7rec_native_create_event,[],4
 mov ep7rec_event_methods,d0
 mov d0,(a0)
 mov 2,d0
 mov d0,(_ep7rec_status)
 mov 1007,d0
 ret [],4
.Lstock_event_create:
 jmp ep7rec_native_create_event

.global ep7dr_rec_hdr_event_bridge
ep7dr_rec_hdr_event_bridge:
 mov (104,a0),a1
 mov (2832,a0),a0
 cmp 0,a1
 beq .Lstock_event
 mov (a1),d0
 cmp ep7rec_event_methods,d0
 bne .Lstock_event
 mov 3,d0
 mov d0,(_ep7rec_status)
 call ep7rec_native_one_shot,[d2,a2,a3],32
.Lrec_take_return:
 ret [],4
.Lstock_event:
 call ep7rec_native_one_shot,[d2,a2,a3],32
 ret [],4

/* The native one-shot gate is the interval-session bit. Rec uses the normal
 * still release checks in ep7rec_begin and enters the same standby handler. */
.global ep7dr_rec_hdr_admission_bridge
ep7dr_rec_hdr_admission_bridge:
 mov (32,sp),d0
 cmp .Lrec_take_return,d0
 bne .Linterval_admission
 call ep7rec_native_capture_state,[],0
 cmp 1,d0
 bne .Lnot_standby
 mov (16,sp),d0
 call _ep7rec_begin,[],0
 cmp 1,d0
 bne .Lreply
 jmp ep7rec_native_capture_standby
.Lnot_standby:
 mov 9,d0 /* REC_NOT_STANDBY */
 mov d0,(_ep7rec_status)
.Lreply:
 jmp ep7rec_native_capture_reply
.Linterval_admission:
 mov (16,sp),a0
 mov 2,d0
 call ep7rec_native_interval_admission,[d2],4
 jmp ep7rec_native_interval_admission_resume

/* Keep native admission and roll back the Rec scope if it refused the shot. */
.global ep7dr_rec_hdr_standby_bridge
ep7dr_rec_hdr_standby_bridge:
 mov (40,sp),d1
 cmp .Lrec_take_return,d1
 bne .Lstock_standby_guard
 mov a0,a2
 add -4,sp
 call ep7rec_native_standby_guard,[a2],8
 mov a2,d0
 call _ep7rec_after_standby_guard,[],0
 ret [a2],12
.Lstock_standby_guard:
 jmp ep7rec_native_standby_guard

/* Native silent eligibility excludes every bracket kind. Admit HDR's kind
 * for the Rec-owned capture and continue with all other native checks. */
.global ep7dr_rec_hdr_silent_guard_bridge
ep7dr_rec_hdr_silent_guard_bridge:
 cmp 0,d0
 beq .Lsilent_continue
 cmp 4,d0
 bne .Lsilent_block
 mov (_ep7rec_owner),d0
 cmp 0,d0
 beq .Lsilent_block
 cmp d0,a2
 bne .Lsilent_block
.Lsilent_continue:
 jmp ep7rec_native_silent_continue
.Lsilent_block:
 jmp ep7rec_native_silent_block

/* The stock reset runs on both standby exit and capture abort. Retain its
 * trigger clear and preserve the caller's MDR across the C helper. */
.global ep7dr_rec_hdr_clear_bridge
ep7dr_rec_hdr_clear_bridge:
 add -20,sp
 mov d0,(4,sp)
 mov a0,(8,sp)
 mov a1,(12,sp)
 mov mdr,d1
 mov d1,(16,sp)
 mov a0,d0
 call _ep7rec_on_trigger_reset,[],0
 mov (16,sp),d1
 mov d1,mdr
 mov (4,sp),d0
 mov (8,sp),a0
 mov (12,sp),a1
 add 20,sp
 jmp ep7rec_native_clear_trigger

/* Native entrySTANDBY has inspected the previous sequence and is about to
 * publish standby and check for new shutter input. */
.global ep7dr_rec_hdr_idle_bridge
ep7dr_rec_hdr_idle_bridge:
 add -4,sp
 mov a3,d0
 call _ep7rec_end,[],0
 add 4,sp
 mov 1,d0
 jmp ep7rec_native_set_capture_state

/* The native BODY wire fields are word-aligned and eight bytes wide.
 * Select a read-only, seven-character label for the last Rec attempt. */
.global ep7dr_rec_hdr_version_body_bridge
ep7dr_rec_hdr_version_body_bridge:
 mov (a1),d0
 cmp 0x002e0031,d0
 bne .Lbody_stock
 mov (4,a1),d0
 cmp 0x00000031,d0
 bne .Lbody_stock
 mov (_ep7rec_status),d0
 cmp 12,d0
 bhi .Lbody_default
 asl 4,d0
 mov _ep7rec_version_labels,a1
 add d0,a1
.Lbody_stock:
 jmp ep7dr_stock_version_set_text_unresolved
.Lbody_default:
 jmp ep7dr_version_body_bridge

.global _ep7rec_get
_ep7rec_get:
 add -4,sp
 call ep7rec_native_get,[],4
 ret [],4

.global _ep7rec_get_setting
_ep7rec_get_setting:
 add -4,sp
 call ep7rec_native_get_setting,[],4
 ret [],4

.global _ep7rec_write_effective
_ep7rec_write_effective:
 add -4,sp
 call ep7rec_native_write_effective,[d2,d3,a2],20
 ret [],4

.global _ep7rec_settings_inhibit
_ep7rec_settings_inhibit:
 jmp ep7rec_native_settings_inhibit

.global _ep7rec_get_trigger
_ep7rec_get_trigger:
 jmp ep7rec_native_get_trigger

.global _ep7rec_judge_sequence
_ep7rec_judge_sequence:
 add -4,sp
 mov d0,a0
 call ep7rec_native_judge_sequence,[d2,d3,a2,a3],24
 ret [],4

.global _ep7rec_publish_sequence
_ep7rec_publish_sequence:
 jmp ep7rec_native_publish_sequence

.global _ep7rec_latch_release
_ep7rec_latch_release:
 jmp ep7rec_native_latch_release

.global _ep7rec_unlatch_release
_ep7rec_unlatch_release:
 jmp ep7rec_native_unlatch_release

.global _ep7rec_get_release_event
_ep7rec_get_release_event:
 jmp ep7rec_native_get_release_event

.global _ep7rec_set_release_event
_ep7rec_set_release_event:
 jmp ep7rec_native_set_release_event

.global _ep7rec_full_release
_ep7rec_full_release:
 add -4,sp
 mov d0,a0
 mov d1,d0
 mov (a0),a1
 mov (4452,a1),a1
 calls (a1)
 ret [],4

.section .rodata
.balign 4
ep7rec_event_methods:
 .long 0x607765f4, 0x60a4d3d7, 0x6077551e, 0x60768470, 0x60768477, 0x60a4d428
 .long 0x60a4d42e, 0x60a4d434, 0x60a4d43a, 0x60a4d440, 0x60a4d446, 0x60a4d3d4
 .long 0x60a4d40c, 0x60a4d404, 0x60a4d410, 0x60a4d408, 0x60a4d413, 0x60a4d3c7

.global ep7dr_rec_hdr_options_bridge
ep7dr_rec_hdr_options_bridge:
 .short 3453, 44, 106, 84, 85, 88, 3461, 34, 3474, 568, 426, 473, 3200
