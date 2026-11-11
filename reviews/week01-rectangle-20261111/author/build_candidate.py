#!/usr/bin/env python3
"""Build the rectangle candidate from a specified, exact integrated baseline."""
import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['LOKY_MAX_CPU_COUNT'] = '1'
os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
import nbformat
from nbconvert import HTMLExporter

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline', required=True, type=Path,
                    help='original integrated notebook at the exact recorded SHA')
parser.add_argument('--output-dir', required=True, type=Path,
                    help='new output directory; existing locations are refused')
args = parser.parse_args()
outdir = args.output_dir.expanduser().resolve()
if outdir.exists():
    parser.error('output directory already exists')
raw = args.baseline.expanduser().resolve().read_bytes()
if hashlib.sha256(raw).hexdigest() != '487379bf0c9c5fae5877d1eb5ec1414dedabbe2f2634a3827ae224f6e31bc568':
    parser.error('baseline SHA-256 differs')
book = nbformat.reads(raw.decode('utf-8'), as_version=4)
assert len(book.cells) == 38

def md(source, cell_id):
    result = nbformat.v4.new_markdown_cell(source)
    result.id = cell_id
    return result

def code(source, cell_id):
    result = nbformat.v4.new_code_cell(source)
    result.id = cell_id
    return result

worked_text = md('''### 격자의 한 영역을 정확히 남기기

앞에서 P02의 잎 관찰 전체를 살폈습니다. 이번에는 원래 격자의 **지정된 위치만** 남기는 다른 합성 연습을 합니다. 다음 작은 표는 행 8, 열 12인 <code>(8,12)</code> 배열이며 값은 위치를 구별하기 위한 숫자입니다. 실제 사진이나 대회 데이터는 아닙니다.

사각형의 왼쪽 위 경계가 <code>(top, left)</code>, 오른쪽 아래 경계가 <code>(bottom, right)</code>라고 약속합니다. 순서는 **행, 열**입니다. 시작은 포함하고 끝은 포함하지 않으므로, 남기는 칸은 <code>top ≤ 행 &lt; bottom</code>, <code>left ≤ 열 &lt; right</code>입니다. 높이 H와 너비 W에서 **비어 있지 않은** 사각형을 이 연습에서는 이렇게 정합니다.

$$0 \\leq top < bottom \\leq H,\\quad 0 \\leq left < right \\leq W,$$
$$\\text{칸 수}=(bottom-top)\\times(right-left).$$

<code>((2,4),(4,7))</code>이면 행 2·3과 열 4·5·6, 모두 <code>2×3=6</code>칸입니다. 아래 합성 계약의 한도도 6칸이므로 정확히 한도에 맞습니다. 전체 96칸 중 6칸은 1/16입니다. 먼저 배열과 마스크의 모양, 선택되는 두 행 세 열을 적어 보세요.

<strong>잘라낸 부분(crop)</strong>은 <code>(2,3)</code>이지만, 위치를 표시하는 **마스크**는 원래 공간 전체인 <code>(8,12)</code>입니다. 마스크의 참은 남길 칸이고, 거짓은 나머지 칸입니다. 원본 크기 결과는 선택 칸의 원래 값을 복사하고 밖을 0으로 둡니다. 원래 값이 0이어도 선택된 칸이면 면적에 포함하므로, 결과의 0이 아닌 값 개수만 세어 면적을 정할 수 없습니다. 원본은 그대로 둡니다.

좌표의 끝이 H나 W와 같은 것은 허용되지만, 끝이 H나 W를 넘거나 끝이 시작보다 크지 않은 영역은 이 계약에서 오류입니다. NumPy는 어떤 범위 밖 슬라이스를 오류 없이 잘라 내므로, **자르기 전에** 범위와 면적을 확인합니다. RGB처럼 채널이 여러 개여도 공간 칸 수는 행×열로 셉니다. 여기서는 2차원 배열만 구현합니다.

<strong>코드 읽기:</strong> <code>np.arange(8 * 12)</code>는 0부터 95까지 숫자를 만들고 <code>reshape</code>는 8행 12열로 놓습니다. <code>np.zeros((H,W), dtype=bool)</code>은 처음에 모두 거짓인 마스크를, <code>np.zeros_like(rectangle_grid)</code>는 원본과 같은 모양·자료형의 숫자 0 배열을 만듭니다. 마스크의 거짓은 ‘이 자리를 남기지 않음’이라는 뜻이고 원본의 숫자 0은 값입니다. 이 둘은 달라서 원본 값이 0인 [2,4]도 마스크에서는 참입니다. <code>region_mask.astype(int)</code>는 참·거짓을 1·0으로 **보여 주는** 변환이며 원래 마스크 자체는 바꾸지 않습니다. <code>.copy()</code>는 여기의 숫자 배열을 따로 보관해 나중에 고쳐도 원본을 바꾸지 않게 합니다.

조건이 맞지 않을 때 <code>raise ValueError</code>는 오류의 이유를 알리고 그 지점에서 계산을 멈춥니다. 원본 본문의 빈 목록 평균 함수도 이렇게 오류를 알립니다. 아래 완성 코드는 좌표와 한도를 미리 정해 한 번 계산하는 절차입니다. 뒤의 독립 과제에서는 배열·좌표·한도를 받아 다른 입력에도 쓸 수 있는 함수를 직접 만듭니다.

이 연습은 [IOAI 2025 Pixel Efficiency 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Pixel/Pixel.ipynb)의 공간 경계를 작게 옮긴 것입니다. 공식 문제의 6.25%=0.0625=1/16이므로 224×224 이미지의 50,176칸 중 최대 3,136칸을 남길 좌표를 고르고 분류 정확도를 평가합니다. 이 크기와 계약은 위 합성 예제와 별도입니다. 실제 제출은 이미지 ID와 좌표의 JSONL이며, 여기의 전체 마스크는 좌표를 **확인하는 중간 결과**입니다. 좌표가 유효해도 분류에 유용한 영역인지는 별도 질문입니다. 이 합성 계산이 국제 문제를 푼 것은 아닙니다.
''', 'rectangle-worked-text')
worked_code = code('''rectangle_grid = np.arange(8 * 12).reshape(8, 12)
rectangle_grid[2, 4] = 0  # 선택할 자리도 원래 값이 0일 수 있습니다
rectangle_before = rectangle_grid.copy()
top, left = 2, 4
bottom, right = 4, 7
H, W = rectangle_grid.shape
max_cells = 6  # 이 (8,12) 합성 예제의 별도 한도

# 범위와 면적을 모두 확인한 뒤에만 슬라이스합니다.
if not (0 <= top < bottom <= H and 0 <= left < right <= W):
    raise ValueError("비어 있거나 격자 밖인 영역입니다")
area = (bottom - top) * (right - left)
if area > max_cells:
    raise ValueError("남길 수 있는 칸 수를 넘었습니다")

crop = rectangle_grid[top:bottom, left:right].copy()
region_mask = np.zeros((H, W), dtype=bool)
region_mask[top:bottom, left:right] = True
kept_grid = np.zeros_like(rectangle_grid)
kept_grid[top:bottom, left:right] = crop
print("선택한 값과 crop shape:\\n", crop, crop.shape)
print("전체 마스크(1=남김):\\n", region_mask.astype(int))
print("원본 / 마스크 / 남긴 결과 shape:", rectangle_grid.shape,
      region_mask.shape, kept_grid.shape)
print("선택 칸 수 / 그중 0이 아닌 값 수:", area, np.count_nonzero(crop))
assert area == int(region_mask.sum()) == 6
assert np.count_nonzero(crop) == 5 and region_mask[2, 4]
assert np.array_equal(rectangle_grid, rectangle_before)
''', 'rectangle-worked-code')

old_end = book.cells[37].source
marker = '- **과제 B:**'
assert old_end.count(marker) == 1
first, rest = old_end.split(marker, 1)
first += '''\n위 과제 A를 먼저 직접 풉니다. 그 뒤 통합 노트북으로 돌아와 바로 아래의 영역 응용을 합니다. 원본 A에서 만든 <code>T</code>는 **별도 커널의 변수**라 이 노트북에서 자동으로 보이지 않습니다. 아래 입력 셀은 같은 숫자를 이 커널에 다시 만듭니다.\n'''
book.cells[37].source = first
independent_text = md('''### 과제 A를 이어 · 다른 영역과 경계를 혼자 검사하기

위의 8×12 완성 예제와 별도 교사용 해설을 가립니다. 원본 A에서 배열을 만들고 reshape·전치·열별·행별 브로드캐스팅과 오류를 직접 확인한 뒤, 아래 입력 셀로 같은 <code>T</code>를 **통합본 커널에 다시 만듭니다**. 어느 커널에서 작업 중인지와 입력값도 확인하세요.

이 **새 합성 명세**에서 입력은 비어 있지 않은 2차원 NumPy 숫자 배열, <code>((top,left),(bottom,right))</code> 네 좌표, 양의 정수 한도입니다. 네 좌표는 Python 정수이며 참·거짓은 들어오지 않는다고 가정합니다. 다른 자료형 입력에 대한 처리는 요구하지 않습니다. 값 0은 유효한 배열 원소입니다. 이번 <code>T</code>는 (2,3), 한도는 **4칸**입니다. 이것은 8×12 예의 6칸 한도나 공식 Pixel의 6.25%와 다른 약속입니다.

함수는 배열·좌표·한도를 **인자**로 받습니다. 좌표가 <code>0 ≤ top &lt; bottom ≤ H</code>, <code>0 ≤ left &lt; right ≤ W</code>를 만족하지 않거나 면적이 한도를 넘으면 슬라이스하기 전에 <code>ValueError</code>로 알립니다. 시작과 끝이 같은 빈 사각형을 오류로 정한 것은 이 합성 명세의 약속입니다. 조건이 맞으면 선택한 값 crop, 전체 크기의 불리언 마스크, 선택 밖을 0으로 둔 전체 크기 결과를 이 순서로 반환합니다. 입력 배열은 바꾸지 않습니다. 기본 슬라이스는 원본의 값을 공유할 수 있으므로 crop을 나중에 수정하려면 별도 복사할 수 있습니다.

1. <code>((0,1),(2,3))</code>과 <code>((0,0),(2,2))</code>의 선택된 **각 값**, crop 모양, 면적과 원래 크기 마스크를 손으로 먼저 구하세요. 두 영역은 모양과 면적이 같은데 같은 위치를 남기나요?
2. 위 계약을 따르는 **하나의 함수**를 직접 작성하고 두 영역 각각을 넣어 예상과 비교하세요. 함수 안에 T의 모양·좌표·결과를 고정하지 않습니다. 전체 결과의 남은 값과 밖의 0, 입력 T가 바뀌지 않았는지도 검사합니다.
3. <code>((1,2),(2,3))</code>이 끝 경계 H·W에 닿아도 왜 가능한지 확인하세요. <code>((0,0),(2,3))</code>은 범위는 맞아도 왜 한도에 걸리나요?
4. <code>((1,1),(3,3))</code>은 수식상 면적이 4이지만 왜 범위 오류인가요? 검사를 빼고 슬라이스하면 NumPy가 무엇을 반환하는지도 **별도로** 확인하세요. <code>((1,1),(1,2))</code>은 왜 이 명세에서 오류인가요? 함수가 오류를 알리는지 직접 검사합니다.

계산과 이유, 직접 작성한 코드, 실행 뒤 달라진 생각과 받은 도움을 남깁니다. 0과 빈 영역은 다릅니다. 마스크 작성과 유효 좌표 확인만으로 실제 분류 결과를 알 수는 없습니다.

내가 고른 칸·면적과 두 영역의 차이:

범위·한도·빈 영역의 이유와 실행 결과:

실행 뒤 달라진 생각 / 받은 도움(없음·힌트·예시·직접 설명):
''', 'rectangle-independent-text')
independent_input = code('''# 원본 A는 별도 커널입니다. 같은 T를 이 통합본 커널에 다시 만듭니다.
import numpy as np
T = np.array([[1, 4, 7], [2, 5, 8]])
print("영역 연습 입력 / shape:\\n", T, T.shape)
''', 'rectangle-independent-input')
independent_blank = code('''# 배열·좌표·한도를 받는 함수를 직접 작성하고 여러 입력을 확인하세요.
''', 'rectangle-independent-answer')
tail = md('### 나머지 원본 필수 연습을 이어 하기\n\n' + marker + rest,
          'rectangle-followup-tail')
book.cells = (book.cells[:17] + [worked_text, worked_code] + book.cells[17:37]
              + [book.cells[37], independent_text, independent_input,
                 independent_blank, tail])
assert len(book.cells) == 44

WORKER = r'''import os, sys
import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager
book = nbformat.reads(sys.stdin.read(), as_version=4)
nbformat.validate(book)
manager = InProcessKernelManager(); manager.start_kernel()
shell = manager.kernel.shell; client = manager.client(); client.start_channels()
try:
    for index, cell in enumerate(book.cells):
        if cell.cell_type != 'code': continue
        client.execute(cell.source, store_history=True)
        reply = client.get_shell_msg(timeout=120)
        if reply['content']['status'] != 'ok':
            raise RuntimeError(f'cell {index}: {reply["content"]}')
        cell.execution_count = reply['content']['execution_count']
        cell.outputs = []
        while True:
            msg = client.get_iopub_msg(timeout=120)
            if msg['msg_type'] == 'status' and msg['content'].get('execution_state') == 'idle': break
            if msg['msg_type'] in ('stream', 'display_data', 'execute_result', 'error'):
                cell.outputs.append(nbformat.v4.output_from_msg(msg))
        if any(output.output_type == 'error' for output in cell.outputs):
            raise RuntimeError(f'cell {index} emitted an error')
finally:
    client.stop_channels(); manager.shutdown_kernel(); shell._atexit_once()
sys.stdout.write(nbformat.writes(book))
'''
with tempfile.TemporaryDirectory(prefix='week01-rectangle-kernel-') as tmp:
    env = {**os.environ, 'IPYTHONDIR': tmp, 'MPLCONFIGDIR': tmp,
           'PYTHONDONTWRITEBYTECODE': '1', 'LOKY_MAX_CPU_COUNT': '1'}
    result = subprocess.run([sys.executable, '-B', '-c', WORKER],
                            cwd=ROOT, input=nbformat.writes(book), text=True,
                            capture_output=True, env=env, timeout=180)
    if result.returncode:
        raise RuntimeError('notebook worker failed:\n' + result.stderr)
    if result.stderr:
        sys.stderr.write(result.stderr)
    book = nbformat.reads(result.stdout, as_version=4)
    nbformat.validate(book)
    html = HTMLExporter().from_notebook_node(book)[0]
    notebook = nbformat.writes(book) + '\n'
outdir.mkdir(parents=True, exist_ok=False)
for name, contents in [('week01_integrated.ipynb', notebook),
                       ('week01_integrated.html', html)]:
    with (outdir / name).open('x', encoding='utf-8') as f:
        f.write(contents)
print('BUILT', len(book.cells), 'cells;', sum(c.cell_type == 'code' for c in book.cells), 'code cells')
