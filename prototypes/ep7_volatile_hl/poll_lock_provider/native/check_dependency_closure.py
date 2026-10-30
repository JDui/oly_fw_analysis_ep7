#!/usr/bin/env python3
"""Finite object-symbol closure of selected CPU reader/provider. NEVER links."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
CORE=ROOT/'prototypes/ep7_volatile_hl';TARGET=CORE/'target'
EXPECTED_EXTERNAL={'_ep7_native_runtime_unresolved','ep7_stock_color_builder_unresolved','ep7_stock_get_tid_unresolved','ep7_stock_raw_sem_wait_unresolved','ep7_stock_raw_sem_signal_unresolved'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def symbols(text):
 defs=set();undef=set()
 for line in text.splitlines():
  parts=line.split()
  if not parts or not re.fullmatch('[0-9a-fA-F]{8}',parts[0]):continue
  if '*UND*' in parts:undef.add(parts[-1])
  elif len(parts)>2 and parts[1]=='g':defs.add(parts[-1])
 return defs,undef
def resolve(objects):
 owners={}
 for obj,info in objects.items():
  for symbol in info['global_definitions']:
   if symbol in owners:raise ValueError('duplicate global definition: '+symbol)
   owners[symbol]=obj
 externals=set();edges=[]
 for obj,info in objects.items():
  for symbol in info['undefined_symbols']:
   if symbol in owners:edges.append(dict(consumer=obj,symbol=symbol,provider=owners[symbol]))
   else:externals.add(symbol)
 if externals!=EXPECTED_EXTERNAL:raise ValueError('unexpected external closure: '+repr(sorted(externals)))
 return sorted(externals),sorted(edges,key=lambda e:(e['consumer'],e['symbol']))
def check():
 manifest=json.loads((TARGET/'build-manifest.json').read_text())
 for path,digest in manifest['tools'].items():
  if sha(ROOT/path)!=digest:raise ValueError('untrusted target tool: '+path)
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 sources={'core':CORE/'ep7p.c','decoder':CORE/'ep7p_decode.c','memory':TARGET/'memory.c','poll_provider':CORE/'poll_lock_provider/ep7_sem_provider.c','raw_callbacks':HERE/'raw_callbacks.c','native_observer':TARGET/'postbuilder/native_observer.c','get_tid_bridge':TARGET/'get_tid_bridge.s','semaphore_bridges':HERE/'sem_bridges.s','postbuilder_bridge':TARGET/'postbuilder/postbuilder_bridge.s'}
 flags=['-B'+str(gcc.parent)+'/','-std=c11','-O2','-ffreestanding','-fno-builtin','-fno-tree-loop-distribute-patterns','-mno-setlb','-mno-liw','-Wall','-Wextra','-Werror','-I'+str(CORE),'-I'+str(TARGET/'include'),'-I'+str(CORE/'poll_lock_provider')]
 objects={}
 with tempfile.TemporaryDirectory(prefix='ep7-unlinked-closure-') as tmp:
  temp=Path(tmp)
  for name,source in sources.items():
   obj=temp/(name+'.o');asm=source
   if source.suffix=='.c':
    asm=temp/(name+'.s');subprocess.run([str(gcc),*flags,'-S',str(source),'-o',str(asm)],check=True)
   subprocess.run([str(gas),'-o',str(obj),str(asm)],check=True)
   header=subprocess.check_output([str(od),'-f',str(obj)],text=True)
   if 'elf32-mn10300' not in header:raise ValueError('not MN10300 object')
   table=subprocess.check_output([str(od),'-t',str(obj)],text=True);defs,undef=symbols(table)
   objects[name]=dict(source=str(source.relative_to(ROOT)),source_sha256=sha(source),object_sha256=sha(obj),global_definitions=sorted(defs),undefined_symbols=sorted(undef))
 external,edges=resolve(objects)
 headers=[CORE/'ep7p.h',CORE/'ep7p_direct.h',CORE/'ep7p_decode.h',CORE/'poll_lock_provider/ep7_sem_provider.h',TARGET/'include/string.h']
 return dict(scope='Selected CPU reader/provider object-symbol closure, not camera end-to-end execution',objects=objects,header_sha256={str(p.relative_to(ROOT)):sha(p) for p in headers},internal_reference_edges=edges,remaining_external_symbols=external,tool_hashes=manifest['tools'],selected_object_count=len(objects),all_self_authored_undefined_references_have_selected_definitions=True,cas_provider_selected=False,gui_installation_selected=False,private_semaphore_initialization_bound=False,native_context_qualified=False,runtime_initialized=False,relocation_ranges_validated=False,target_linked=False,target_executed=False,firmware_input_used=False,flash_ready=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
