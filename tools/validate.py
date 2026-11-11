#!/usr/bin/env python3
"""Check a proposed graph's basic structure; no network access or mutation."""
import json
import sys
from pathlib import Path

NODE_TYPES = {'request', 'skill', 'artifact', 'evidence', 'decision', 'review'}
STATUSES = {'proposed', 'planned', 'in_progress', 'blocked', 'completed', 'verified', 'superseded'}
EDGE_TYPES = {'depends_on', 'supports', 'revises', 'informs'}


def validate(graph):
    errors, warnings = [], []
    if not isinstance(graph, dict):
        return ['graph must be an object'], []
    nodes, edges = graph.get('nodes'), graph.get('edges')
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return ['nodes and edges must be arrays'], []
    ids, dependencies = set(), {}
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f'node {i}: must be an object'); continue
        nid = node.get('id')
        if not isinstance(nid, str) or not nid.strip():
            errors.append(f'node {i}: id must be nonempty'); continue
        if any(0xD800 <= ord(char) <= 0xDFFF for char in nid):
            errors.append(f'node {i}: id contains invalid Unicode surrogate'); continue
        if nid in ids:
            errors.append(f'node {i}: duplicate id {nid}')
        ids.add(nid)
        if not isinstance(node.get('type'), str) or node.get('type') not in NODE_TYPES: errors.append(f'node {nid}: invalid type')
        if not isinstance(node.get('status'), str) or node.get('status') not in STATUSES: errors.append(f'node {nid}: invalid status')
        if not isinstance(node.get('label'), str) or not node['label'].strip(): errors.append(f'node {nid}: label must be nonempty')
        dependencies.setdefault(nid, [])
    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f'edge {i}: must be an object'); continue
        src, dst, typ = edge.get('from'), edge.get('to'), edge.get('type')
        if not isinstance(src, str) or src not in ids: errors.append(f'edge {i}: unknown source')
        if not isinstance(dst, str) or dst not in ids: errors.append(f'edge {i}: unknown target')
        if not isinstance(typ, str) or typ not in EDGE_TYPES: errors.append(f'edge {i}: invalid type')
        if typ == 'depends_on' and isinstance(src, str) and isinstance(dst, str) and src in ids and dst in ids:
            dependencies[src].append(dst)
    # Iterative DFS avoids recursion limits. Report dependency cycles; do not reject
    # ordinary feedback cycles or mutate any data.
    colors = {node: 0 for node in ids}
    for root in sorted(ids):
        if colors[root]: continue
        colors[root] = 1
        stack = [(root, iter(dependencies[root]))]
        while stack:
            node, children = stack[-1]
            try: child = next(children)
            except StopIteration:
                colors[node] = 2; stack.pop(); continue
            if colors[child] == 1:
                warnings.append(f'dependency cycle detected: {node} -> {child}')
            elif colors[child] == 0:
                colors[child] = 1; stack.append((child, iter(dependencies[child])))
    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print('usage: python3 tools/validate.py graph.json', file=sys.stderr); return 2
    try:
        graph = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f'error: {exc}', file=sys.stderr); return 2
    errors, warnings = validate(graph)
    for message in errors: print('ERROR:', message)
    for message in warnings: print('WARNING:', message)
    print(f'{len(errors)} error(s), {len(warnings)} warning(s)')
    return 1 if errors else 0

if __name__ == '__main__':
    raise SystemExit(main())
