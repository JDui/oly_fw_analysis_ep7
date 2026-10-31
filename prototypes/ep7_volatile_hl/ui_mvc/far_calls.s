/* Original short-call order matches cohort.c. No padding between veneers. */
.include "far_call.inc"
.section .text.ep7_mvc_far_calls,"ax"
.global ep7_mvc_far_calls
ep7_mvc_far_calls:
EP7_FAR_CALL ep7_mvc_far_60e261d4,ep7_native_content_rebuild_bridge,0x60e261d9,0xf0,28
EP7_FAR_CALL ep7_mvc_far_60e26201,ep7_native_content_rebuild_bridge,0x60e26206,0xf0,28
EP7_FAR_CALL ep7_mvc_far_60e26226,ep7_native_content_rebuild_bridge,0x60e2622b,0xf0,28
EP7_FAR_CALL ep7_mvc_far_60e269f0,ep7_native_content_rebuild_bridge,0x60e269f5,0xf0,28
.global ep7_mvc_far_calls_end
ep7_mvc_far_calls_end:
