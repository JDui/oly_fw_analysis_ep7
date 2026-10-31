/* Same short-site order as native/cohort.c; exactly30 bytes per resident row.
 * The shared macro preserves original CALL mask/frame, stack RA and MDR. */
.include "far_call.inc"
.section .text.ep7_pipeline_far_calls,"ax"
.global ep7_pipeline_far_calls
ep7_pipeline_far_calls:
EP7_FAR_CALL ep7_pipeline_far_602ac3de,ep7_native_capture_scope_bridge,0x602ac3e3,0xb0,32
EP7_FAR_CALL ep7_pipeline_far_603ef8b5,ep7_native_descriptor_receive_bridge,0x603ef8ba,0xf0,44
EP7_FAR_CALL ep7_pipeline_far_603ef8d2,ep7_native_descriptor_receive_bridge,0x603ef8d7,0xf0,44
EP7_FAR_CALL ep7_pipeline_far_603ef8fd,ep7_native_descriptor_receive_bridge,0x603ef902,0xf0,44
EP7_FAR_CALL ep7_pipeline_far_603ef91a,ep7_native_descriptor_receive_bridge,0x603ef91f,0xf0,44
EP7_FAR_CALL ep7_pipeline_far_603f2722,ep7_native_worker_scope_bridge,0x603f2727,0x30,56
EP7_FAR_CALL ep7_pipeline_far_603dfc67,ep7_native_ack_bridge,0x603dfc6c,0x30,32
EP7_FAR_CALL ep7_pipeline_far_603e05c6,ep7_native_ack_bridge,0x603e05cb,0x30,32
.global ep7_pipeline_far_calls_end
ep7_pipeline_far_calls_end:
