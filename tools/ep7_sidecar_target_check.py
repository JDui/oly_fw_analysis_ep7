#!/usr/bin/env python3
"""Compile current sidecar sources with explicitly selected installed MN103 tools."""
from pathlib import Path
import argparse,json,subprocess,tempfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--tool-prefix',required=True,help='trusted installed tool path prefix ending mn10300-elf-')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1];core=root/'prototypes/ep7_volatile_hl';prefix=args.tool_prefix
versions={n:subprocess.check_output([prefix+n,'--version'],text=True).splitlines()[0] for n in ['gcc','as','ld','objdump']}
include=subprocess.check_output([prefix+'gcc','-print-file-name=include'],text=True).strip()
flags=['-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-mno-setlb','-mno-liw','-nostdinc','-I'+str(core/'target/include'),'-I'+include,'-I'+str(core)]
files={'sidecar':core/'controller_sidecar/sidecar.c','transition':core/'controller_sidecar/transition_binding.c','observer':core/'capture_state_guard/observer.c','bridge':core/'capture_state_guard/bridge.s','core':core/'ep7p.c','decode':core/'ep7p_decode.c','memory':core/'target/memory.c'}
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
external=undefined-set(definitions)
if external!={'_ep7_controller_sidecar_unresolved','ep7_stock_state_service_unresolved'}:raise ValueError('unexpected external symbols '+repr(external))
report=dict(scope='Current seven-object controller sidecar target compile and symbol closure only',versions=versions,objects=objects,remaining_external_symbols=sorted(external),hash_checks_performed=False,target_linked=False,target_executed=False,firmware_built=False,native_adapter_installed=False)
print(json.dumps(report,indent=2))
