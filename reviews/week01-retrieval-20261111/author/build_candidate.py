#!/usr/bin/env python3
"""Build both candidate notebooks in a new output directory from pinned artifacts."""
import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["LOKY_MAX_CPU_COUNT"] = "1"
os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
from ipykernel.inprocess.manager import InProcessKernelManager
import nbformat
from nbconvert import HTMLExporter

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir",required=True,type=Path,
                    help="New directory; an existing directory is never overwritten")
args=parser.parse_args()
outdir=args.output_dir.expanduser().resolve()
if outdir.exists():
    parser.error("output directory already exists")
baseline_paths={
    "week01_axes_linear_bridge": ("reviews/week01-pipeline-20261111/discovery/runs/bridge-navigation-01/artifact-exact.ipynb",
                                  "09efa4d1a8ebf918dab7fc0b30f60f8130e817729d70cfe93cd7c60f15b5767f"),
    "week01_integrated": ("reviews/week01-deepening-20261111/system-context/candidate-ca89-01/artifact-exact.ipynb",
                          "ca89cf21b31a82e51f083344f3d156e046ad1356d31c22ffd87607aeeddd4551"),
}
def baseline(name):
    rel,expected=baseline_paths[name]
    raw=(ROOT/rel).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError("baseline digest changed: "+rel)
    return nbformat.reads(raw.decode("utf-8"),as_version=4)

def md(source,cid):
    cell=nbformat.v4.new_markdown_cell(source);cell.id=cid;return cell
def code(source,cid):
    cell=nbformat.v4.new_code_cell(source);cell.id=cid;return cell

bridge=baseline("week01_axes_linear_bridge")
c=bridge.cells
assert len(c)==29
c[13].source="""## 5. 질문과 후보의 벡터를 비교하고 실제 ID 찾기

두 질문과 네 후보는 각각 같은 순서의 두 특성으로 이미 표현되었다고 가정합니다. 각 행은 하나의 대상, 각 열은 그 대상의 같은 특성입니다. 이것은 합성 숫자이며 이미지 인코더를 학습하거나 실제 대회 문제를 해결한 것은 아닙니다.

| 배열 | shape | 축의 뜻 |
|---|---|---|
| Q | (2, 2) | 질문, 두 특성 |
| G | (4, 2) | 후보, 두 특성 |
| G.T | (2, 4) | 두 특성, 후보 |
| Q @ G.T | (2, 4) | 질문, 후보 |

원시 내적을 크게 하는 규칙도 문제에서 그렇게 요구한다면 유효합니다. 첫 질문 [1,0]과 후보 42 [3,4], 후보 19 [2,0]의 내적은 3과 2라서 이 규칙에서는 42가 앞섭니다. 그런데 후보 42는 길이가 5이고 후보 19는 길이가 2입니다. **방향**을 비교하는 규칙이라면 결과가 달라질까요?

벡터 v의 L2 길이는 **||v|| = √(v[0]² + … + v[d−1]²)**입니다. 후보 [3,4]의 길이는 √(3²+4²)=5이고 [2,0]의 길이는 2입니다. 길이가 0이 아닌 벡터를 자기 길이로 나누면 같은 방향의 길이 1인 벡터가 됩니다. 손으로 [3,4]와 [2,0]을 각각 나눠 보세요.

앞의 화분 분류는 **제곱거리의 최솟값**을 골랐습니다. 이 절의 원시 내적과 다음 코사인 유사도는 각각 **최댓값**을 고릅니다. 다른 질문이므로 항상 같은 후보를 고르지는 않습니다. 실제로 첫 질문 [1,0]에서 후보 42·19·35까지의 제곱거리는 각각 20·1·0.25이므로 최소는 35입니다.
"""
c[14].source="""query_ids = np.array([103, 109])
candidate_ids = np.array([42, 7, 19, 35])
Q = np.array([[1, 0], [0, 1]])
G = np.array([[3, 4], [0, 2], [2, 0], [1, 0.5]])

raw_scores = Q @ G.T
print("Q/G shape:", Q.shape, G.shape)
print("원시 내적 점수표:\\n", raw_scores)
print("원시 내적 최댓값의 후보 ID:", candidate_ids[np.argmax(raw_scores, axis=1)])
print("후보 행별 L2 길이:", np.linalg.norm(G, axis=1))
assert np.array_equal(raw_scores, [[3, 0, 2, 1], [4, 2, 0, 0.5]])
"""

norm_text=md("""### 길이로 나눈 뒤 내적하기

길이가 0이 아닌 두 벡터의 **코사인 유사도**는 다음과 같습니다.

**cos(q,g) = (q · g) ÷ (||q|| × ||g||)**

즉 두 벡터를 각각 자기 길이로 나눈 뒤 내적해도 됩니다. 첫 질문 [1,0]과 후보 42 [3,4]의 코사인은 3÷(1×5)=0.6, 후보 19 [2,0]은 2÷(1×2)=1입니다. 방향이 같은 후보 19가 더 큽니다. 이것이 항상 더 좋은 검색 규칙이거나 확률이라는 뜻은 아닙니다.

아래 함수의 연습 범위는 **비어 있지 않은 2차원 숫자 배열**, 한 행이 한 대상, 공통 열이 같은 순서의 특성인 유한한 실수입니다. 각 행의 길이가 계산 가능한 양수여야 합니다. 0벡터의 수학적 코사인은 분모가 0이므로 정의되지 않습니다. 이 합성 명세는 0·NaN·무한대·계산할 수 없는 길이를 입력 오류로 알립니다. 다른 문제나 API는 무효 표시나 별도 0/epsilon 관례를 정할 수 있으며, 그 출력이 0벡터를 단위 벡터로 바꾸는 것은 아닙니다.

행의 길이는 **특성 축 axis=1**에서 구합니다. Q는 길이 분모가 (2,1), G는 (4,1)입니다. <code>keepdims=True</code>로 열 자리를 남겨 각 행을 그 행의 길이로 나눕니다. 정규화된 Q와 G의 행렬곱은 여전히 질문×후보 (2,4)입니다.
""","retrieval-norm-text")
norm_code=code("""def normalize_rows(vectors):
    rows = np.asarray(vectors, dtype=float)
    if rows.ndim != 2 or 0 in rows.shape:
        raise ValueError("비어 있지 않은 2차원 배열이 필요합니다")
    if not np.isfinite(rows).all():
        raise ValueError("각 값은 유한해야 합니다")
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        lengths = np.linalg.norm(rows, axis=1, keepdims=True)
    if not np.isfinite(lengths).all() or (lengths == 0).any():
        raise ValueError("각 행의 길이는 계산 가능한 양수여야 합니다")
    return rows / lengths

def cosine_scores(queries, candidates):
    query_unit = normalize_rows(queries)
    candidate_unit = normalize_rows(candidates)
    if query_unit.shape[1] != candidate_unit.shape[1]:
        raise ValueError("질문과 후보의 특성 수가 달라요")
    return query_unit @ candidate_unit.T

Q_unit = normalize_rows(Q)
G_unit = normalize_rows(G)
scores = cosine_scores(Q, G)
positions = np.argmax(scores, axis=1)
matched_ids = candidate_ids[positions]
print("길이 분모 shape:", np.linalg.norm(Q, axis=1, keepdims=True).shape,
      np.linalg.norm(G, axis=1, keepdims=True).shape)
print("각 후보 정규화 후 길이:", np.linalg.norm(G_unit, axis=1))
print("코사인 점수표:", np.round(scores, 3), "/ shape:", scores.shape)
print("질문 ID → 코사인 최댓값 후보 ID:",
      dict(zip(query_ids.tolist(), matched_ids.tolist())))
assert scores.shape == (2, 4) and np.allclose(np.linalg.norm(G_unit, axis=1), 1)
assert np.array_equal(matched_ids, [19, 7])
""","retrieval-norm-code")

limits_text=md("""### 배율, 축과 경계 확인

벡터 **전체에 양수**를 곱하면 길이도 같은 양수 배로 바뀌므로 방향과 코사인은 같습니다. 한 벡터에 음수를 곱하면 방향이 뒤집혀 코사인의 부호가 바뀝니다. 음수를 곱했다고 모든 문제의 최댓값 ID가 반드시 바뀐다는 뜻은 아닙니다. 벡터의 열마다 서로 다른 배율을 적용하거나 평균을 빼는 것은 이 규칙과 다릅니다.

2주차의 열별 표준화는 훈련 **각 특성 열**의 평균·표준편차로 값을 바꿉니다. 여기서는 **각 대상 행**을 그 행의 길이로 나눕니다. 서로 다른 목적과 축이므로 바꿔 쓸 수 없습니다. 특히 본문의 화분 분류 입력 P01은 [0,0]인 유효한 관측입니다. 이 검색의 0벡터 오류 규칙을 그 분류에 적용하지 않습니다.

이 예에서는 점수가 정확히 같으면 현재 후보 순서에서 **첫 위치**를 선택합니다. 따라서 동률 후보를 같이 재정렬할 때 첫 위치의 ID가 바뀔 수 있습니다. 다른 문제의 동률 정책이 주어지면 그 정책을 따릅니다. 아래의 잘못된 열별 나눗셈과 올바른 행별 나눗셈은 shape가 같아도 각 행의 길이가 다릅니다.
""","retrieval-limits-text")
limits_code=code("""wrong_axis = G / np.linalg.norm(G, axis=0, keepdims=True)
print("열별로 잘못 나눈 shape / 행 길이:",
      wrong_axis.shape, np.round(np.linalg.norm(wrong_axis, axis=1), 3))
print("양수 배율의 점수 불변:", np.allclose(cosine_scores(3 * Q, G), scores))
print("한 질문에 음수를 곱한 점수:", np.round(cosine_scores(-Q[:1], G), 3))
assert np.allclose(cosine_scores(-Q[:1], G), -scores[:1])

tie_ids = np.array([19, 8])
tie_scores = cosine_scores([[1, 0]], [[2, 0], [4, 0]])[0]
print("동률 점수 / 현재 첫 ID:", tie_scores, tie_ids[np.argmax(tie_scores)])
print("동률 행·ID를 함께 뒤집은 첫 ID:", tie_ids[::-1][np.argmax(tie_scores[::-1])])
for invalid in ([[0, 0]], [[np.nan, 1]], [[np.inf, 1]]):
    try:
        normalize_rows(invalid)
    except ValueError as error:
        print("입력 거부:", error)
""","retrieval-limits-code")

c[15].source="""첫 질문의 코사인 최댓값 위치는 2, 실제 후보 ID는 <code>candidate_ids[2] = 19</code>입니다. 둘째 질문은 위치 1, 후보 ID 7입니다. 이 예의 최댓값에는 동점이 없습니다. 후보 ID의 크기는 유사도가 아닙니다.

### 같은 shape인데 ID가 바뀌는 반례

후보 행 순서를 바꿀 때 ID를 함께 바꾸지 않으면 점수표와 ID 목록의 shape는 그대로지만 이름표가 잘못 붙습니다. 아래에서 두 질문의 결과를 비교하세요. **유일한 최댓값**이므로 후보와 ID를 함께 옮겼다면 같은 ID를 찾아야 합니다.
"""
c[16].source="""order = np.array([2, 0, 3, 1])
G_shuffled = G[order]
correct_ids = candidate_ids[order]
new_positions = np.argmax(cosine_scores(Q, G_shuffled), axis=1)
right = correct_ids[new_positions]
wrong = candidate_ids[new_positions]  # 행만 섞고 ID는 그대로 둔 실수
print("이전/새 G shape:", G.shape, G_shuffled.shape)
print("새 점수의 열 위치:", new_positions)
print("ID도 같이 이동:", right)
print("ID를 그대로 둔 오류:", wrong)
assert np.array_equal(right, [19, 7])
assert np.array_equal(wrong, [42, 35])
"""
c[24].source="""### 필수 B · 내적과 코사인으로 검색하고 ID 찾기

아래 새 입력의 각 행은 같은 순서의 두 특성을 가진 질문 또는 후보 벡터입니다. 이 합성 명세는 모두 **유한한 비영 벡터**이며, 원시 내적을 쓰는 경우와 코사인을 쓰는 경우를 각각 비교합니다. 유일한 최댓값에서는 그 위치의 후보 ID를 반환합니다.

1. 각 질문과 후보의 길이를 직접 구하세요. 원시 내적 점수표와 그 최댓값 위치·후보 ID를 구합니다.
2. 각 행을 자기 길이로 나눈 뒤 코사인 점수표를 구하세요. shape와 축, 두 질문의 위치·후보 ID가 무엇인가요? 첫 질문에서 원시 내적과 코사인이 다른 후보를 고르는 이유는 무엇인가요?
3. 후보 행을 <code>[2,0,3,1]</code> 순서로 옮길 때 ID도 함께 옮기세요. 새 위치와 실제 ID를 적으세요. 행만 옮기고 ID를 그대로 두면 어떤 잘못된 ID가 나오나요?
4. 한 질문에 양수 또는 음수를 곱하면 점수가 어떻게 바뀌나요? 0벡터나 NaN이 들어오면 위 합성 명세에서는 어떻게 처리하나요? 동점에는 어떤 정책이 쓰이나요?
5. 아래 빈 코드 셀에 직접 계산·확인하는 코드를 작성하고 손계산과 비교하세요. 앞의 함수를 활용할 수 있지만, 각 축과 분모의 뜻도 설명해야 합니다.
"""
c[26].source="""내적과 코사인의 점수표·위치·ID 및 다른 이유:

행별 길이와 축, 후보·ID 순서 변경의 결과:

양수·음수 배율과 0·비유한값·동률의 처리:

실행 뒤 달라진 생각 / 받은 도움(없음·힌트·예시·직접 설명):
"""
c[28].source=c[28].source.replace(
    "행·축·예측시점 선수의", "행·축·예측시점 선수의")
c[28].source += """
[IOAI 2026 Find the Order 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/1_Find_the_Order/statement.md)의 각 조각별 시간 순위는 여기서 배운 최댓값 위치→ID와 **다른 출력 계약**입니다. 이 교량은 그 역순위 변환이나 오디오 모델을 완수하지 않습니다.
"""
new=[]
for i,cell in enumerate(c):
    new.append(cell)
    if i==14:
        new.extend([norm_text,norm_code,limits_text,limits_code])
bridge.cells=new

integrated=baseline("week01_integrated")
ic=integrated.cells
assert len(ic)==38
ic[34].source="""panel_examples = {
    "A": np.array([[[0,2],[1,0]], [[0,2],[0,0]]]),
    "B": np.array([[[1,0],[1,2]], [[0,2],[0,0]]]),
    "C": np.array([[[1,2],[1,2]], [[0,2],[0,0]]]),
    "D": np.array([[[1,2],[1,2]], [[1,2],[0,0]]]),
}
exercise_train = pd.DataFrame([
    ("T1", 0.0, panel_examples["D"], "정상"),
    ("T2", 3.0, panel_examples["B"], "정상"),
    ("T3", np.nan, panel_examples["C"], "점검"),
    ("T4", 9.0, panel_examples["A"], "점검"),
    ("T5", 100.0, panel_examples["D"], "?"),
], columns=["unit", "signal", "panel", "label"])
exercise_validation = pd.DataFrame([
    ("V9", 3.0, panel_examples["D"], "정상"),
    ("V4", 8.0, panel_examples["A"], "점검"),
    ("V7", 4.0, panel_examples["D"], "점검"),
], columns=["unit", "signal", "panel", "label"])
exercise_input = pd.DataFrame([
    ("N3", 8.0, panel_examples["A"]),
    ("N1", 1.0, panel_examples["D"]),
    ("N7", 8.0, panel_examples["B"]),
], columns=["unit", "signal", "panel"])
exercise_order = ["N7", "N3", "N1"]
print("훈련 / 검증 / 새 기기 행 수:",
      len(exercise_train), len(exercise_validation), len(exercise_input))
"""
old="""새 선형 변환과 검색 결과 위치·ID를 계산하고 설명하세요. 막히면 앞의 해당 원리를 확인합니다. stack·lookup은 선택 교량입니다."""
new="""새 선형 변환과 검색 결과를 계산합니다. 검색 B에서는 원시 내적과 행별 길이·코사인을 비교하고 위치를 실제 ID로 돌려줍니다. 이 검색의 0벡터 정책은 위 화분 분류에 적용하지 않습니다. 막히면 앞의 해당 원리를 확인합니다. stack·lookup은 선택 교량입니다."""
if old not in ic[37].source: raise ValueError("integrated link text changed")
ic[37].source=ic[37].source.replace(old,new)
anchor="‘6. 낯선 입력으로 혼자 풀기’에서 필수 A와 B는 각각"
if anchor not in ic[37].source:
    raise ValueError("bridge preparation guidance changed")
