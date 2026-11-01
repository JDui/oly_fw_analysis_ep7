#!/usr/bin/env python3
"""Resume native device sampling with explicit register inputs, then geometry.

The two cases vary only the GPIO bit queried as device1215. They are controlled
offline inputs, not camera measurements or complete peripheral emulation.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER,require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import native_call,summarize_message,result_ok
from ep7_candidate_device_state_sim import device_context,admit
from penf_emulator import Region


def input_context(directory,prefix,engine):
    upstream,context=device_context(directory,prefix,engine)
    base,syms=context['machine'],context['syms']
    capture=base.read(CAPTURE,SIZE)
    ports=[struct.unpack('<I',base.read(0x601aa228+24*i,4))[0] for i in range(9)]
    require(ports==[102,80,81,89,94,144,91,145,143] and
            base.read(0x601aa1e8,8)==struct.pack('<I4B',0x1215,1,1,0,0) and
            base.read(0x601168b2,5)==bytes.fromhex('cd08000004'),
            'original device1215 input/record/reset binding changed')
    rows=[]
    outputs=[]
    for input_bit in (0,1):
        machine=base.clone()
        pins={}
        for port in ports:
            address=struct.unpack('<I',machine.read(0x60024078+4*port,4))[0]
            value=(0x12345678&~16) | (16 if port==80 and input_bit else 0)
            admit(machine,f'device_pin_{port}',address,struct.pack('<I',value),'r')
            pins[port]=dict(address=hex(address),value=hex(value),bit4=int(port==80 and input_bit))
        # Resume the first actual GPIO read from its saved registers and stack.
        sampled=machine.resume(context['device_gpio_result']['registers'],0x6011813d,
            full_trace=True,limit=20000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808])
        result_ok(machine,sampled,0x6011813d,CALL_SP-60)
        bitmap=bytes([input_bit<<1,0])
        all_trace=context['device_gpio_result']['trace']+sampled['trace']
        require(machine.read(0xa272bce8,2)==machine.read(0x621db584,2)==bitmap and
                [r['d0'] for r in all_trace if r['pc']==0x60021ffe]==ports,
                'native GPIO snapshot or original getter sequence differs from modeled input')
        sample_row=summarize_message('native_gpio_snapshot_resume',sampled,CALL_SP)
        sample_row.update(native_pin_getters=9,bitmap=bitmap.hex(),
            stop_before_event_registration='0x6011813d',complete_initializer_returned=False)
        direct_pins={}
        for address in range(0x98e00058,0x98e0006c,4):
            value=0x76543210 # bit31=0; all other bits are ignored by the sampler.
            admit(machine,f'device_direct_pin_{address:x}',address,struct.pack('<I',value),'r')
            direct_pins[hex(address)]=hex(value)
        admit(machine,'device_direct_pin_snapshot',0xa272bcec,b'\xa5')
        admit(machine,'device_direct_pin_shadow',0x621db5a4,b'\xa5')
        direct=native_call(machine,syms,0x60118545,0,4,limit=1000)
        require(machine.read(0xa272bcec,1)==machine.read(0x621db5a4,1)==b'\0',
                'native direct-pin snapshot differs from modeled bit31 inputs')
        admit(machine,'device_reset_flags',0xa272bcdc,b'\xa5'*3)
        reset=native_call(machine,syms,0x601168ba,0,4,limit=5000)
        require(machine.read(0xa272bcdc,3)==b'\0\x01\0',
                'native initial256 query/reset flags differ from modeled direct pins')
        predicate=native_call(machine,syms,0x601168ed,0xf0,24,dict(d0=0x1215),limit=5000)
        require(predicate['registers']['d0']==1-input_bit,'native1215 predicate polarity changed')
        # Only restore the original suspended configuration stack, not its RAM
        # state or registers. Native initialization above supplies the inputs.
        machine.regions['stack']=context['geometry_stack']
        machine.regions['caller']=Region('caller',CALLER,
            b'\xdd'+struct.pack('<i',0x6042760c-CALLER)+bytes([0xf0,16]),'rx')
        configured=machine.resume(context['geometry_configuration']['registers'],CALLER+7,
            full_trace=True,limit=80000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808])
        configuration_row=summarize_message('native_geometry_resume_with_device_inputs',configured,CALL_SP)
        if configured['status']!='returned':
            configuration_row['d0_at_stop']=configuration_row.pop('returned_d0')
        configuration_row['stop_registers']={k:hex(v) for k,v in configured['registers'].items()}
        expected=[(0x6016bff6,0x62221d80,2,0x60165665),
                  (0x60163281,0x622211e2,1,0x601655f2)][input_bit]
        pc,address,width,return_pc=expected
        require(configured['status']=='memory_fault' and configured['fault']==dict(
                kind=1,pc=pc,map=0,address=address,size=width,access='read') and
                configured['registers']['mdr']==return_pc and
                not any(r['pc']==0x6042805e for r in configured['trace']),
                'native geometry state frontier changed: '+str(configured['fault']))
        require(machine.read(CAPTURE,SIZE)==capture,'device-input geometry probe changed partial capture')
        rows.append(dict(gpio80_input_bit4=input_bit,gpio_register_inputs=pins,
            direct_pin_register_inputs=direct_pins,native_query1215_result=1-input_bit,
            frontier=dict(pc=hex(pc),address=hex(address),width=width,
                native_return_pc=hex(return_pc)),
            cases=[sample_row]+[summarize_message(name,result,CALL_SP) for name,result in (
                ('native_direct_pin_snapshot',direct),('native_device_reset',reset),
                ('native_device1215_predicate',predicate))]+[configuration_row],
            geometry_configuration_passed=configured['status']=='returned',
            geometry_dynamic_setter_executed=any(r['pc']==0x6042805e for r in configured['trace']),
            capture_unchanged=True))
        outputs.append(dict(machine=machine,configuration_result=configured))
    report=dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),cases=rows,native_device_sampling_and_reset_passed=True,
        input_values_are_camera_evidence=False,geometry_resumed=True,population_resumed=False,
        hash_checks_performed=False,native_api_success_stubs=False,firmware_files_modified=False,
        hardware_executed=False,installable=False,
        limits=['All14 sampled register words are explicit stable offline inputs; no camera measurements, IRQ events, peripheral timing or read side effects are asserted.',
                'Original GPIO sampling resumes its actual fault registers and stops before event registration. The complete initializer/task schedule remains outside this model.',
                'Native direct-pin sampling and601168ba reset execute;1215 polarity is tested at both inputs using the same original tables.',
                'Geometry resumes the saved registers/stack from its real device-query frontier. It may still require further original data or state; no dynamic geometry success is inferred from sampler success.',
                'Conditional ROM loading/BSS and upstream object fixtures remain inherited. Partial capture stays unchanged; worker execution and installation qualification remain incomplete.'])
    return report,dict(upstream=context,cases=outputs)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(input_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
