#!/usr/bin/env python3
"""Build the sequence candidate from explicitly supplied baseline notebooks."""
import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ["PYTHONDONTWRITEBYTECODE"]="1"
os.environ["LOKY_MAX_CPU_COUNT"]="1"
os.environ["PYDEVD_DISABLE_FILE_VALIDATION"]="1"
ROOT=Path(__file__).resolve().parents[3]
os.chdir(ROOT)
import nbformat
from nbconvert import HTMLExporter

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--bridge-baseline",required=True,type=Path)
parser.add_argument("--integrated-baseline",required=True,type=Path)
parser.add_argument("--output-dir",required=True,type=Path,
                    help="new directory; existing directories are refused")
args=parser.parse_args()
outdir=args.output_dir.expanduser().resolve()
if outdir.exists():
    parser.error("output directory already exists")
def read_baseline(path,expected):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:
        parser.error("baseline SHA-256 differs: "+str(path))
    return nbformat.reads(raw.decode("utf-8"),as_version=4)
bridge=read_baseline(args.bridge_baseline,"de5ba77f7cd1325769ca4af29a8fd9c851d14c8c83d5acb88a127bc277579ef0")
main=read_baseline(args.integrated_baseline,"b530a36ae4f0b4fe9237fb29d604dc288198df7027c85c2e99d1a2e6f2a41611")
assert len(bridge.cells)==33 and len(main.cells)==38

def md(source,cid):
    cell=nbformat.v4.new_markdown_cell(source);cell.id=cid;return cell
def code(source,cid):
    cell=nbformat.v4.new_code_cell(source);cell.id=cid;return cell

c=bridge.cells
old="**우선:** 1~3절, 5절의 검색과 ID, 6절 필수 문항. **선택 교량:** 4절의 stack·concatenate, 5절의 lookup과 6절 선택 문항은 관련 후속 단원 전에 다시 써도 됩니다."
new="**우선:** 1~3절, 5절의 검색·조회와 유효 위치 평균, 6절 필수 문항. **선택 교량:** 4절의 stack·concatenate와 6절 선택 문항은 관련 후속 단원 전에 다시 써도 됩니다."
if old not in c[0].source: raise ValueError("bridge scope anchor changed")
c[0].source=c[0].source.replace(old,new)

c[21].source="""행과 ID는 항상 같은 순서로 옮기고, 제출할 때 요구된 질문 ID 순서도 확인합니다. <code>위치 + 1</code>이 실제 ID라는 규칙은 따로 주어졌을 때만 쓸 수 있습니다.

### 토큰 조회와 유효 위치 평균

아래는 설명용으로 **이미 주어진 고정 숫자표**입니다. 각 어휘 ID가 표의 어느 행을 가리키는지만 다룹니다. 실제 토크나이저나 학습된 언어 모델을 실행하는 것은 아닙니다.

| ID | 표시 | 한 행의 뜻 |
|---:|---|---|
| 0 | PAD | 빈 자리를 채우는 약속된 표시 |
| 1 | 봄 | 실제 토큰 |
| 2 | 비 | 실제 토큰 |
| 3 | 나무 | 실제 토큰 |
| 4 | 해 | 실제 토큰 |
| 5 | 쉼 | 실제 토큰, 제공된 벡터가 우연히 [0,0,0] |

한 문장의 토큰 수가 달라도 함께 배열에 담으려고 빈자리에 PAD를 넣습니다. 이 **합성 명세에서만** 0이 PAD이며, 표의 PAD 행은 일부러 [8,8,8]로 두었습니다. 벡터의 값이 0인지가 아니라 **토큰 ID가 PAD인지**로 유효 위치를 구별합니다. 실제 토큰 ID 5는 벡터가 0이어도 개수에 포함합니다.

표 E의 shape는 (V,d), 토큰 ID I는 (B,T), 조회 결과 H는 (B,T,d)입니다. V는 어휘 행 수, T는 문장의 저장 위치 수, d는 벡터 좌표 수, B는 문장 수입니다. 한 위치의 조회는 **H[b,t,j] = E[I[b,t],j]**입니다. 여기서는 V=6, T=4, d=3, B=2입니다. ID는 곱할 숫자가 아니라 표 행을 고르는 이름입니다.

**먼저 예상:** 둘째 문장의 ID 3은 몇 번 나타나고 어느 벡터를 찾나요? ID 5의 [0,0,0]은 문장의 길이에 들어가나요? ID -1을 그대로 NumPy에서 조회하면 왜 의도하지 않은 행이 나올 수 있나요?
"""
c[22].source="""embedding_table = np.array([
    [8, 8, 8],  # 이 예의 PAD 행: 일부러 0이 아님
    [2, 0, 1], [0, 2, 1], [2, 2, 0],
    [5, -1, 3], [0, 0, 0],  # ID 5는 유효한 실제 토큰
], dtype=float)
token_indices = np.array([[1, 2, 0, 0], [3, 5, 3, 0]])
looked_up = embedding_table[token_indices]  # 예제 ID는 모두 범위 안
external_id_to_row = {41: 3, 87: 1}
print("표 / 토큰 ID / 조회 shape:",
      embedding_table.shape, token_indices.shape, looked_up.shape)
print("조회한 벡터:\\n", looked_up)
print("외부 ID 41 → 표 행:", external_id_to_row[41],
      "→", embedding_table[external_id_to_row[41]])
assert looked_up.shape == (2, 4, 3)
assert np.array_equal(looked_up[1, 0], looked_up[1, 2])
"""

mean_text=md("""### 빈 위치를 빼고 각 문장의 평균 구하기

m[b,t]를 실제 토큰이면 1, PAD이면 0이라고 합시다. 각 문장의 유효 개수와 좌표별 평균은

**count[b] = Σ_t m[b,t]**  
**mean[b,j] = Σ_t (m[b,t] × H[b,t,j]) ÷ count[b]** (count가 0보다 클 때)

첫 문장은 [2,0,1]과 [0,2,1] 두 벡터의 합 [2,2,2]를 2로 나눠 [1,1,1]입니다. 둘째 문장은 ID 3이 두 번, ID 5가 한 번이므로 합 [4,4,0]을 **3**으로 나눕니다. 같은 토큰이 반복돼도 위치마다 셉니다.

m은 (B,T)이고 각 벡터의 좌표에 같은 참·거짓을 적용하려고 <code>m[:,:,None]</code>으로 (B,T,1)을 만듭니다. 위치 축 T를 더하면 합과 평균은 (B,d), 개수 분모는 (B,1)입니다. 아래 함수는 이 예에서 **0을 PAD ID로 약속**합니다. 작은 유한 실수 표와 비어 있지 않은 정수 ID 배열만 받으며, 음수나 표의 행 수 이상인 ID 및 전부 PAD인 문장은 오류로 알립니다. NumPy의 -1은 오류 없이 마지막 행을 가리킬 수 있기 때문에 **조회 전**에 검사합니다.

전부 PAD이면 분모가 0이라 이 평균은 없습니다. 반면 ID 5 하나는 유효 개수 1에 평균 [0,0,0]인 정상 사례입니다. 그 영벡터를 나중에 코사인 검색에 넣을 수 있는지는 앞에서 정한 **별도의 검색 경계**입니다.

**코드 읽기:** <code>valid = ids != 0</code>은 각 위치가 유효한지 참·거짓으로 표시합니다. <code>np.where(valid[:,:,None], vectors, 0)</code>은 참인 위치의 조회 벡터를 남기고 거짓인 위치를 0으로 바꿉니다. <code>sum(axis=1)</code>으로 위치 축을 더한 뒤 <code>counts</code>로 나누는 부분이 위 평균 수식입니다. 그 밖의 표·ID 크기와 종류·범위 및 계산 결과 검사는 안전 확인입니다. <code>dtype=object</code>는 참·거짓이 정수로 바뀌기 전에 종류를 확인하기 위한 것이고, <code>errstate</code>는 계산 중 경고를 조절한 뒤 결과가 유한한지 검사하기 위한 보조 설정입니다. 둘은 평균의 중심 계산이 아닙니다.
""","sequence-mean-text")

mean_code=code("""def lookup_and_masked_mean(table, token_ids):
    table = np.asarray(table)
    ids = np.asarray(token_ids, dtype=object)  # True가 정수 ID로 바뀌지 않게 확인
    if (table.ndim != 2 or 0 in table.shape or table.dtype.kind not in "iuf"
            or not np.isfinite(table).all()):
        raise ValueError("표는 비어 있지 않은 유한 실수 배열이어야 합니다")
    if ids.ndim != 2 or 0 in ids.shape:
        raise ValueError("ID는 비어 있지 않은 2차원 배열이어야 합니다")
    if any(isinstance(i, (bool, np.bool_)) or not isinstance(i, (int, np.integer))
           for i in ids.flat):
        raise ValueError("토큰 ID는 정수여야 합니다")
    if any(i < 0 or i >= table.shape[0] for i in ids.flat):
        raise ValueError("토큰 ID가 어휘표 범위를 벗어났습니다")
    ids = ids.astype(np.intp)
    valid = ids != 0                 # 이 예의 PAD ID
    counts = valid.sum(axis=1, keepdims=True)
    if (counts == 0).any():
        raise ValueError("전부 PAD이면 평균이 없습니다")
    vectors = table[ids]
    with np.errstate(over="ignore", invalid="ignore"):
        sums = np.where(valid[:, :, None], vectors, 0).sum(axis=1, dtype=float)
        means = sums / counts
    if not np.isfinite(means).all():
        raise ValueError("유한한 평균을 계산할 수 없습니다")
    return vectors, valid, sums, counts, means

vectors, valid, sums, counts, means = lookup_and_masked_mean(
    embedding_table, token_indices)
print("유효 위치:\\n", valid)
print("유효 합 / 개수:\\n", sums, "\\n", counts)
print("문장별 평균:", means)
print("잘못 전체 네 칸으로 평균:", vectors.mean(axis=1))
reversed_vectors, _, _, _, reversed_means = lookup_and_masked_mean(
    embedding_table, token_indices[:, ::-1])
print("순서를 바꾸면 조회 자리는 같은가요?", np.array_equal(vectors, reversed_vectors))
print("순서를 바꾸어도 평균은 같은가요?", np.allclose(means, reversed_means))
assert counts.ravel().tolist() == [2, 3]
assert np.allclose(means, [[1, 1, 1], [4/3, 4/3, 0]])
assert not np.array_equal(vectors, reversed_vectors)
assert np.allclose(means, reversed_means)
""","sequence-mean-code")

