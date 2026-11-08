#!/usr/bin/env python3
"""Actual installed 015 snapshot seams to immutable rendering-only RGB tables.

RAM owners, native job shapes and settings are fixture inputs. No exposure
calculator, sensor MMIO or ISP pixels are simulated by this focused replay.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import runpy
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from ep7_candidate_startup_sim import BASE, CALLER, Machine, Region, SP, STACK, require, returned
from ep7_highlight_gamma import gamma_table

GAMMA = runpy.run_path(str(Path(__file__).with_name('single-dr-gamma-target-probe.py')))
GAMMA['run_builder'].__globals__['gamma_table'] = gamma_table
ACTIVE, CAPTURE, CLONE, LIVE = 0x6250ba00, 0xaf6037c0, 0xaf900000, 0xa2731098


def inspect(directory, engine):
    report = json.loads((directory / 'report.json').read_text())
    require(report['strategy'] == 'highlight_mapping_only' and
            report['exposure_iso_gain_unchanged'], 'wrong strategy')
    image = (directory / report['image']).read_bytes()
    m = Machine(image, engine)
    sites = {row['target']: int(row['site'], 16) for row in report['patches'] if 'target' in row}
    syms = {key: int(row['address'], 16) for key, row in
            json.loads((directory / 'symbols.json').read_text()).items()}

    def add(name, address, data, alias=None):
        m.regions[name] = Region(name, address, data, 'rw', True, alias_of=alias)

    def write(name, offset, data):
        m.mutate(name, offset, data)
        for key, row in list(m.regions.items()):
            if row.alias_of == name:
                m.regions[key] = replace(row, data=m.regions[name].data)

    def word(name, offset, value):
        write(name, offset, struct.pack('<I', value))

    active = image[0x600b90cc-BASE:0x600b90cc-BASE+3560*4]
    add('active', ACTIVE, active)
    add('active_alias', ACTIVE+0x40000000, active, 'active')
    add('settings', 0x62253594, struct.pack('<I', ACTIVE))
    add('readonly_root', 0xa2711a88, struct.pack('<I', 0x60078e2c))
    add('ring', 0xa2715c8c, bytes(4))
    for address in (0x62257b04, 0x61fa7538):
        add(f'busy_{address:x}', address, bytes(4))
    # Real first entry returns with this latch still set (018 screen 0010).
    # Keep it set throughout capture, clone, preview and actual gamma replay.
    add('native_session_latch', 0x622484fa, b'\x01')
    add('capture', CAPTURE, bytes(41984))
    add('live', LIVE, bytes(5*980))
    add('context', GAMMA['CONTEXT'], bytes(200))
    add('cache', GAMMA['CACHE'], bytes(6000))
    add('outputs', GAMMA['OUTPUTS'], bytes(3*GAMMA['OUTPUT_STRIDE']))

    def level(property_id, value):
        word('active', 4*(1769+property_id), (0, 0x445201fe, 0x445202fd)[value])

    def installed(helper, d0, d1=0):
        site = sites[f'ep7dr_{helper}_bridge']
        result = m.run(site, site+7, overrides=dict(d0=d0, d1=d1), limit=10000)
        returned(result, site+7)
        require(result['registers']['sp'] == SP, '015 observer stack differs')
        return result['completed']

    def job(index, key, variant=0, live=False):
        GAMMA['job_fixture'](m, index, key, variant, 0)
        if live:
            word(f'job_{index}', 4, 0x60306ad5)
        return GAMMA['JOBS']+index*GAMMA['JOB_STRIDE']

    def check_level(index, value):
        address = GAMMA['JOBS']+index*GAMMA['JOB_STRIDE']+15512
        require(m.read(address, 4) == struct.pack('<I', value), 'owner snapshot lost')

    def render(index, key, pointer, value, reuse=False):
        m.regions['caller'] = Region('caller', CALLER, b'\xdd'+struct.pack('<i', GAMMA['BUILDER']-CALLER)+b'\xf0\x10', 'rx')
        return GAMMA['run_builder'](m, image, index, key, pointer, value, reuse=reuse)

    def helper(name, d0=0, d1=0, selector_status=1):
        target = syms[name]
        if name == '_ep7dr_gamma_apply':
            word('stack',SP-STACK+12,selector_status)
        m.regions['caller'] = Region('caller', CALLER,
            b'\xdd'+struct.pack('<i', target-CALLER)+bytes(2), 'rx')
        result = m.run(CALLER, CALLER+7, overrides=dict(d0=d0,d1=d1), limit=2000)
        returned(result, CALLER+7)
        return result['registers']['d0']

    def observed(path, expected):
        require(helper('_ep7dr_highlight_observation', path) == expected,
                f'path {path} pipeline observation differs from {expected:#x}')

    def upload(index, bank, expected_pointer, value, reuse=False):
        # Execute the original table copier against explicit RAM at its MMIO
        # address. The two OS mutex helpers are isolated service boundaries.
        # This proves CPU stores, not ISP activation or image pixels.
        uploader, service = 0x60346e37, 0x19700000
        bank_address = (0x9f00a400, 0x9f00d000)[bank]
        state = m.clone()
        state.regions['upload_bank'] = Region('upload_bank', bank_address,
                                              b'\xa5'*1024, 'rw', True)
        state.regions['upload_identity'] = Region('upload_identity', 0xa27360ec,
                                                  struct.pack('<2I',0x1234,0x1234),'rw',True)
        state.regions['mutex_returns'] = Region('mutex_returns', service,
                                                b'\xdf\xc0\x0c'+bytes(5)+b'\xdf\xa0\x0c','rx')
        state.mutate('context',56,struct.pack('<I',0x1234))
        state.mutate('context',196,struct.pack('<I',bank))
        state.mutate('outputs',index*GAMMA['OUTPUT_STRIDE']+4,struct.pack('<I',16))
        state.regions['caller'] = Region('caller',CALLER,
            b'\xdd'+struct.pack('<i',uploader-CALLER)+b'\xf0\x34','rx')
        services = {0x603b30e7: service, 0x603b3109: service+8}
        result = state.run(CALLER,CALLER+7,
            overrides=dict(a0=bank_address,a1=GAMMA['CONTEXT']),breakpoints=services,limit=5000)
        calls=[]
        while result['status'] == 'breakpoint':
            registers = result['registers']
            target = registers['pc']
            require(target in services and registers['d0']==4 and len(calls)<2,
                    'unexpected uploader service boundary')
            calls.append(target)
            result = state.resume(dict(registers,pc=services[target]),CALLER+7,
                                  breakpoints=services,limit=5000)
        returned(result,CALLER+7)
        require(calls==list(services),'uploader did not use expected mutex pair')
        expected = (b'\xa5'*1024 if reuse else struct.pack('<256I',
            *struct.unpack('<256H',gamma_table(image,expected_pointer,value))))
        require(state.read(bank_address,1024)==expected,'native RGB table upload differs')

    # Native COLOR1 H1 is distinct and must survive every new observer.
    word('active', 4*(1769+927), 0x4831bc43)
    level(963, 1)
    write('capture', 24053, b'\x0b')
    write('capture', 24083, b'\x01')
    sampled = installed('capture_sample', CAPTURE)
    installed('capture_clone', CLONE, CAPTURE)
    level(963, 2)
    installed('capture_sample', CAPTURE)  # original pool slot reused
    a = job(0, 11, 4)
    b = job(1, 11, 4)
    installed('capture_to_job', CLONE, a+36)
    installed('capture_to_job', CAPTURE, b+36)
    check_level(0, 1)
    check_level(1, 2)
    require(m.read(a+15488, 1) == b'\x03' and m.read(a+15500, 1) == b'\x04',
            '015 H/L snapshot changed')
    first = render(0, 11, 0x604f3e78, 1)
    observed(1, 0x45)
    render(0, 11, 0x604f3e78, 1, reuse=True)
    second = render(1, 11, 0x604f3e78, 2)
    require(first['lut'] != second['lut'], 'two strengths share one LUT')
    upload(1,1,0x604f3e78,2)
    render(1,11,0x604f3e78,2,reuse=True)
    upload(1,1,0x604f3e78,2,reuse=True)
    render(0,11,0x604f3e78,1)
    upload(0,1,0x604f3e78,1)
    upload(0,0,0x604f3e78,1)
    render(1,11,0x604f3e78,2)

    # The actual native dispatcher admits BOTH 0 and 16 for families 1/2.
    # Stop at its selected wrapper before unrelated ISP preparation services.
    dispatcher_routes=[]
    for request_type in (0,16):
        for family,wrapper in ((1,0x603b17e6),(2,0x603b1819)):
            write('job_1',11364+16,bytes([request_type]))
            write('job_1',11364+29,bytes([family]))
            reached=m.run(0x603aaced,wrapper,overrides=dict(a0=GAMMA['CONTEXT']),limit=50)
            require(reached['registers']['pc']==wrapper and reached['fault'] is None,
                    'native COLOR request route differs')
            dispatcher_routes.append(dict(type=request_type,family=family,wrapper=hex(wrapper)))
    write('job_1',11364+29,b'\x01')
    type16_capture=render(1,11,0x604f3e78,2,reuse=True)
    observed(1,0x46)

    # A COLOR-origin job keeps its frozen strength when native processing
    # requests use another ordinary key. The old P91 rejected this despite
    # an unchanged owner, pass type and verified RGB tuple.
    word('job_1',11364+8,0x00020000)
    retargeted_capture=render(1,2,0x604f3e78,2,reuse=True)
    observed(1,0x76)
    write('job_1',11364+14,b'\x00\x00')
    second_variant=render(1,2,0x604ee078,2)
    observed(1,0x74)
    upload(1,1,0x604ee078,2)
    write('job_1',11364+14,b'\x02\x00')
    word('job_1',11364+8,0x000b0000)

    # A selector status of zero previously bypassed the observer entirely,
    # leaving a stale V42/P42. Execute the real special selector and compare
    # its full native outputs/cache against the displaced stock instruction.
    write('job_1',11364+1838,b'\x01\x01')
    m.regions['caller']=Region('caller',CALLER,
        b'\xdd'+struct.pack('<i',GAMMA['BUILDER']-CALLER)+b'\xf0\x10','rx')
    reference=m.clone()
    reference.mutate('candidate',GAMMA['HOOK']-BASE,GAMMA['PREIMAGE'])
    for model in (m,reference):
        result=model.run(CALLER,CALLER+7,overrides=dict(a0=GAMMA['CONTEXT']),limit=3000)
        returned(result,CALLER+7)
    for region in ('context','cache','outputs'):
        require(m.regions[region].data==reference.regions[region].data,
                'selector-zero observer altered native '+region)
    observed(1,0xc0)
    write('job_1',11364+1838,b'\x00\x00')
    render(1,11,0x604f3e78,2)

    # Conversion type 3 and unsupported families remain excluded. The new
    # read-only diagnostics identify the field instead of overloading P90.
    for request_type,family,code in ((3,1,0xe3),(255,1,0xef),(16,3,0xf3),(16,255,0xff)):
        write('job_1',11364+16,bytes([request_type]))
        write('job_1',11364+29,bytes([family]))
        write('outputs',0,struct.pack('<3I',*([0x604f3e78]*3)))
        helper('_ep7dr_gamma_apply',b+11364,GAMMA['OUTPUTS'])
        require(m.read(GAMMA['OUTPUTS'],12)==struct.pack('<3I',*([0x604f3e78]*3)),
                'unsupported request changed RGB tuple')
        observed(1,code)
    write('job_1',11364+16,b'\x10')
    write('job_1',11364+29,b'\x01')

    # Exercise the actual stock borrowed-table selector, not a fabricated
    # selected tuple. This supported COLOR path was unconditionally rejected
    # by 019 because request+1524 is nonzero.
    BORROWED = 0x19600000
    borrowed = struct.pack('<I', 0x604f3e78)+bytes(24)+b'\x01'+bytes(3)
    add('borrowed', BORROWED, borrowed)
    word('job_1', 11364+1524, BORROWED)
    borrowed_capture = render(1, 11, 0x604f3e78, 2, reuse=True)
    require(m.read(BORROWED,len(borrowed)) == borrowed, 'shared borrowed object changed')
    observed(1, 0x46)

    # A mismatch in the borrowed object's variant falls back through the
    # native selector; the resulting whitelisted stock tuple still maps.
    write('borrowed',28,b'\x00')
    render(1,11,0x604f3e78,2,reuse=True)
    write('borrowed',28,b'\x01')
    word('borrowed',0,0x604edc78)  # stock identity, outside supported RGB rows
    before_borrowed=m.read(BORROWED,32)
    m.regions['caller']=Region('caller',CALLER,
        b'\xdd'+struct.pack('<i',GAMMA['BUILDER']-CALLER)+b'\xf0\x10','rx')
    unknown=m.run(CALLER,CALLER+7,overrides=dict(a0=GAMMA['CONTEXT']),limit=3000)
    returned(unknown,CALLER+7)
    require(m.read(GAMMA['OUTPUTS']+GAMMA['OUTPUT_STRIDE']+2596,12)==
            struct.pack('<3I',*([0x604edc78]*3)) and
            m.read(BORROWED,32)==before_borrowed,
            'unknown borrowed tuple was altered')
    observed(1,0xb1)

    # Preview snapshots use their own five native sources, including reused
    # owner skip semantics. No sensor-gain receipt is required or fabricated.
    level(963, 2)
    write('live', 941, b'\x0b')
    write('live', 944, b'\x01')
    preview_sampled = installed('live_sample', LIVE)
    level(963, 0)
    p = job(2, 11, live=True)
    installed('live_to_job', LIVE, p)
    check_level(2, 2)
    preview = render(2, 11, 0x604ede78, 2)
    word('job_2',11364+8,0x00020000)
    retargeted_preview=render(2,2,0x604ede78,2,reuse=True)
    observed(0,0x72)
    word('job_2',11364+8,0x000b0000)
    word('borrowed',0,0x604ede78)
    write('borrowed',28,b'\x00')
    word('job_2',11364+1524,BORROWED)
    borrowed_preview = render(2,11,0x604ede78,2,reuse=True)
    observed(0,0x42)
    write('live', 181, b'\x40')
    installed('live_sample', LIVE)
    installed('live_to_job', LIVE, p)
    check_level(2, 2)
    write('live', 181, b'\x00')
    installed('live_sample', LIVE)
    installed('live_to_job', LIVE, p)
    check_level(2, 0)
    off = render(2, 11, 0x604ede78, 0)
    require(off['lut'] == '0x604ede78', 'OFF did not restore stock gamma')
    observed(0,0xd0)

    # A valid read-only settings snapshot can be acquired on either other core.
    for core in (1, 2):
        m.regions['cpu_id'] = replace(m.regions['cpu_id'], data=struct.pack('<I', core))
        level(963, core)
        installed('live_sample', LIVE)
        installed('live_to_job', LIVE, p)
        check_level(2, core)
    m.regions['cpu_id'] = replace(m.regions['cpu_id'], data=bytes(4))

    # Busy native bank state cannot leak a half-applied settings transaction.
    word('ring', 0, 1)
    installed('live_sample', LIVE)
    installed('live_to_job', LIVE, p)
    check_level(2, 0)
    observed(0,0x50)
    word('ring', 0, 0)
    installed('live_to_job', LIVE+1, p)
    check_level(2, 0)

    # A job with unsupported native gradation keeps the original gamma even
    # when its selected rendering strength was captured earlier.
    installed('live_sample', LIVE)
    installed('live_to_job', LIVE, p)
    write('job_2', 11364+1797, b'\x02')
    # Direct interposition check uses the stock tuple as selected by that path.
    tuple_address = GAMMA['OUTPUTS']
    word('outputs', 0, 0x604ee278)
    word('outputs', 4, 0x604ee278)
    word('outputs', 8, 0x604ee278)
    helper('_ep7dr_gamma_apply',p+11364,tuple_address)
    require(m.read(tuple_address, 12) == struct.pack('<3I', *([0x604ee278]*3)),
            'unsupported gradation was remapped')
    observed(0,0xa0)

    # The user explicitly narrowed rendering support to COLOR1-4. A Natural
    # source clears its row, even when its operation key is rewritten to COLOR.
    write('live',941,b'\x02')
    installed('live_sample',LIVE)
    installed('live_to_job',LIVE,p)
    check_level(2,0)
    observed(0,0x60)
    write('job_2',11364+1797,b'\x00')
    word('job_2',11364+8,0x000b0000)
    write('outputs',0,struct.pack('<3I',*([0x604ede78]*3)))
    helper('_ep7dr_gamma_apply',p+11364,tuple_address)
    require(m.read(tuple_address,12)==struct.pack('<3I',*([0x604ede78]*3)),
            'non-COLOR request was remapped')
    observed(0,0x60)  # unsupported source takes precedence over RGB detail
    write('live',941,b'\x0b')
    installed('live_sample',LIVE)
    installed('live_to_job',LIVE,p)
    helper('_ep7dr_gamma_apply',p+11364,tuple_address,selector_status=0)
    observed(0,0xc0)
    helper('_ep7dr_highlight_clear_observations')
    observed(0,0)
    observed(1,0)
    return dict(status='passed', strategy=report['strategy'],
                capture_snapshot_instructions=sampled, preview_snapshot_instructions=preview_sampled,
                retained_clone_lut=first['lut'], later_capture_lut=second['lut'], preview_lut=preview['lut'],
                native_h1_preserved=True, cache_reuse=True, native_off_restored=True,
                supported_picture_modes='COLOR1-4', non_color_keeps_stock=True,
                borrowed_capture_lut=borrowed_capture['lut'], borrowed_preview_lut=borrowed_preview['lut'],
                borrowed_variant_fallback_and_object_unchanged=True,
                unknown_borrowed_tuple_keeps_stock=True,
                native_dispatcher_routes=dispatcher_routes,type16_capture_lut=type16_capture['lut'],
                color_origin_retargeted_capture_lut=retargeted_capture['lut'],
                color_origin_retargeted_preview_lut=retargeted_preview['lut'],
                rgb_variant_observation_and_upload=second_variant['lut'],
                selector_zero_native_equivalence=True,
                unsupported_type_and_family_keep_stock=True,split_rejection_codes=True,
                native_rgb_upload_two_modeled_banks=True,
                upload_cache_reuse_and_changed_level=True,
                pipeline_observations_and_clear=True,
                persistent_native_session_latch=1,
                read_only_snapshots_all_three_cores=True, pending_bank_and_unknown_owner_off=True,
                exposure_iso_gain_unchanged=True, hash_checks_performed=False,
                boundaries=['Capture/live owners, native job geometry and active settings are fixture inputs.',
                            'Actual installed 015 helper CALLs, getters, snapshots and RGB builder run.',
                            'Native uploader stores into modeled MMIO RAM; its two mutex calls are service shells.',
                            'No sensor/ISP pixels, complete preview scheduler or physical storage.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = inspect(args.candidate, args.engine)
    text = json.dumps(result, indent=2)+'\n'
    if args.out:
        args.out.write_text(text)
    print(text, end='')
