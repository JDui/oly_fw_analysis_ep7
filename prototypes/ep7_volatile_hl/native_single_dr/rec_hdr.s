.text

/* The stock HDR action has already passed the still-view admission check.
 * D0 is the normalized key event and D2 is its native action. */
.global ep7dr_rec_hdr_press_bridge
ep7dr_rec_hdr_press_bridge:
 cmp 14,d2
 bne .Lstock_key
 cmp 0x01000006,d0
 bcs .Lstock_key
 cmp 0x01000009,d0
 bhi .Lstock_key
 cmp 0x01000006,d0
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
.Lstock_key:
 mov d0,d1
 mov d2,d0
 call ep7rec_native_key_record,[d2,d3],12
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
 call ep7rec_native_one_shot,[d2,a2,a3],32
.Lrec_take_return:
 ret [],4
.Lstock_event:
 call ep7rec_native_one_shot,[d2,a2,a3],32
 ret [],4

/* This seam follows the native permission guard. A marked request requires
 * standby so it cannot take over a physical half-press already in progress. */
.global ep7dr_rec_hdr_admission_bridge
ep7dr_rec_hdr_admission_bridge:
 call ep7rec_native_capture_state,[],0
 mov (32,sp),d1
 cmp .Lrec_take_return,d1
 bne .Lstock_admission
 cmp 1,d0
 bne .Lreply
 mov (16,sp),d0
 call _ep7rec_begin,[],0
 cmp 1,d0
 bne .Lreply
 jmp ep7rec_native_capture_standby
.Lreply:
 jmp ep7rec_native_capture_reply
.Lstock_admission:
 cmp 1,d0
 bne .Lother_state
 jmp ep7rec_native_capture_standby
.Lother_state:
 jmp ep7rec_native_capture_other_state

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

/* Both terminal paths clear the native trigger bit. Restore the effective
 * mode before that bit can admit another release. The original leaf returns
 * via MDR, so keep the caller's MDR across the C helper. */
.global ep7dr_rec_hdr_clear_bridge
ep7dr_rec_hdr_clear_bridge:
 add -20,sp
 mov d0,(4,sp)
 mov a0,(8,sp)
 mov a1,(12,sp)
 mov mdr,d1
 mov d1,(16,sp)
 mov d0,d1
 mov a0,d0
 call _ep7rec_end,[],0
 mov (16,sp),d1
 mov d1,mdr
 mov (4,sp),d0
 mov (8,sp),a0
 mov (12,sp),a1
 add 20,sp
 jmp ep7rec_native_clear_trigger

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

.section .rodata
.balign 4
ep7rec_event_methods:
 .long 0x607765f4, 0x60a4d3d7, 0x6077551e, 0x60768470, 0x60768477, 0x60a4d428
 .long 0x60a4d42e, 0x60a4d434, 0x60a4d43a, 0x60a4d440, 0x60a4d446, 0x60a4d3d4
 .long 0x60a4d40c, 0x60a4d404, 0x60a4d410, 0x60a4d408, 0x60a4d413, 0x60a4d3c7

.global ep7dr_rec_hdr_options_bridge
ep7dr_rec_hdr_options_bridge:
 .short 3453, 44, 106, 84, 85, 88, 3461, 34, 3474, 568, 426, 473, 3200
