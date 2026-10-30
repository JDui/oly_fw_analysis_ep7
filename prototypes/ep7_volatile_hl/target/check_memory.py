#!/usr/bin/env python3
"""Execute only self-authored HOST tests; compile target object without execution."""
import hashlib,json,re,subprocess,tempfile,os
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
    manifest=json.loads((HERE/'build-manifest.json').read_text())
    for name,expected in manifest['tools'].items():
        if digest(ROOT/name)!=expected:raise ValueError('trusted tool hash mismatch: '+name)
    flags=['-std=c11','-O2','-Wall','-Wextra','-Werror','-pedantic','-fno-builtin','-fno-tree-loop-distribute-patterns']
    gcc=ROOT/'toolchains/gcc-13.4.0-mn10300-build/gcc/xgcc'
    gas=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new'
    od=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
    tests=[]
    with tempfile.TemporaryDirectory(prefix='ep7-memory-') as temp:
        for sanitize in (False,True):
            exe=Path(temp)/('host-sanitized' if sanitize else 'host')
            extra=['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer'] if sanitize else []
            subprocess.run(['cc',*flags,'-Dmemcpy=ep7_test_memcpy','-Dmemset=ep7_test_memset',*extra,str(HERE/'memory.c'),str(HERE/'test_memory.c'),'-o',str(exe)],check=True)
            environment=os.environ.copy()
            if sanitize:environment['ASAN_OPTIONS']='detect_leaks=0'
            result=subprocess.check_output([str(exe)],text=True,env=environment).strip()
            tests.append(dict(sanitized=sanitize,result=result))
        asm=Path(temp)/'memory.s';obj=Path(temp)/'memory.o'
        subprocess.run([str(gcc),'-B'+str(gcc.parent)+'/',*flags,'-ffreestanding','-S',str(HERE/'memory.c'),'-o',str(asm)],check=True)
        subprocess.run([str(gas),'-o',str(obj),str(asm)],check=True)
        symbols=subprocess.check_output([str(od),'-t',str(obj)],text=True)
        disassembly=subprocess.check_output([str(od),'-dr',str(obj)],text=True)
        if '*UND*' in symbols:raise ValueError('unresolved target symbol')
        for name in ('_memcpy','_memset'):
            if name not in symbols:raise ValueError('missing target definition: '+name)
        if re.search(r'\b(?:call|calls|jsr)\b',asm.read_text()):raise ValueError('unexpected target call/recursion')
        if 'elf32-mn10300' not in disassembly:raise ValueError('wrong target format')
        return dict(source_sha256=digest(HERE/'memory.c'),test_sha256=digest(HERE/'test_memory.c'),flags=flags,
                    tool_hashes=manifest['tools'],host_tests=tests,target_object_sha256=digest(obj),
                    target_undefined_symbols=[],target_call_instructions=0,target_linked=False,
                    target_executed=False,firmware_input_used=False,native_ABI_qualified=False,leak_sanitizer_enabled=False)
if __name__=='__main__':print(json.dumps(check(),indent=2))
