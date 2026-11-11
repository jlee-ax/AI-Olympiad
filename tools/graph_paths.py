#!/usr/bin/env python3
"""Inspect explicit learning-path declarations and local file bindings, read-only."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from validate import validate

ROLES = ('source', 'demand', 'prerequisite', 'theory_explanation',
         'coding_practice', 'independent_assessment', 'feedback')
SHA256 = re.compile(r'[0-9a-f]{64}\Z')
LIMITATIONS = [
    'Only explicitly declared demands, roles, direct edges and local files are checked; undeclared learning requirements are not discovered.',
    'Role labels, provenance locators, revision/origin claims and assessment support conditions are declarations, not semantic verification.',
    'Current SHA-256 bindings establish local byte equality, not source authenticity, official status, truth or educational adequacy.',
    'Reviewer independence, unaided learner performance, timing, execution and contest readiness are not checked.',
    'This opt-in report is advisory and does not change the legacy structural validator or any earlier quality evaluation.',
]


def _json_errors(value, name):
    """Reject non-JSON values without relying on stdout's Unicode encoding."""
    errors, pending = [], [(value, name, frozenset())]
    while pending:
        item, location, ancestors = pending.pop()
        if isinstance(item, (dict, list)):
            if id(item) in ancestors:
                errors.append({'path': location, 'code': 'invalid_json', 'message': 'Cyclic containers are not JSON input.'})
                continue
            ancestors = ancestors | {id(item)}
        if isinstance(item, str):
            if any(0xD800 <= ord(char) <= 0xDFFF for char in item):
                errors.append({'path': location, 'code': 'invalid_unicode', 'message': 'Lone Unicode surrogates are not allowed.'})
        elif isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    errors.append({'path': location, 'code': 'invalid_json', 'message': 'Object keys must be strings.'})
                else:
                    pending.extend([(key, location + '.key', ancestors), (child, location + '.' + key, ancestors)])
        elif isinstance(item, list):
            pending.extend((child, f'{location}[{i}]', ancestors) for i, child in enumerate(item))
        elif item is None or type(item) in (bool, int):
            pass
        elif isinstance(item, float) and math.isfinite(item):
            pass
        else:
            errors.append({'path': location, 'code': 'invalid_json', 'message': 'Only finite JSON values are allowed.'})
    return errors


def inspect_paths(graph, path_spec, root):
    """Return advisory gap/staleness findings; never infer roles or mutate inputs.

    root is the explicit local provenance root. Status precedence is invalid,
    stale, gap, declared_path_complete. All submitted paths are requirements.
    """
    report = {'authority': 'advisory_only', 'status': 'invalid', 'synthetic': None,
              'errors': [], 'findings': [], 'warnings': [], 'paths': [], 'bindings': [],
              'verification': {'semantics': 'not_checked', 'source_authenticity': 'not_checked',
                               'learner_independence': 'not_checked'},
              'limitations': list(LIMITATIONS)}
    errors, findings = report['errors'], report['findings']

    def error(location, code, message):
        errors.append({'path': location, 'code': code, 'message': message})

    def gap(location, code, message, status='gap'):
        findings.append({'path': location, 'code': code, 'message': message, 'status': status})

    def string(value, location):
        if value is None:
            gap(location, 'missing_metadata', 'A nonempty string is required.')
            return None
        if not isinstance(value, str) or not value.strip():
            error(location, 'invalid_value', 'Expected a nonempty string.')
            return None
        return value

    errors.extend(_json_errors(graph, 'graph'))
    errors.extend(_json_errors(path_spec, 'path_spec'))
    if errors:
        return report
    structural_errors, report['warnings'] = validate(graph)
    for message in structural_errors:
        error('graph', 'invalid_graph', message)
    if not isinstance(path_spec, dict):
        error('path_spec', 'invalid_type', 'Path specification must be an object.')
        return report
    if errors:
        return report
    try:
        report['graph_sha256'] = hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(',', ':'),
                                                          ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        error('graph', 'invalid_json', 'Cannot serialize graph: ' + str(exc))
        return report
    if 'schema_version' not in path_spec:
        gap('schema_version', 'missing_metadata', 'Explicit schema_version 1 is required.')
    elif type(path_spec['schema_version']) is not int or path_spec['schema_version'] != 1:
        error('schema_version', 'invalid_version', 'Expected integer schema_version 1.')
    if 'synthetic' not in path_spec:
        gap('synthetic', 'missing_metadata', 'Explicit synthetic boolean is required.')
    elif type(path_spec['synthetic']) is not bool:
        error('synthetic', 'invalid_type', 'Expected a boolean.')
    else:
        report['synthetic'] = path_spec['synthetic']
    try:
        local_root = Path(root).resolve(strict=True)
        if not local_root.is_dir():
            raise ValueError('Root must be a directory.')
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        error('root', 'invalid_root', str(exc))
        return report
    nodes = {node['id']: node for node in graph['nodes']}
    required = path_spec.get('required_demands')
    if required is None or required == []:
        gap('required_demands', 'missing_required_demands', 'Declare at least one required demand; empty scope cannot pass.')
        required = []
    elif not isinstance(required, list):
        error('required_demands', 'invalid_type', 'Expected an array of demand node IDs.')
        required = []
    required_ids = set()
    for i, value in enumerate(required):
        demand = string(value, f'required_demands[{i}]')
        if demand is not None:
            if demand in required_ids:
                error(f'required_demands[{i}]', 'duplicate_demand', 'Required demand IDs must be distinct.')
            required_ids.add(demand)
            if demand not in nodes:
                gap(f'required_demands[{i}]', 'missing_node', 'Required demand node is absent from the graph: ' + demand)
    declarations = path_spec.get('paths')
    if declarations is None or declarations == []:
        gap('paths', 'missing_path_declarations', 'Declare explicit seven-role paths for the required demands.')
        declarations = []
    elif not isinstance(declarations, list):
        error('paths', 'invalid_type', 'Expected an array of path declarations.')
        declarations = []
    ids, covered, cache = set(), set(), {}
    edges = {(edge['from'], edge['to'], edge['type']): i for i, edge in enumerate(graph['edges'])}

    for i, declaration in enumerate(declarations):
        location = f'paths[{i}]'
        before = (len(errors), len(findings))
        result = {'id': None, 'status': 'gap', 'edges': []}
        report['paths'].append(result)
        if not isinstance(declaration, dict):
            error(location, 'invalid_type', 'Path declaration must be an object.')
            result['status'] = 'invalid'
            continue
        identifier = string(declaration.get('id'), location + '.id')
        result['id'] = identifier
        if identifier is not None:
            if identifier in ids:
                error(location + '.id', 'duplicate_path', 'Path IDs must be distinct.')
            ids.add(identifier)
        if 'comparison_id' in declaration:
            string(declaration['comparison_id'], location + '.comparison_id')
            result['comparison_id'] = declaration['comparison_id']
        roles = declaration.get('roles')
        if roles is None:
            gap(location + '.roles', 'missing_roles', 'All seven role assignments are required.')
            roles = {}
        elif not isinstance(roles, dict):
            error(location + '.roles', 'invalid_type', 'Roles must be an object.')
            roles = {}
        for extra in sorted(set(roles) - set(ROLES)):
            error(location + '.roles.' + extra, 'unknown_role', 'Unknown role; use the fixed seven-role contract.')
        selected = {}
        for role in ROLES:
            node_id = string(roles.get(role), location + '.roles.' + role)
            if node_id is not None:
                selected[role] = node_id
                if node_id not in nodes:
                    gap(location + '.roles.' + role, 'missing_node', 'Declared role node is absent: ' + node_id)
                elif nodes[node_id]['status'] in ('blocked', 'superseded'):
                    gap(location + '.roles.' + role, 'inactive_node', 'A blocked or superseded node cannot supply a current route.')
        if len(set(selected.values())) != len(selected):
            gap(location + '.roles', 'collapsed_roles', 'Each of the seven roles must have a distinct node ID.')
        demand = selected.get('demand')
        if demand is not None:
            covered.add(demand)
            if demand not in required_ids:
                error(location + '.roles.demand', 'unscoped_demand', 'Path demand must be listed in required_demands.')
        for prior, following in zip(ROLES, ROLES[1:]):
            if prior not in selected or following not in selected:
                continue
            src, dst = selected[prior], selected[following]
            candidates = ((src, dst, 'supports'), (src, dst, 'informs'), (dst, src, 'depends_on'))
            match = next((key for key in candidates if key in edges), None)
            if match is None:
                gap(location + '.roles.' + following, 'missing_edge',
                    f'No direct supports/informs {src} -> {dst} or depends_on {dst} -> {src} edge.')
            else:
                result['edges'].append({'prior_role': prior, 'next_role': following,
                                        'from': match[0], 'to': match[1], 'type': match[2], 'graph_edge_index': edges[match]})
        assessment = declaration.get('assessment')
        if assessment is None:
            gap(location + '.assessment', 'missing_assessment_conditions', 'Explicit independent-task support and answer conditions are required.')
        elif not isinstance(assessment, dict):
            error(location + '.assessment', 'invalid_type', 'Assessment conditions must be an object.')
        else:
            independent = assessment.get('independent')
            if independent is None:
                gap(location + '.assessment.independent', 'missing_assessment_conditions', 'Declare whether the task is independent.')
            elif type(independent) is not bool:
                error(location + '.assessment.independent', 'invalid_type', 'Expected a boolean.')
            elif not independent:
                gap(location + '.assessment.independent', 'assisted_assessment', 'An explicitly assisted assessment does not supply this role.')
            for field in ('allowed_support', 'answer_conditions'):
                string(assessment.get(field), location + '.assessment.' + field)
        provenance = declaration.get('provenance')
        if provenance is None:
            gap(location + '.provenance', 'missing_provenance', 'Per-role local provenance bindings are required.')
            provenance = {}
        elif not isinstance(provenance, dict):
            error(location + '.provenance', 'invalid_type', 'Provenance must be an object keyed by role.')
            provenance = {}
        for extra in sorted(set(provenance) - set(ROLES)):
            error(location + '.provenance.' + extra, 'unknown_role', 'Unknown provenance role.')
        for role in ROLES:
            bound_location = location + '.provenance.' + role
            binding = provenance.get(role)
            if binding is None:
                gap(bound_location, 'missing_provenance', 'A local byte binding for this role is required.')
                continue
            if not isinstance(binding, dict):
                error(bound_location, 'invalid_type', 'Expected a provenance object.')
                continue
            for field in ('origin', 'revision', 'locator'):
                string(binding.get(field), bound_location + '.' + field)
            filename = string(binding.get('path'), bound_location + '.path')
            expected = string(binding.get('sha256'), bound_location + '.sha256')
            if expected is not None and not SHA256.fullmatch(expected):
                error(bound_location + '.sha256', 'invalid_sha256', 'Expected 64 lowercase hexadecimal characters.')
                expected = None
            if filename is None or expected is None:
                continue
            entry = {'path_id': identifier, 'role': role, 'node_id': selected.get(role),
                     'path': filename, 'expected_sha256': expected, 'actual_sha256': None, 'status': 'unavailable'}
            report['bindings'].append(entry)
            relative = Path(filename)
            if relative.is_absolute() or '..' in relative.parts:
                error(bound_location + '.path', 'unsafe_path', 'Use a root-relative local path without parent traversal.')
                continue
            try:
                actual_path = (local_root / relative).resolve(strict=True)
                if not actual_path.is_relative_to(local_root):
                    error(bound_location + '.path', 'unsafe_path', 'Resolved file escapes the local root.')
                    continue
                if not actual_path.is_file():
                    gap(bound_location + '.path', 'unavailable_file', 'Binding must name a regular file.')
                    continue
                if actual_path not in cache:
                    cache[actual_path] = hashlib.sha256(actual_path.read_bytes()).hexdigest()
                entry['actual_sha256'] = cache[actual_path]
                entry['status'] = 'current' if cache[actual_path] == expected else 'stale'
                if entry['status'] == 'stale':
                    gap(bound_location + '.sha256', 'stale_binding', 'Declared SHA-256 differs from current local file bytes.', 'stale')
            except (OSError, RuntimeError, ValueError) as exc:
                gap(bound_location + '.path', 'unavailable_file', 'Cannot read bound regular file: ' + str(exc))
        local_findings = findings[before[1]:]
        result['status'] = ('invalid' if len(errors) > before[0] else
                            'stale' if any(item['status'] == 'stale' for item in local_findings) else
                            'gap' if local_findings else 'declared_path_complete')
    for demand in sorted(required_ids - covered):
        gap('paths', 'uncovered_demand', 'No seven-role declaration covers required demand: ' + demand)
    report['status'] = ('invalid' if errors else 'stale' if any(item['status'] == 'stale' for item in findings)
                        else 'gap' if findings else 'declared_path_complete')
    return report


# A consistent short name for callers using the other read-only inspectors.
inspect = inspect_paths


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-finite JSON number: ' + value)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('graph', type=Path)
    parser.add_argument('--spec', type=Path, help='Explicit path specification; defaults to graph.path_spec or an empty spec.')
    parser.add_argument('--root', type=Path, help='Local provenance root; defaults to graph parent directory.')
    args = parser.parse_args()
    try:
        graph = load_json(args.graph)
        spec = load_json(args.spec) if args.spec else graph.get('path_spec', {}) if isinstance(graph, dict) else {}
        report = inspect_paths(graph, spec, args.root if args.root is not None else args.graph.resolve().parent)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print(json.dumps({'authority': 'advisory_only', 'status': 'invalid',
                          'errors': [{'path': 'input', 'code': 'unreadable_input', 'message': str(exc)}]}))
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False))
    return 2 if report['status'] == 'invalid' else 0 if report['status'] == 'declared_path_complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
