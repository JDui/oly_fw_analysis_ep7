#!/usr/bin/env python3
"""Collect a compiler-derived cold-bootstrap call graph, retaining unknown native stack boundaries."""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from ep7_installation_manifest import CORE, ROOT, implementation_sources
from ep7_native_bindings import bindings

REFERENCE = 'https://gcc.gnu.org/onlinedocs/gcc-13.4.0/gcc/Developer-Options.html'
ENTRY = 'ep7r_bootstrap_initialize'
QUOTED = r'"((?:\\.|[^"\\])*)"'

# This is the concrete cold-bootstrap composition, not a points-to assertion
# for other users of the reusable provider/query/runtime interfaces.
CALLBACKS = {
    'b->native.raw.get_tid': 'poll_lock_provider/native/raw_callbacks.c:current',
    'n.create': 'poll_lock_provider/bootstrap/native_callbacks.c:create',
    'b->native.delete_unpublished': 'poll_lock_provider/bootstrap/native_callbacks.c:drop',
    'r->env.installation_ready': 'runtime/cold_bootstrap.c:installed',
    'r->env.queue': 'runtime/native_context.c:queue',
    'ops->get_tid': 'runtime/task_context_native.c:query',
    'ops->read32': 'runtime/task_context_native.c:read_word',
    'ops->read16': 'runtime/task_context_native.c:read_half',
}
COMPOSITION = {
    'runtime/cold_bootstrap.c': [
        'ep7b_prepare(&storage.boot,&storage.core,ep7b_unresolved_native())',
        'ep7r_prepare(&storage.runtime,&storage.boot,ep7r_native_environment(NULL,installed))'],
    'poll_lock_provider/bootstrap/native_callbacks.c': [
        'n.create=create;n.delete_unpublished=drop;n.raw=ep7s_unresolved_raw_callbacks();'],
    'poll_lock_provider/native/raw_callbacks.c': ['ep7s_native n={0,current,poll,signal};'],
    'runtime/native_context.c': ['ep7r_environment e={ctx,ready,task,queue,delay_one,quarantine};'],
    'runtime/task_context_native.c': [
        'static const ep7n_task_ops native_ops={NULL,query,read_word,read_half};',
        'return ep7n_query_task(&native_ops,anchor,out);',
        'return ep7n_query_queue(&native_ops,handle,out);'],
}
# Frame sums at ASM boundaries are charged separately: the bridge's MOVM/ADD
# frame and its native CALL frame. They are not additional GCC .su frames.
ASSEMBLY = {
    'ep7_gcc_get_tid': (20, 'native_get_tid_leaf', 'target/get_tid_bridge.s'),
    'ep7_gcc_raw_sem_create': (32, 'native_sem_create_body_unknown', 'poll_lock_provider/bootstrap/create_delete_bridges.s'),
    'ep7_gcc_raw_sem_delete_unpublished': (36, 'native_sem_delete_body_unknown', 'poll_lock_provider/bootstrap/create_delete_bridges.s'),
    'ep7_gcc_quarantine': (0, 'exception_entry_stack_unknown', 'runtime/quarantine.s'),
}


def normalize(text):
    return text.replace(str(CORE)+'/', '')


def fields(line):
    return {key:json.loads('"'+value+'"') for key,value in
            re.findall(r'(\w+):\s*'+QUOTED, line)}


def graph(text):
    nodes = {}; edges = {}
    for line in text.splitlines():
        if line.startswith('node:'):
            row = fields(line)
            if not {'title','label'} <= set(row):
                raise ValueError('unrecognized GCC node')
            size = re.search(r'\n(\d+) bytes \(([^)]+)\)$', row['label'])
            if size:
                if size[2] != 'static':
                    raise ValueError('nonstatic frame needs separate review: '+row['title'])
                nodes[normalize(row['title'])] = dict(frame_bytes=int(size[1]),
                    compiler_location=normalize(row['label'].splitlines()[-2]))
        elif line.startswith('edge:'):
            row = fields(line)
            if not {'sourcename','targetname'} <= set(row) or set(row)-{'sourcename','targetname','label'}:
                raise ValueError('unrecognized GCC edge: '+line)
            edges.setdefault(normalize(row['sourcename']),[]).append(dict(
                target=normalize(row['targetname']), location=normalize(row.get('label','<compiler-generated>'))))
    return nodes, edges


