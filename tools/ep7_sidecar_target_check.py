#!/usr/bin/env python3
"""Compile current sidecar sources with explicitly selected installed MN103 tools."""
from pathlib import Path
import argparse,json,re,runpy,subprocess,tempfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--tool-prefix',required=True,help='trusted installed tool path prefix ending mn10300-elf-')
mode=parser.add_mutually_exclusive_group()
mode.add_argument('--transport-only',action='store_true',help='compile snapshot transport, wire codec, owned queue I/O and existing memory support')
mode.add_argument('--queue-abi-only',action='store_true',help='assemble raw queue and notification-preserving send veneers plus GCC caller probes')
mode.add_argument('--materializer-abi-only',action='store_true',help='compile exact materializer receiver, frame mapper and local queue bridge closure')
mode.add_argument('--receive-abi-only',action='store_true',help='compile command and descriptor receiver bridges and bounded stack mappers')
mode.add_argument('--queue-pipeline-abi-only',action='store_true',help='compile command/descriptor receive and descriptor forward bridges')
mode.add_argument('--task-context-only',action='store_true',help='compile read-only actual current-TCB stack view and reuse get_tid veneer')
mode.add_argument('--ui-context-only',action='store_true',help='compile native text rollback context callbacks and audited native selection leaves')
mode.add_argument('--ui-create-only',action='store_true',help='compile context-preserving text factory result bridge with existing rollback bindings')
mode.add_argument('--ui-lifecycle-only',action='store_true',help='compile actual text creation/attach/bind/set/rollback callback composition')
mode.add_argument('--ui-owner-only',action='store_true',help='compile request278 owner capture/revoke, actual table cohort and native method bridges')
mode.add_argument('--ui-selector-only',action='store_true',help='compile guarded six-entry selector storage upgrade after original ID193 initialization')
mode.add_argument('--ui-mvc-only',action='store_true',help='compile GUI041d container/parent/viewer lifetime capture and pre-destruction revocation')
mode.add_argument('--ui-content-only',action='store_true',help='compile owned H/L content rebuild with native destruction and MVC/cohort closure')
mode.add_argument('--ui-viewer-only',action='store_true',help='compile joined MVC/content/model/owner/viewer and shared runtime core closure')
mode.add_argument('--ui-input-only',action='store_true',help='compile event-scoped full wheel samples and native input transaction with the joined UI graph')
mode.add_argument('--ui-gate-only',action='store_true',help='compile COLOR gating and allocation-before-free stock restoration with the joined UI graph')
args=parser.parse_args()
receiver_mode=args.receive_abi_only or args.queue_pipeline_abi_only
materializer_mode=args.materializer_abi_only or receiver_mode
graph_mode=args.ui_owner_only or args.ui_mvc_only or args.ui_content_only or args.ui_viewer_only or args.ui_input_only or args.ui_gate_only
ui_lifecycle_mode=args.ui_lifecycle_only or graph_mode
ui_create_mode=args.ui_create_only or ui_lifecycle_mode
ui_mode=args.ui_context_only or ui_create_mode
mvc_mode=graph_mode
selector_mode=args.ui_selector_only or mvc_mode
root=Path(__file__).resolve().parents[1];core=root/'prototypes/ep7_volatile_hl';prefix=args.tool_prefix
versions={n:subprocess.check_output([prefix+n,'--version'],text=True).splitlines()[0] for n in ['gcc','as','ld','objdump']}
include=subprocess.check_output([prefix+'gcc','-print-file-name=include'],text=True).strip()
flags=['-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-mno-setlb','-mno-liw','-nostdinc','-I'+str(core/'target/include'),'-I'+include,'-I'+str(core)]
files={'sidecar':core/'controller_sidecar/sidecar.c','transition':core/'controller_sidecar/transition_binding.c','observer':core/'capture_state_guard/observer.c','bridge':core/'capture_state_guard/bridge.s','core':core/'ep7p.c','decode':core/'ep7p_decode.c','memory':core/'target/memory.c'}
if args.transport_only:
 files={'transport':core/'snapshot_transport/transport.c','wire':core/'snapshot_transport/wire.c','owned_io':core/'snapshot_transport/owned_io.c','memory':core/'target/memory.c'}
 flags.append('-fstack-usage')
if args.queue_abi_only:
 files={'queue_bridge':core/'snapshot_transport/native/queue_bridges.s','caller':core/'snapshot_transport/native/bridge_caller.c'}
if args.task_context_only:
 files={'task_context':core/'runtime/task_context.c','task_native':core/'runtime/task_context_native.c',
        'queue_context':core/'runtime/queue_context.c',
        'get_tid':core/'target/get_tid_bridge.s','task_delay':core/'runtime/delay_bridge.s','memory':core/'target/memory.c'}
 flags.append('-fstack-usage')
if ui_mode:
 files={n:core/'text_rollback'/p for n,p in [('text_rollback','rollback.c'),
     ('ui_context','native_context.c'),('ui_context_bridges','context_bridges.s'),
     ('text_cleanup_bridge','cleanup_destroy.s')]}
 files.update({n:core/'runtime'/p for n,p in [('task_context','task_context.c'),
     ('task_native','task_context_native.c'),('queue_context','queue_context.c')]})
 files.update({'get_tid':core/'target/get_tid_bridge.s','memory':core/'target/memory.c'})
 flags.append('-fstack-usage')
 if ui_create_mode:
  files.update({n:core/'text_lifecycle'/p for n,p in [('text_factory_bridge','native_create.s'),
      ('text_factory_caller','factory_caller.c'),('text_lifecycle','lifecycle.c')]})
 if ui_lifecycle_mode:
  files.update({'text_native_lifecycle':core/'text_lifecycle/native_lifecycle.c',
      'text_attach_bind':core/'text_lifecycle/attach_bind.s','text_setter':core/'text_viewer/set_text.s',
      'text_find_child':core/'text_lifecycle/find_child.s',
      'text_native_resource':core/'text_lifecycle/native_resource.c'})
 if graph_mode:
  files.update({n:core/'ui_owner'/p for n,p in [('ui_owner','owner.c'),
      ('ui_owner_cohort','cohort.c'),('ui_owner_bridges','bridges.s')]})
  files['quarantine']=core/'runtime/quarantine.s'
if selector_mode:
 if not ui_mode:files={}
 files.update({n:core/'ui_selector'/p for n,p in [('ui_selector','selector.c'),('ui_selector_bridges','bridges.s')]})
 files.update({n:core/'runtime'/p for n,p in [('task_context','task_context.c'),
     ('task_native','task_context_native.c'),('queue_context','queue_context.c')]})
 files.update({'get_tid':core/'target/get_tid_bridge.s','memory':core/'target/memory.c'})
 flags.append('-fstack-usage')
 if mvc_mode:
  files.update({n:core/'ui_mvc'/p for n,p in [('mvc_lifetime','lifetime.c'),
      ('mvc_cohort','cohort.c'),('mvc_bridges','bridges.s')]})
  files['quarantine']=core/'runtime/quarantine.s'
  files.update({n:core/'ui_content'/p for n,p in [('ui_content','content.c'),('ui_content_bridges','bridges.s')]})
  files.update({'ui_model':core/'ui_model/model.c','ui_public_mode':core/'ui_model/public_mode.s',
      'ui_viewer':core/'ui_render/viewer.c','ui_viewer_bridge':core/'ui_render/bridge.s',
      'ui_portable':core/'ep7p_ui.c','ui_formatter':core/'text_viewer/text.c',
      'runtime':core/'runtime/runtime.c','core':core/'ep7p.c','decode':core/'ep7p_decode.c',
      'poll_provider':core/'poll_lock_provider/ep7_sem_provider.c',
      'bootstrap':core/'poll_lock_provider/bootstrap/bootstrap.c',
      'transport':core/'snapshot_transport/transport.c','wire':core/'snapshot_transport/wire.c'})
if graph_mode:
 files.update({n:core/'ui_native'/p for n,p in [('ui_input','input.c'),('ui_input_cohort','cohort.c'),
     ('ui_input_bridges','input_bridges.s'),('ui_input_route','bridge.c'),('ui_event_bridge','bridge.s')]})
 files['ui_raw']=core/'ep7p_ui_raw.c'
 files.update({'ui_gate':core/'ui_gate/gate.c','ui_stock_restore':core/'ui_content/stock.c',
     'ui_stock_bridges':core/'ui_content/stock_bridges.s','ui_original_draw':core/'ui_render/original_draw.s'})
if materializer_mode:
 files={'materializer_bridge':core/'snapshot_transport/native/materializer_bridge.s',
        'materializer_layout':core/'snapshot_transport/native/materializer_layout.c',
        'materializer_binding':core/'snapshot_transport/native/materializer_binding.c',
        'queue_bridge':core/'snapshot_transport/native/queue_bridges.s',
        'stack':core/'snapshot_transport/native/stack.c',
        'owned_io':core/'snapshot_transport/owned_io.c','wire':core/'snapshot_transport/wire.c','memory':core/'target/memory.c'}
 flags.append('-fstack-usage')
if receiver_mode:
 files.update({n:core/'snapshot_transport/native'/p for n,p in
     [('descriptor_receive_bridge','descriptor_receive_bridge.s'),('descriptor_receive_layout','descriptor_receive_layout.c'),('descriptor_receive_binding','descriptor_receive_binding.c')]})
if args.queue_pipeline_abi_only:
 flags.append('-I'+str(core/'poll_lock_provider'))
 files['postbuilder_bridge']=core/'target/postbuilder/postbuilder_bridge.s'
 files['postbuilder_observer']=core/'target/postbuilder/native_observer.c'
 files['capture_sidecar']=core/'controller_sidecar/sidecar.c'
 files['capture_native']=core/'controller_sidecar/native_binding.c'
 files['capture_cohort']=core/'controller_sidecar/cohort.c'
 files['capture_bridges']=core/'controller_sidecar/native_bridges.s'
 files['wait_bridges']=core/'controller_sidecar/wait_bridges.s'
 files['engine_bridges']=core/'controller_sidecar/engine_bridges.s'
 files['capture_state_observer']=core/'capture_state_guard/observer.c'
 files['capture_state_bridge']=core/'capture_state_guard/bridge.s'
 files.update({n:core/'runtime'/p for n,p in [
     ('runtime','runtime.c'),('contexts','contexts.c'),('runtime_native','native_context.c'),
     ('task_context','task_context.c'),('task_native','task_context_native.c'),('queue_context','queue_context.c'),
     ('task_delay','delay_bridge.s'),('quarantine','quarantine.s'),
     ('kernel_gate','kernel_gate.c'),('kernel_gate_bridges','kernel_gate_bridges.s')]})
 files['get_tid']=core/'target/get_tid_bridge.s'
 files.update({n:core/'poll_lock_provider'/p for n,p in [
     ('poll_provider','ep7_sem_provider.c'),('bootstrap','bootstrap/bootstrap.c'),
     ('raw_callbacks','native/raw_callbacks.c'),('sem_bridge','native/sem_bridges.s'),
     ('bootstrap_native','bootstrap/native_callbacks.c'),('bootstrap_bridge','bootstrap/create_delete_bridges.s')]})
 files['forward']=core/'snapshot_transport/forward.c'
 files['transport']=core/'snapshot_transport/transport.c'
 files['producer']=core/'snapshot_transport/producer.c'
 files['consumer']=core/'snapshot_transport/consumer.c'
 files['job']=core/'snapshot_transport/job.c'
 files['core']=core/'ep7p.c'
 files['decode']=core/'ep7p_decode.c'
 files.update({n:core/'snapshot_transport/native'/p for n,p in
     [('worker_bridge','worker_bridges.s'),('worker_layout','worker_layout.c'),('worker_binding','worker_binding.c'),('worker_caller','worker_caller.c')]})
 files.update({n:core/'snapshot_transport/native'/p for n,p in
     [('ack_bridge','ack_bridge.s'),('ack_layout','ack_layout.c'),('ack_binding','ack_binding.c')]})
 files['queue_send_binding']=core/'snapshot_transport/native/queue_send_binding.c'
 files.update({n:core/'snapshot_transport/native'/p for n,p in
     [('descriptor_send_bridge','descriptor_send_bridge.s'),('descriptor_send_layout','descriptor_send_layout.c'),('descriptor_send_binding','descriptor_send_binding.c'),
      ('producer_bridge','producer_bridge.s'),('producer_layout','producer_layout.c'),('producer_binding','producer_binding.c')]})
objects={};definitions={};undefined=set()
with tempfile.TemporaryDirectory() as temp:
 for name,src in files.items():
  obj=Path(temp)/(name+'.o')
  if src.suffix=='.c':subprocess.run([prefix+'gcc',*flags,'-c',str(src),'-o',str(obj)],check=True)
  else:subprocess.run([prefix+'as','-o',str(obj),str(src)],check=True)
  syms=subprocess.check_output([prefix+'objdump','-t',str(obj)],text=True);defs=set();und=set()
  for line in syms.splitlines():
   bits=line.split()
   if '*UND*' in bits:und.add(bits[-1])
   elif len(bits)>4 and bits[1]=='g':defs.add(bits[-1])
  for symbol in defs:
   if symbol in definitions:raise ValueError('duplicate global '+symbol)
   definitions[symbol]=name
  undefined|=und
  objects[name]=dict(source=str(src.relative_to(root)),definitions=sorted(defs),undefined=sorted(und))
  if args.queue_pipeline_abi_only or ui_mode or selector_mode:
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   audit=re.findall(r'^\s*[0-9a-f]+:[ \t]+(?:[0-9a-f]{2}[ \t]+)+([a-z][a-z0-9]*)(?:[ \t]+([^\n]*))?$',dis,re.M)
   forbidden={'setlb','leq','lne','lgt','lge','lle','llt','lhi','lcc','lls','lcs','lra'}
   # Objdump's numeric branch address e0 is not the extended register e0.
   # Strip only its explicit address<label> annotation, retaining real operands.
   suspicious=[(mn,operands) for mn,operands in audit if mn in forbidden or re.search(
       r'\b(?:lir|lar|epsw|mdrq|mcrh|mcrl|mcvf|e[0-7]|fs[0-9]+)\b',
       re.sub(r'\b[0-9a-f]+\s+<[^>]+>','',operands))]
   if suspicious:raise ValueError('unqualified loop/extended register state in '+name+': '+repr(suspicious))
   objects[name]['loop_extended_state_audited']=True
  if name=='ui_input_bridges':
   validator=runpy.run_path(str(core/'ui_native/validate_input.py'))
   objects[name].update(validator['validate'](dis))
  if name=='ui_event_bridge':
   legacy=runpy.run_path(str(core/'ui_native/check.py'))
   count=legacy['validate_assembly'](dis,subprocess.check_output([prefix+'objdump','-h',str(obj)],text=True))
   objects[name].update(checked_instructions=count,own_frame_bytes=48,stock_delegate_original_preserved=True)
  if name=='text_factory_bridge':
   # CLR D0 is opcode00. At a local-symbol boundary objdump's default zero
   # suppression can hide this real instruction, so decode zero bytes too.
   dis=subprocess.check_output([prefix+'objdump','-dr','-z','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^[ \t]*[0-9a-f]+:[ \t]+(?:[0-9a-f]{2}[ \t]+)+([a-z][a-z0-9]*)(?:[ \t]+([^\n]*))?$',dis,re.M)
   expected=[('movm','[d2,d3,a2,a3],(sp)'),('add','-24,sp'),('mov','d0,(12,sp)'),
       ('mov','d1,(16,sp)'),('mov','(52,sp),d0'),('mov','d0,(20,sp)'),('call',None),
       ('mov','a0,(4,sp)'),('mov','sp,a1'),('add','8,a1'),('mov','a1,d0'),('add','1,d0'),('call',None),
       ('mov','(12,sp),d1'),('mov','(16,sp),a1'),('mov','32784,d0'),('call',None),
       ('cmp','0,a0'),('bne',None),('clr','d0'),('mov','(20,sp),a1'),('mov','a0,(a1)'),('mov','d0,(4,a1)'),
       ('mov','(4,sp),a0'),('movbu','(8,sp),d0'),('movbu','(9,sp),d1'),('call',None),('ret','[d2,d3,a2,a3],40')]
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    raise ValueError('factory result/context preservation changed: '+repr(ins))
   if not ins[16][1].endswith(',[d2,a2,a3],24') or any(not ins[i][1].endswith(',[],0') for i in [6,12,26]):
    raise ValueError('factory/context native call frame changed')
   relocs=re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',dis)
   expected_relocs=[('PCREL32',s+'+0x1') for s in ['ep7_stock_ui_service_unresolved',
       'ep7_stock_ui_context_get_unresolved','ep7_stock_widget_factory_unresolved']]+[
       ('PCREL8','.Ltext_allocated+0x1'),('PCREL32','ep7_stock_ui_context_set_unresolved+0x1')]
   if relocs!=expected_relocs:raise ValueError('factory native/branch relocation changed')
   addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+[a-z]',dis,re.M)
   rows={line.split()[-1]:int(line.split()[0],16) for line in syms.splitlines() if len(line.split())>=5 and '*UND*' not in line and re.fullmatch('[0-9a-f]+',line.split()[0])}
   if rows.get('.Ltext_allocated')!=int(addresses[20],16):raise ValueError('factory null branch result destination changed')
   objects[name].update(checked_instructions=len(ins),own_frame_bytes=40,native_factory_frame_bytes=24,
       third_gcc_argument_offset=52,independent_result_child_offset=0,independent_result_status_offset=4,
       prior_context_restored_on_normal_return=True)
  if name=='text_factory_caller':
   assembly=Path(temp)/'text_factory_caller.s'
   subprocess.run([prefix+'gcc',*flags,'-S',str(src),'-o',str(assembly)],check=True)
   caller=assembly.read_text()
   body=caller.split('_ep7_text_factory_probe:\n',1)[1].split('\t.size',1)[0]
   expected=['add -24,sp','mov sp,a0','add 16,a0','mov a0,(12,sp)',
       'call _ep7_gcc_text_factory,[],0','mov (16,sp),d0','cmp 0,d0','beq .L3',
       'mov (20,sp),d1','mov (36,sp),a0','mov d1,(a0)','mov d0,a0','ret [],24',
       '.L3:','mov d0,d1','mov (36,sp),a0','mov d1,(a0)','mov d0,a0','ret [],24']
   if [line.strip() for line in body.splitlines() if line.strip()]!=expected:
    raise ValueError('GCC third argument/result layout changed')
   objects[name].update(compiler_assembly=caller,compiler_abi_checked=True,
       caller_frame_bytes=24,third_argument_slot=12,result_local_offset=16,pointer_return_register='a0')
  if name=='text_cleanup_bridge':
   # Reuse the existing exact sequence/relocation validator only. Its legacy
   # main/tool SHA guard is not invoked in this explicitly selected tool mode.
   legacy=runpy.run_path(str(core/'text_rollback/check.py'))
   legacy['validate'](dis,subprocess.check_output([prefix+'objdump','-h',str(obj)],text=True))
   objects[name].update(checked_instructions=13,own_frame_bytes=32)
  if name=='text_setter':
   legacy=runpy.run_path(str(core/'text_viewer/check.py'))
   legacy['validate'](dis,subprocess.check_output([prefix+'objdump','-h',str(obj)],text=True))
   objects[name].update(checked_instructions=5,own_frame_bytes=12,native_frame_bytes=24)
  if name=='text_attach_bind':
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   expected=[('add','-4,sp'),('mov','d0,a0'),('mov','d1,a1'),('call',None),('ret','[],4')]*2
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    raise ValueError('attach/bind argument/frame routing changed')
   if not ins[3][1].endswith(',[a2],8') or not ins[8][1].endswith(',[],0'):
    raise ValueError('attach/bind native frame changed')
   relocs=re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',dis)
   if relocs!=[('PCREL32',s+'+0x1') for s in ['ep7_stock_ui_attach_unresolved','ep7_stock_text_bind_unresolved']]:
    raise ValueError('attach/bind native targets changed')
   objects[name].update(checked_instructions=10,own_frame_bytes=[4,4],native_frames=[8,12],
       bind_native_frame_is_self_prologue=True)
  if name=='text_find_child':
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   expected=[('add','-12,sp'),('mov','d0,a0'),('mov','a0,(4,sp)'),
       ('mov','(108,a0),d0'),('mov','d0,(8,sp)'),('mov','d1,d0'),('call',None),
       ('mov','(4,sp),a1'),('mov','(8,sp),d0'),('mov','d0,(108,a1)'),
       ('mov','a0,d0'),('ret','[],12')]
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    raise ValueError('child lookup argument/iterator/frame routing changed')
   if not ins[6][1].endswith(',[],0') or re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',dis)!=[
       ('PCREL32','ep7_stock_ui_find_child_unresolved+0x1')]:
    raise ValueError('child lookup native target/frame changed')
   objects[name].update(checked_instructions=12,own_frame_bytes=12,native_self_frame_bytes=24,
       owner_list_offset=92,preserved_iterator_offset=108,pointer_result_register='a0')
  if name=='mvc_bridges':
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   prologue=[('movm','[d2,d3,a2,a3],(sp)'),('add','-32,sp')]
   save=[('mov','a0,(12,sp)'),('mov','d0,(16,sp)'),('mov','d1,(20,sp)'),('mov','a1,(24,sp)')]
   restore=[('mov','(12,sp),a0'),('mov','(16,sp),d0'),('mov','(20,sp),d1'),('mov','(24,sp),a1')]
   end=[('ret','[d2,d3,a2,a3],48')]
   entry=prologue+save+[('call',None)]+restore+[('call',None)]+save+[
       ('mov','a0,d0'),('call',None)]+restore+end
   retire=prologue+save+[('mov','a0,d0'),('call',None)]+restore+[('call',None)]+end
   expected=entry+retire*3
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    raise ValueError('MVC lifetime native register/frame routing changed')
   if any(not op.endswith(',[],0') for m,op in ins if m=='call'):
    raise ValueError('MVC bridges must call full self-prologue entries')
   targets=['_ep7m_gui_begin','ep7_stock_mvc_gui_entry_unresolved','_ep7m_gui_complete',
       '_ep7m_before_gui_exit','ep7_stock_mvc_gui_exit_unresolved',
       '_ep7m_before_parent_destroy','ep7_stock_mvc_parent_destroy_unresolved',
       '_ep7m_before_viewer_destroy','ep7_stock_mvc_viewer_destroy_unresolved']
   if re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',dis)!=[('PCREL32',s+'+0x1') for s in targets]:
    raise ValueError('MVC lifetime call targets changed')
   objects[name].update(checked_instructions=65,own_frame_bytes=[48]*4,
       original_self_frames=[4,8,28,8],original_entry_scratch_results_preserved=True,
       original_destructor_a0_results_preserved=True)
  if name=='ui_content_bridges':
   dis=subprocess.check_output([prefix+'objdump','-dr','-z','--insn-width=16',str(obj)],text=True)
   # Each body is independently selected: near entry is a separate placement section.
   def body(symbol):
    part=dis.split('<'+symbol+'>:\n',1)[1].split('\n\n',1)[0]
    return re.findall(r'^\s*[0-9a-f]+:[ \t]+(?:[0-9a-f]{2}[ \t]+)+([a-z][a-z0-9]*)(?:[ \t]+([^\n]*))?$',part,re.M)
   expected_bodies={
       'ep7_native_content_rebuild_bridge':[('mov','a0,d0'),('call',None),('ret','[d2,d3,a2,a3],28')],
       '_ep7_gcc_mvc_stock_rebuild':[('add','-4,sp'),('mov','d0,a0'),('call',None),('ret','[],4')],
       '_ep7_gcc_mvc_scalar_new':[('add','-4,sp'),('call',None),('mov','a0,d0'),('ret','[],4')],
       '_ep7_gcc_mvc_base_init':[('add','-4,sp'),('mov','d0,a0'),('call',None),('ret','[],4')],
       '_ep7_gcc_mvc_dispose':[('movm','[a2],(sp)'),('add','-4,sp'),('mov','d0,a2'),('mov','a2,a0'),
           ('mov','(a0),a1'),('mov','(40,a1),a1'),('calls','(a1)'),('mov','a0,a1'),('cmp','0,a0'),
           ('beq',None),('mov','a2,a0'),('calls','(a1)'),('ret','[a2],8')],
       '.Lscalar_delete':[('mov','a2,a0'),('call',None),('ret','[a2],8')],
       'ep7_native_content_destroy_bridge':[('movm','[d2,d3,a2,a3],(sp)'),('add','-16,sp'),
           ('mov','a0,(12,sp)'),('mov','a0,d0'),('call',None),('mov','(12,sp),a0'),('call',None),
           ('ret','[d2,d3,a2,a3],32')],
       'ep7_native_content_zero':[('clr','d0'),('retf','[],0')],
       'ep7_native_content_null':[('mov','0,a0'),('retf','[],0')]}
   for symbol,want in expected_bodies.items():
    got=body(symbol)
    if len(got)!=len(want) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(got,want)):
     raise ValueError('content ABI changed in '+symbol+': '+repr(got))
   frames={'ep7_native_content_rebuild_bridge':[',[],0'],'_ep7_gcc_mvc_stock_rebuild':[',[d2,d3,a2,a3],28'],
       '_ep7_gcc_mvc_scalar_new':[',[],4'],'_ep7_gcc_mvc_base_init':[',[],0'],'.Lscalar_delete':[',[],4'],
       'ep7_native_content_destroy_bridge':[',[],0',',[],0']}
   for symbol,want in frames.items():
    calls=[op for mn,op in body(symbol) if mn=='call']
    if any(not op.endswith(suffix) for op,suffix in zip(calls,want)):raise ValueError('content CALL frame changed')
   relocs=re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',dis)
   want=[('PCREL32',s+'+0x1') for s in ['ep7_stock_mvc_rebuild_unresolved','ep7_stock_mvc_scalar_new_unresolved',
       'ep7_stock_mvc_base_init_unresolved']]+[('PCREL8','.Lscalar_delete+0x1')]+[
       ('PCREL32',s+'+0x1') for s in ['ep7_stock_mvc_scalar_delete_unresolved','_ep7c_before_destroy',
       'ep7_stock_mvc_base_destroy_unresolved','_ep7c_rebuild']]
   if relocs!=want:raise ValueError('content native/C relocation targets changed: '+repr(relocs))
   data_relocs=subprocess.check_output([prefix+'objdump','-r','-j','.rodata',str(obj)],text=True)
   rows=re.findall(r'^([0-9a-f]+)\s+R_MN10300_32\s+(\S+)',data_relocs,re.M)
   vtable=['ep7_native_content_zero']*18;vtable[7]='ep7_native_content_null';vtable[10]='ep7_native_content_destroy_bridge'
   if rows!=[(f'{i*4:08x}',v) for i,v in enumerate(vtable)]:raise ValueError('private MVC vtable changed')
   objects[name].update(checked_instructions=sum(map(len,expected_bodies.values())),vtable_entries_checked=18,
       rebuild_inherited_frame_bytes=28,rebuild_own_frame_bytes=0,destructor_own_frame_bytes=32,
       near_call_target_range=['0x60e1e9f0','0x60e2e1d3'],stock_rebuild_entry_remains_unpatched=True,
       destructor_returns_original_base_a0=True,pointer_return_a0_preserved=True)
  if name=='ui_viewer_bridge':
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   save=[('mov','a0,(12,sp)'),('mov','d0,(16,sp)'),('mov','d1,(20,sp)'),('mov','a1,(24,sp)')]
   restore=[('mov','(12,sp),a0'),('mov','(16,sp),d0'),('mov','(20,sp),d1'),('mov','(24,sp),a1')]
   expected=[('movm','[d2,d3,a2,a3],(sp)'),('add','-40,sp')]+save+[
       ('mov','a0,(32,sp)'),('mov','a0,d0'),('call',None),('mov','d0,(28,sp)')]+restore+[
       ('call',None)]+save+[('mov','(32,sp),d0'),('mov','(28,sp),d1'),('call',None)]+restore+[
       ('ret','[d2,d3,a2,a3],56')]
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    raise ValueError('viewer full-method ABI changed')
   if any(not op.endswith(',[],0') for mn,op in ins if mn=='call'):raise ValueError('viewer CALL frame changed')
   targets=['_ep7v_draw_begin','ep7_stock_mvc_viewer_draw_unresolved','_ep7v_draw_end']
   if re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',dis)!=[('PCREL32',s+'+0x1') for s in targets]:
    raise ValueError('viewer call targets changed')
   objects[name].update(checked_instructions=27,own_frame_bytes=56,original_self_frame_bytes=36,
       original_arguments_and_scratch_results_preserved=True,held_token_offset=28,viewer_offset=32)
  if name in ('ui_stock_bridges','ui_original_draw'):
   dis=subprocess.check_output([prefix+'objdump','-dr','-z','--insn-width=16',str(obj)],text=True)
   objects[name].update(runpy.run_path(str(core/'ui_gate/validate_bridges.py'))['validate'](name,dis))
  if name=='ui_public_mode':
   dis=subprocess.check_output([prefix+'objdump','-dr','-z','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*[0-9a-f]+:[ \t]+(?:[0-9a-f]{2}[ \t]+)+([a-z][a-z0-9]*)(?:[ \t]+([^\n]*))?$',dis,re.M)
   expected=[('movm','[a2],(sp)'),('add','-16,sp'),('clr','d0'),('mov','d0,(12,sp)'),
       ('call',None),('cmp','0,a0'),('beq',None),('mov','(a0),a2'),('mov','(8,a2),a2'),
       ('mov','sp,a1'),('add','12,a1'),('mov','111,d0'),('calls','(a2)'),('mov','(12,sp),d0'),('ret','[a2],20')]
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    raise ValueError('actual public-mode getter ABI changed')
   if not ins[4][1].endswith(',[],4') or re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',dis)!=[
       ('PCREL32','ep7_stock_property_service_unresolved+0x1'),('PCREL8','.Lmode_done+0x1')]:
    raise ValueError('property getter frame/relocation changed')
   objects[name].update(checked_instructions=15,own_frame_bytes=20,property_id=111,
       output_offset=12,output_initialized_zero=True,null_service_rejects=True)
  if name=='ui_selector_bridges':
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   expected=[('movm','[d2,d3,a2,a3],(sp)'),('add','-40,sp'),('mov','a0,(12,sp)'),
       ('mov','d0,(16,sp)'),('call',None),('mov','a0,(20,sp)'),('mov','d0,(24,sp)'),
       ('mov','d1,(28,sp)'),('mov','a1,(32,sp)'),('mov','(12,sp),d0'),('mov','(16,sp),d1'),
       ('call',None),('mov','(20,sp),a0'),('mov','(24,sp),d0'),('mov','(28,sp),d1'),
       ('mov','(32,sp),a1'),('ret','[d2,d3,a2,a3],56'),
       ('add','-4,sp'),('call',None),('mov','a0,d0'),('ret','[],4'),
       ('add','-4,sp'),('mov','d0,a0'),('call',None),('ret','[],4')]
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    raise ValueError('selector initializer or array ABI changed')
   if [op.split(',')[-1] for m,op in ins if m=='call']!=['0','0','4','4']:
    raise ValueError('selector initializer/array native frame changed')
   targets=['ep7_stock_selector_init_unresolved','_ep7s_expand_after_init',
       'ep7_stock_mvc_array_new_unresolved','ep7_stock_mvc_array_delete_unresolved']
   if re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',dis)!=[('PCREL32',s+'+0x1') for s in targets]:
    raise ValueError('selector initializer/array targets changed')
   objects[name].update(checked_instructions=25,own_frame_bytes=[56,4,4],
       original_initializer_self_frame=12,original_array_caller_frames=[4,4],
       original_initializer_scratch_results_preserved=True)
  if name=='ui_owner_bridges':
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   screen=[('movm','[d2,d3,a2,a3],(sp)'),('add','-48,sp'),('mov','a0,(12,sp)'),
       ('mov','d0,(16,sp)'),('mov','d1,(28,sp)'),('mov','a1,(32,sp)'),
       ('mov','sp,a0'),('add','12,a0'),('mov','a0,d0'),('call',None),
       ('mov','(12,sp),a0'),('mov','(16,sp),d0'),('mov','(28,sp),d1'),
       ('mov','(32,sp),a1'),('call',None),('mov','d0,(20,sp)'),
       ('mov','a0,(36,sp)'),('mov','d1,(40,sp)'),('mov','a1,(44,sp)'),
       ('mov','sp,a0'),('add','12,a0'),('mov','a0,d0'),('call',None),
       ('mov','(20,sp),d0'),('mov','(36,sp),a0'),('mov','(40,sp),d1'),
       ('mov','(44,sp),a1'),('ret','[d2,d3,a2,a3],64')]
   retire_prefix=[('movm','[d2,d3,a2,a3],(sp)'),('add','-32,sp'),('mov','a0,(12,sp)'),
       ('mov','d0,(16,sp)'),('mov','d1,(20,sp)'),('mov','a1,(24,sp)'),
       ('mov','a0,d0')]
   retire_suffix=[('call',None),('mov','(12,sp),a0'),('mov','(16,sp),d0'),
       ('mov','(20,sp),d1'),('mov','(24,sp),a1'),('call',None),('ret','[d2,d3,a2,a3],48')]
   expected=screen+[item for stage in [1,2,3] for item in retire_prefix+[('mov',str(stage)+',d1')]+retire_suffix]
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    raise ValueError('owner full-method argument/result/frame routing changed')
   if any(not operand.endswith(',[],0') for mnemonic,operand in ins if mnemonic=='call'):
    raise ValueError('owner bridge must call full self-prologue entries')
   targets=['_ep7u_screen_enter','ep7_stock_screen_manager_unresolved','_ep7u_screen_leave']
   for target in ['cleanup','bulk','destructor']:
    targets+=['_ep7u_before_retire','ep7_stock_ui_owner_'+target+'_unresolved']
   if re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',dis)!=[('PCREL32',s+'+0x1') for s in targets]:
    raise ValueError('owner method/callback targets changed')
   objects[name].update(checked_instructions=73,own_frame_bytes=[64,48,48,48],
       original_method_self_frames=[64,36,32,4],original_screen_scratch_results_preserved=True,
       destructor_result_a0_preserved=True)
  if name=='ui_context_bridges':
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   expected=[('add','-4,sp'),('call',None),('mov','a0,d0'),('ret','[],4'),
       ('movm','[a2],(sp)'),('add','-16,sp'),('mov','d0,a2'),('mov','d1,(12,sp)'),
       ('mov','a2,a0'),('mov','sp,a1'),('add','8,a1'),('mov','a1,d0'),('add','1,d0'),('call',None),
       ('mov','a2,a0'),('mov','(12,sp),d0'),('mov','d0,d1'),('lsr','8,d1'),('call',None),
       ('movbu','(8,sp),d0'),('movbu','(9,sp),d1'),('asl','8,d1'),('or','d1,d0'),('ret','[a2],20'),
       ('add','-4,sp'),('mov','d0,a0'),('mov','d1,d0'),('lsr','8,d1'),('call',None),('ret','[],4')]
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    raise ValueError('UI context argument/return/save-slot routing changed: '+repr(ins))
   if any(not op.endswith(',[],0') for mn,op in ins if mn=='call'):raise ValueError('UI leaf call frame changed')
   relocs=re.findall(r'R_MN10300_(\w+)\s+([^\n]+)',dis)
   targets=['ep7_stock_ui_service_unresolved','ep7_stock_ui_context_get_unresolved',
       'ep7_stock_ui_context_set_unresolved','ep7_stock_ui_context_set_unresolved']
   if relocs!=[('PCREL32',target+'+0x1') for target in targets]:raise ValueError('UI leaf relocations changed')
   objects[name].update(checked_instructions=len(ins),own_frame_bytes=[4,20,4],
       exchange_saved_selection_offsets=[8,9],exchange_requested_selection_offset=12,
       exchange_saved_a2_offset=16,native_getter_self_frame_bytes=4)
  if name=='postbuilder_bridge':
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   expected=[('call',None),('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),('mov','a0,(20,sp)'),('mov','a1,(24,sp)'),
       ('mov','mdr,d2'),('mov','d2,(28,sp)'),('mov','a2,d0'),('call',None),('mov','(12,sp),d0'),('mov','(16,sp),d1'),
       ('mov','(20,sp),a0'),('mov','(24,sp),a1'),('mov','(28,sp),d2'),('mov','d2,mdr'),('ret','[d2,d3,a2,a3],96')]
   if len(ins)!=len(expected) or any(actual[0]!=want[0] or (want[1] is not None and actual[1]!=want[1]) for actual,want in zip(ins,expected)):
    raise ValueError('postbuilder register/MDR/frame preservation changed')
   if not ins[0][1].endswith(',[d2,d3,a2,a3],96') or not ins[8][1].endswith(',[],0'):
    raise ValueError('postbuilder native/GCC call frame changed')
   if dis.count('R_MN10300_PCREL32')!=2 or any(s+'+0x1' not in dis for s in ['ep7_stock_color_builder_unresolved','_ep7_gcc_postbuilder_observer']):
    raise ValueError('postbuilder relocation changed')
   objects[name].update(checked_instructions=16,additional_native_frame_bytes=96)
  if name=='postbuilder_observer':
   assembly=Path(temp)/'postbuilder_observer.s'
   subprocess.run([prefix+'gcc',*flags,'-S',str(src),'-o',str(assembly)],check=True)
   caller=assembly.read_text()
   if und!={'_ep7_native_runtime_slot','_ep7r_apply'}:raise ValueError('postbuilder must use shared runtime reader')
   for offset in [4,5,6,7,12,13,14,15]:
    if not re.search(r'\bmovbu \('+str(offset)+r',a0\),d[0-3]',caller):raise ValueError('missing native setup byte read')
   for witness in ['mov _ep7_native_runtime_slot,d0','call _ep7r_apply,[],0','mov 976,a1','mov a1,(16,sp)','mov d2,(12,sp)','ret [d2,d3],28']:
    if witness not in caller:raise ValueError('shared reader argument/frame mismatch')
   objects[name].update(checked_setup_byte_reads=8,shared_runtime_reader_bound=True,output_extent=976)
  if (args.queue_abi_only or args.queue_pipeline_abi_only) and name in {'queue_bridge','caller'}:
   if name=='queue_bridge':
    dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
    ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
    expected_ins=[('movm','[a2],(sp)'),('add','-12,sp'),('mov','d1,a0'),('mov','(28,sp),d1'),('call',None),('ret','[a2],16'),
                  ('movm','[a2],(sp)'),('add','-12,sp'),('mov','d1,a0'),('mov','(28,sp),d1'),('mov','(32,sp),a1'),('call',None),('ret','[a2],16'),
                  ('movm','[a2],(sp)'),('add','-20,sp'),('mov','d1,(12,sp)'),('mov','(36,sp),d1'),('mov','d1,(16,sp)'),
                  ('mov','sp,a0'),('add','12,a0'),('mov','(40,sp),d1'),('call',None),('ret','[a2],24')]
    if len(ins)!=len(expected_ins):raise ValueError('queue bridge instruction count changed')
    for actual,want in zip(ins,expected_ins):
     if actual[0]!=want[0] or (want[1] is not None and actual[1].strip()!=want[1]):raise ValueError('queue bridge operand changed')
    if ',[d2,d3,a2,a3],32' not in ins[4][1] or ',[d2,d3,a2,a3],40' not in ins[11][1] or ',[d2,d3,a2,a3],48' not in ins[21][1]:raise ValueError('queue native save/frame changed')
    if dis.count('R_MN10300_PCREL32')!=3:raise ValueError('queue bridge relocation count changed')
    for target in ('ep7_stock_queue_receive_local_unresolved','ep7_stock_queue_send_local_unresolved','ep7_stock_queue_send_preserving_unresolved'):
     if target+'+0x1' not in dis:raise ValueError('queue bridge relocation target changed')
    objects[name]['checked_instructions']=len(ins)
    objects[name]['own_frame_bytes']=[16,16,24]
    objects[name]['native_nested_frames']=[32,40,48]
    addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+[a-z]',dis,re.M)
    rows={line.split()[-1]:int(line.split()[0],16) for line in syms.splitlines() if len(line.split())>=5 and '*UND*' not in line and re.fullmatch('[0-9a-f]+',line.split()[0])}
    for symbol,index in [('_ep7_queue_receive_native_return',5),('_ep7_queue_raw_send_native_return',12),('_ep7_queue_named_send_native_return',22)]:
     if rows.get(symbol)!=int(addresses[index],16):raise ValueError('queue ownership return label changed: '+symbol)
    objects[name]['checked_native_return_labels']=3
   else:
    assembly=Path(temp)/'caller.s'
    subprocess.run([prefix+'gcc',*flags,'-S',str(src),'-o',str(assembly)],check=True)
    caller=assembly.read_text()
    expected_calls={
     '_ep7_queue_receive_probe':['add -16,sp','mov -1,d1','mov d1,(12,sp)','mov d0,d1','mov 75,d0','call _ep7_gcc_queue_receive_local,[],0','ret [],16'],
     '_ep7_queue_send_probe':['add -20,sp','mov -1,d1','mov d1,(16,sp)','mov 312,d1','mov d1,(12,sp)','mov d0,d1','mov 76,d0','call _ep7_gcc_queue_send_local,[],0','ret [],20']}
    for label,expected_body in expected_calls.items():
     body=caller.split(label+':\n',1)[1].split('\t.size',1)[0]
     if [line.strip() for line in body.splitlines() if line.strip()]!=expected_body:raise ValueError('GCC queue caller ABI changed: '+label)
    objects[name]['compiler_assembly']=caller
    objects[name]['checked_instructions']=sum(map(len,expected_calls.values()))
  if materializer_mode and name=='materializer_bridge':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   if len(ins)!=4 or ins[0]!=('mov','sp,a1') or ins[1]!=('mov','a1,d1') or ins[2][0]!='call' or not ins[2][1].endswith(',[],0') or ins[3]!=('ret','[d2,d3,a2,a3],44'):
    raise ValueError('materializer bridge ABI changed')
   if dis.count('R_MN10300_PCREL32')!=1 or '_ep7q_materializer_entry+0x1' not in dis:
    raise ValueError('materializer entry relocation changed')
   objects[name]['checked_instructions']=len(ins)
   objects[name]['incoming_native_frame_bytes']=44
   objects[name]['additional_bridge_frame_bytes']=0
  if receiver_mode and name=='descriptor_receive_bridge':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   wanted=[('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),('mov','a0,(20,sp)'),('mov','a1,(24,sp)'),
           ('mov','sp,a0'),('add','12,a0'),('mov','a0,d0'),('mov','sp,a1'),('mov','a1,d1'),
           ('call',None),('cmp','256,d0'),('bne',None),('mov','(12,sp),d0'),('mov','(16,sp),d1'),
           ('mov','(20,sp),a0'),('mov','(24,sp),a1'),('jmp',None),('ret','[d2,d3,a2,a3],44')]
   if len(ins)!=len(wanted):raise ValueError('descriptor receive bridge instruction count changed')
   for actual,want in zip(ins,wanted):
    if actual[0]!=want[0] or (want[1] is not None and actual[1].strip()!=want[1]):raise ValueError('descriptor receive bridge operand changed')
   addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+[a-z]',dis,re.M)
   target_rows=[line.split() for line in syms.splitlines() if line.split() and line.split()[-1]=='.Lreceived']
   if not ins[9][1].endswith(',[],0') or len(target_rows)!=1 or int(target_rows[0][0],16)!=int(addresses[-1],16) or dis.count('R_MN10300_PCREL8')!=1 or '.Lreceived+0x1' not in dis:
    raise ValueError('descriptor receive call/return branch changed')
   if dis.count('R_MN10300_PCREL32')!=2 or '_ep7q_descriptor_receive_entry+0x1' not in dis or 'ep7_stock_receive_wrapper_unresolved+0x1' not in dis:
    raise ValueError('descriptor receive relocation changed')
   objects[name]['checked_instructions']=len(ins)
   objects[name]['incoming_native_frame_bytes']=44
   objects[name]['additional_bridge_frame_bytes']=0
  if args.queue_pipeline_abi_only and name=='descriptor_send_bridge':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   wanted=[('mov','d0,(12,sp)'),('mov','a0,(16,sp)'),('mov','a1,(20,sp)'),
           ('mov','sp,a0'),('add','12,a0'),('mov','a0,d0'),('mov','sp,a1'),('mov','a1,d1'),
           ('call',None),('cmp','256,d0'),('bne',None),('mov','(12,sp),d0'),('mov','300,d1'),
           ('mov','(16,sp),a0'),('mov','(20,sp),a1'),('jmp',None),('ret','[d2,d3,a2],36')]
   if len(ins)!=len(wanted):raise ValueError('descriptor send bridge instruction count changed')
   for actual,want in zip(ins,wanted):
    if actual[0]!=want[0] or (want[1] is not None and actual[1].strip()!=want[1]):raise ValueError('descriptor send bridge operand changed')
   addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+[a-z]',dis,re.M)
   target_rows=[line.split() for line in syms.splitlines() if line.split() and line.split()[-1]=='.Lsent']
   if not ins[8][1].endswith(',[],0') or len(target_rows)!=1 or int(target_rows[0][0],16)!=int(addresses[-1],16) or dis.count('R_MN10300_PCREL8')!=1 or '.Lsent+0x1' not in dis:
    raise ValueError('descriptor send call/return branch changed')
   if dis.count('R_MN10300_PCREL32')!=2 or '_ep7q_descriptor_send_entry+0x1' not in dis or 'ep7_stock_send_wrapper_unresolved+0x1' not in dis:
    raise ValueError('descriptor send relocation changed')
   objects[name]['checked_instructions']=len(ins)
   objects[name]['incoming_native_frame_bytes']=36
   objects[name]['additional_bridge_frame_bytes']=0
  if args.queue_pipeline_abi_only and name=='producer_bridge':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   wanted=[('add','-64,sp'),('mov','d0,(16,sp)'),('mov','a2,d1'),('mov','d1,(20,sp)'),
           ('mov','sp,a0'),('add','24,a0'),('mov','a0,(12,sp)'),('call',None),('mov','(16,sp),d0'),
           ('call',None),('add','64,sp'),('ret','[d2,a2,a3],32'),
           ('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),('mov','a0,(20,sp)'),('mov','a1,(24,sp)'),
           ('mov','sp,a0'),('add','12,a0'),('mov','a0,d0'),('mov','sp,a1'),('mov','a1,d1'),
           ('call',None),('cmp','256,d0'),('bne',None),('mov','(12,sp),d0'),('mov','(16,sp),d1'),
           ('mov','(20,sp),a0'),('mov','(24,sp),a1'),('jmp',None),('ret','[d2,d3],48')]
   if len(ins)!=len(wanted):raise ValueError('producer bridge instruction count changed')
   for actual,want in zip(ins,wanted):
    if actual[0]!=want[0] or (want[1] is not None and actual[1].strip()!=want[1]):raise ValueError('producer bridge operand changed')
   addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+[a-z]',dis,re.M)
   rows={line.split()[-1]:int(line.split()[0],16) for line in syms.splitlines() if line.split() and line.split()[-1] in {'.Lproduced','_ep7_capture_scope_native_return'}}
   if not ins[7][1].endswith(',[],0') or not ins[9][1].endswith(',[d2,a2,a3],32') or not ins[21][1].endswith(',[],0') or rows.get('_ep7_capture_scope_native_return')!=int(addresses[10],16) or rows.get('.Lproduced')!=int(addresses[-1],16):
    raise ValueError('producer scope return label or native/GCC frames changed')
   if dis.count('R_MN10300_PCREL32')!=4 or dis.count('R_MN10300_PCREL8')!=1 or '.Lproduced+0x1' not in dis:
    raise ValueError('producer bridge relocation count/branch changed')
   for symbol in ['_ep7q_capture_scope_entry','ep7_stock_kind19_metadata_producer_unresolved','_ep7q_producer_entry','ep7_stock_command_send_unresolved']:
    if symbol+'+0x1' not in dis:raise ValueError('producer bridge relocation target changed')
   objects[name]['checked_instructions']=len(ins)
   objects[name]['owned_scope_frame_bytes']=64
   objects[name]['additional_native_frame_bytes']=32
   objects[name]['owned_scope_offset']=24
  if args.queue_pipeline_abi_only and name=='wait_bridges':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   save=[('add','-40,sp'),('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),('mov','a0,(20,sp)'),
         ('mov','a1,(24,sp)'),('mov','d2,(32,sp)'),('mov','mdr,d2'),('mov','d2,(28,sp)')]
   restore=[('mov','(28,sp),d2'),('mov','d2,mdr'),('mov','(32,sp),d2'),('mov','(12,sp),d0'),
            ('mov','(16,sp),d1'),('mov','(20,sp),a0'),('mov','(24,sp),a1'),('add','40,sp')]
   wanted=save+[('mov','d0,d1'),('mov','a0,d0'),('call',None),('mov','d0,(12,sp)')]+restore+[('ret','[],8')]
   wanted+=save+[('mov','a0,d0'),('mov','sp,a0'),('add','40,a0'),('mov','a0,d1'),('call',None),('mov','d0,(12,sp)')]+restore+[('ret','[],24')]
   wanted+=save+[('call',None)]+restore+[('jmp',None)]
   scope_begin=len(wanted)
   wanted+=[('add','-64,sp'),('mov','sp,a0'),('add','24,a0'),('mov','a0,d0'),('clr','d1'),
            ('mov','d1,(12,sp)'),('call',None),('call',None),('add','64,sp'),('ret','[d2],8')]
   wanted+=[('movm','[a2],(sp)'),('add','-12,sp'),('mov','d0,a0'),('mov','d1,d0'),('call',None),('ret','[a2],16'),
            ('movm','[a2],(sp)'),('add','-12,sp'),('mov','d0,a0'),('call',None),('ret','[a2],16')]
   if len(ins)!=len(wanted):raise ValueError('waiting-list bridge instruction count changed')
   for actual,want in zip(ins,wanted):
    if actual[0]!=want[0] or (want[1] is not None and actual[1].strip()!=want[1]):raise ValueError('waiting-list bridge operand changed')
   frames=[x[1].split(',',1)[1].strip() for x in ins if x[0]=='call']
   if frames!=['[],0','[],0','[],0','[],0','[d2],8','[],8','[],24']:
    raise ValueError('waiting-list native/GCC call frames changed')
   addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+[a-z]',dis,re.M)
   rows=[line.split() for line in syms.splitlines() if line.split() and line.split()[-1]=='_ep7_wait_scope_native_return']
   if len(rows)!=1 or int(rows[0][0],16)!=int(addresses[scope_begin+8],16):raise ValueError('deferred owned scope return label changed')
   relocations=['_ep7cn_wait_enqueue','_ep7cn_wait_pop','_ep7cn_wait_reset','ep7_stock_wait_initialize_unresolved',
                '_ep7q_capture_scope_init','ep7_stock_wait_service_unresolved','ep7_stock_associated_enqueue_unresolved','ep7_stock_wait_pop_unresolved']
   if dis.count('R_MN10300_PCREL32')!=len(relocations):raise ValueError('waiting-list relocation count changed')
   if any(symbol+'+0x1' not in dis for symbol in relocations):raise ValueError('waiting-list relocation target changed')
   objects[name].update(checked_instructions=len(ins),transaction_bridge_frame_bytes=40,
       owned_scope_frame_bytes=64,owned_scope_offset=24,pop_scope_offset=56,send_scope_offset=112,
       initializer_tail_preserves_incoming_tag=True)
  if args.queue_pipeline_abi_only and name=='engine_bridges':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   body=[('add','-40,sp'),('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),('mov','a0,(20,sp)'),
         ('mov','a1,(24,sp)'),('mov','d2,(32,sp)'),('mov','mdr,d2'),('mov','d2,(28,sp)'),('call',None),
         ('mov','(28,sp),d2'),('mov','d2,mdr'),('mov','(32,sp),d2'),('mov','(12,sp),d0'),
         ('mov','(16,sp),d1'),('mov','(20,sp),a0'),('mov','(24,sp),a1'),('add','40,sp'),('jmp',None)]
   if len(ins)!=2*len(body):raise ValueError('engine epoch bridge instruction count changed')
   for actual,want in zip(ins,body*2):
    if actual[0]!=want[0] or (want[1] is not None and actual[1].strip()!=want[1]):raise ValueError('engine epoch bridge operand changed')
   if any(not x[1].endswith(',[],0') for x in ins if x[0]=='call') or dis.count('R_MN10300_PCREL32')!=4:
    raise ValueError('engine epoch bridge call frame/relocations changed')
   for symbol in ['_ep7cn_engine_epoch','ep7_stock_engine_configure_unresolved','ep7_stock_engine_pool_unresolved']:
    if symbol+'+0x1' not in dis:raise ValueError('engine epoch bridge target changed')
   objects[name].update(checked_instructions=len(ins),additional_bridge_frame_bytes=40,
       both_original_calls_tail_transferred=True)
  if name=='worker_bridge':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   expected=['add','mov','mov','mov','mov','mov','mov','add','mov','call','mov','mov','mov','mov','call','add','ret',
             'mov','mov','add','call','add','ret','movm','add','call','ret']
   observer=['add','mov','mov','mov','mov','mov','mov','add','mov','call','mov','mov','mov','mov','add','jmp']
   if [mn for mn,op in ins]!=expected+observer+observer:raise ValueError('worker bridge instruction sequence changed')
   literals={0:'-80,sp',1:'d0,(16,sp)',2:'d1,(20,sp)',3:'a0,(24,sp)',4:'a1,(28,sp)',
             5:'sp,a0',6:'a0,d1',7:'32,a0',8:'a0,d0',10:'(16,sp),d0',11:'(20,sp),d1',
             12:'(24,sp),a0',13:'(28,sp),a1',15:'80,sp',16:'[a2,a3],56',
             17:'sp,a0',18:'a0,d1',19:'-16,sp',21:'16,sp',22:'[],4',23:'[a2],(sp)',24:'-12,sp',26:'[a2],16'}
   observer_ops={0:'-16,sp',1:'d0,(12,sp)',2:'d1,(16,sp)',3:'a0,(20,sp)',4:'a1,(24,sp)',5:'a0,d0',
                 6:'sp,a0',7:'16,a0',8:'a0,d1',10:'(12,sp),d0',11:'(16,sp),d1',12:'(20,sp),a0',13:'(24,sp),a1',14:'16,sp'}
   for base in [27,43]:literals.update({base+i:op for i,op in observer_ops.items()})
   if any(ins[i][1]!=op for i,op in literals.items()):raise ValueError('worker bridge frame/input preservation changed')
   for i,mask in {9:',[],0',14:',[a2,a3],56',20:',[],0',25:',[],4',36:',[],0',52:',[],0'}.items():
    if not ins[i][1].endswith(mask):raise ValueError('worker bridge native/GCC call frame changed')
   addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+[a-z]',dis,re.M)
   rows={line.split()[-1]:int(line.split()[0],16) for line in syms.splitlines() if len(line.split())>=5 and '*UND*' not in line and re.fullmatch('[0-9a-f]+',line.split()[0])}
   if rows.get('_ep7_worker_native_return')!=int(addresses[15],16):raise ValueError('worker scope return label changed')
   targets=['_ep7q_worker_scope_entry','ep7_stock_worker_job_unresolved','_ep7q_worker_allocate_entry',
            'ep7_stock_job_allocate_unresolved','_ep7q_worker_process_entry','ep7_stock_worker_process_unresolved',
            '_ep7q_worker_cleanup_entry','ep7_stock_worker_cleanup_unresolved']
   if dis.count('R_MN10300_PCREL32')!=8 or any(symbol+'+0x1' not in dis for symbol in targets):
    raise ValueError('worker bridge relocation targets changed')
   objects[name].update(checked_instructions=len(ins),owned_wrapper_bytes=80,additional_native_frame_bytes=56,
                        owned_scope_bytes=48,owned_scope_offset=32,pointer_result_register='a0')
  if name=='ack_bridge':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   expected=[('add','-16,sp'),('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),('mov','a0,(20,sp)'),
             ('mov','a1,(24,sp)'),('mov','a0,d0'),('mov','sp,a0'),('add','16,a0'),('mov','a0,d1')]
   after=[('mov','(12,sp),d0'),('mov','(16,sp),d1'),('mov','(20,sp),a0'),('mov','(24,sp),a1'),('add','16,sp')]
   if len(ins)!=16 or ins[:9]!=expected or ins[10:15]!=after or ins[9][0]!='call' or not ins[9][1].endswith(',[],0') or ins[15][0]!='jmp':
    raise ValueError('ACK native input/frame preservation changed')
   if dis.count('R_MN10300_PCREL32')!=2 or any(s+'+0x1' not in dis for s in ['_ep7q_ack_entry','ep7_stock_ack_unresolved']):
    raise ValueError('ACK bridge relocation changed')
   objects[name].update(checked_instructions=len(ins),own_frame_bytes=16,native_tail_frame_bytes=32)
  if name=='worker_caller':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   if '_ep7_gcc_job_allocate+0x1' not in dis or not re.search(r'mov\s+a0,d0',dis):
    raise ValueError('GCC pointer result no longer consumed from a0')
   objects[name]['gcc_pointer_result_a0_confirmed']=True
  if name=='capture_bridges':
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   ins=[(mn,re.sub(r'\(([0-9a-f]+) <[^>]+>\)',lambda m:'(0x'+m[1]+')',op)) for mn,op in ins]
   save=[('add','-40,sp'),('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),('mov','a0,(20,sp)'),
       ('mov','a1,(24,sp)'),('mov','d2,(32,sp)'),('mov','mdr,d2'),('mov','d2,(28,sp)')]
   restore=[('mov','(28,sp),d2'),('mov','d2,mdr'),('mov','(32,sp),d2'),('mov','(12,sp),d0'),
       ('mov','(16,sp),d1'),('mov','(20,sp),a0'),('mov','(24,sp),a1'),('add','40,sp')]
   expected=save+[('call',None)]+restore+[('movhu','d0,(0x62234fc0)'),('jmp',None)]
   expected+=[('call',None)]+save+[('mov','a0,d0'),('call',None)]+restore+[('ret','[d2,a2],28')]
   expected+=[('call',None)]+save+[('mov','a2,d0'),('clr','d1'),('call',None)]+restore+[('ret','[d2,d3,a2,a3],20')]
   expected+=[('call',None)]+save+[('mov','a2,d0'),('mov','1,d1'),('call',None)]+restore+[('ret','[d2,d3,a2,a3],48')]
   expected+=save+[('mov','a0,d0'),('call',None)]+restore+[('jmp',None)]
   expected+=save+[('mov','a2,d0'),('call',None)]+restore+[('jmp',None)]
   for phase in [('clr','d1'),('mov','1,d1')]:
    expected+=[('call',None)]+save+[('mov','a0,d0'),phase,('call',None)]+restore+[('ret','[],24')]
   expected+=save+[('mov','a3,d0'),('mov','a2,d1'),('call',None)]+restore+[('jmp',None)]
   expected+=save+[('call',None)]+restore+[('jmp',None)]
   expected+=[('movm','[a2],(sp)'),('add','-12,sp'),('call',None),('ret','[a2],16')]
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    raise ValueError('capture bridge input/result/MDR preservation changed')
   calls=[op for mn,op in ins if mn=='call']
   masks=[',[],0',',[d2,a2],28',',[],0',',[d2,d3,a2,a3],20',',[],0',',[d2,d3,a2,a3],48',',[],0',',[],0',',[],0',',[],24',',[],0',',[],24',',[],0',',[],0',',[],0',',[],24']
   if len(calls)!=len(masks) or any(not op.endswith(mask) for op,mask in zip(calls,masks)):
    raise ValueError('capture native/GCC call masks changed')
   expected_refs=['_ep7cn_initialize','ep7_stock_capture_init_continue_unresolved','ep7_stock_capture_fresh_unresolved',
       '_ep7cn_fresh','ep7_stock_capture_population_unresolved','_ep7cn_population','ep7_stock_capture_postpopulation_unresolved',
       '_ep7cn_population','_ep7cn_free','ep7_stock_capture_node_free_unresolved','_ep7cn_release_capture',
       'ep7_stock_capture_pool_release_unresolved','ep7_stock_capture_lookup_unresolved','_ep7cn_prewrite',
       'ep7_stock_capture_lookup_unresolved','_ep7cn_prewrite','_ep7cn_associated_recycle',
       'ep7_stock_associated_enqueue_unresolved','_ep7cn_associated_reset',
       'ep7_stock_associated_initialize_unresolved','ep7_stock_capture_lookup_unresolved']
   refs=re.findall(r'R_MN10300_PCREL32\s+([^\s+]+)\+0x1',dis)
   if refs!=expected_refs:raise ValueError('capture relocation ordering changed')
   objects[name].update(checked_instructions=len(ins),observer_frame_bytes=40,lookup_own_frame_bytes=16,
       added_nested_native_frames=[28,20,48,24],pointer_result_register='a0',free_and_release_tail_calls=True,
       common_prewrite_lookup_result_and_mdr_preserved=True,
       associated_recycle_and_initializer_tail_transfer=True,initializer_incoming_stack_arguments_preserved=True)
  if name=='capture_state_bridge':
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   expected=[('call',None),('add','-32,sp'),('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),
       ('mov','a0,(20,sp)'),('mov','a1,(24,sp)'),('mov','mdr,d2'),('mov','d2,(28,sp)'),('call',None),
       ('mov','(12,sp),d0'),('mov','(16,sp),d1'),('mov','(20,sp),a0'),('mov','(24,sp),a1'),
       ('mov','(28,sp),d2'),('mov','d2,mdr'),('add','32,sp'),('ret','[d2,d3,a2,a3],32')]
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    raise ValueError('reused state bridge ABI changed')
   if not ins[0][1].endswith(',[d2,d3,a2,a3],32') or not ins[8][1].endswith(',[],0'):
    raise ValueError('reused state bridge call frame changed')
   refs=re.findall(r'R_MN10300_PCREL32\s+([^\s+]+)\+0x1',dis)
   if refs!=['ep7_stock_state_service_unresolved','_ep7_gcc_state_transition_observer']:
    raise ValueError('reused state bridge relocation changed')
   objects[name].update(checked_instructions=17,own_frame_bytes=32,additional_nested_native_frame=32)
  if name=='kernel_gate':
   wanted={'_ep7_native_runtime_slot','_ep7r_get','_ep7r_io_open','_ep7r_guard_queue','_ep7r_note_queue_delete',
       '_ep7_queue_receive_native_return','_ep7_queue_raw_send_native_return','_ep7_queue_named_send_native_return'}
   if und!=wanted:raise ValueError('kernel gate acquired an unqualified dependency: '+repr(und))
   objects[name].update(native_api_calls=False,private_lock_calls=False,caller_return_offsets=[32,40,88])
  if args.queue_pipeline_abi_only and name=='runtime':
   pure=['_ep7r_get','_ep7r_stop','_ep7r_io_open','_ep7r_guard_queue','_ep7r_note_queue_delete']
   bodies=dict(re.findall(r'(?ms)^[0-9a-f]+ <([^>]+)>:\n(.*?)(?=^[0-9a-f]+ <|\Z)',dis))
   for symbol in pure:
    body=bodies.get(symbol)
    if body is None or re.search(r'\b(?:call|calls)\s',body):raise ValueError('kernel-critical runtime helper gained a call: '+symbol)
    refs=re.findall(r'R_MN10300_[A-Z0-9]+\s+([^\s+]+)',body)
    if any(not ref.startswith('.L') for ref in refs):raise ValueError('kernel-critical runtime helper gained a dependency: '+symbol+' '+repr(refs))
   objects[name]['kernel_critical_helpers_without_calls_or_external_dependencies']=pure
  if name=='kernel_gate_bridges':
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   # Relocatable objects annotate absolute memory operands with a nearby symbol.
   ins=[(mn,re.sub(r'\(([0-9a-f]+) <[^>]+>\)',lambda m:'(0x'+m[1]+')',op)) for mn,op in ins]
   save=[('add','-40,sp'),('mov','d0,(12,sp)'),('mov','d1,(16,sp)'),('mov','a0,(20,sp)'),
       ('mov','a1,(24,sp)'),('mov','d2,(32,sp)'),('mov','mdr,d2'),('mov','d2,(28,sp)')]
   restore=[('mov','(28,sp),d2'),('mov','d2,mdr'),('mov','(32,sp),d2'),('mov','(12,sp),d0'),
       ('mov','(16,sp),d1'),('mov','(20,sp),a0'),('mov','(24,sp),a1'),('add','40,sp')]
   route=[('mov','sp,a0'),('add','40,a0'),('mov','a0,d0'),('mov','a2,d1'),('call',None),('cmp','0,d0'),('beq',None)]
   receive=save+route+restore+[('mov','(0x8050),d0'),('asl2','d0'),('mov','-1880096764,a0'),('jmp',None)]+restore+[('mov','-42,d0'),('jmp',None)]
   send=save+route+restore+[('mov','(20,sp),d0'),('mov','20,d3'),('add','a2,d3'),('jmp',None)]+restore+[('mov','-42,d0'),('jmp',None)]
   delete=save+[('mov','a3,d0'),('call',None)]+restore+[('mov','20,a0'),('add','a3,a0'),('movbu','(a0),d0'),('jmp',None)]
   expected=receive+send+delete
   if len(ins)!=len(expected) or any(a[0]!=b[0] or (b[1] is not None and a[1]!=b[1]) for a,b in zip(ins,expected)):
    differences=[(i,a,b) for i,(a,b) in enumerate(zip(ins,expected)) if a[0]!=b[0] or (b[1] is not None and a[1]!=b[1])]
    raise ValueError('kernel gate sequence changed: lengths '+repr((len(ins),len(expected)))+' '+repr(differences[:5]))
   if any(not op.endswith(',[],0') for mn,op in ins if mn=='call'):raise ValueError('kernel gate GCC call frame changed')
   addresses=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+[a-z]',dis,re.M)
   rows={line.split()[-1]:int(line.split()[0],16) for line in syms.splitlines() if len(line.split())>=5 and '*UND*' not in line and re.fullmatch('[0-9a-f]+',line.split()[0])}
   for symbol,index in [('.Lreceive_rejected',27),('.Lsend_rejected',len(receive)+27)]:
    if rows.get(symbol)!=int(addresses[index],16) or symbol+'+0x1' not in dis:raise ValueError('kernel gate reject branch changed')
   targets=['_ep7r_native_receive_gate','_ep7r_native_send_gate','_ep7r_native_delete_observer',
       'ep7_stock_receive_gate_continue_unresolved','ep7_stock_receive_gate_error_unresolved',
       'ep7_stock_send_gate_continue_unresolved','ep7_stock_send_gate_error_unresolved','ep7_stock_delete_gate_continue_unresolved']
   if dis.count('R_MN10300_PCREL32')!=len(targets) or dis.count('R_MN10300_PCREL8')!=2 or any(s+'+0x1' not in dis for s in targets):
    raise ValueError('kernel gate relocation targets changed')
   objects[name].update(checked_instructions=len(ins),own_frame_bytes=40,inline_entry=True,register_and_mdr_preserved=True)
  if name=='task_delay':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   if len(ins)!=5 or ins[:3]!=[('movm','[a2],(sp)'),('add','-12,sp'),('mov','1,d0')] or ins[4]!=('ret','[a2],16') or not ins[3][1].endswith(',[d2,a2,a3],16'):
    raise ValueError('task delay frame/input changed')
   if dis.count('R_MN10300_PCREL32')!=1 or 'ep7_stock_task_delay_unresolved+0x1' not in dis:raise ValueError('task delay relocation changed')
   objects[name].update(checked_instructions=5,fixed_input_units=1,status_preserved=True)
  if name=='quarantine':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*([0-9a-f]+):[ \t]+(?:[0-9a-f]{2}[ \t]+)+([a-z][a-z0-9]*)(?:[ \t]+([^\n]*))?$',dis,re.M)
   rows={line.split()[-1]:int(line.split()[0],16) for line in syms.splitlines() if len(line.split())>=5 and '*UND*' not in line and re.fullmatch('[0-9a-f]+',line.split()[0])}
   if len(ins)!=2 or [i[1] for i in ins]!=['break','bra'] or rows.get('.Lquarantined')!=int(ins[0][0],16):
    raise ValueError('quarantine must trap and branch back without return/free/reset')
   if dis.count('R_MN10300_PCREL8')!=1 or '.Lquarantined+0x1' not in dis:
    raise ValueError('quarantine loop relocation changed')
   objects[name].update(checked_instructions=2,owned_terminal_loop=True,native_exception_behavior_executed=False)
  if name=='get_tid':
   dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
   ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
   if len(ins)!=5 or ins[:3]!=[('movm','[a2],(sp)'),('add','-12,sp'),('mov','d0,a0')] or ins[4]!=('ret','[a2],16') or not ins[3][1].endswith(',[a2],4'):
    raise ValueError('existing get_tid veneer frame/argument routing changed')
   if dis.count('R_MN10300_PCREL32')!=1 or 'ep7_stock_get_tid_unresolved+0x1' not in dis:raise ValueError('get_tid relocation changed')
   objects[name]['checked_instructions']=5
  if args.transport_only or materializer_mode or args.task_context_only or ui_mode or selector_mode:
   objects[name]['size_output']=subprocess.check_output([prefix+'size',str(obj)],text=True).splitlines()[1].split()[:4]
   if src.suffix=='.c':objects[name]['stack_usage']=obj.with_suffix('.su').read_text().splitlines()
external=undefined-set(definitions)
expected=set() if args.transport_only else {'_ep7_controller_sidecar_unresolved','ep7_stock_state_service_unresolved'}
if args.task_context_only:expected={'ep7_stock_get_tid_unresolved','ep7_stock_task_delay_unresolved'}
if ui_mode:expected={'ep7_stock_get_tid_unresolved','ep7_stock_ui_service_unresolved',
    'ep7_stock_ui_context_get_unresolved','ep7_stock_ui_context_set_unresolved',
    'ep7_stock_text_cleanup_unresolved','ep7_stock_text_destructor_unresolved'}
if ui_create_mode:expected.add('ep7_stock_widget_factory_unresolved')
if ui_lifecycle_mode:expected|={'ep7_stock_ui_attach_unresolved','ep7_stock_text_bind_unresolved',
    'ep7_stock_text_setter_unresolved','ep7_stock_ui_find_child_unresolved',
    '_ep7_stock_hl_text_descriptor_unresolved','_ep7_stock_hl_text_layouts_unresolved'}
if graph_mode:expected|={'ep7_stock_screen_manager_unresolved',
    'ep7_stock_ui_owner_cleanup_unresolved','ep7_stock_ui_owner_bulk_unresolved',
    'ep7_stock_ui_owner_destructor_unresolved','_ep7_stock_ui_service_vtable_unresolved',
    '_ep7_stock_ui_display_vtable_unresolved'}
if selector_mode:
 if not ui_mode:expected=set()
 expected|={'ep7_stock_get_tid_unresolved','ep7_stock_selector_init_unresolved',
     '_ep7_stock_selector_initializer_unresolved','ep7_stock_mvc_array_new_unresolved',
     'ep7_stock_mvc_array_delete_unresolved'}
if mvc_mode:expected|={'_ep7_stock_gui_color_entry_unresolved','_ep7_stock_gui_color_exit_unresolved',
    '_ep7_stock_mvc_parent_vtable_unresolved','_ep7_stock_mvc_viewer_vtable_unresolved',
    '_ep7_stock_color_container_unresolved','ep7_stock_mvc_gui_entry_unresolved',
    'ep7_stock_mvc_gui_exit_unresolved','ep7_stock_mvc_parent_destroy_unresolved',
    'ep7_stock_mvc_viewer_destroy_unresolved','_ep7_stock_mvc_rebuild_initial_call_unresolved',
    '_ep7_stock_mvc_rebuild_previous_call_unresolved','_ep7_stock_mvc_rebuild_next_call_unresolved',
    '_ep7_stock_mvc_rebuild_touch_call_unresolved',
    '_ep7_stock_selector_remembered_unresolved','ep7_stock_mvc_rebuild_unresolved',
    'ep7_stock_mvc_scalar_new_unresolved','ep7_stock_mvc_scalar_delete_unresolved',
    'ep7_stock_mvc_base_init_unresolved','ep7_stock_mvc_base_destroy_unresolved'}
if graph_mode:expected|={'ep7_stock_property_service_unresolved','ep7_stock_mvc_viewer_draw_unresolved'}
if graph_mode:expected|={'_ep7_stock_gui_machine_unresolved','_ep7_stock_ui_input_gate_unresolved',
    '_ep7_stock_ui_repeat_context_unresolved','ep7_stock_ui_preprocess_unresolved','ep7_stock_ui_dispatch_unresolved',
    'ep7_stock_ui_wheel_set_unresolved','ep7_stock_ui_event_unresolved','ep7_stock_ui_drop_event_unresolved',
    '_ep7_stock_ui_preprocess_call_unresolved','_ep7_stock_ui_dispatch_call_unresolved',
    '_ep7_stock_ui_wheel_1_call_unresolved','_ep7_stock_ui_wheel_0_call_unresolved',
    '_ep7_stock_ui_wheel_2_call_unresolved','_ep7_stock_ui_wheel_4_call_unresolved',
    '_ep7_stock_ui_wheel_3_call_unresolved'}
if graph_mode:expected|={'_ep7_stock_mvc_category_keys_unresolved','_ep7_stock_ui_active_content_unresolved',
    'ep7_stock_mvc_creator0_unresolved','ep7_stock_mvc_creator7_unresolved','ep7_stock_mvc_creator14_unresolved',
    'ep7_stock_mvc_stock_selected_unresolved','ep7_stock_mvc_stop535_unresolved','ep7_stock_ui_timer_cancel_unresolved'}
if args.queue_abi_only:expected={'ep7_stock_queue_receive_local_unresolved','ep7_stock_queue_send_local_unresolved','ep7_stock_queue_send_preserving_unresolved'}
if args.materializer_abi_only:expected={'_ep7q_materializer_context_unresolved','ep7_stock_queue_receive_local_unresolved','ep7_stock_queue_send_local_unresolved','ep7_stock_queue_send_preserving_unresolved'}
if receiver_mode:expected={'_ep7q_materializer_context_unresolved','_ep7q_descriptor_receive_context_unresolved','ep7_stock_queue_receive_local_unresolved','ep7_stock_queue_send_local_unresolved','ep7_stock_queue_send_preserving_unresolved','ep7_stock_receive_wrapper_unresolved'}
if args.queue_pipeline_abi_only:expected|={'_ep7q_descriptor_send_context_unresolved','ep7_stock_send_wrapper_unresolved',
    '_ep7q_capture_snapshot_unresolved','_ep7q_producer_context_unresolved','ep7_stock_kind19_metadata_producer_unresolved','ep7_stock_command_send_unresolved',
    '_ep7q_worker_context_unresolved','ep7_stock_worker_job_unresolved','ep7_stock_job_allocate_unresolved',
    'ep7_stock_worker_process_unresolved','ep7_stock_worker_cleanup_unresolved','_ep7q_ack_context_unresolved','ep7_stock_ack_unresolved'}
if args.queue_pipeline_abi_only:
 expected-={'_ep7q_materializer_context_unresolved','_ep7q_descriptor_receive_context_unresolved',
     '_ep7q_descriptor_send_context_unresolved','_ep7q_producer_context_unresolved',
     '_ep7q_worker_context_unresolved','_ep7q_ack_context_unresolved','_ep7q_capture_snapshot_unresolved'}
 expected|={'ep7_stock_get_tid_unresolved','ep7_stock_task_delay_unresolved',
     'ep7_stock_color_builder_unresolved',
     'ep7_stock_state_service_unresolved','ep7_stock_capture_init_continue_unresolved',
     'ep7_stock_capture_fresh_unresolved','ep7_stock_capture_population_unresolved',
     'ep7_stock_capture_postpopulation_unresolved','ep7_stock_capture_node_free_unresolved',
     'ep7_stock_capture_pool_release_unresolved','ep7_stock_capture_lookup_unresolved',
     'ep7_stock_associated_enqueue_unresolved','ep7_stock_associated_initialize_unresolved',
     'ep7_stock_wait_pop_unresolved','ep7_stock_wait_initialize_unresolved','ep7_stock_wait_service_unresolved',
     'ep7_stock_engine_configure_unresolved','ep7_stock_engine_pool_unresolved',
     'ep7_stock_receive_gate_continue_unresolved','ep7_stock_receive_gate_error_unresolved',
     'ep7_stock_send_gate_continue_unresolved','ep7_stock_send_gate_error_unresolved','ep7_stock_delete_gate_continue_unresolved',
     'ep7_stock_raw_sem_wait_unresolved','ep7_stock_raw_sem_signal_unresolved',
     'ep7_stock_raw_sem_create_unresolved','ep7_stock_raw_sem_delete_unresolved'}
if external!=expected:raise ValueError('unexpected external symbols '+repr(external))
scope='Snapshot transport, wire codec, owned queue I/O and memory target objects only' if args.transport_only else 'Current seven-object controller sidecar target compile and symbol closure only'
if args.queue_abi_only:scope='Raw queue and notification-preserving send callable ABI bridges; no native invocation'
if args.materializer_abi_only:scope='Exact materializer receive bridge and bounded frame mapper; context provider/native addresses unresolved'
if args.receive_abi_only:scope='Command and descriptor receive bridges with bounded stack mappers; native context providers/addresses unresolved'
if args.queue_pipeline_abi_only:scope='Owned pipeline, shared runtime, native capture source and kernel-critical queue gate candidates; installation, full lifetime closure and native addresses remain unbound'
if args.task_context_only:scope='Read-only current-task stack and actual local queue views with existing get_tid/delay veneers; no lifetime lease, installation flag or native execution'
if ui_mode:scope='Fresh text rollback with actual native context callbacks; qualified object/service lifetime and serialized GUI ownership remain caller obligations'
if ui_create_mode:scope='Existing text factory result/context bridge and native rollback closure; resource/UI ownership and actual lifecycle attachment remain unqualified'
if ui_lifecycle_mode:scope='Actual text create/attach/bind/set/rollback C and native ABI closure; concrete live owner/GUI entry, resource semantics and teardown hooks remain unqualified'
if args.ui_owner_only:scope='Request278 owner capture and matching retirement with native table cohort and text lifecycle; cold installation, bypass closure, GUI exclusion, MVC/renderer and placement remain unqualified'
if args.ui_selector_only:scope='Native ID193 post-initializer six-entry storage upgrade with H/L disabled and allocation-failure stock fallback; no MVC/viewer/input admission or installation'
if graph_mode:scope='COLOR-qualified H/L masks, safe stock restoration and event-scoped input joined to actual UI graph/core; cold placement/installation, native bypass closure, total stack, hardware and LCD acceptance pending'
report=dict(scope=scope,versions=versions,objects=objects,remaining_external_symbols=sorted(external),hash_checks_performed=False,target_linked=False,target_executed=False,firmware_built=False,native_adapter_installed=False)
print(json.dumps(report,indent=2))