c[23].source="""고정된 각 위치의 벡터를 **그냥 합해 평균**하면 위치 순서를 잃습니다. 위에서는 토큰 순서를 바꾸어 조회한 자리별 결과가 달라도 평균은 같습니다. 대화 조각의 시간 순서가 중요한 문제를 이 평균만으로 구별할 수는 없습니다. 위치나 문맥을 다른 방식으로 반영하는 모델 전체에도 반드시 순서 정보가 없다는 뜻은 아닙니다.

유효 위치를 가려 평균하는 이 연습은 attention 계산이나 언어 모델 학습이 아닙니다. 실제 모델의 PAD ID·마스크 규약과 빈 입력 처리는 그 명세를 읽어야 합니다. [IOAI 2026 Potato](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/3_Potato/statement.md)는 어휘의 각 행에 공개 벡터를 대응시키지만, 심판의 비공개 표현과 상호작용을 포함합니다. 이 작은 고정표 연습은 그 국제 과제를 푼 것이 아닙니다. [Find the Order](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/1_Find_the_Order/statement.md)의 시간 순위도 별도 과제입니다.
"""
c[28].source="""### 필수 B · 토큰에서 질문을 만들고 검색하기

새 입력의 고정 어휘표 행은 토큰 ID, 열은 벡터 좌표입니다. 0만 PAD이고 **ID 4는 실제 토큰**입니다. PAD 행은 일부러 0이 아니며 실제 ID 4의 벡터는 0입니다. 두 질문의 ID는 문장을 찾는 이름이고, 각 문장 안 토큰 ID와 다릅니다. 후보 행은 같은 순서의 두 벡터 특성으로 주어집니다.

1. 새 표·ID·조회 결과의 shape와 각 축을 쓰세요. 각 위치의 벡터, PAD를 제외한 위치, 유효 개수와 좌표별 합을 손으로 구하세요. 토큰이 반복되면 어떻게 세나요?
2. 유효 합을 각 문장의 유효 개수로 나누어 <code>query_new</code>를 직접 만드세요. 벡터 값이 0인 실제 ID 4를 분모에서 빼면 안 되는 이유를 설명하세요. 잘못 모든 저장 위치 4개로 나눈 값과 비교하세요.
3. 각 질문과 후보의 원시 내적 점수표·최댓값 위치·후보 ID를 구하세요. 이어 각 행의 길이로 정규화해 코사인 점수표·위치·ID를 구하고, 두 규칙이 첫 질문에서 왜 다른 후보를 고르는지 설명하세요.
4. 후보 행과 ID를 함께 <code>[2,0,3,1]</code> 순서로 옮긴 뒤 코사인 최댓값의 새 위치와 실제 ID를 적으세요. 행만 옮기면 어떤 ID가 잘못 붙나요?
5. 예제 표의 PAD 행만 [0,0]으로 바꾸고 **틀리게 네 칸 전부로 나누어도**, 각 잘못된 질문이 올바른 질문의 양의 배수가 됩니다. 이 경우 코사인과 최종 ID만 확인하면 분모 오류를 찾을 수 있나요? 유효 개수와 각 평균 좌표도 검사하세요.
6. ID -1·어휘 행 수 이상, 전부 PAD인 문장은 어떻게 알릴까요? 유효 토큰 하나가 영벡터인 정상 평균과 그 벡터를 코사인 검색에 쓰는 별도 경계를 구분하세요. 정규화 동률·음수 배율의 정책도 설명하세요.

아래 빈 코드 셀에 직접 계산·확인하는 코드를 작성하고 손계산과 비교하세요. 앞의 함수를 활용할 수 있지만 각 축과 분모의 뜻도 설명해야 합니다.
"""
c[29].source="""q_ids_new = np.array([61, 22])        # 질문 문장의 ID
g_ids_new = np.array([90, 8, 53, 17])  # 후보의 ID
token_table_new = np.array([[7, 11], [2, 0], [2, 9], [6, 4], [0, 0]])
query_tokens_new = np.array([[1, 1, 2, 0], [3, 4, 0, 0]])
gallery_new = np.array([[2, 1], [0, 3], [1, 1], [2, 0]])
# query_new는 유효 위치의 평균으로 직접 만드세요.
"""
c[30].source="""조회 값·유효 개수·합·평균과 각 축의 뜻:

내적과 코사인의 점수표·위치·ID 및 다른 이유:

PAD·유효 영벡터·오류 정책과 평균이 잃는 순서:

실행 뒤 달라진 생각 / 받은 도움(없음·힌트·예시·직접 설명):
"""
newcells=[]
for i,cell in enumerate(c):
    newcells.append(cell)
    if i==22:
        newcells.extend([mean_text,mean_code])