def inspect(prefix, decoded):
    prior = json.loads((ROOT/'research/ep7/installation-manifest.json').read_text(encoding='utf-8-sig'))['object_inventory']
    owners = {name:source for source,row in prior['objects'].items() for name in row['definitions']}
    sources = set(implementation_sources())
    if set(prior['objects']) != sources:
        raise ValueError('implementation source inventory changed')
    for relative, snippets in COMPOSITION.items():
        source = re.sub(r'\s+','',(CORE/relative).read_text())
        if any(re.sub(r'\s+','',s) not in source for s in snippets):
            raise ValueError('cold callback composition changed: '+relative)
    include = subprocess.check_output([prefix+'gcc','-print-file-name=include'],text=True).strip()
    flags = ['-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin',
             '-mno-setlb','-mno-liw','-nostdinc','-I'+str(CORE/'target/include'),'-I'+include,
             '-I'+str(CORE),'-I'+str(CORE/'poll_lock_provider'),'-fstack-usage','-fcallgraph-info=su']
    nodes = {}; edges = {}; compiled = {}; resolved = []; seen = set(); pending = [ENTRY]
    with tempfile.TemporaryDirectory(prefix='ep7-bootstrap-stack-') as temp:
        def compile_source(relative):
            if relative in compiled:
                return
            if relative not in sources or not relative.endswith('.c'):
                raise ValueError('not a current implementation C source: '+relative)
            obj = Path(temp)/(str(len(compiled))+'.o')
            extra = ['-fno-tree-loop-distribute-patterns'] if relative == 'target/memory.c' else []
            subprocess.run([prefix+'gcc',*flags,*extra,'-c',str(CORE/relative),'-o',str(obj)],check=True,timeout=60)
            local_nodes, local_edges = graph(obj.with_suffix('.ci').read_text())
            if set(local_nodes) & set(nodes):
                raise ValueError('duplicate compiler graph definition')
            current_size = [int(v) for v in subprocess.check_output([prefix+'size',str(obj)],text=True).splitlines()[-1].split()[:3]]
            if current_size != prior['objects'][relative]['text_data_bss']:
                raise ValueError('callgraph collection changed object size: '+relative)
            old_usage = {}
            for line in prior['objects'][relative]['stack_usage']:
                name,size,kind = line.split('\t')
                old_usage[name.rsplit(':',1)[-1]] = (int(size),kind)
            for name,row in local_nodes.items():
                usage_name = re.sub(r'\.(constprop|isra)\.\d+$',r'.\1',name.rsplit(':',1)[-1])
                if old_usage.get(usage_name) != (row['frame_bytes'],'static'):
                    raise ValueError('callgraph and current object .su differ: '+name)
                row.update(source=relative, kind='gcc_static_frame')
            nodes.update(local_nodes); edges.update(local_edges)
            compiled[relative] = dict(text_data_bss=current_size, all_reported_frames_match_prior_su=True)

        while pending:
            name = pending.pop()
            if name in seen:
                continue
            if name in ASSEMBLY:
                size, boundary, source = ASSEMBLY[name]
                nodes[name] = dict(frame_bytes=size, kind='assembly_frame_and_native_call',
                    boundary=boundary, source=source)
                edges[name] = []; seen.add(name); continue
            if name not in nodes:
                relative = name.split(':',1)[0] if ':' in name else owners.get('_'+name)
                if relative is None:
                    raise ValueError('unknown direct callee '+name)
                compile_source(relative)
            if name not in nodes:
                raise ValueError('callee has no compiler frame '+name)
            seen.add(name)
            for edge in edges.get(name,[]):
                if edge['target'] == '__indirect_call':
                    relative,line,column = edge['location'].rsplit(':',2)
                    text = (CORE/relative).read_text().splitlines()[int(line)-1][int(column)-1:]
                    match = re.search(r'([\w.>\-]+)\(', text)
                    expression = match[1] if match else None
                    if expression not in CALLBACKS:
                        raise ValueError('unresolved callback '+name+' '+edge['location']+' '+repr(text))
                    target = CALLBACKS[expression]
                    resolved.append(dict(caller=name, location=edge['location'], expression=expression, target=target))
                    edge.update(target=target, indirect=True, expression=expression)
                pending.append(edge['target'])

    reachable_nodes = {name:nodes[name] for name in sorted(seen)}
    reachable_edges = {name:edges.get(name,[]) for name in sorted(seen)}
    # Ordinary call sums deliberately overcount sibling/tail-call frame reuse.
    # Unknown native bodies and trap entry are not assigned fictitious zero bounds.
    memo = {}; active = set()

    def visit(name):
        if name in active:
            raise ValueError('recursive startup edge needs an explicit bound: '+name)
        if name in memo:
            return memo[name]
        active.add(name); row=nodes[name]; children=[visit(e['target']) for e in edges.get(name,[])]
        boundary = row.get('boundary')
        complete = boundary in (None,'native_get_tid_leaf') and all(c['complete'] for c in children)
        child = max(children,key=lambda c:c['prefix_bytes'],default=dict(prefix_bytes=0,path=[]))
        value = dict(prefix_bytes=row['frame_bytes']+child['prefix_bytes'], path=[name]+child['path'], complete=complete)
        memo[name] = value; active.remove(name); return value

    root = visit(ENTRY)
    boundaries = []

    def walk(name, total, path):
        row = nodes[name]; total += row['frame_bytes']; path = path+[name]
        if row.get('boundary') not in (None,'native_get_tid_leaf'):
            boundaries.append(dict(boundary=row['boundary'],known_prefix_bytes=total,path=path))
        for target in sorted({edge['target'] for edge in edges.get(name,[])}):
            walk(target,total,path)

    walk(ENTRY,0,[])
    # Check the complete tiny native get_tid body for stack neutrality. This is
    # not a complete native semaphore or exception/IRQ call graph.
    start = bindings()['ep7_stock_get_tid_unresolved']['address']; end=0x600317f0
    asm = subprocess.check_output([prefix+'objdump','-D','-z','-b','binary','-m','mn10300',
        '--insn-width=16','--adjust-vma=0x60020020',f'--start-address={start:#x}',f'--stop-address={end:#x}',str(decoded)],text=True)
    insns = re.findall(r'^([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*([^\n]*)$',asm,re.M)
    allowed = {'mov','movbu','movhu','asl2','cmp','bne','beq','bra','clr','retf'}
    if not insns or sum(len(b.split()) for _,b,_,_ in insns) != end-start:
        raise ValueError('incomplete native get_tid body')
    for pc, _, mn, operands in insns:
        if mn not in allowed or re.search(r'\bsp\b',operands):
            raise ValueError('native get_tid stack effects changed')
        if mn in {'bne','beq','bra'} and not start <= int(operands,16) < end:
            raise ValueError('native get_tid has an out-of-body branch')
    if insns[-1][2:] != ('retf','[a2],4'):
        raise ValueError('native get_tid return frame changed')
    full = dict(root)
    full['complete_stack_bound_bytes'] = root['prefix_bytes'] if root['complete'] else None
    return dict(scope=__doc__,compiler_reference=REFERENCE,root=ENTRY,compiled_sources=compiled,
        compiled_c_source_count=len(compiled),reachable_function_count=len(seen),
        reachable_nodes=reachable_nodes,reachable_edges=reachable_edges,
        resolved_cold_callbacks=resolved,unresolved_cold_callbacks=[],recursive_reachable_edges=False,
        native_get_tid_instructions_checked=len(insns),native_get_tid_body_extra_stack_bytes=0,
        root_stack=full,unknown_native_boundaries=boundaries,
        usr3_own_prologue_bytes=44,original_call_frame_bytes=4,cold_bridge_bytes=40,
        known_prefix_below_usr3_entry_bytes=44+4+40+root['prefix_bytes'],
        configured_usr3_stack_bytes=2048,complete_task_stack_bound_proven=False,
        capacity_remaining_bytes=None,
        limits=['Graph and callback mapping are only for this fixed one-shot bootstrap composition.',
                'Per-function static frames and all child edges are summed conservatively; mutually exclusive paths are not summed together.',
                'Native semaphore create/delete bodies, exception/IRQ stack, task initial context and other Usr3 paths remain outside the bound.',
                'The known prefix is not an upper bound on the complete native/task stack and is not subtracted from 2048 as available headroom.',
                'Existing assembly frame and Usr3 prologue witnesses are reused; only native get_tid is newly disassembled here.',
                'No hardware, target code, full firmware linker or application test suite is executed.'],
        target_linked=False,target_executed=False,firmware_built=False,hash_checks_performed=False)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.tool_prefix,args.decoded),indent=2))
