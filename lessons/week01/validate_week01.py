"""Execute examples and check lesson content. Never fill or grade student responses."""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
import argparse, base64, hashlib, importlib.metadata, json, math, os, re, time
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from ipykernel.inprocess.manager import InProcessKernelManager
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
FIGDIR = ROOT / '.validation'
FIGDIR.mkdir(exist_ok=True)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--inprocess', action='store_true', help='Use a fresh socket-free IPython kernel')
args = parser.parse_args()
path = ROOT / 'week01_python_tables.ipynb'
nb = nbformat.read(path, 4)
nbformat.validate(nb)
source_projection = lambda book: [{k: c.get(k) for k in ('id', 'cell_type', 'source', 'attachments')} for c in book.cells]
source_before = source_projection(nb)


def execute(notebook, directory):
    if not args.inprocess:
        NotebookClient(notebook, timeout=180, kernel_name='python3',
                       resources={'metadata': {'path': str(directory)}}).execute()
        return
    previous = Path.cwd()
    os.chdir(directory)
    manager = InProcessKernelManager()
    manager.start_kernel()
    client = manager.client()
    client.start_channels()
    try:
        for cell in notebook.cells:
            if cell.cell_type != 'code':
                continue
            client.execute(cell.source, store_history=True)
            reply = client.get_shell_msg(timeout=180)
            if reply['content']['status'] != 'ok':
                raise RuntimeError(reply['content'])
            cell.execution_count = reply['content']['execution_count']
            cell.outputs = []
            while True:
                message = client.get_iopub_msg(timeout=180)
                kind = message['msg_type']
                if kind == 'status' and message['content'].get('execution_state') == 'idle':
                    break
                if kind in ('stream', 'display_data', 'execute_result', 'error'):
                    cell.outputs.append(nbformat.v4.output_from_msg(message))
            if any(output.output_type == 'error' for output in cell.outputs):
                raise RuntimeError('Execution error in cell ' + cell.id)
    finally:
        client.stop_channels()
        manager.shutdown_kernel()
        os.chdir(previous)


