#!/usr/bin/env python3
"""Verify local student HTML against the exact supplied notebook, not learner work."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote

import nbformat
from bs4 import BeautifulSoup
from nbconvert import HTMLExporter

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument('--execution-dir', type=Path, required=True)
p.add_argument('--refresh-html', action='store_true')
a = p.parse_args()
lesson = ROOT / 'lessons/week01'
source = lesson / 'week01_integrated.ipynb'
html_path = lesson / 'week01_integrated.html'
expected = '59ca974390172e4ce3339260bec23dd39a449c0b1d36e053997e2d5d8b34bb44'
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(source.read_bytes()) == expected
book = nbformat.read(source, as_version=4)
nbformat.validate(book)
executed = nbformat.read(a.execution_dir / 'integrated-executed.ipynb', as_version=4)
execution = json.loads((a.execution_dir / 'integrated-execution.json').read_text())
assert execution['status'] == 'passed' and execution['source_sha256'] == expected
assert execution['code_cells_executed'] == 22 and not execution['errors']
projection = lambda b: [{k: c.get(k) for k in ('id', 'cell_type', 'source', 'attachments')} for c in b.cells]
assert projection(book) == projection(executed)
# Prompt execution counters and PNG renderer versions are not calculation results.
normalized = lambda o: {k: v for k, v in o.items() if k != 'execution_count'}
output_differences = []
for old, new in zip(book.cells, executed.cells):
    if old.cell_type != 'code':
        continue
    assert len(old.outputs) == len(new.outputs)
    for before, after in zip(old.outputs, new.outputs):
        if normalized(before) == normalized(after):
            continue
        assert old.id == '7591b8af'  # the unchanged scatter plot, manually inspected
        assert before.output_type == after.output_type == 'display_data'
        assert before.metadata == after.metadata
        assert before.data['text/plain'] == after.data['text/plain']
        assert set(before.data) == set(after.data) == {'image/png', 'text/plain'}
        output_differences.append({'cell': old.id, 'field': 'image/png',
                                   'reason': 'saved Matplotlib 3.11.2 vs execution 3.10.8; graph inspected'})
if a.refresh_html:
    # Never replace an unexpected intervening local edit.
    assert sha(html_path.read_bytes()) == '4ab46a7834892af8b295cc627cf03be4779fdb5cbe91afc408d657a84d4f4f42'
    html, _ = HTMLExporter().from_notebook_node(book)
    html_path.write_text(html, encoding='utf-8')
html = BeautifulSoup(html_path.read_text(encoding='utf-8'), 'html.parser')
dom_cells = html.select('.jp-Cell')
assert [c.get('id') for c in dom_cells] == ['cell-id=' + c.id for c in book.cells]
assert len(dom_cells) == 46
question = html.find(id='cell-id=303c6117')
answer_text = html.find(id='cell-id=97f45dbb')
assert '상태 변경 코드를 실행하기 전에' in question.get_text(' ', strip=True)
assert '별도 사본' in question.get_text(' ', strip=True)
assert '실행 전 예상과 이유' in answer_text.get_text(' ', strip=True)
assert '예상과 달랐던 점' in answer_text.get_text(' ', strip=True)
blank_ids = ['e49ac1c2', 'exercise-validation-answer', 'rectangle-independent-answer']
for cid in blank_ids:
    cell = next(c for c in book.cells if c.id == cid)
    assert all(not line.strip() or line.lstrip().startswith('#') for line in cell.source.splitlines())
    assert not cell.outputs
    assert not html.find(id='cell-id=' + cid).select('.jp-OutputArea-output')
student_text = html.get_text(' ', strip=True)
assert 'T2 상태 변화 실험.' not in student_text  # teacher heading must not appear
assert '실험 배열과 뷰는 0' not in student_text  # particular teacher key must not appear
links = []
for link in html.select('a[href]'):
    href = link['href']
    if href.startswith(('#', 'http:', 'https:', 'data:', 'mailto:')):
        continue
    target = lesson / unquote(href.split('#', 1)[0])
    assert target.is_file(), href
    links.append(href)
assert set(links) == {'week01_integrated_validation_labels.csv', 'week01_python_tables.ipynb',
                      'week01_axes_linear_bridge.ipynb', 'week01_problem_pipeline.ipynb'}
progress_rows = html.find(id='cell-id=4042bdda').select('tbody tr')
assert len(progress_rows) == 12
assert sha(source.read_bytes()) == expected
result = {'status': 'passed', 'source_sha256': expected, 'html_sha256': sha(html_path.read_bytes()),
          'html_export': 'saved source notebook; no execution or source outputs overwritten',
          'full_execution_code_cells': 22, 'dom_cell_ids_in_order': 46,
          'blank_answer_cells': blank_ids, 'state_question_and_reflection': 'present',
          'teacher_key_markers': 'absent from student HTML', 'relative_links': links,
          'progress_table_rows': 12, 'execution_output_differences': output_differences,
          'limits': ['DOM checks and one inspected plot, not a full browser rendering test',
                     'reviewer execution, not learner performance or timing',
                     'socket Jupyter not verified; in-process kernel used']}
print(json.dumps(result, ensure_ascii=False, indent=2))
