"""Build1100 native five-slot live H/L transport, using exact source bytes."""
PATCHES=[
 dict(site=0x6030bb19,original_hex='cdb301f014',target='ep7h_live_sample_bridge',encoding='JMP32_NOP_suffix'),
 dict(site=0x603119bb,original_hex='dd2f070100f030',target='ep7h_live_to_job_bridge',encoding='JMP32_NOP_suffix'),
]

def bindings():
 return dict(ep7_stock_h_live_s_unresolved=0x6030bccc,
             ep7_stock_h_live_s_resume_unresolved=0x6030bb1e,
             ep7_stock_h_live_setter_unresolved=0x603220ea,
             ep7_stock_h_live_setter_resume_unresolved=0x603119c2)