# A transient final check cell tests the real executed functions/variables. It is never
# saved in the student notebook, and does not complete the student modification task.
qa = nbformat.v4.new_code_cell(r'''
from fractions import Fraction
import math
assert mean_of_numbers([1, 3, 8]) == 4
assert mean_of_numbers([7]) == 7
assert mean_of_numbers([-5, 1]) == -2
try:
    mean_of_numbers([])
    raise AssertionError('Empty input must fail')
except ValueError:
    pass
assert average == 4 and reconstructed_total == 12
assert returned == 6 and shown is None
before = plants.copy(deep=True)
selected = require_columns(plants, ['height_cm', 'pot_id'])
assert selected.columns.tolist() == ['height_cm', 'pot_id']
assert selected.shape == (6, 2) and plants.equals(before)
try:
    require_columns(plants, ['pot_id', 'height'])
    raise AssertionError('Missing column must fail')
except KeyError as error:
    assert 'height' in str(error)
assert features.shape == (6, 2) and target.shape == (6,)
assert plants[['height_cm']].shape == (6, 1)
assert enough_light.tolist() == [False, False, True, True, False, True]
assert plants.loc[enough_light, ['pot_id', 'sunlight_hours', 'height_cm']].shape == (3, 3)
assert plants.loc[plants.sunlight_hours.ge(6), 'pot_id'].tolist() == ['P04', 'P06']
assert changed_plants.loc[changed_plants.sunlight_hours.le(4), ['pot_id', 'measured_height_cm']].shape == (3, 2)
assert plants.loc[plants.water_ml.isna(), 'pot_id'].tolist() == ['P03']
assert plants.loc[plants.water_ml.eq(0), 'pot_id'].tolist() == ['P01']
assert len(recorded_water) == 5 and recorded_water.sum() == 140 and recorded_water.mean() == 28
assert plants.shape == (6, 5) and plants.water_ml.isna().sum() == 1
assert math.isnan(pd.Series([float('nan'), float('nan')]).mean())
assert A.shape == (3, 2) and A[1, 0] == 6
manual_columns = [sum(row[j] for row in A.tolist()) / len(A) for j in range(A.shape[1])]
manual_rows = [sum(row) / len(row) for row in A.tolist()]
assert manual_columns == [6, 8] and manual_rows == [3, 7, 11]
assert np.allclose(column_means, manual_columns) and column_means.shape == (2,)
assert np.allclose(row_means, manual_rows) and row_means.shape == (3,)
assert A.mean() == 7
assert B.shape == (2, 3) and B[1, 2] == 11
assert B.mean(axis=0).tolist() == [2, 6, 10]
assert B.mean(axis=1).tolist() == [5, 7]
assert math.isclose(B[0].var(ddof=0), float(Fraction(32, 3)))
assert math.isclose(lengths.var(ddof=0), float(Fraction(8, 3)))
assert math.isclose(pd.Series(lengths).var(ddof=0), float(Fraction(8, 3)))
assert math.isclose((lengths + 10).var(ddof=0), lengths.var(ddof=0))
assert math.isclose(np.tile(lengths, 2).var(ddof=0), lengths.var(ddof=0))
assert np.array([7]).var(ddof=0) == 0
assert new_plants.loc[new_plants.light_hours.ge(4), 'sample_id'].tolist() == ['Q03', 'Q04']
assert new_plants.water_amount_ml.count() == 3 and new_plants.water_amount_ml.mean() == 20
assert new_plants.loc[new_plants.water_amount_ml.isna(), 'sample_id'].tolist() == ['Q02']
assert new_plants.loc[new_plants.water_amount_ml.eq(0), 'sample_id'].tolist() == ['Q01']
joined = new_plants.merge(site_notes, on='site', how='left', validate='many_to_one')
assert len(joined) == 4 and joined.note.isna().sum() == 0
try:
    new_plants.merge(pd.concat([site_notes, site_notes.iloc[:1]]), on='site', how='left', validate='many_to_one')
    raise AssertionError('Duplicate lookup key must fail')
except pd.errors.MergeError:
    pass
unknown_site = new_plants.copy()
unknown_site.loc[0, 'site'] = '미등록'
joined_unknown = unknown_site.merge(site_notes, on='site', how='left', validate='many_to_one')
assert len(joined_unknown) == 4 and joined_unknown.note.isna().sum() == 1
assert np.histogram(plants.height_cm, bins=[6, 10, 14, 18, 22])[0].tolist() == [1, 3, 1, 1]
assert np.allclose(place_summary['mean'].to_numpy(), sorted([float(Fraction(28, 3)), float(Fraction(44, 3))]))
assert (grid + column_offsets).tolist() == [[3, 14], [7, 18], [11, 22]]
assert (grid + row_offsets).tolist() == [[3, 5], [16, 18], [110, 112]]
assert quantities @ unit_prices == 3500
assert np.array([1, 4, 2]) @ np.array([800, 500, 1200]) == 5200
shifted_table = plants.copy(deep=True)
shifted_table['sunlight_hours'] = shifted_table.sunlight_hours + 1
assert (shifted_table.sunlight_hours - plants.sunlight_hours).eq(1).all()
assert shifted_table.height_cm.equals(plants.height_cm)
print('Actual executed example/function assertions passed')
''')
qa.id = 'transient-validator-assertions'
nb.cells.append(qa)
started = time.monotonic()
execute(nb, ROOT)
elapsed = time.monotonic() - started
qa_output = ''.join(o.get('text', '') for o in nb.cells.pop().outputs)
assert 'assertions passed' in qa_output
assert source_projection(nb) == source_before
nbformat.validate(nb)
# Leave the supplied notebook bytes unchanged; the executed copy is in memory.

# Teacher-key modification is tested independently of unfilled student cells.
teacher = (ROOT / 'teacher-notes.txt').read_text()
match = re.search(r'^  def shifted_mean\(numbers, offset\):\n(?:^  .*\n|^\n)+', teacher, re.M)
assert match is not None
import textwrap, statistics
key_namespace = {}
exec(textwrap.dedent(match.group()).strip(), key_namespace)
shifted_mean = key_namespace['shifted_mean']
for values, offset in [([1, 3, 8], 2), ([7], 2), ([-5, 1], -3), ([0, 0], 0)]:
    assert shifted_mean(values, offset) == statistics.mean(v + offset for v in values)
try:
    shifted_mean([], 2)
    raise AssertionError('Teacher key must preserve empty-list error')
except ValueError:
    pass

# Independent exact arithmetic checks do not reuse NumPy's variance implementation.
for values, expected in [([2, 4, 6], Fraction(8, 3)), ([12, 14, 16], Fraction(8, 3)),
                         ([1, 5, 9], Fraction(32, 3)), ([3, 4, 5], Fraction(2, 3))]:
    mean = Fraction(sum(values), len(values))
    assert sum((Fraction(v) - mean)**2 for v in values) / len(values) == expected

manifest = json.loads((ROOT / 'lesson-manifest.json').read_text())
blocks = manifest['class_blocks']
assert blocks[0]['start'] == 0 and blocks[-1]['end'] == 120
assert all(a['end'] == b['start'] for a, b in zip(blocks, blocks[1:]))
totals = {k: sum(b['end'] - b['start'] for b in blocks if b['type'] == k)
          for k in ('theory', 'noncoding', 'coding')}
assert totals == {'theory': 20, 'noncoding': 20, 'coding': 80}
assert [sum(r[i] for r in manifest['homework_ranges_minutes']) for i in (0, 1)] == [300, 420]
assert manifest['schedules_created'] is False
markdown = '\n'.join(c.source for c in nb.cells if c.cell_type == 'markdown')
assert not re.search(r'\d+\s*[~∼-]\s*\d+\s*(분|시간)|\d+\s*분|SHA256|Humanizer|휴머나이저|승인 계획|걸린 시간|실제 시간', markdown, re.I)
assert not re.search(r'\b[0-9a-f]{40,64}\b', markdown)
assert not (ROOT / 'README.md').exists()
assert not any(ord(x) < 32 and x not in '\n\t\r' for x in markdown)
assert r'9\\3' in next(c.source for c in nb.cells if c.id == 'd60c3acd')
assert sum('student-response' in c.get('metadata', {}).get('tags', []) for c in nb.cells) >= 10
for c in nb.cells:
    if 'student-code' in c.get('metadata', {}).get('tags', []):
        assert all(not line.strip() or line.lstrip().startswith('#') for line in c.source.splitlines())
codes = [c for c in nb.cells if c.cell_type == 'code']
assert all(isinstance(c.execution_count, int) for c in codes)
assert not [o for c in codes for o in c.outputs if o.output_type == 'error']
png_cells = []
for index, cell in enumerate(nb.cells):
    for output in cell.get('outputs', []):
        png = output.get('data', {}).get('image/png')
        if png:
            (FIGDIR / f'figure_cell_{index:02}.png').write_bytes(base64.b64decode(png))
            png_cells.append(index)
    for name, attachment in cell.get('attachments', {}).items():
        if 'image/png' in attachment:
            (FIGDIR / name).write_bytes(base64.b64decode(attachment['image/png']))
assert len(png_cells) == 5
assert sum(len(c.get('attachments', {})) for c in nb.cells) == 2

exporter = HTMLExporter()
exporter.exclude_input_prompt = True
exporter.exclude_output_prompt = True
html, _ = exporter.from_notebook_node(nb)
html = html.replace('</head>', "<style>body{font-family:'Noto Sans CJK KR','Noto Sans CJK JP',sans-serif}.jp-RenderedHTMLCommon{font-size:16px;line-height:1.75}.jp-Notebook{max-width:1100px;margin:auto}.jp-RenderedHTMLCommon img{max-width:100%;height:auto}</style></head>")
(ROOT / 'week01_python_tables.html').write_text(html, encoding='utf-8')
standalone = FIGDIR / 'standalone-check'
standalone.mkdir(exist_ok=True)
assert not (standalone / 'data').exists()
fallback = nbformat.read(path, 4)
execute(fallback, standalone)
fallback_text = ' '.join(o.get('text', '') for c in fallback.cells for o in c.get('outputs', []))
assert '노트북에 포함된 예제 (외부 파일 없음)' in fallback_text
report = {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'notebook': path.name, 'revision': manifest['revision'],
    'skills_reference_commit': manifest['skills_reference_commit'],
    'nbformat_validation': 'passed', 'top_to_bottom_execution': 'passed',
    'execution_method': 'fresh IPython InProcessKernelManager per run' if args.inprocess else 'fresh separate nbclient kernel per run',
    'execution_seconds': round(elapsed, 3), 'cells': len(nb.cells),
    'code_cells': len(codes), 'executed_code_cells': len(codes), 'error_outputs': 0,
    'actual_function_and_state_assertions': 'passed', 'teacher_modification_key_tests': 'passed',
    'independent_fraction_arithmetic': 'passed', 'csv_mask_shape_missing_and_merge_checks': 'passed',
    'plot_output_cells': png_cells, 'plot_output_count': len(png_cells), 'embedded_diagrams': 2,
    'student_text_meta_removal': 'passed', 'student_answers': 'blank_not_assessed',
    'student_mastery': 'not_observed', 'classroom_timing': 'estimated_not_observed',
    'teacher_only_class_total': 120, 'teacher_only_time_minutes': totals,
    'baseline_required_homework_minutes': [300, 420], 'revised_homework_time': 'not_estimated_or_observed',
    'standalone_without_csv_files': 'passed',
    'visual_inspection': 'not_performed_by_script', 'browser_preview': 'not_performed_by_script',
    'packages': {p: (importlib.metadata.version(p) if p != 'jupyterlab' or importlib.util.find_spec('jupyterlab') else 'not installed') for p in ('numpy', 'pandas', 'matplotlib', 'seaborn', 'jupyterlab', 'nbclient', 'nbformat', 'ipykernel')},
    'notebook_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'persisted_notebook': 'unchanged; executed copy held in memory',
    'html_sha256': hashlib.sha256((ROOT / 'week01_python_tables.html').read_bytes()).hexdigest(),
    'source_attachment_projection_sha256': hashlib.sha256(json.dumps(source_projection(nb), ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
    'source_projection_unchanged_by_execution': True, 'schedules_created': False,
}
(ROOT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
