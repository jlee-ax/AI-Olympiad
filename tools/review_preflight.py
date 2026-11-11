#!/usr/bin/env python3
"""Read current local review evidence together; never execute or update a cycle."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import contest_depth
import discovery_loop
import graph_paths
import workflow


def local_file(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('Expected a root-relative local file path')
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('File is missing or outside the selected root: ' + ascii(name))
    return path


def local_source_path(root, uri):
    """Resolve declared local URIs conservatively; never fetch external sources.

    Bare values name root-relative files, including filenames containing colons.
    File URIs may name a root-relative path or an absolute path inside root.
    URI authorities, queries and fragments are unsupported for local files.
    Explicit scheme:// URIs are external declarations and remain unverified.
    """
    if not isinstance(uri, str) or not uri:
        raise ValueError('Expected a nonempty source URI')
    if any(ord(char) < 32 or ord(char) == 127 for char in uri):
        raise ValueError('Source URI contains whitespace or control characters: ' + ascii(uri))
    explicit_uri = re.match(r'^[A-Za-z][A-Za-z0-9+.-]*://', uri)
    file_uri = uri[:5].lower() == 'file:'
    web_uri = uri.lower().startswith(('http:', 'https:'))
    if not (explicit_uri or file_uri or web_uri):
        return uri
    if ' ' in uri:
        raise ValueError('Source URI must percent-encode spaces: ' + ascii(uri))
    if re.search(r'%(?![0-9A-Fa-f]{2})', uri):
        raise ValueError('Source URI has an invalid percent escape: ' + ascii(uri))
    parsed = urlsplit(uri)
    if file_uri:
        if parsed.netloc or '?' in uri or '#' in uri:
            raise ValueError('Local file URI must have no authority, query or fragment: ' + ascii(uri))
        name = unquote(parsed.path, encoding='utf-8', errors='strict')
        if not name:
            raise ValueError('Local file URI has no path: ' + ascii(uri))
        path = Path(name)
        if path.is_absolute():
            path = path.resolve()
            if not path.is_relative_to(root):
                raise ValueError('Local file URI is outside the selected root: ' + ascii(uri))
            return str(path.relative_to(root))
        return name
    if not parsed.netloc or not parsed.hostname:
        raise ValueError('External source URI must have a host: ' + ascii(uri))
    # Accessing port also rejects malformed bracket/port declarations without IO.
    parsed.port
    return None


def load(path):
    return json.loads(path.read_text(encoding='utf-8'), parse_constant=contest_depth.reject_constant,
                      object_pairs_hook=contest_depth.unique_pairs)


def context_manifests(depth_bundle, graph, paths, semantic_review=None, sources=None, discovery_state=None):
    """Content bindings needed before a fresh aggregate workflow review."""
    values = [('depth', depth_bundle), ('graph', graph), ('paths', paths)]
    if semantic_review is not None:
        values.append(('semantic-review', semantic_review))
    if sources is not None:
        values.append(('source-catalog', sources))
    result = [{'id': 'review:' + name, 'revision': 'review-preflight-v1',
             'sha256': hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                                separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()}
            for name, value in values]
    if discovery_state is not None:
        result.append(discovery_loop.manifest(discovery_state))
    return result


def preflight(root, depth_bundle, graph, paths, state, quality_bundle=None, semantic_review=None, discovery_state=None, legacy_scope=False):
    try:
        root = Path(root).resolve()
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        return {'authority': 'advisory_only', 'status': 'invalid', 'errors': [str(exc)]}
    if (any(not isinstance(value, dict) for value in (depth_bundle, graph, paths, state)) or
            not isinstance(depth_bundle.get('target', {}), dict) or
            not isinstance(state.get('context', {}), dict)):
        return {'authority': 'advisory_only', 'status': 'invalid',
                'errors': ['Depth, graph, paths, state, target and context must be objects.']}
    blockers, errors, bindings, unverified_sources = [], [], [], []
    def block(code, detail):
        blockers.append({'code': code, 'detail': detail})
    def bind(path, expected, kind, source_id=None, uri=None):
        try:
            actual = hashlib.sha256(local_file(root, path).read_bytes()).hexdigest()
            matched = actual == expected
            binding = {'kind': kind, 'path': path, 'expected_sha256': expected,
                       'actual_sha256': actual, 'matched': matched}
            if source_id is not None:
                binding.update(source_id=source_id, uri=uri)
            bindings.append(binding)
            if not matched:
                block('stale_' + kind, path)
            return actual
        except (OSError, RuntimeError, ValueError, UnicodeError) as exc:
            block('unreadable_' + kind, str(exc))
            return None

    depth_report = contest_depth.inspect(depth_bundle)
    graph_report = graph_paths.inspect_paths(graph, paths, root)
    semantic_report = graph_paths.inspect_semantic_review(graph, paths, semantic_review, root)
    state_errors, state_warnings = workflow.validate_state(state)
    errors.extend(state_errors)
    if depth_report['errors']:
        errors.append('Invalid contest-depth bundle')
    if graph_report['status'] == 'invalid':
        errors.append('Invalid graph path declaration')
    if semantic_report['status'] == 'invalid':
        errors.append('Invalid graph semantic review')
    if semantic_review is None:
        block('missing_semantic_review', 'A current content review of each declared path is required; role declarations alone do not establish adequacy.')
    elif semantic_report['status'] != 'recorded_design_met':
        block('semantic_review_' + semantic_report['status'], 'Read the scoped content-review judgments; learner performance remains unobserved.')
    if depth_report['status'] != 'recorded_met':
        block('contest_depth_' + depth_report['status'], 'Read scoped findings; learner outcomes remain separate.')
    if graph_report['status'] != 'declared_path_complete':
        block('graph_paths_' + graph_report['status'], 'Missing or stale declared paths cannot be reused.')

    target = depth_bundle.get('target', {}) if isinstance(depth_bundle, dict) else {}
    actual = bind(target.get('artifact'), target.get('artifact_sha256'), 'artifact')
    current_manifest = state.get('context', {}).get('artifact') if isinstance(state, dict) else None
    if not isinstance(current_manifest, dict) or actual is None or current_manifest.get('sha256') != actual:
        block('workflow_artifact_stale', 'Workflow artifact digest does not bind the actual depth-review artifact.')

    declared_paths = paths.get('paths', []) if isinstance(paths, dict) else []
    declared_paths = declared_paths if isinstance(declared_paths, list) else []
    comparisons = depth_bundle.get('comparisons', [])
    for comparison in comparisons if isinstance(comparisons, list) else []:
        if not isinstance(comparison, dict):
            continue
        cid = comparison.get('id')
        matching = [p for p in declared_paths if isinstance(p, dict) and p.get('comparison_id') == cid]
        if not matching:
            block('comparison_path_missing', cid)
        elif not any(any(isinstance(v, dict) and v.get('path') == target.get('artifact') and
                         v.get('sha256') == target.get('artifact_sha256')
                         for v in p.get('provenance', {}).values())
                     for p in matching if isinstance(p.get('provenance'), dict)):
            block('comparison_artifact_unbound', cid)

    markers = [depth_report.get('synthetic'), graph_report.get('synthetic'),
               state.get('synthetic') if isinstance(state, dict) else None]
    if any(type(v) is not bool for v in markers) or len(set(markers)) != 1:
        block('synthetic_context_mismatch', 'Depth, paths and state must declare the same synthetic status.')
    discovery_report = None
    real_context = state.get('synthetic') is False
    if legacy_scope:
        block('legacy_inspection_not_readiness', 'Historical registered comparisons only; no broad readiness or completion claim is supported.')
    if discovery_state is None:
        if real_context or any(item.get('id') == 'review:discovery' for item in state.get('context', {}).get('inputs', []) if isinstance(item, dict)):
            block('discovery_missing', 'Seed an external frontier and run source discovery, direct reading, requirement extraction and actual-lesson comparison.')
    else:
        try:
            discovery_report = discovery_loop.inspect(discovery_state, root)
            if discovery_report['synthetic'] != state.get('synthetic'):
                block('discovery_synthetic_mismatch', 'Discovery and review must have the same real/synthetic declaration.')
            scope = discovery_report['scope']
            discovery_artifact = scope.get('artifact_path', scope['lesson_path'])
            if discovery_artifact != target.get('artifact'):
                block('discovery_artifact_mismatch', 'Discovery must bind the same reviewed artifact; a projection additionally needs artifact_path/artifact_sha256.')
            if not discovery_report['ready_for_review']:
                block('discovery_' + discovery_report['status'], discovery_report['queue'])
            # All actively covered demands need a graph binding. Deferred/out-of-scope
            # placement remains visible without forcing later concepts into this lesson.
            mapped = {p.get('discovery_demand_id') for p in declared_paths if isinstance(p, dict)}
            for comparison in discovery_report['comparisons']:
                did = comparison['demand_id']
                if comparison['judgment'] == 'covered' and did not in discovery_report['retired_demands'] and did not in mapped:
                    block('discovery_demand_path_missing', did)
        except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError) as exc:
            errors.append('Invalid discovery session: ' + str(exc))
    required_inputs = context_manifests(depth_bundle, graph, paths, semantic_review, state.get('sources'), discovery_state) if not errors else []
    if not state_errors:
        inputs = state['context']['inputs']
        if any(not any(all(item.get(key) == value for key, value in required.items())
                       for item in inputs) for required in required_inputs):
            block('review_context_not_bound', 'Bind required_inputs and obtain a new current-context review; copying hashes creates no acceptance.')
    records = []
    if not state_errors:
        records = workflow.recall_records(state)
        # Every declared local catalog version must still match, including
        # context-only references, unused entries and superseded record sources.
        used = {r['source_id'] for record in records for r in record['source_refs']}
        for source in sorted(state['sources'], key=lambda item: item['id']):
            sid, uri = source['id'], source['uri']
            kind = 'recalled_source' if sid in used else 'declared_source'
            try:
                path = local_source_path(root, uri)
            except (OSError, RuntimeError, ValueError, UnicodeError) as exc:
                block('unreadable_' + kind, str(exc))
                continue
            if path is None:
                unverified_sources.append({'id': sid, 'uri': uri, 'reason': 'external_uri_not_fetched'})
            else:
                bind(path, source['sha256'], kind, source_id=sid, uri=uri)

    quality_report = None
    if quality_bundle is not None:
        import quality
        try:
            quality_report = quality.evaluate(quality_bundle, root)
            if quality_report['status'] != 'passed' or not quality_report['ready_for_review']:
                block('quality_not_ready', quality_report['status'])
        except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError, OverflowError) as exc:
            errors.append('Quality evaluation unavailable: ' + str(exc))
    decision = workflow.decide(state, quality_report, discovery_report)
    if decision['status'] not in ('continue', 'noop') and decision.get('reason') != 'verified_completion_claim':
        block('workflow_' + decision['status'], decision['reason'])
    return {'authority': 'advisory_only', 'status': 'invalid' if errors else 'blocked' if blockers else 'consistent_recorded_context',
            'synthetic': markers[0], 'errors': errors, 'blockers': blockers, 'bindings': bindings,
            'required_inputs': required_inputs,
            'review_scope': 'legacy_inspection_not_ready' if legacy_scope else 'external_frontier' if discovery_state is not None else 'synthetic_registered_comparisons' if not real_context else 'discovery_required',
            'discovery': discovery_report,
            'contest_depth': depth_report, 'graph_paths': graph_report, 'semantic_review': semantic_report, 'workflow': decision,
            'quality': quality_report,
            'selective_review': quality_report.get('selective_review') if quality_report else None,
            'recall': {'record_ids': [r['id'] for r in records], 'warnings': state_warnings},
            'unverified_sources': unverified_sources,
            'limits': ['No work, review, state update, publication or scheduling is executed.',
                       'Matching bytes and declarations do not establish semantic adequacy, consent, independent judgment or learner outcomes.',
                       'Declared local provenance and every local source catalog entry are checked; external source truth, pathless manifests and omitted dependencies remain unverified.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    for name in ('depth', 'graph', 'state'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--paths', help='Missing declaration is reported as a graph gap')
    parser.add_argument('--quality')
    parser.add_argument('--discovery', help='Replayable external requirement discovery session; required for real readiness')
    parser.add_argument('--legacy-scope', action='store_true', help='Inspect historical comparisons only; always blocks readiness')
    parser.add_argument('--semantic-review', help='Current content review of each declared graph path')
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        read = lambda name: load(local_file(root, name))
        report = preflight(root, read(args.depth), read(args.graph), read(args.paths) if args.paths else {},
                           read(args.state), read(args.quality) if args.quality else None,
                           read(args.semantic_review) if args.semantic_review else None,
                           read(args.discovery) if args.discovery else None, args.legacy_scope)
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError, OverflowError) as exc:
        report = {'authority': 'advisory_only', 'status': 'invalid', 'errors': [str(exc)]}
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False))
    return 2 if report['status'] == 'invalid' else 1 if report['status'] == 'blocked' else 0


if __name__ == '__main__':
    raise SystemExit(main())
