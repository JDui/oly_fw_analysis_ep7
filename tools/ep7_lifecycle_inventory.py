#!/usr/bin/env python3
"""Cross-reference existing probe literals; never import probes or read firmware.

A passing inventory is NOT native lifecycle closure or byte revalidation.
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def witnesses(path):
    result = {}
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            try:
                address, instruction = ast.literal_eval(key), ast.literal_eval(value)
            except (ValueError, TypeError):
                continue
            if (not isinstance(address, int) or not isinstance(instruction, tuple)
                    or len(instruction) != 2 or instruction[0] != 'call'):
                continue
            if address in result and result[address]['instruction'] != instruction:
                raise ValueError(f'conflicting witness at {address:#x}')
            result[address] = dict(instruction=instruction, line=key.lineno)
    return result


def inspect():
    manifest = json.loads((ROOT / 'research/ep7/lifecycle-hook-inventory.json').read_text())
    evidence = {name: witnesses(ROOT / source['probe'])
                for name, source in manifest['sources'].items()}
    checked = []
    seen = set()
    for row in manifest['free_sites'] + manifest['state_service_sites']:
        address = int(row['address'], 16)
        if address in seen:
            raise ValueError(f'duplicate inventory address {address:#x}')
        seen.add(address)
        expected = row.get('expected_operand', '0x60022732,[],4')
        actual = evidence[row['source']].get(address)
        if actual is None or actual['instruction'] != ('call', expected):
            raise ValueError(f'missing or changed call witness {address:#x}')
        source = manifest['sources'][row['source']]
        checked.append(dict(address=row['address'], probe=source['probe'],
                            line=actual['line'], classification=row.get('object_kind', 'state_service')))
    # Every free in these three bounded witness sets must have a classification.
    # This is intentionally NOT a scan of firmware or transitive callees.
    probe_frees = {address for name in ('expanded', 'disposal', 'states')
                   for address, value in evidence[name].items()
                   if value['instruction'] == ('call', '0x60022732,[],4')}
    declared_frees = {int(row['address'], 16) for row in manifest['free_sites']}
    if probe_frees != declared_frees:
        raise ValueError('unclassified or extra free call in bounded evidence set')
    return dict(scope=__doc__.strip(), source_inventory_consistent=True,
                node_free_sites=sum(row['object_kind'] == 'node' for row in manifest['free_sites']),
                non_node_free_sites=sum(row['object_kind'] != 'node' for row in manifest['free_sites']),
                state_service_sites=len(manifest['state_service_sites']), checked=checked,
                hash_checks_performed=False, stock_bytes_revalidated=False,
                native_closure_proven=False, target_compiled=False,
                firmware_compile_ready=False, camera_accessed=False)


if __name__ == '__main__':
    print(json.dumps(inspect(), indent=2))
