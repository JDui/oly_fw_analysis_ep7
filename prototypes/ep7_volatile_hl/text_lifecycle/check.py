#!/usr/bin/env python3
"""Compile-only lifecycle scaffold and host mocks; never execute target object."""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def run(a,**kw):return subprocess.check_output([str(x) for x in a],text=True,**kw)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(t):
 manifest=json.loads((ROOT/"prototypes/ep7_volatile_hl/target/build-manifest.json").read_text())
 for name,h in manifest["tools"].items():
  if digest(ROOT/name)!=h:raise ValueError("trusted tool hash")
 flags=['-std=c11','-Wall','-Wextra','-Werror','-pedantic']
 host=t/'test-host'
 run(['cc',*flags,'-fsanitize=address,undefined','-fno-sanitize-recover=all',HERE/'lifecycle.c',HERE/'test_lifecycle.c','-o',host])
 run([host],env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'})
 gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc'
 gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new'
 nm=ROOT/'toolchains/binutils-2.45-build/binutils/nm-new'
 targetflags=['-mno-setlb','-mno-liw','-ffreestanding','-fno-builtin','-nostdinc']
 run([gcc/'xgcc',f'-B{gcc}/',*flags,*targetflags,f'-I{ROOT}/prototypes/ep7_volatile_hl/target/include',f'-I{gcc}/include','-S',HERE/'lifecycle.c','-o',t/'lifecycle.s'])
 run([gas,'-o',t/'lifecycle.o',t/'lifecycle.s'])
 und=run([nm,'-u',t/'lifecycle.o']).strip()
 if und:raise ValueError('unexpected undefined symbols:'+und)
 return dict(scope='Normalized lifecycle callbacks, not native bindings',host_mock_scenarios=7,host_asan_ubsan_passed=True,leak_sanitizer_enabled=False,target_executed=False,target_flags=targetflags,undefined_symbols=[],sources={p.name:digest(p) for p in [HERE/'lifecycle.h',HERE/'lifecycle.c',HERE/'test_lifecycle.c',HERE/'CONTRACT.md',HERE/'check.py']},tools={str(p.relative_to(ROOT)):digest(p) for p in [gcc/'xgcc',gas,nm]},object_sha256=digest(t/'lifecycle.o'),native_resource_provider_qualified=False,native_unattached_destroy_binding_qualified=False,flash_ready=False)
def main():
 with tempfile.TemporaryDirectory(prefix='ep7-text-lifecycle-') as temp:
  return check(Path(temp))
if __name__=='__main__':print(json.dumps(main(),indent=2))