instruction=("B에서 앞의 함수를 다시 쓰려면 ‘5. 질문과 후보의 벡터를 비교하고 실제 ID 찾기’ 아래 "
             "<code>query_ids =</code>로 시작하는 입력 코드와 이어지는 "
             "<code>def normalize_rows(vectors):</code>로 시작하는 함수 코드를 이 순서로 실행합니다. "
             "함수 코드에는 앞 입력이 필요합니다. 실행한 다음 완성 예제를 가립니다. "
             "직접 함수를 작성한다면 이 두 예제 코드를 대신 실행할 필요는 없습니다. ")
ic[37].source=ic[37].source.replace(anchor,instruction+anchor)

WORKER = r"""
import os,sys,tempfile
import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager
book=nbformat.reads(sys.stdin.read(),as_version=4)
nbformat.validate(book)
with tempfile.TemporaryDirectory(prefix="week01-retrieval-build-worker-") as tmp:
    os.environ["IPYTHONDIR"]=tmp
    os.environ["MPLCONFIGDIR"]=tmp
    manager=InProcessKernelManager();manager.start_kernel()
    shell=manager.kernel.shell
    client=manager.client();client.start_channels()
    try:
        for index,cell in enumerate(book.cells):
            if cell.cell_type!="code": continue
            client.execute(cell.source,store_history=True)
            reply=client.get_shell_msg(timeout=120)
            if reply["content"]["status"]!="ok":
                raise RuntimeError(f"cell {index}: {reply['content']}")
            cell.execution_count=reply["content"]["execution_count"]
            cell.outputs=[]
            while True:
                msg=client.get_iopub_msg(timeout=120)
                if msg["msg_type"]=="status" and msg["content"].get("execution_state")=="idle": break
                if msg["msg_type"] in ("stream","display_data","execute_result","error"):
                    cell.outputs.append(nbformat.v4.output_from_msg(msg))
            if any(o.output_type=="error" for o in cell.outputs):
                raise RuntimeError(f"cell {index} emitted an error")
    finally:
        client.stop_channels();manager.shutdown_kernel();shell._atexit_once()
sys.stdout.write(nbformat.writes(book))
"""
def execute(book,name):
    env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","LOKY_MAX_CPU_COUNT":"1"}
    proc=subprocess.run([sys.executable,"-B","-c",WORKER],input=nbformat.writes(book),
                        text=True,capture_output=True,timeout=180,env=env)
    if proc.returncode:
        raise RuntimeError(f"{name} fresh worker failed: {proc.stderr}")
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return nbformat.reads(proc.stdout,as_version=4)

bridge=execute(bridge,"bridge")
integrated=execute(integrated,"integrated")
rendered={}
for name,book in (("week01_axes_linear_bridge",bridge),("week01_integrated",integrated)):
    rendered[name]=(nbformat.writes(book)+"\n",HTMLExporter().from_notebook_node(book)[0])
outdir.mkdir(parents=True,exist_ok=False)
for name,(notebook,html) in rendered.items():
    with (outdir/(name+".ipynb")).open("x",encoding="utf-8") as f: f.write(notebook)
    with (outdir/(name+".html")).open("x",encoding="utf-8") as f: f.write(html)
    print("BUILT",name,len((bridge if name.endswith("bridge") else integrated).cells))
