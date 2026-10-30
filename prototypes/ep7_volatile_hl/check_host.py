#!/usr/bin/env python3
"""Compile and execute only this self-authored HOST prototype, never firmware."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent

def check(cc, sanitize=False):
    compiler = shutil.which(str(cc))
    if not compiler:
        raise ValueError('a trusted host C11 compiler must be supplied')
    flags = ['-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic']
    cases = [('core', ['ep7p.c', 'test_ep7p.c']),
             ('normalized_ui_to_output', ['ep7p.c', 'ep7p_ui.c', 'test_ui_integration.c'])]
    results = []
    with tempfile.TemporaryDirectory(prefix='ep7-host-prototype-') as temporary:
        for kind in (['strict', 'asan_ubsan'] if sanitize else ['strict']):
            extra = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer'] if kind != 'strict' else []
            for name, sources in cases:
                binary = Path(temporary) / (name + '-' + kind)
                subprocess.run([compiler, *flags, *extra,
                    *(str(HERE / source) for source in sources), '-o', str(binary)], check=True)
                environment = os.environ.copy()
                if kind != 'strict':
                    environment['ASAN_OPTIONS'] = 'detect_leaks=0'
                output = subprocess.check_output([str(binary)], text=True, env=environment)
                results.append(dict(test=name, configuration=kind, passed=True, output=output.strip()))
        subprocess.run([compiler, *flags, '-fsyntax-only', str(HERE/'test_ui_contract.c')], check=True)
    return dict(
        scope='Self-authored host integration only; native adapters remain unbound',
        compiler_version=subprocess.check_output([compiler, '--version'], text=True).splitlines()[0],
        compiler_sha256=hashlib.sha256(Path(compiler).read_bytes()).hexdigest(),
        sources={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(HERE.iterdir()) if p.suffix in ('.c', '.h')},
        tests=results, ui_header_syntax_passed=True,
        asan_ubsan_requested=sanitize, sanitizer_recovery_enabled=False, leak_sanitizer_enabled=False,
        actual_multithread_stress_tested=False, host_prototype_executed=True,
        firmware_executed=False, native_adapter_installed=False,
        camera_accessed=False, pixel_calibration_verified=False, flash_ready=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc', default='cc')
    parser.add_argument('--sanitize', action='store_true')
    args = parser.parse_args()
    print(json.dumps(check(args.cc, args.sanitize), indent=2))
