#!/usr/bin/env python3
"""Compile current sidecar sources with explicitly selected installed MN103 tools."""
from pathlib import Path
import argparse,json,re,subprocess,tempfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--tool-prefix',required=True,help='trusted installed tool path prefix ending mn10300-elf-')
mode=parser.add_mutually_exclusive_group()
mode.add_argument('--transport-only',action='store_true',help='compile snapshot transport, wire codec and existing memory support')
mode.add_argument('--queue-abi-only',action='store_true',help='assemble local raw queue veneers and compile their GCC caller probes')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1];core=root/'prototypes/ep7_volatile_hl';prefix=args.tool_prefix
versions={n:subprocess.check_output([prefix+n,'--version'],text=True).splitlines()[0] for n in ['gcc','as','ld','objdump']}
include=subprocess.check_output([prefix+'gcc','-print-file-name=include'],text=True).strip()
flags=['-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-mno-setlb','-mno-liw','-nostdinc','-I'+str(core/'target/include'),'-I'+include,'-I'+str(core)]
files={'sidecar':core/'controller_sidecar/sidecar.c','transition':core/'controller_sidecar/transition_binding.c','observer':core/'capture_state_guard/observer.c','bridge':core/'capture_state_guard/bridge.s','core':core/'ep7p.c','decode':core/'ep7p_decode.c','memory':core/'target/memory.c'}
if args.transport_only:
 files={'transport':core/'snapshot_transport/transport.c','wire':core/'snapshot_transport/wire.c','memory':core/'target/memory.c'}
 flags.append('-fstack-usage')
if args.queue_abi_only:
 files={'queue_bridge':core/'snapshot_transport/native/queue_bridges.s','caller':core/'snapshot_transport/native/bridge_caller.c'}
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
  if args.queue_abi_only:
   if name=='queue_bridge':
    dis=subprocess.check_output([prefix+'objdump','-dr','--insn-width=16',str(obj)],text=True)
    ins=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s+([^\n]+)',dis,re.M)
    expected_ins=[('movm','[a2],(sp)'),('add','-12,sp'),('mov','d1,a0'),('mov','(28,sp),d1'),('call',None),('ret','[a2],16'),
                  ('movm','[a2],(sp)'),('add','-12,sp'),('mov','d1,a0'),('mov','(28,sp),d1'),('mov','(32,sp),a1'),('call',None),('ret','[a2],16')]
    if len(ins)!=len(expected_ins):raise ValueError('queue bridge instruction count changed')
    for actual,want in zip(ins,expected_ins):
     if actual[0]!=want[0] or (want[1] is not None and actual[1].strip()!=want[1]):raise ValueError('queue bridge operand changed')
    if ',[d2,d3,a2,a3],32' not in ins[4][1] or ',[d2,d3,a2,a3],40' not in ins[11][1]:raise ValueError('queue native save/frame changed')
    if dis.count('R_MN10300_PCREL32')!=2:raise ValueError('queue bridge relocation count changed')
    for target in ('ep7_stock_queue_receive_local_unresolved','ep7_stock_queue_send_local_unresolved'):
     if target+'+0x1' not in dis:raise ValueError('queue bridge relocation target changed')
    objects[name]['checked_instructions']=len(ins)
    objects[name]['own_frame_bytes']=16
    objects[name]['native_nested_frames']=[32,40]
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
  if args.transport_only:
   objects[name]['size_output']=subprocess.check_output([prefix+'size',str(obj)],text=True).splitlines()[1].split()[:4]
   objects[name]['stack_usage']=obj.with_suffix('.su').read_text().splitlines()
external=undefined-set(definitions)
expected=set() if args.transport_only else {'_ep7_controller_sidecar_unresolved','ep7_stock_state_service_unresolved'}
if args.queue_abi_only:expected={'ep7_stock_queue_receive_local_unresolved','ep7_stock_queue_send_local_unresolved'}
if external!=expected:raise ValueError('unexpected external symbols '+repr(external))
scope='Snapshot transport, wire codec and memory target objects only' if args.transport_only else 'Current seven-object controller sidecar target compile and symbol closure only'
if args.queue_abi_only:scope='Local raw queue callable ABI bridges only; no native queue invocation'
report=dict(scope=scope,versions=versions,objects=objects,remaining_external_symbols=sorted(external),hash_checks_performed=False,target_linked=False,target_executed=False,firmware_built=False,native_adapter_installed=False)
print(json.dumps(report,indent=2))
