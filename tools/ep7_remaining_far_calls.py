#!/usr/bin/env python3
"""Qualify the remaining UI/CPU short-call veneers against current decoded bytes and real cohorts."""
import argparse
import json
import os
import re
import runpy
import subprocess
import tempfile
from pathlib import Path

from ep7_far_call_check import ROOT,validate_object

CORE=ROOT/'prototypes/ep7_volatile_hl'
GROUPS={
    'mvc':dict(folder='ui_mvc',target='ep7_native_content_rebuild_bridge',mask=0xf0,frame=28,
        original=0x60e266a9,prefix='ep7_stock_mvc_rebuild_',call='rebuild_call',
        sites=[('initial',0x60e261d4),('previous',0x60e26201),('next',0x60e26226),('touch',0x60e269f0)]),
    'input':dict(folder='ui_native',target='ep7_native_ui_wheel_sample_bridge',mask=0,frame=0,
        original=0x60ea3b2c,prefix='ep7_stock_ui_wheel_',call='sample_call',
        sites=[('1',0x60ea0070),('0',0x60ea00f7),('2',0x60ea0d70),('4',0x60ea0deb),('3',0x60ea0e66)]),
    'postbuilder':dict(folder='target/postbuilder',target='ep7_native_postbuilder_bridge',mask=0xf0,frame=96,
        original=0x603b0068,sites=[('color',0x603b02d9)])}


def group_rows(group):
    spec=GROUPS[group]
    expected=[(pc,spec['target'],spec['mask'],spec['frame']) for _,pc in spec['sites']]
    source=(CORE/spec['folder']/'far_calls.s').read_text()
    rows=re.findall(r'^EP7_FAR_CALL ep7_'+group+r'_far_([0-9a-f]+),(\w+),(0x[0-9a-f]+),(0x[0-9a-f]+),(\d+)$',source,re.M)
    actual=[]
    for pc,target,resume,mask,frame in rows:
        if int(resume,16)!=int(pc,16)+5:raise ValueError('incorrect original resume in '+group)
        actual.append((int(pc,16),target,int(mask,0),int(frame)))
    if actual!=expected:raise ValueError('veneer rows differ from reviewed '+group+' sites')
    cohort=(CORE/spec['folder']/'cohort.c').read_text()
    if group!='postbuilder':
        refs=re.findall(spec['call']+r'\('+spec['prefix']+r'(\w+)_call_unresolved,(\d+)\)',cohort)
        if refs!=[(name,str(i)) for i,(name,_) in enumerate(spec['sites'])]:
            raise ValueError('cohort order differs from '+group+' veneer order')
    elif 'UINT32_C(0x603b02d9)' not in cohort:
        raise ValueError('postbuilder cohort site changed')
    return expected


def validate_group_object(obj,prefix,group):
    return validate_object(obj,prefix,group_rows(group),'.text.ep7_'+group+'_far_calls')


def stock_sites(decoded):
    main=decoded.read_bytes();base=0x60020020
    if len(main)!=26214336:raise ValueError('unsupported decoded main length')
    checked=[]
    for group,spec in GROUPS.items():
        for pc,_,mask,frame in group_rows(group):
            expected=b'\xcd'+(spec['original']-pc).to_bytes(2,'little',signed=True)+bytes([mask,frame])
            if main[pc-base:pc-base+5]!=expected:raise ValueError('original five-byte CALL differs at '+hex(pc))
            checked.append(dict(group=group,site=hex(pc),original=hex(spec['original']),
                                original_resume=hex(pc+5),mask=hex(mask),frame=frame))
    return checked


def host_checks():
    capture=runpy.run_path(str(CORE/'controller_sidecar/check_native.py'))['SOURCES']
    ui=[p for p in runpy.run_path(str(CORE/'ui_render/check.py'))['SOURCES'] if p!='ui_render/test_viewer.c']
    ui+=['target/test_far_cohorts.c','target/postbuilder/cohort.c','ui_native/bridge.c',
         'ui_native/input.c','ui_native/cohort.c','ep7p_ui_raw.c']
    result={}
    with tempfile.TemporaryDirectory(prefix='ep7-far-cohorts-') as temp:
        for mode,extra in [('strict',[]),('asan_ubsan',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            for group,sources,args in [('capture',capture,['cohort']),('ui_cpu',ui,[])]:
                exe=Path(temp)/(group+'-'+mode)
                subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
                    '-DEP7CN_HOST_FIXTURE','-fno-pie','-no-pie',*extra,'-I'+str(CORE),
                    *[str(CORE/p) for p in sources],'-o',str(exe)],check=True,timeout=60)
                subprocess.run([str(exe),*args],check=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
                result[group+'_'+mode]=dict(passed=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded',type=Path,required=True)
    args=parser.parse_args()
    rows=stock_sites(args.decoded)
    print(json.dumps(dict(scope=__doc__,decoded_bytes=args.decoded.stat().st_size,
        original_short_calls_checked=rows,host_checks=host_checks(),
        capture_39_sites_and_reject_before_node_read_checked=True,
        ui_9_sites_resume_and_crosswired_veneer_rejected=True,
        cpu_color_site_resume_mdr_and_target_rejected=True,
        whole_lifecycle_suites_rerun=False,fixture_machine_code_executed=False,
        container_identity_rechecked=False,firmware_modified=False,firmware_built=False,
        camera_executed=False,hash_checks_performed=False),indent=2))
