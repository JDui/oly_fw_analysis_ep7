#!/usr/bin/env python3
"""Compile-only contract check; does not link or execute MN10300 code."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
AS=ROOT/'toolchains/binutils-2.45-gas-build/gas/as-new'
OD=ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
expected=['get_tid','constructor','process','cleanup']
assert hashlib.sha256(AS.read_bytes()).hexdigest()=='5833fa140051525c4d432be6a931abc32e6b866f2a7152f16c1751a5f3122d6c'
with tempfile.TemporaryDirectory(prefix='ep7-compile-only-') as temp:
 obj=Path(temp)/'forwarders.o'
 subprocess.run([str(AS),'-o',str(obj),str(HERE/'native_forwarders.s')],check=True)
 dis=subprocess.check_output([str(OD),'-dr',str(obj)],text=True)
 assert 'elf32-mn10300' in dis
 assert dis.count('R_MN10300_PCREL32')==4
 for name in expected:
  assert f'ep7_stock_{name}_unresolved+0x1' in dis
 instructions=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+([a-z][a-z0-9]*)\s',dis,re.M)
 assert instructions==['jmp']*4, instructions
 sections=subprocess.check_output([str(OD),'-h',str(obj)],text=True)
 assert re.search(r'^\s*\d+\s+\.text\s+00000014\s',sections,re.M)
 assert '\tcall\t' not in dis
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-pedantic','-x','c','-fsyntax-only',str(HERE/'native_boundary_contract.h')],check=True)
 report=dict(assembler_sha256=hashlib.sha256(AS.read_bytes()).hexdigest(),
             source_sha256=hashlib.sha256((HERE/'native_forwarders.s').read_bytes()).hexdigest(),
             header_sha256=hashlib.sha256((HERE/'native_boundary_contract.h').read_bytes()).hexdigest(),
             objdump_sha256=hashlib.sha256(OD.read_bytes()).hexdigest(),
             object_sha256=hashlib.sha256(obj.read_bytes()).hexdigest(),
             relocations_unresolved=4,exact_tail_jump_count=4,text_bytes=20,header_syntax_passed=True,assembled=True,
             linked=False,executed=False,installed=False,native_C_ABI_qualified=False)
 print(json.dumps(report,indent=2))
