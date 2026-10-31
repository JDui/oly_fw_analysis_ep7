.include "far_call.inc"
.section .text.ep7_postbuilder_far_calls,"ax"
.global ep7_postbuilder_far_calls
ep7_postbuilder_far_calls:
EP7_FAR_CALL ep7_postbuilder_far_603b02d9,ep7_native_postbuilder_bridge,0x603b02de,0xf0,96
.global ep7_postbuilder_far_calls_end
ep7_postbuilder_far_calls_end:
