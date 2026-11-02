"""Native E-P7 H/L transport sites. Exact originals, no hashes or private queues."""
PATCHES=[
 dict(site=0x603537f0,original_hex='2c803c',encoding='literal',literal_hex='2c983c'),
 dict(site=0x6035390c,original_hex='8510',encoding='literal',literal_hex='8528'),
 dict(site=0x602a886a,original_hex='dd0761dbffc00c',target='ep7h_capture_sample_bridge',encoding='CALL32',mask=0xc0,frame=12),
 dict(site=0x603e669f,original_hex='5c14fa40165e',target='ep7h_capture_to_job_bridge',encoding='JMP32_NOP_suffix'),
 dict(site=0x603e91e4,original_hex='5c18fa40165e',target='ep7h_alternate_to_job_bridge',encoding='JMP32_NOP_suffix'),
 dict(site=0x603edbce,original_hex='dd8434c1e6f01c',target='ep7h_capture_clone_bridge',encoding='CALL32',mask=0xf0,frame=28),
 dict(site=0x603b02d9,original_hex='cd8ffdf060',target='ep7h_color_builder_bridge',encoding='JMP32_NOP_suffix'),
 dict(site=0x603b027c,original_hex='cd18f9f050',target='ep7h_generic_color_bridge',encoding='JMP32_NOP_suffix'),
]
def bindings():
 return dict(ep7_stock_h_capture_get_unresolved=0x6005e971,
             ep7_stock_h_capture_copy_resume_unresolved=0x603e66a5,
             ep7_stock_h_alternate_copy_resume_unresolved=0x603e91ea,
             ep7_stock_h_capture_memcpy_unresolved=0x47001052,
             ep7_stock_h_color_builder_unresolved=0x603b0068,
             ep7_stock_h_color_resume_unresolved=0x603b02de,
             ep7_stock_h_generic_builder_unresolved=0x603afb94,
             ep7_stock_h_generic_resume_unresolved=0x603b0281)
