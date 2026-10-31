/* Original short-call order matches cohort.c. No padding between veneers. */
.include "far_call.inc"
.section .text.ep7_input_far_calls,"ax"
.global ep7_input_far_calls
ep7_input_far_calls:
EP7_FAR_CALL ep7_input_far_60ea0070,ep7_native_ui_wheel_sample_bridge,0x60ea0075,0x00,0
EP7_FAR_CALL ep7_input_far_60ea00f7,ep7_native_ui_wheel_sample_bridge,0x60ea00fc,0x00,0
EP7_FAR_CALL ep7_input_far_60ea0d70,ep7_native_ui_wheel_sample_bridge,0x60ea0d75,0x00,0
EP7_FAR_CALL ep7_input_far_60ea0deb,ep7_native_ui_wheel_sample_bridge,0x60ea0df0,0x00,0
EP7_FAR_CALL ep7_input_far_60ea0e66,ep7_native_ui_wheel_sample_bridge,0x60ea0e6b,0x00,0
.global ep7_input_far_calls_end
ep7_input_far_calls_end:
