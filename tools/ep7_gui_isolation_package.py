#!/usr/bin/env python3
"""Create 007D by restoring the complete GUI patch group in the compiled 006 image.

This is a one-variable startup diagnostic, not a black-screen fix or H/L release.
Reuses fishcu's container format and the existing native bootstrap probe. No SHA.
"""
import argparse
import json
from pathlib import Path
import zipfile

from ep7_candidate_package import check_candidate, check_components
from ep7_candidate_startup_sim import require, CALLER
from ep7_candidate_static_kernel_sim import inspect as static_kernel
from ep7_candidate_state_sim import SNAPSHOT, guarded, gcc_call
from ep7_offline_candidate import BASE, ELF_NAME, symbols
from ep7_sim_probe import brief
from oly_container import parse, reconstruct, replace_payload


# Exactly the complete section6 group in 006: input/preprocess/dispatch, content,
# screen owner, selector, MVC entry/exit and parent/viewer virtual methods.
GUI_SITES = (
    0x60cfd53a,0x60cfd558,0x60e261d4,0x60e26201,0x60e26226,0x60e269f0,
    0x60ea0070,0x60ea00f7,0x60ea0d70,0x60ea0deb,0x60ea0e66,
    0x60faadc4,0x61032f10,0x61032fa8,0x610330c0,0x6114f334,
    0x6118957c,0x611895a4,0x61189ba8,0x61189bac,0x611a3b50,0x611a3bc4,
)
GUI_LOW, GUI_HIGH = 0x60ba7000, 0x61243000


def isolate(original, candidate, build):
    require(build['source_revision'].startswith('a059e5f') and len(build['patches'])==98,
            '007D must derive from the delivered final 006 source')
    rows = [p for p in build['patches'] if p['load_stage']=='section6']
    require({int(p['site'],16) for p in rows}==set(GUI_SITES) and len(rows)==22,
            '006 GUI patch inventory changed')
    data = bytearray(candidate)
    for row in rows:
        start, size = int(row['site'],16)-BASE, row['bytes']
        require(candidate[start:start+size]!=original[start:start+size], 'GUI site is already stock')
        data[start:start+size] = original[start:start+size]
    data = bytes(data)
    low, high = GUI_LOW-BASE, GUI_HIGH-BASE
    require(data[low:high]==original[low:high], 'GUI section is not wholly stock')
    require(data[:low]==candidate[:low] and data[high:]==candidate[high:],
            'non-GUI bytes changed during isolation')
    require(data[:0x60030000-BASE]==original[:0x60030000-BASE], 'boot prefix changed')
    return data, rows


def verify_startup(data, build, candidate_dir, prefix, engine):
    addresses = {k:v['address'] for k,v in symbols(prefix,candidate_dir/ELF_NAME).items()}
    machine, syms, _, setup = static_kernel(None,None,engine,context_only=True,
        candidate_override=(data,addresses,build))
    checks = []
    for name in ('_ep7i_native_cohort_present','_ep7m_native_cohort_present','_ep7u_native_cohort_present'):
        row = machine.call(syms[name])
        require(row['status']=='returned' and row['registers']['pc']==CALLER+7 and
                row['registers']['d0']==0, 'disabled GUI cohort unexpectedly accepted')
        checks.append(dict(symbol=name,**brief(row),returned_d0=0))
    guarded(machine,'isolation_snapshot',SNAPSHOT,b'\xcc'*25)
    frozen = gcc_call(machine,syms,'_ep7p_capture',[setup['core'],11,4,SNAPSHOT],wanted=1)
    require(machine.read(SNAPSHOT,25)==b'\x03'+bytes(24), 'default H/L is not neutral')
    return dict(status='passed',native_static_semaphores=132,private_semaphore_id=setup['private_id'],
        native_initialization=setup['initialization'],native_create=setup['native_create'],
        published=setup['published'],disabled_GUI_cohorts=checks,
        neutral_COLOR4_snapshot='03'+'00'*24,freeze=brief(frozen),
        hardware_executed=False,full_boot_executed=False,hash_checks_performed=False,
        limits=[
            'Native semaphore creation/publication and neutral capture execute against the exact 007D bytes.',
            'Current task, ready lists, queue objects/backing identities and uncontended shared lock remain explicit fixtures.',
            'Whole camera startup, physical cache/multicore behavior, display and photo output are not simulated.',
            'Original GUI section is restored as bytes; its full construction/scheduling is not executed.'])


