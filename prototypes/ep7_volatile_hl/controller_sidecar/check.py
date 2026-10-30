#!/usr/bin/env python3
"""Self-authored host tests and target symbol closure; never link/execute target."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile,os,importlib.util
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];CORE=ROOT/'prototypes/ep7_volatile_hl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def check_host(cc='cc',sanitize=False):
 """Run the existing C fixture without firmware, target tools or hashing."""
 host=[]
 with tempfile.TemporaryDirectory(prefix='ep7-sidecar-host-') as td:
  configurations=[('strict',[])]
  if sanitize:
   configurations.append(('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']))
  for name,opts in configurations:
   exe=Path(td)/(name+('.exe' if os.name=='nt' else ''))
   subprocess.run([cc,'-std=c11','-Wall','-Wextra','-Werror','-pedantic',*opts,'-I'+str(CORE),str(HERE/'sidecar.c'),str(HERE/'transition_binding.c'),str(HERE/'test_sidecar.c'),str(CORE/'ep7p.c'),str(CORE/'ep7p_decode.c'),'-o',str(exe)],check=True)
   subprocess.run([str(exe)],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
   host.append(name)
 return dict(host_tests=host,passed=True,compiler_version=subprocess.check_output([cc,'--version'],text=True).splitlines()[0],
  scope='Controller sidecar host fixture including current-live node/token resolution',
  hash_checks_performed=False,native_lifetime_proven=False,native_free_coverage_proven=False,
  target_compiled=False,target_executed=False,firmware_modified=False,camera_accessed=False,flash_ready=False)
def check():
 manifest=json.loads((CORE/'target/build-manifest.json').read_text())
 for n,d in manifest['tools'].items():
  if sha(ROOT/n)!=d:raise ValueError('tool hash mismatch')
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc';gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new';od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
 files={'sidecar':HERE/'sidecar.c','transition':HERE/'transition_binding.c','observer':CORE/'capture_state_guard/observer.c','bridge':CORE/'capture_state_guard/bridge.s','core':CORE/'ep7p.c','decode':CORE/'ep7p_decode.c','memory':CORE/'target/memory.c'}
 # The already reviewed freestanding memory implementation lives under runtime.
 if not files['memory'].exists():files['memory']=CORE/'target/freestanding_memory.c'
 if not files['memory'].exists():files['memory']=CORE/'target/runtime/memory.c'
 host=check_host(sanitize=True)['host_tests'];objects={};definitions={};undefined=set()
 with tempfile.TemporaryDirectory(prefix='ep7-controller-sidecar-') as td:
  td=Path(td)
  flags=['-B'+str(gcc.parent)+'/','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-mno-setlb','-mno-liw','-nostdinc','-I'+str(CORE/'target/include'),'-I'+str(gcc.parent/'include'),'-I'+str(CORE)]
  for name,src in files.items():
   asm=src;obj=td/(name+'.o')
   if src.suffix=='.c':
    asm=td/(name+'.s');subprocess.run([str(gcc),*flags,'-S',str(src),'-o',str(asm)],check=True)
   subprocess.run([str(gas),'-o',str(obj),str(asm)],check=True)
   syms=subprocess.check_output([str(od),'-t',str(obj)],text=True);defs=set();und=set()
   for line in syms.splitlines():
    bits=line.split()
    if '*UND*' in bits:und.add(bits[-1])
    elif len(bits)>4 and bits[1]=='g':defs.add(bits[-1])
   for symbol in defs:
    if symbol in definitions:raise ValueError('duplicate global '+symbol)
    definitions[symbol]=name
   undefined|=und
   objects[name]=dict(source=str(src.relative_to(ROOT)),source_sha256=sha(src),object_sha256=sha(obj),definitions=sorted(defs),undefined=sorted(und))
 external=undefined-set(definitions)
 if external!={'_ep7_controller_sidecar_unresolved','ep7_stock_state_service_unresolved'}:raise ValueError('unexpected externals '+repr(external))
 return dict(host_tests=host,objects=objects,remaining_external_symbols=sorted(external),sources={n:sha(HERE/n) for n in ['sidecar.h','sidecar.c','transition_binding.c','test_sidecar.c','check.py','README.md']},tool_hashes=manifest['tools'],transition_callback_defined=True,controller_runtime_initialized=False,serialized_controller_required=True,native_prefix_dereferenced=False,native_free_coverage_proven=False,target_linked=False,target_executed=False,firmware_modified=False)
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--host-only',action='store_true',help='No target toolchain, firmware or hash checks')
 parser.add_argument('--cc',default='cc',help='Host C11 compiler (host-only mode)')
 parser.add_argument('--sanitize',action='store_true',help='Also run ASan/UBSan (host-only mode)')
 args=parser.parse_args()
 if not args.host_only and (args.cc!='cc' or args.sanitize):
  parser.error('--cc and --sanitize require --host-only')
 print(json.dumps(check_host(args.cc,args.sanitize) if args.host_only else check(),indent=2))
