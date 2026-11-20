"""Execute examples and check lesson content. Never fill or grade student responses."""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
import argparse, ast, base64, contextlib, hashlib, importlib.metadata, json, math, os, re, shutil, subprocess, sys, tempfile, textwrap, time
import importlib.resources
import nbformat
from nbclient import NotebookClient
from ipykernel.inprocess.manager import InProcessKernelManager
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))


def execute_inprocess(notebook):
    """The caller starts this function in a new interpreter for every notebook."""
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


if sys.argv[1:] == ['--inprocess-worker']:
    notebook = nbformat.read(sys.stdin, 4)
    with contextlib.redirect_stdout(sys.stderr):
        execute_inprocess(notebook)
    sys.stdout.write(nbformat.writes(notebook))
    sys.exit(0)


def execute(notebook, directory, inprocess):
    if inprocess:
        result = subprocess.run(
            [sys.executable, '-B', str(Path(__file__).resolve()), '--inprocess-worker'],
            input=nbformat.writes(notebook), cwd=directory, capture_output=True, text=True, timeout=420)
        if result.returncode:
            raise RuntimeError(result.stderr)
        notebook.cells = nbformat.reads(result.stdout, 4).cells
    else:
        NotebookClient(notebook, timeout=180, kernel_name='python3',
                       resources={'metadata': {'path': str(directory)}}).execute(cwd=str(directory))


def teacher_function(guide, name):
    """Read the function definition from the published teacher guide."""
    lines = guide.splitlines()
    hits = [i for i, line in enumerate(lines) if re.match(r'^\s*def ' + name + r'\(', line)]
    if len(hits) != 1:
        raise ValueError('Expected one teacher function ' + name)
    first = hits[0]
    indent = len(lines[first]) - len(lines[first].lstrip())
    stop = first + 1
    while stop < len(lines) and (not lines[stop].strip() or len(lines[stop]) - len(lines[stop].lstrip()) > indent):
        stop += 1
    source = textwrap.dedent('\n'.join(lines[first:stop]))
    namespace = {'math': math, 'np': np, 'pd': pd}
    exec(compile(ast.parse(source), '<teacher guide>', 'exec'), namespace)
    return namespace[name]


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--inprocess', action='store_true', help='Start a separate socket-free Python process per run')
parser.add_argument('--write', type=Path, default=ROOT / 'validation.json',
                    help='Write the Python-tables execution receipt here')
args = parser.parse_args()
path = ROOT / 'week01_python_tables.ipynb'
teacher_path = ROOT / 'teacher-notes.txt'
html_path = ROOT / 'week01_python_tables.html'
data_paths = [ROOT / 'data' / f for f in ('week1_plants.csv', 'week1_plants_new.csv')]
bound = [path, teacher_path, html_path, *data_paths, Path(__file__).resolve()]
hashes_before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in bound}
renderer_path = ROOT.parents[1] / 'tools/check_week01_render.py'
renderer_sha256 = hashlib.sha256(renderer_path.read_bytes()).hexdigest()
saved = nbformat.read(path, 4)
nb = nbformat.read(path, 4)
nbformat.validate(nb)
source_projection = lambda book: [{k: c.get(k) for k in ('id', 'cell_type', 'source', 'attachments')} for c in book.cells]
source_before = source_projection(nb)

# A transient final check cell tests the real executed functions/variables. It is never
# saved in the student notebook, and does not complete the student modification task.
qa = nbformat.v4.new_code_cell(r'''
from fractions import Fraction
import math
from io import StringIO
from sklearn.datasets import load_digits
source_digits = load_digits(as_frame=True)
assert source_digits.data.shape == (1797, 64) and source_digits.images.shape == (1797, 8, 8)
assert set(source_digits.target) == set(range(10))
assert sample_indices == [7, 2, 11] and pixel_features == ["pixel_2_3", "pixel_4_4"]
expected_pixels = source_digits.data.loc[sample_indices, pixel_features].to_numpy(dtype=int)
np.testing.assert_array_equal(H, expected_pixels)
np.testing.assert_array_equal(H[:, 0], source_digits.images[sample_indices, 2, 3])
np.testing.assert_array_equal(H[:, 1], source_digits.images[sample_indices, 4, 4])
assert sample_targets == source_digits.target.loc[sample_indices].tolist() == [7, 2, 1]
assert H[1, 0] == 13
np.testing.assert_allclose(H.mean(axis=0), [9, 46/3])
np.testing.assert_allclose(H.mean(axis=1), [7.5, 14, 15])
assert list(practice_indices) == [47, 10, 56, 30, 21, 36]
observations = pd.read_csv(StringIO(measure_csv))
labels_by_id = pd.read_csv(StringIO(labels_csv))
expected_practice = source_digits.data.loc[practice_indices, ["pixel_3_5", "pixel_2_3"]]
assert observations.sample_index.tolist() == list(practice_indices)
assert labels_by_id.sample_index.tolist() == list(reversed(practice_indices))
np.testing.assert_array_equal(observations[expected_practice.columns].to_numpy(), expected_practice.to_numpy())
joined_digits = observations.merge(labels_by_id, on="sample_index", how="left", validate="one_to_one")
assert joined_digits.digit.tolist() == source_digits.target.loc[practice_indices].tolist()
np.testing.assert_allclose(joined_digits.groupby("digit").pixel_2_3.mean().loc[[0,1]], [22/3, 14])
assert np.histogram(joined_digits.pixel_2_3, bins=[0, 8, 12, 16])[0].tolist() == [1, 2, 3]
missing_label = observations.merge(labels_by_id[labels_by_id.sample_index.ne(30)], on="sample_index", how="left", validate="one_to_one")
assert missing_label.loc[missing_label.digit.isna(), "sample_index"].tolist() == [30]
try:
    observations.merge(pd.concat([labels_by_id, labels_by_id[labels_by_id.sample_index.eq(47)]]),
                       on="sample_index", validate="one_to_one")
except pd.errors.MergeError:
    pass
else:
    raise AssertionError("A repeated label ID was accepted")
assert csv_path.is_file() and new_path.is_file()
from tempfile import TemporaryDirectory
with TemporaryDirectory(prefix="tables-data-variants-") as directory:
    trial = Path(directory) / "plants.csv"
    first_row = csv_text.splitlines()[1]
    _, separator, remainder = first_row.partition(",")
    wrong = csv_text.replace(first_row, "changed-source-id" + separator + remainder, 1)
    assert wrong != csv_text
    trial.write_text(wrong, encoding="utf-8")
    before_bytes = trial.read_bytes()
    try:
        load_verified_example_csv(trial, csv_text)
    except ValueError:
        pass
    else:
        raise AssertionError("A changed physical row was accepted")
    assert trial.read_bytes() == before_bytes
    try:
        load_verified_example_csv(Path(directory), csv_text)
    except ValueError:
        pass
    else:
        raise AssertionError("A directory was accepted as a data file")
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
before = digit_rows.copy(deep=True)
selected = require_columns(digit_rows, list(reversed(pixel_features)))
assert list(selected.columns) == list(reversed(pixel_features))
assert selected.shape == (3, 2) and digit_rows.equals(before)
try:
    require_columns(digit_rows, [pixel_features[0], 'unknown_pixel'])
except KeyError:
    pass
else:
    raise AssertionError("The missing pixel column was accepted")
assert features.shape == (3, 2) and target.shape == (3,)
assert pixel_mask.tolist() == [False, True, True]
assert digit_rows[pixel_features[0]].tolist() == [0, 13, 14]
assert pixel_copy.loc[pixel_copy[pixel_features[0]].isna(), "sample_index"].tolist() == [11]
assert pixel_copy.loc[pixel_copy[pixel_features[0]].eq(0), "sample_index"].tolist() == [7]
assert list(recorded_pixels) == [0, 13] and recorded_pixels.mean() == 6.5
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
for_target = source_digits.frame.loc[[0, 20, 48, 1, 11, 42], ["pixel_2_3", "pixel_3_5", "target"]]
assert original_pairs.equals(for_target)
assert original_pairs.index[original_pairs.pixel_3_5.ne(permuted_pairs.pixel_3_5)].tolist() == [20, 1]
assert sorted(original_pairs.pixel_3_5) == sorted(permuted_pairs.pixel_3_5)
assert original_pairs.pixel_2_3.equals(permuted_pairs.pixel_2_3)
assert digit_summary.loc[[0, 1], "mean"].tolist() == [9, 8]
assert digit_summary.loc[[0, 1], ["size", "count"]].to_numpy().tolist() == [[3, 3], [3, 3]]
assert (grid + column_offsets).tolist() == [[3, 14], [7, 18], [11, 22]]
assert (grid + row_offsets).tolist() == [[3, 5], [16, 18], [110, 112]]
assert dot_features == pixel_features
np.testing.assert_array_equal(pixel_values, source_digits.data.loc[2, pixel_features].to_numpy())
np.testing.assert_array_equal(pixel_weights, [1, -1])
np.testing.assert_array_equal(pixel_products, [13, -15])
assert pixel_difference == sum(int(x) * int(w) for x, w in zip(pixel_values, pixel_weights)) == -2
control = batch_source.copy(deep=True)
assert batch_contrasts.index.tolist() == [2, 7, 11] and batch_contrasts.tolist() == [-2, -15, -2]
changed_batch = control.iloc[::-1].copy()
changed_batch.loc[2, "pixel_2_3"] -= 3
changed = pixel_contrasts(changed_batch)
assert changed.index.tolist() == [11, 7, 2] and changed.tolist() == [-2, -15, -5]
assert batch_source.equals(control)
print('Actual executed example/function assertions passed')
''')
qa.id = 'transient-validator-assertions'
nb.cells.append(qa)
started = time.monotonic()
with tempfile.TemporaryDirectory(prefix='week01-tables-files-') as temp:
    physical = Path(temp)
    (physical / 'data').mkdir()
    for data_path in data_paths:
        shutil.copyfile(data_path, physical / 'data' / data_path.name)
    execute(nb, physical, args.inprocess)
elapsed = time.monotonic() - started
qa_output = ''.join(o.get('text', '') for o in nb.cells.pop().outputs)
assert 'assertions passed' in qa_output
assert source_projection(nb) == source_before
nbformat.validate(nb)
# Leave the supplied notebook bytes unchanged; the executed copy is in memory.

# Teacher-key modification is tested independently of unfilled student cells.
teacher = teacher_path.read_text(encoding='utf-8')
import statistics
shifted_mean = teacher_function(teacher, 'shifted_mean')
for values, offset in [([1, 3, 8], 2), ([7], 2), ([-5, 1], -3), ([0, 0], 0)]:
    assert shifted_mean(values, offset) == statistics.mean(v + offset for v in values)
try:
    shifted_mean([], 2)
    raise AssertionError('Teacher key must preserve empty-list error')
except ValueError:
    pass

recorded_mean = teacher_function(teacher, 'recorded_mean')
for values, count, average in [([2,None,8,10], 3, 20/3), ([None,None,0], 1, 0), ([None], 0, None)]:
    before = values.copy()
    n, mean = recorded_mean(values)
    assert n == count and (mean is None if average is None else math.isclose(mean, average))
    assert values == before

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
assert not any(ord(x) < 32 and x not in '\n\t\r' for x in markdown)
assert any('student-code' in c.metadata.get('tags', []) for c in nb.cells)
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
            assert base64.b64decode(png, validate=True).startswith(b'\x89PNG\r\n\x1a\n')
            png_cells.append(index)
    for attachment in cell.get('attachments', {}).values():
        if 'image/png' in attachment:
            assert base64.b64decode(attachment['image/png'], validate=True).startswith(b'\x89PNG\r\n\x1a\n')
assert len(png_cells) == 5
assert sum(len(c.get('attachments', {})) for c in nb.cells) == 2

from check_week01_render import verify
render_check = verify(saved, nb, html_path.read_text(encoding='utf-8'), stem=path.stem)
with tempfile.TemporaryDirectory(prefix='week01-tables-standalone-') as temp:
    standalone = Path(temp)
    assert not (standalone / 'data').exists()
    fallback = nbformat.read(path, 4)
    fallback.cells.append(nbformat.v4.new_code_cell(
        "assert not csv_path.exists() and not new_path.exists()\n"
        "pd.testing.assert_frame_equal(plants, pd.read_csv(StringIO(csv_text)))\n"
        "pd.testing.assert_frame_equal(new_plants, pd.read_csv(StringIO(new_csv_text)))"))
    execute(fallback, standalone, args.inprocess)
assert hashes_before == {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in bound}
assert renderer_sha256 == hashlib.sha256(renderer_path.read_bytes()).hexdigest()
report = {
    'canonical_renderer_sha256': renderer_sha256,
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'notebook': path.name, 'revision': manifest.get('current_release', {}).get('revision', manifest['revision']),
    'historical_tables_revision': manifest['revision'], 'source_sha256': hashes_before,
    'render_validation': render_check, 'input_files_unchanged': True,
    'distinct_interpreters_for_physical_and_fallback_runs': True,
    'skills_reference_commit': manifest['skills_reference_commit'],
    'nbformat_validation': 'passed', 'top_to_bottom_execution': 'passed',
    'execution_method': 'fresh IPython InProcessKernelManager per run' if args.inprocess else 'fresh separate nbclient kernel per run',
    'execution_seconds': round(elapsed, 3), 'cells': len(nb.cells),
    'code_cells': len(codes), 'executed_code_cells': len(codes), 'error_outputs': 0,
    'actual_function_and_state_assertions': 'passed', 'teacher_modification_key_tests': 'passed',
    'independent_fraction_arithmetic': 'passed', 'csv_mask_shape_missing_and_merge_checks': 'passed',
    'plot_output_cells': png_cells, 'plot_output_count': len(png_cells), 'embedded_diagrams': 2,
    'digits_source_sample_axes_and_data_join': 'passed', 'student_answers': 'blank_not_assessed',
    'student_mastery': 'not_observed', 'classroom_timing': 'estimated_not_observed',
    'teacher_only_class_total': 120, 'teacher_only_time_minutes': totals,
    'baseline_required_homework_minutes': [300, 420], 'revised_homework_time': 'not_estimated_or_observed',
    'standalone_without_csv_files': 'passed', 'changed_csv_rejected_without_rewrite': True,
    'allocation_scope': 'The class blocks and baseline homework range come from the retained historical tables plan.',
    'visual_inspection': 'not_performed_by_script', 'browser_preview': 'not_performed_by_script',
    'digits_dataset': {'loader': 'sklearn.datasets.load_digits', 'images': 1797, 'pixels': 64,
        'packaged_csv_gz_sha256': hashlib.sha256(importlib.resources.files('sklearn.datasets.data').joinpath('digits.csv.gz').read_bytes()).hexdigest(),
        'source_rows': [7, 2, 11], 'class_labels': [7, 2, 1], 'worked_features': ['pixel_2_3', 'pixel_4_4'],
        'fresh_rows': [47, 10, 56, 30, 21, 36]},
    'packages': {p: (importlib.metadata.version(p) if p != 'jupyterlab' or importlib.util.find_spec('jupyterlab') else 'not installed') for p in ('numpy', 'pandas', 'scikit-learn', 'matplotlib', 'seaborn', 'jupyterlab', 'nbclient', 'nbformat', 'ipykernel')},
    'notebook_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'persisted_notebook': 'unchanged; executed copy held in memory',
    'html_sha256': hashlib.sha256((ROOT / 'week01_python_tables.html').read_bytes()).hexdigest(),
    'source_attachment_projection_sha256': hashlib.sha256(json.dumps(source_projection(nb), ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
    'source_projection_unchanged_by_execution': True, 'schedules_created': False,
}
args.write.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
