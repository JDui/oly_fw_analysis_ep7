#!/usr/bin/env python3
"""Build the existing strict GNU runner from explicit local inputs, without SHA checks.

Run in the research Linux container with a private writable work directory.
This is a separate provenance mode; the original pinned PEN-F builders and
their hash gates are not called or modified. No network or firmware input.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

from build_mn103_emulator import CONFIGURE, REVISION

ROOT=Path(__file__).resolve().parents[1]
REFERENCE_FILES=('interp.c','mn10300.igen')
ARCHIVE_ROOT='sourceware-mirror-binutils-gdb-'+REVISION


def run(command,log,cwd):
    print('Running: '+' '.join(map(str,command)),flush=True)
    with log.open('w') as stream:
        result=subprocess.run(command,cwd=cwd,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:
        lines=log.read_text(errors='replace').splitlines()
        failures=[i for i,line in enumerate(lines) if 'error:' in line or '***' in line]
        selected=set(range(max(0,len(lines)-15),len(lines)))
        for i in failures[:6]:selected.update(range(max(0,i-2),min(len(lines),i+3)))
        print('\n'.join(lines[i] for i in sorted(selected)),flush=True)
        raise RuntimeError('command failed; see '+str(log))


def prepare(archive,reference_dir,work,unsigned_multiply_fix=False):
    source=work/ARCHIVE_ROOT
    marker=source/'.ep7-source.json'
    originals={name:(reference_dir/name).read_bytes() for name in REFERENCE_FILES}
    if not marker.is_file():
        if source.exists():
            raise ValueError('unrecorded source directory exists; inspect it before retrying')
        with tarfile.open(archive,'r:gz') as bundle:
            members=bundle.getmembers()
            if not members or any(Path(m.name).is_absolute() or '..' in Path(m.name).parts or
                    Path(m.name).parts[0]!=ARCHIVE_ROOT for m in members):
                raise ValueError('unexpected source archive root/path')
            for name,expected in originals.items():
                stream=bundle.extractfile(ARCHIVE_ROOT+'/sim/mn10300/'+name)
                if stream is None or stream.read()!=expected:
                    raise ValueError('archive differs from separately retrieved source '+name)
            version=bundle.extractfile(ARCHIVE_ROOT+'/bfd/version.h').read()
            if b'#define BFD_VERSION_DATE 20260923' not in version:
                raise ValueError('unexpected upstream version date')
            bundle.getmember(ARCHIVE_ROOT+'/libctf/swap.h')
            bundle.getmember(ARCHIVE_ROOT+'/gdb/version.in')
            # The existing Debian Python predates tarfile's data filter. Only
            # ordinary files/directories are needed; reject links and devices
            # before extraction rather than follow an archive-controlled path.
            if any(not (m.isfile() or m.isdir()) for m in members):
                raise ValueError('source archive contains links or special files')
            bundle.extractall(work)
        marker.write_text(json.dumps(dict(revision=REVISION,archive_name=archive.name,
            archive_bytes=archive.stat().st_size,archive_members=len(members),
            reference_byte_comparisons=list(REFERENCE_FILES),hash_checks_performed=False),indent=2)+'\n')
    record=json.loads(marker.read_text())
    if record.get('revision')!=REVISION or record.get('hash_checks_performed') is not False:
        raise ValueError('unexpected source provenance mode')

    # Produce expected files by applying the existing patch to the separately
    # retrieved originals. Accept only those originals or that exact result.
    # This also rejects stale/foreign modifications on an incremental build.
    patch=(ROOT/'tools/mn103_strict.patch').read_text()
    with tempfile.TemporaryDirectory(prefix='ep7-strict-patch-') as temp:
        stage=Path(temp);native=stage/'sim/mn10300';native.mkdir(parents=True)
        for name,data in originals.items():(native/name).write_bytes(data)
        result=subprocess.run(['patch','--batch','--fuzz=0','-p1'],input=patch,
            text=True,cwd=stage,capture_output=True)
        if result.returncode or 'offset' in result.stdout.lower():
            raise ValueError('strict patch does not apply exactly: '+result.stdout+result.stderr)
        baseline={name:(native/name).read_bytes() for name in REFERENCE_FILES}
        patch_log=result.stdout
        if unsigned_multiply_fix:
            correction=(ROOT/'tools/mn103_mulqu_unsigned.patch').read_text()
            result=subprocess.run(['patch','--batch','--fuzz=0','-p1'],input=correction,
                text=True,cwd=stage,capture_output=True)
            if result.returncode or 'offset' in result.stdout.lower():
                raise ValueError('unsigned multiply patch does not apply exactly: '+result.stdout+result.stderr)
            patch_log+=result.stdout
        for name,original in originals.items():
            target=source/'sim/mn10300'/name;expected=(native/name).read_bytes()
            current=target.read_bytes()
            if current not in (original,baseline[name],expected):
                raise ValueError('refusing unexpected local simulator change: '+str(target))
            if current!=expected:target.write_bytes(expected)
    (work/'strict-patch-applied.txt').write_text(patch_log)
    return source,record


def build(args):
    work=args.work.resolve()
    if work==Path('/') or work==ROOT or work in ROOT.parents:
        raise ValueError('use a dedicated research work directory')
    if not 1<=args.jobs<=8:raise ValueError('jobs must be between 1 and 8')
    work.mkdir(parents=True,exist_ok=True)
    source,record=prepare(args.archive,args.reference_dir,work,args.unsigned_multiply_fix)
    output=work/'build';output.mkdir(exist_ok=True)
    configure=list(CONFIGURE)
    if args.mpfr_include or args.mpfr_lib:
        if not args.mpfr_include or not args.mpfr_lib:
            raise ValueError('both existing MPFR include and library paths are required')
        configure += ['--with-mpfr-include='+str(args.mpfr_include),
                      '--with-mpfr-lib='+str(args.mpfr_lib)]
    settings=output/'ep7-configure.json'
    if (output/'Makefile').is_file():
        if not settings.is_file() or json.loads(settings.read_text())!=configure:
            raise ValueError('existing build has different/unrecorded configuration')
    else:
        run([str(source/'configure'),*configure],output/'configure.log',output)
        settings.write_text(json.dumps(configure,indent=2)+'\n')
    suffix='-mulqu' if args.unsigned_multiply_fix else ''
    executable='ep7-mn103'+suffix
    run(['make','-j'+str(args.jobs),'all-sim','MAKEINFO=true'],output/('build'+suffix+'.log'),output)
    # The wrapper stays unchanged; the optional model correction is isolated
    # in its separately reviewed patch and does not add camera addresses.
    runner=output/'ep7_runner.c'
    original_runner=(ROOT/'tools/mn103_runner.c').read_text()
    if not runner.is_file() or runner.read_text()!=original_runner:runner.write_text(original_runner)
    makefile=output/('sim/ep7-harness'+suffix+'.mk')
    makefile.write_text('''mn10300/ep7_runner.o: ../ep7_runner.c
\t$(COMPILE) -c -o $@ $<

../ep7-mn103: mn10300/ep7_runner.o mn10300/libsim.a $(SIM_COMMON_LIBS)
\t$(LINK) mn10300/ep7_runner.o mn10300/libsim.a $(SIM_COMMON_LIBS) $(LIBS)
'''.replace('../ep7-mn103:', '../'+executable+':'))
    run(['make','-f','Makefile','-f',makefile.name,'../'+executable,'V=1'],
        output/('harness-build'+suffix+'.log'),output/'sim')
    result=dict(scope=__doc__,source=record,configure=configure,
        strict_patch='tools/mn103_strict.patch',wrapper='tools/mn103_runner.c',
        executable=str(output/executable),executable_bytes=(output/executable).stat().st_size,
        unsigned_multiply_patch='tools/mn103_mulqu_unsigned.patch' if args.unsigned_multiply_fix else None,
        compiler=subprocess.check_output(['cc','--version'],text=True).splitlines()[0],
        hash_checks_performed=False,old_hash_gates_modified=False,
        firmware_built=False,firmware_executed=False,camera_accessed=False,
        limits=['Archive identity is recorded by HTTPS source/revision and two complete file comparisons, not a cryptographic archive identity claim.',
                'The existing MAC extension is a manufacturer-based model with deterministic undefined flags, not E-P7 silicon validation.',
                'The optional MULQIU fix changes immediate extension only; general CPU and delayed flag timing remain outside this acceptance.',
                'Building the strict engine is not firmware construction or a boot/placement acceptance test.'])
    (output/('ep7-build'+suffix+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--reference-dir',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--jobs',type=int,default=4)
    p.add_argument('--mpfr-include',type=Path)
    p.add_argument('--mpfr-lib',type=Path)
    p.add_argument('--unsigned-multiply-fix',action='store_true',
                   help='apply the manufacturer zero-extension correction; preserve the old executable')
    build(p.parse_args())