def package(stock_path, decoded_path, candidate_dir, prefix, engine, output):
    require(not output.exists(), 'output already exists; preserve previous artifacts')
    destination = output.resolve()
    for source in (stock_path.resolve(), decoded_path.resolve(), candidate_dir.resolve()):
        require(destination!=source and source not in destination.parents and
                destination not in source.parents, 'output overlaps source')
    original = decoded_path.read_bytes()
    candidate, build, _ = check_candidate(decoded_path,candidate_dir,prefix)
    data, reverted = isolate(original,candidate,build)
    startup = verify_startup(data,build,candidate_dir,prefix,engine)
    raw = stock_path.read_bytes()
    blocks = parse(raw)
    check_components(blocks)
    require(len(raw)==111017984 and blocks[0].payload==original,
            'stock source does not match decoded main')
    packed = reconstruct([replace_payload(blocks[0],data),*blocks[1:]])
    checked = parse(packed)  # Native additive sums; never SHA.
    check_components(checked)
    require(len(packed)==len(raw) and checked[0].payload==data,
            'container main/size differs')
    require(packed[blocks[1].offset:]==raw[blocks[1].offset:], 'unchanged components differ')
    require(all(a.header==b.header and a.trailer[:28]==b.trailer[:28]
                for a,b in zip(blocks,checked)), 'component metadata differs')

    guide = '''# EP7HSL 007D：原厂GUI启动隔离包

仅用于定位005/006黑屏，不是修复版。复用006已编译代码，恢复全部22处GUI补丁；
启动、内核队列、capture及worker改动保持006字节。H/L编辑入口没有启用，易失H/L
初值为零；此包不能用于验收H/L编辑和照片处理。

每次只复制一个来源的DCOLYMP文件夹到卡根目录：
- install/DCOLYMP/E1429999.BIN：007D诊断固件。
- restore-stock/DCOLYMP/E1429999.BIN：原厂1.1；与官方输入逐字节相同。

沿用此前成功的SD流程：充满电、关机插卡，按住OK开机，更新指示开始后松开。
常亮期间保持供电；明确转为完成快闪后拨OFF。完成快闪可持续，不用等它自行停止。
关机后取出更新卡，不按OK正常开机。005/006不要重新安装。

只做一次启动观察，优先保持此前A档、前拨杆COLOR：
1. 是否出现稳定画面，菜单/回放是否响应。
2. 蓝牙图标是否只出现一次，AF灯状态，以及画面是否持续变化。
3. 若正常，打开菜单和回放各一次即可；本次不验收H/L、不要求拍摄。

若007D能启动，GUI改动或其与其余改动的交互成为重点；这不直接定位某一个函数。
若仍黑屏，说明恢复GUI这一组不足以修复，下一步检查保留的启动/内核/拍摄组。
失败后按此前成功路线回刷restore-stock；不重复刷同一诊断包。

验证只覆盖差分闭合、真实候选启动片段/私有锁/零值冻结及fishcu五组件封装。
没有完整原生mode2重验、物理flash读回、完整GUI、缓存/多核或独立恢复保证。
本次实验镜像尚未通过机身启动验收。相机实际操作由用户决定。
'''
    manifest = dict(kind='startup_diagnostic_not_HL_release',diagnostic_id='007D',
        source_candidate='006-r2',compiled_source_revision=build['source_revision'],
        existing_compiled_code_reused=True,new_compilation_performed=False,
        gui_patch_sites_restored=len(reverted),restored_GUI_patch_spans=reverted,
        retained_patch_sites=98-len(reverted),entire_GUI_section_equals_stock=True,
        all_bytes_outside_GUI_section_equal_006=True,boot_prefix_unchanged=True,
        private_state_initialization_unchanged=True,HL_editor_enabled=False,
        black_screen_root_cause_confirmed=False,black_screen_fixed=False,
        package_bytes=len(packed),component_count=5,all_native_additive_checksums_valid=True,
        component_metadata_preserved=True,other_four_encoded_components_unchanged=True,
        restore_equals_official_input=True,hash_checks_performed=False,
        native_full_decode_and_checksum_passed=False,physical_flash_performed=False,
        full_device_boot_verified=False,independent_recovery_proven=False,
        workflow='fishcu oly_container.parse -> replace_payload -> reconstruct',
        startup_validation=startup)
    output.mkdir(parents=True)
    for name, payload in (('install',packed),('restore-stock',raw)):
        path=output/name/'DCOLYMP'/'E1429999.BIN'
        path.parent.mkdir(parents=True)
        path.write_bytes(payload)
        require(path.read_bytes()==payload,'disk readback differs: '+name)
    (output/'007D.decoded-main.bin').write_bytes(data)
    (output/'READ-ME-FIRST.md').write_text(guide,encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    archive=output.parent/(output.name+'-SD.zip')
    require(not archive.exists(),'ZIP already exists')
    members=[p for p in output.rglob('*') if p.is_file() and p.name!='007D.decoded-main.bin']
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in members:z.write(path,path.relative_to(output))
    with zipfile.ZipFile(archive) as z:
        require(z.testzip() is None and len(z.infolist())==4,'ZIP CRC/member check failed')
        for path in members:
            require(z.read(path.relative_to(output).as_posix())==path.read_bytes(),'ZIP readback differs')
    return dict(manifest,zip_bytes=archive.stat().st_size,zip_members=4,zip_CRC_and_readback_passed=True,
                output=str(output),zip=str(archive))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True)
    p.add_argument('--decoded-stock',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--tool-prefix',required=True)
    p.add_argument('--engine',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(package(a.stock,a.decoded_stock,a.candidate,a.tool_prefix,a.engine,a.out),indent=2))
