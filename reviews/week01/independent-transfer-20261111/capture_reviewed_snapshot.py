#!/usr/bin/env python3
"""Capture only this independently checked snapshot; refuse altered review evidence."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[3]
out = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'tools'))
import contest_depth
import graph_paths
import quality
import review_preflight
import workflow

expected = {
    'lessons/week01/week01_python_tables.ipynb': 'ee8279b1af621c22da5094d765ea424171c5448527d931b943a6a30cb7c2f6b7',
    'lessons/week01/teacher-notes.txt': 'bb2c8e3777dac240197fa422e8ca067379ca038dc81a2a2e35c82e4b7c41b8ec',
    'lessons/week01/validation.json': '1d610414e48a02ba14d81b13eb86e27463b3d740ab71a20e6c49ffe2ac8528b7',
    'reviews/week01/independent-transfer-20261111/source-brief.md': 'dc13d394c39c2e16361341cfb61a9c2ecf2342b47e51b5a0b1ae6ffb03e4b1c7',
    'reviews/week01/independent-transfer-20261111/independent-review.md': '02b1c89449b2ce5c32102752e95955cad0aadfc7f3629a6509328a98bd8eff57',
    'reviews/week01/independent-transfer-20261111/graph.json': 'de4c9556a2b93a30205f290062c668dca4a82871a32fe9b05960dd067265403d',
    'reviews/week01/independent-transfer-20261111/paths.json': 'ae5f2cf2a01dce72005a063d8bcb91badb80d5d11b836971c13edf77b497b4b8',
    'reviews/week01/independent-transfer-20261111/content-check.json': '082bf99c0b3428dc173a66450d4d2a2a4b5c067dec569ad3ca5f855f18a814f8',
}
def sha(p):
    return hashlib.sha256((root / p).read_bytes()).hexdigest()
def read(name):
    return json.loads((out / name).read_text())
def save(name, value):
    (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
for name, digest in expected.items():
    if sha(name) != digest:
        raise SystemExit('Refusing to reuse a review for changed evidence: ' + name)
book = 'lessons/week01/week01_python_tables.ipynb'
depth = read('depth.json')
depth['target']['artifact_sha256'] = sha(book)
for source in depth['problem_sources']:
    if source['id'] == 'example-knn':
        source['read_extent'] = 'Question 2 function input/output shapes, majority-vote tie rule, and recommendation to use broadcasting for distance calculation'
save('depth.json', depth)
depth_report = contest_depth.inspect(depth)
save('depth-inspection.json', depth_report)
if depth_report['errors']:
    raise SystemExit('Invalid depth record: ' + repr(depth_report['errors']))
graph, paths = read('graph.json'), read('paths.json')
semantic = read('semantic-review.json')
semantic['graph_sha256'] = graph_paths.canonical_sha256(graph)
semantic['path_spec_sha256'] = graph_paths.canonical_sha256(paths)
semantic['reviewer']['method'] = ('Separate reviewer read exact notebook, teacher keys and final five source-brief paths, checked official references and independently executed calculations; GPT-6.1 Terra Max requested, runtime identity not separately attested.')
locators = {'traceback':'표의 traceback 행', 'chart':'표의 그래프 행', 'broadcast':'표의 broadcasting 행', 'variance':'표의 분산 행', 'merge':'표의 병합 행'}
by_id = {item['id']: item for item in paths['paths']}
review_path = 'reviews/week01/independent-transfer-20261111/independent-review.md'
for item in semantic['comparisons']:
    path = by_id[item['path_id']]
    for dimension in ('problem_specific_key', 'feedback', 'independent_assessment'):
        role = 'independent_assessment' if dimension == 'independent_assessment' else 'feedback'
        src = path['provenance'][role]
        item[dimension]['evidence'] = [
            {key: src[key] for key in ('path', 'sha256', 'locator')},
            {'path': review_path, 'sha256': sha(review_path), 'locator': locators[item['comparison_id']]},
        ]
save('semantic-review.json', semantic)
semantic_report = graph_paths.inspect_semantic_review(graph, paths, semantic, root)
save('semantic-inspection.json', semantic_report)
if semantic_report['status'] != 'recorded_design_met':
    raise SystemExit('Semantic record not current: ' + repr(semantic_report))
bundle = quality.load(out / 'quality.json')
bundle['artifact']['sha256'] = sha(book)
units = {unit['id']: unit for unit in bundle['units']}
for unit in units.values():
    unit['execution']['artifact_sha256'] = sha(book)
    for evidence in unit['execution']['evidence']:
        evidence['sha256'] = sha(evidence['path'])
for dep in bundle['dependencies']:
    if dep['id'] in ('followup:teacher-notes', 'followup:source-brief'):
        dep['sha256'] = sha(dep['path'])
    if dep['id'] in units:
        dep['sha256'] = quality.digest(units[dep['id']])
save('quality.json', bundle)
quality_report = quality.evaluate(bundle, root)
save('quality-evaluation.json', quality_report)
state = read('workflow.json')
state['context']['artifact']['sha256'] = sha(book)
for source in state['sources']:
    if source['id'] in ('followup:source-brief', 'followup:execution', 'followup:content-check', 'followup:independent-review'):
        source['sha256'] = sha(source['uri'])
now = datetime.now(timezone.utc)
request = datetime.fromisoformat('2026-11-11T02:02:58.415376+00:00')
checkpoint = datetime.fromisoformat(read('checkpoint.json')['checkpoint_utc'])
state['usage']['elapsed_minutes'] = int((now-request).total_seconds()//60)
state['usage']['minutes_since_checkpoint'] = int((now-checkpoint).total_seconds()//60)
state['snapshot_note'] = ('30-minute manual checkpoint recorded at 2026-11-11T02:33:41.661809+00:00; counters captured at ' + now.isoformat() + '. Counters must be refreshed on resume. Criteria and finite budgets remain unagreed.')
required = {
    'quality:bundle': {'id':'quality:bundle','revision':quality_report['revision'],'sha256':quality_report['bundle_sha256']},
    'quality:criteria': {'id':'quality:criteria','revision':quality_report['specification_revision'],'sha256':quality_report['specification_sha256']},
    'quality:evaluator': {'id':'quality:evaluator','revision':'quality-v1','sha256':quality_report['evaluator_sha256']},
}
required.update({x['id']: x for x in review_preflight.context_manifests(depth, graph, paths, semantic, state['sources'])})
state['context']['inputs'] = [required.pop(x['id'], x) for x in state['context']['inputs']]
state['context']['inputs'].extend(required.values())
errors, warnings = workflow.validate_state(state)
if errors:
    raise SystemExit('Invalid workflow state: ' + repr(errors))
save('workflow.json', state)
result = review_preflight.preflight(root, depth, graph, paths, state, bundle, semantic_review=semantic)
save('preflight.json', result)
print(json.dumps({'depth':depth_report['status'], 'semantic':semantic_report['status'], 'quality':quality_report['status'], 'workflow_errors':errors, 'workflow_warnings':warnings, 'preflight':result['status'], 'blockers':result['blockers'], 'errors':result['errors'], 'elapsed_minutes':state['usage']['elapsed_minutes'], 'minutes_since_checkpoint':state['usage']['minutes_since_checkpoint']},ensure_ascii=False,indent=2))
