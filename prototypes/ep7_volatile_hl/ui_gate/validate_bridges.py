"""Exact native creator, postselect, timer and original-draw veneer ABI checks."""
import re
def validate(name,dis):
    ins=re.findall(r'^[ \t]*[0-9a-f]+:[ \t]+(?:[0-9a-f]{2}[ \t]+)+([a-z][a-z0-9]*)(?:[ \t]+([^\n]*))?$',dis,re.M)
    if name=='ui_original_draw':
        expected=[('add','-4,sp'),('mov','d0,a0'),('call',None),('ret','[],4')]
        refs=[('PCREL32','ep7_stock_mvc_viewer_draw_unresolved+0x1')];frames=['[],0']
    else:
        expected=[('movm','[d2,d3,a2,a3],(sp)'),('add','-4,sp'),('mov','d1,a0'),
            ('cmp','0,d0'),('beq',None),('cmp','3,d0'),('beq',None),('call',None),('bra',None),
            ('call',None),('bra',None),('call',None),('mov','a0,d0'),('ret','[d2,d3,a2,a3],20'),
            ('add','-4,sp'),('mov','d0,a0'),('call',None),('ret','[],4'),
            ('add','-4,sp'),('call',None),('mov','537,d0'),('call',None),('mov','572,d0'),('call',None),('ret','[],4')]
        refs=[('PCREL8','.Lstock_create0+0x1'),('PCREL8','.Lstock_create14+0x1'),
            ('PCREL32','ep7_stock_mvc_creator7_unresolved+0x1'),('PCREL8','.Lstock_created+0x1'),
            ('PCREL32','ep7_stock_mvc_creator0_unresolved+0x1'),('PCREL8','.Lstock_created+0x1'),
            ('PCREL32','ep7_stock_mvc_creator14_unresolved+0x1'),
            ('PCREL32','ep7_stock_mvc_stock_selected_unresolved+0x1'),
            ('PCREL32','ep7_stock_mvc_stop535_unresolved+0x1'),
            ('PCREL32','ep7_stock_ui_timer_cancel_unresolved+0x1'),('PCREL32','ep7_stock_ui_timer_cancel_unresolved+0x1')]
        frames=['[],0','[],0','[],0','[a2],8','[],4','[d2],8','[d2],8']
    if len(ins)!=len(expected) or any(a!=b or (v is not None and op!=v) for (a,op),(b,v) in zip(ins,expected)):
        raise ValueError('stock/gate ABI changed: '+repr(ins))
    if re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',dis)!=refs:raise ValueError('stock/gate relocations changed')
    calls=[op for mn,op in ins if mn=='call']
    if len(calls)!=len(frames) or any(not op.endswith(','+frame) for op,frame in zip(calls,frames)):
        raise ValueError('stock/gate CALL frame changed')
    return dict(checked_instructions=len(ins),native_call_frames_checked=frames,
        full_original_entries_unpatched=True,pointer_return_a0_preserved=True)