bridge.cells=newcells

ic=main.cells
assert len(ic)==38
old=("B에서 앞의 함수를 다시 쓰려면 ‘5. 질문과 후보의 벡터를 비교하고 실제 ID 찾기’ 아래 "
     "<code>query_ids =</code>로 시작하는 입력 코드와 이어지는 "
     "<code>def normalize_rows(vectors):</code>로 시작하는 함수 코드를 이 순서로 실행합니다. "
     "함수 코드에는 앞 입력이 필요합니다. 실행한 다음 완성 예제를 가립니다. "
     "직접 함수를 작성한다면 이 두 예제 코드를 대신 실행할 필요는 없습니다. ")
new=("B에서 앞의 함수를 다시 쓰려면 ‘5. 질문과 후보의 벡터를 비교하고 실제 ID 찾기’ 아래 "
     "<code>query_ids =</code> 입력 코드와 <code>def normalize_rows(vectors):</code> 함수 코드, "
     "이어 ‘토큰 조회와 유효 위치 평균’의 <code>embedding_table =</code> 입력 코드와 "
     "<code>def lookup_and_masked_mean(table, token_ids):</code> 함수 코드를 이 순서로 실행합니다. "
     "함수 코드에는 각각 앞 입력이 필요합니다. 실행한 다음 완성 예제를 가립니다. "
     "직접 함수를 작성한다면 이 예제 코드를 대신 실행할 필요는 없습니다. ")
if old not in ic[37].source: raise ValueError("integrated preparation anchor changed")
ic[37].source=ic[37].source.replace(old,new)
ic[37].source=ic[37].source.replace(
    "검색 B에서는 원시 내적과 행별 길이·코사인을 비교하고 위치를 실제 ID로 돌려줍니다.",
    "검색 B에서는 토큰을 조회해 유효 위치 평균으로 질문을 만든 뒤 원시 내적과 행별 길이·코사인을 비교하고 위치를 실제 ID로 돌려줍니다.")
ic[37].source=ic[37].source.replace("stack·lookup은 선택 교량입니다.","stack·concatenate는 선택 교량입니다.")

WORKER=r"""
import os,sys,tempfile
import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager
book=nbformat.reads(sys.stdin.read(),as_version=4)
nbformat.validate(book)
with tempfile.TemporaryDirectory(prefix="week01-sequence-worker-") as tmp:
    os.environ["IPYTHONDIR"]=tmp
    os.environ["MPLCONFIGDIR"]=tmp
    manager=InProcessKernelManager();manager.start_kernel()
    shell=manager.kernel.shell;client=manager.client();client.start_channels()
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
                if msg["msg_type"]=="status" and msg["content"].get("execution_state")=="idle":break
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
    if proc.returncode: raise RuntimeError(f"{name} worker failed: {proc.stderr}")
    if proc.stderr: sys.stderr.write(proc.stderr)
    return nbformat.reads(proc.stdout,as_version=4)

bridge=execute(bridge,"bridge")
main=execute(main,"integrated")
rendered={}
for name,book in (("week01_axes_linear_bridge",bridge),("week01_integrated",main)):
    rendered[name]=(nbformat.writes(book)+"\n",HTMLExporter().from_notebook_node(book)[0])
outdir.mkdir(parents=True,exist_ok=False)
for name,(notebook,html) in rendered.items():
    with (outdir/(name+".ipynb")).open("x",encoding="utf-8") as f: f.write(notebook)
    with (outdir/(name+".html")).open("x",encoding="utf-8") as f: f.write(html)
    print("BUILT",name,len((bridge if name.endswith("bridge") else main).cells))
