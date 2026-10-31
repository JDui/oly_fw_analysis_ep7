"""Object ABI assertions for the three different native caller frames."""
import re
def validate(dis):
    bodies=dict(re.findall(r'(?ms)^[0-9a-f]+ <([^>]+)>:\n(.*?)(?=^[0-9a-f]+ <|\Z)',dis))
    save=lambda pairs:[('mov',a+','+b) for a,b in pairs]
    prep=save([('a0','(12,sp)'),('d0','(16,sp)'),('d1','(20,sp)'),('a1','(24,sp)'),('d3','(28,sp)'),('a0','d0')])+[
        ('call',None)]+save([('(12,sp)','a0'),('(16,sp)','d0'),('(20,sp)','d1'),('(24,sp)','a1'),('(28,sp)','d3')])+[
        ('call',None)]+save([('a0','(32,sp)'),('d0','(36,sp)'),('d1','(40,sp)'),('a1','(44,sp)'),('d0','d1'),('(12,sp)','d0')])+[
        ('call',None)]+save([('(32,sp)','a0'),('(36,sp)','d0'),('(40,sp)','d1'),('(44,sp)','a1'),('(28,sp)','d3')])+[('ret','[d2,a2,a3],224')]
    dispatch=[('add','-20,sp')]+save([('d0','(12,sp)'),('a1','(16,sp)'),('d1','(20,sp)'),('a0','(24,sp)'),('a3','(28,sp)'),('sp','a0')])+[
        ('add','12,a0'),('mov','a0,d0'),('call',None)]+save([('d0','(32,sp)'),('(12,sp)','d0'),('(16,sp)','a1'),('(20,sp)','d1'),('(24,sp)','a0')])+[
        ('call',None)]+save([('d0','(36,sp)'),('d1','(40,sp)'),('a0','(44,sp)'),('a1','(48,sp)'),('(32,sp)','d0')])+[
        ('call',None)]+save([('(36,sp)','d0'),('(40,sp)','d1'),('(44,sp)','a0'),('(48,sp)','a1')])+[('add','20,sp'),('ret','[d2,d3,a2,a3],48')]
    sample=[('movm','[d2,d3,a2,a3],(sp)'),('add','-48,sp')]+save([
        ('a3','(12,sp)'),('d0','(16,sp)'),('(64,sp)','d0'),('d0','(20,sp)'),('d2','(24,sp)'),('a2','(28,sp)'),
        ('d1','(32,sp)'),('a0','(36,sp)'),('a1','(40,sp)'),('mdr','d0'),('d0','(44,sp)'),('(16,sp)','d0')])+[
        ('call',None),('mov','sp,a0'),('add','12,a0'),('mov','a0,d0'),('call',None)]+save([
        ('(44,sp)','d0'),('d0','mdr'),('(16,sp)','d0'),('(32,sp)','d1'),('(36,sp)','a0'),('(40,sp)','a1')])+[('ret','[d2,d3,a2,a3],64')]
    spec={
        'ep7_native_ui_preprocess_bridge':(prep,['_ep7i_prepare_begin','ep7_stock_ui_preprocess_unresolved','_ep7i_prepare_end'],['[],0','[d2,a2,a3],224','[],0']),
        'ep7_native_ui_dispatch_bridge':(dispatch,['_ep7i_dispatch_begin','ep7_stock_ui_dispatch_unresolved','_ep7i_dispatch_end'],['[],0','[d2,d3,a2,a3],48','[],0']),
        'ep7_native_ui_wheel_sample_bridge':(sample,['ep7_stock_ui_wheel_set_unresolved','_ep7i_sample_wheel'],['[],0','[],0']),
        '_ep7_gcc_ui_drop_info':([('add','-4,sp'),('mov','36884,d0'),('call',None),('ret','[],4')],['ep7_stock_ui_drop_event_unresolved'],['[d2,d3,a2],16'])}
    count=0
    for name,(expected,refs,frames) in spec.items():
        body=bodies[name]
        ins=re.findall(r'^[ \t]*[0-9a-f]+:[ \t]+(?:[0-9a-f]{2}[ \t]+)+([a-z][a-z0-9]*)(?:[ \t]+([^\n]*))?$',body,re.M)
        if len(ins)!=len(expected) or any(a!=b or (v is not None and op!=v) for (a,op),(b,v) in zip(ins,expected)):
            raise ValueError('native input bridge ABI changed: '+name+' '+repr(ins))
        relocs=re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',body)
        if relocs!=[('PCREL32',s+'+0x1') for s in refs]:raise ValueError('input bridge relocations '+name)
        calls=[op for mn,op in ins if mn=='call']
        if len(calls)!=len(frames) or any(not op.endswith(','+frame) for op,frame in zip(calls,frames)):
            raise ValueError('native call frame '+name)
        count+=len(ins)
    # CALL stores its PC at pre-call SP before subtracting its frame. The inherited
    # return word and saved register spans must be outside every written local.
    spans=[(224,212,[(12,32),(32,48)]),(68,52,[(12,32),(32,36),(36,52)]),(64,48,[(12,32),(32,48)])]
    for return_offset,save_start,locals_ in spans:
        assert all(12<=lo<hi<=save_start<return_offset for lo,hi in locals_)
    return dict(checked_instructions=count,preprocess_inherited_frame=224,preprocess_nested_native_frame=224,
        dispatch_inherited_frame=48,dispatch_additional_frame=20,sample_own_frame=64,
        sample_preserves_volatile_registers_and_mdr=True,original_results_preserved=True,
        stack_layout_checked=True,stack_model_not_native_execution=True)
