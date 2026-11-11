#!/usr/bin/env python3
"""Build the candidate from the pinned pre-candidate notebook and execute in process."""
import argparse
import hashlib
import os
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

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir", required=True, type=Path,
                    help="A new directory to create; existing directories are refused")
parser.add_argument("--baseline", type=Path,
                    default=ROOT / "reviews/week01-integration-20261111/discovery/runs/integrated-candidate-01/artifact-exact.ipynb")
args = parser.parse_args()
output_dir = args.output_dir.expanduser().resolve()
if output_dir.exists():
    parser.error(f"output directory already exists: {output_dir}")
raw = args.baseline.read_bytes()
expected = "15ab0101edbca3c0c669e551cb723b401d168d9730523fa1ac1263a0d7538120"
if hashlib.sha256(raw).hexdigest() != expected:
    parser.error("baseline SHA-256 differs from the fixed pre-candidate artifact")
book = nbformat.reads(raw.decode("utf-8"), as_version=4)
assert len(book.cells) == 34
cells = book.cells

cells[0].source = """# 1주차 · 관찰을 읽고 예측하기

## 하나의 질문으로 시작합니다

**일주일 동안의 기록과 잎 관찰이 있는 화분에서, 아직 재지 않은 높이를 어떻게 예상하고 확인할까요?** 한 행의 뜻과 정보를 알 수 있는 순간부터 정합니다. 표와 배열의 관찰에서 특성을 만들고, 임의로 정한 식과 자료에서 실제로 배운 모델을 구분합니다. 그다음 다른 명세를 읽고 스스로 선택해 봅니다.

아래 자료는 모두 이해를 위해 만든 **합성 자료**입니다. 실제 식물의 성장 법칙이나 대회 데이터가 아닙니다. Python 변수·리스트·반복문·함수를 접한 학생을 위한 자료입니다. NumPy, pandas, Matplotlib, scikit-learn이 있는 Jupyter에서 위에서 아래로 Shift+Enter를 누르세요. 각 질문은 **먼저 예상과 이유를 적고**, 실행한 뒤 비교합니다.
"""

cells[1].source = """## 1. 무엇을 언제 아나요?

일주일 동안 매일 같은 양의 빛과 물을 받았고 그 기록과 잎 관찰이 완성된 **뒤**, 높이를 재기 **직전**이라고 가정합니다. 기록과 잎 관찰은 사용할 수 있지만 일주일 뒤 높이는 아직 모릅니다. 심는 날에 예측한다면 앞으로 실제 받을 빛과 물은 아직 모릅니다. 계획과 실제 기록도 같다고 단정할 수 없습니다.

| 항목 | 한 화분에서의 뜻 | 이 예제의 역할 |
|---|---|---|
| pot_id | 화분을 찾는 이름 | ID, 결과와 관찰을 연결 |
| place | 관찰 장소 | 기록·비교용 |
| light_h | 하루 빛 시간(h) | 예측 직전 알 수 있는 특성 |
| water_ml | 하루 물의 양(ml), 빈칸은 기록 없음 | 예측 직전 알 수 있는 특성 |
| 잎 관찰 | 잎과 배경을 표시한 작은 합성 격자 | 예측 직전 알 수 있는 관찰 |
| height_cm | 일주일 뒤 잰 높이(cm) | 나중에 비교할 정답 |

한 행은 화분 하나입니다. 높이로부터 만든 판정도 높이를 재기 전에는 입력에 넣을 수 없습니다. 여기서 pot_id는 연결용이지만 **다른 문제의 ID도 항상 입력에서 빼야 한다는 규칙은 아닙니다.** 그 ID가 예측 시점에 주어지고 대상의 차이를 설명할 수 있는지는 명세와 문제 목적을 보고 판단합니다.

아래 표는 기존 화분 예시를 참고하되, 새로운 비교를 위해 두 행의 일부 값을 바꾼 별도 합성 표입니다.

**먼저 예상:** P01의 물 0과 P03의 빈칸은 같은 뜻인가요? 높이를 예측할 때 <code>height_cm</code>을 입력으로 쓰면 왜 안 될까요?

먼저 CSV 문자열을 읽을 StringIO, 숫자 배열용 NumPy, 표를 다룰 pandas와 표를 보여 줄 display를 준비합니다. 그림과 모델 도구는 해당 단계에서 따로 불러옵니다.
"""

new = []
def md(source, cid):
    c = nbformat.v4.new_markdown_cell(source)
    c.id = cid
    return c
def code(source, cid):
    c = nbformat.v4.new_code_cell(source)
    c.id = cid
    return c

grid_intro = md("""### 같은 화분의 잎 관찰을 특성으로 만들기

이제 각 화분에 **예측 직전에 얻은** 작은 합성 잎 관찰을 하나씩 붙입니다. 사진 모델을 배우는 예제가 아니라 값의 뜻과 축을 읽는 연습입니다. 화분 하나의 관찰은 <code>(2,2,2)</code>: **행, 열, 채널** 순서입니다.

| 채널 | 코드의 뜻 |
|---|---|
| 0: 물체 | 0은 배경, 1은 잎 |
| 1: 색 | 잎이면 0은 초록, 1은 노랑. **배경의 색 코드는 의미 없음** |

예를 들어 P02의 <code>[0,1]</code>은 [잎, 노랑], <code>[1,0]</code>은 [잎, 초록]입니다. 코드는 **종류를 표시하는 이름**이므로 1이 0보다 크다는 사실만으로 잎이나 색의 크기·거리를 뜻하지 않습니다. 한 칸은 0부터 세고 <code>관찰[행, 열, 채널]</code>로 찾습니다.

**먼저 예상:** P02에서 노란 잎은 몇 칸인가요? 색 코드가 1인 모든 칸을 세면 배경도 세게 될까요? 행과 열을 바꾼 뒤에도 shape가 같다면 같은 위치의 뜻도 항상 같을까요?
""", "deep-leaf-intro")

grid_code = code("""leaf_images = {
    "P01": np.array([[[1,0],[1,0]], [[0,1],[0,1]]]),
    "P02": np.array([[[0,1],[1,1]], [[1,0],[0,1]]]),
    "P03": np.array([[[0,0],[1,1]], [[1,1],[1,0]]]),
    "P04": np.array([[[1,1],[1,0]], [[1,1],[1,1]]]),
    "P05": np.array([[[1,0],[1,1]], [[1,1],[1,0]]]),
    "P06": np.array([[[1,1],[1,1]], [[0,1],[1,1]]]),
}
p02_image = leaf_images["P02"]
print("P02 shape (행, 열, 채널):", p02_image.shape)
print("P02 [0,1] / [1,0]:", p02_image[0,1], "/", p02_image[1,0])
swapped = p02_image.transpose(1, 0, 2)
print("행·열을 바꾼 shape / [0,1]:", swapped.shape, "/", swapped[0,1])
assert swapped.shape == p02_image.shape
assert not np.array_equal(swapped[0,1], p02_image[0,1])
""", "deep-leaf-grid")

grid_meaning = md("""한 칸이 잎 **이면서** 노랑일 때만 1, 그렇지 않으면 0으로 셉니다. 행을 r, 열을 c, 관찰을 G라고 하면

**노란 잎 수 = Σ(r=0부터 1) Σ(c=0부터 1) [G[r,c,0]=1 이고 G[r,c,1]=1]**

대괄호의 조건이 참이면 1, 거짓이면 0입니다. P02의 네 칸을 차례로 확인하면 0+1+0+0=1입니다. 다음 함수는 **한 화분의 유효한 (2,2,2) 관찰**을 받아 정수 개수를 돌려줍니다. 물체와 색 코드를 각각 비교한 뒤 <code>&amp;</code>로 두 조건을 합칩니다. 배경 색만 바뀌어도 답은 그대로여야 합니다.

ID는 이미지를 화분에 연결하는 데 씁니다. 표 행의 순서로 ID를 찾아 각각의 개수를 만들므로, 표만 정렬해도 다른 화분의 이미지가 섞이지 않습니다. 숫자 코드끼리 평균을 내는 대신, 이처럼 명세에 맞는 의미 있는 양을 만듭니다.
""", "deep-count-intro")

grid_count = code("""def count_yellow_leaf(image):
    objects = image[:, :, 0]
    colors = image[:, :, 1]
    return int(((objects == 1) & (colors == 1)).sum())

print("P02 색 1인 모든 칸:", int((p02_image[:, :, 1] == 1).sum()))
print("P02 노란 잎 수:", count_yellow_leaf(p02_image))
background_changed = p02_image.copy()
background = background_changed[:, :, 0] == 0
background_changed[:, :, 1][background] = 1 - background_changed[:, :, 1][background]
print("배경 색만 바꾼 뒤:", count_yellow_leaf(background_changed))

yellow_by_id = {pot: count_yellow_leaf(image) for pot, image in leaf_images.items()}
print("각 ID의 노란 잎 수:", yellow_by_id)
assert count_yellow_leaf(p02_image) == 1
assert count_yellow_leaf(background_changed) == 1
assert [yellow_by_id[pot] for pot in plants["pot_id"]] == [0, 1, 2, 3, 2, 3]
""", "deep-count-code")

cells[17].source = """### 이제 질문을 바꾸어 작은 분류 모델을 학습하기

이번에는 높이 자체가 아니라 **높이가 12cm 이상인지**를 예측합니다. 나중에 잰 높이로 만든 0/1이 정답입니다. 이 두 질문의 출력 뜻과 단위가 다릅니다. P01~P04는 훈련, P05~P06은 별도 검증으로 정합니다. 서로 다른 화분이라고 가정합니다.

이 예의 입력으로 **물의 양과 방금 만든 노란 잎 수**를 고릅니다. 빛도 사용할 수 있지만 이번 모델에서는 쓰지 않습니다. 나중 높이·그 높이에서 만든 정답·연결용 ID는 모델 입력에 넣지 않습니다. 우선 훈련의 물 [0,20,결측,40] 중 관측한 값으로 평균 (0+20+40)÷3 = **20ml**를 배워 빈칸을 채웁니다. 전체 기록의 평균 24ml를 쓰면 검증 정보가 섞입니다.

물을 미리 정한 **10ml 단위**로 나타내면 20ml는 숫자 2입니다. 이것은 이 예에서 정한 기준이지 자료를 보고 찾은 최적값이 아닙니다. 두 입력은 순서대로 [물/10ml, 노란 잎 수]입니다. 각 행의 ID로 관찰을 찾아야 물과 잎 수가 같은 화분의 값이 됩니다.
"""

cells[18].source = """from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestCentroid

training = plants.iloc[:4].copy()
validation = plants.iloc[4:].copy()
y_train = (training["height_cm"] >= 12).astype(int)
y_validation = (validation["height_cm"] >= 12).astype(int)

fill = SimpleImputer(strategy="mean")
train_water = fill.fit_transform(training[["water_ml"]]).ravel()
train_leaves = np.array([count_yellow_leaf(leaf_images[pot])
                         for pot in training["pot_id"]])
x_train = np.column_stack((train_water / 10, train_leaves))
print("훈련 ID:", training["pot_id"].tolist())
print("훈련에서 배운 물 대체값(ml):", fill.statistics_)
print("X = [물/10ml, 노란 잎 수]:\\n", x_train)
print("X / y shape:", x_train.shape, "/", y_train.shape)
assert np.allclose(fill.statistics_, [20])
assert np.array_equal(x_train, [[0,0], [2,1], [2,2], [4,3]])
"""

cells[19].source = """### 평균은 왜 중심이 될까요?

정답이 0인 훈련 화분의 물은 0ml와 20ml입니다. 대표값 후보를 0·10·20ml로 놓으면, 각 값에서 후보를 뺀 뒤 제곱해 더한 값은 각각 **400·200·400ml²**입니다. 평균 10ml에서 가장 작습니다. 실제로 후보를 m이라 할 때

**(0−m)² + (20−m)² = 2(m−10)² + 200**

제곱은 0 이상이므로 10ml가 이 합을 가장 작게 합니다. 두 값의 분산은 가장 작은 합 200을 개수 2로 나눈 100ml²입니다. 이 성질 때문에 각 정답별 특성의 평균을 **중심**으로 쓰는 방법을 살펴봅니다. 이것이 모든 분류기의 최선이라는 뜻은 아닙니다.

각 정답 c와 입력 열 j에 대해 중심 μ(c,j)는 **그 정답인 훈련 행들의 j열 합 ÷ 그 행의 개수**입니다. 방금 만든 X에서 0의 중심은 [1, 0.5], 1의 중심은 [3, 2.5]입니다. 예를 들어 0의 첫 좌표는 (0+2)÷2=1입니다.

새 입력 x와 중심 μ의 **제곱거리**는 각 열의 차이를 제곱해 더한 Σ(j=1부터 2) (x(j)−μ(c,j))²입니다. 두 값이 음수가 아니므로 제곱근을 계산하지 않아도 어느 쪽이 가까운지 비교할 수 있습니다. 물/10ml와 잎 수를 같은 한 좌표씩 비교하는 선택은 두 특성의 상대적 영향에 영향을 줍니다. 기준을 다르게 정하면 예측이 달라질 수 있습니다. 다음은 여러 가능한 분류기 중 하나입니다.
"""

cells[20].source = """model = NearestCentroid()
model.fit(x_train, y_train)
print("중심에 대응하는 정답:", model.classes_)
print("훈련에서 배운 두 특성의 중심:\\n", model.centroids_)
assert np.allclose(model.centroids_, [[1, 0.5], [3, 2.5]])
"""

cells[21].source = """### 별도 검증에서 예측 확인

훈련에서 배운 20ml 대체값을 검증에 그대로 적용하고, 같은 ID의 잎 관찰을 찾고, **같은 열 순서와 10ml 기준**을 사용합니다. P05는 물 10ml·노란 잎 2개이므로 입력은 [1,2]입니다.

직접 구하면 0의 중심까지 제곱거리 (1−1)²+(2−0.5)²=**2.25**, 1의 중심까지 (1−3)²+(2−2.5)²=**4.25**입니다. 가까운 0을 예측하지만 P05의 나중 높이는 14cm이므로 실제 정답은 1입니다. P06도 확인해 **맞은 수 ÷ 검증 수**를 구하세요.
"""

cells[22].source = """valid_water = fill.transform(validation[["water_ml"]]).ravel()
valid_leaves = np.array([count_yellow_leaf(leaf_images[pot])
                         for pot in validation["pot_id"]])
x_validation = np.column_stack((valid_water / 10, valid_leaves))
print("검증 X:", x_validation)
print("P05의 두 중심까지 제곱거리:",
      ((model.centroids_ - x_validation[0]) ** 2).sum(axis=1))
predictions = model.predict(x_validation)
result = pd.DataFrame({"pot_id": validation["pot_id"].to_numpy(),
                       "actual": y_validation.to_numpy(),
                       "prediction": predictions})
result["correct"] = result["actual"] == result["prediction"]
display(result)
validation_accuracy = result["correct"].sum() / len(result)
print("검증 정확도:", validation_accuracy)
assert predictions.tolist() == [0, 1] and validation_accuracy == 0.5
"""

cells[23].source = """검증 두 화분 중 한 개가 맞아 1/2입니다. 검증이 매우 작고 두 정답 모두 1이어서 현실 성능이나 다른 경우의 정확도를 추정할 수 없습니다. 검증은 모델·설정을 고르는 데 쓸 수 있지만 반복해 같은 검증만 보면 그 자료에 맞춰질 수 있습니다. 모든 선택을 마친 뒤의 **별도 최종 테스트**는 여기 제공하지 않습니다.

또한 [0,4]와 [1,3]은 평균이 모두 2이지만 분산은 각각 4와 1입니다. 중심 하나만 저장하면 퍼짐은 알 수 없습니다. 잎의 위치가 달라도 노란 잎 수와 물이 같으면 이 모델의 두 입력이 같아지므로 두 관찰을 구별하지 못합니다. 어떤 정보를 남길지는 문제에 따라 달라집니다.

훈련 P04의 물 40을 60으로 바꾼 복사본으로 새 대체값과 모델을 fit합니다. 원래 모델은 덮어쓰지 않습니다. **물 20ml·노란 잎 2개**의 예측이 달라질까요? 이 실험은 검증 점수로 두 모델을 고르는 단계가 아닙니다.
"""

cells[24].source = """changed_training = training.copy()
changed_training.loc[changed_training["pot_id"] == "P04", "water_ml"] = 60
changed_fill = SimpleImputer(strategy="mean")
changed_water = changed_fill.fit_transform(changed_training[["water_ml"]]).ravel()
changed_leaves = np.array([count_yellow_leaf(leaf_images[pot])
                           for pot in changed_training["pot_id"]])
changed_x = np.column_stack((changed_water / 10, changed_leaves))
changed_model = NearestCentroid().fit(changed_x, y_train)
probe = np.array([[20 / 10, 2]])
original_prediction = int(model.predict(probe)[0])
changed_prediction = int(changed_model.predict(probe)[0])
print("같은 물 20ml·잎 2개의 원래 / 새 예측:", original_prediction, "/", changed_prediction)
print("원래 / 새 모델 중심:\\n", model.centroids_, "\\n", changed_model.centroids_)
assert (original_prediction, changed_prediction) == (1, 0)
"""

cells[29].source = """## 7. 새로운 문제를 스스로 해결하기

**앞의 완성 예제를 가리고** 입력·정답·ID·시점·출력 조건을 먼저 적으세요. 아래 데이터는 새로운 합성 기기 문제입니다. 값의 뜻이 앞의 잎 관찰과 같다고 가정하지 마세요.

### 합성 기기 점검 명세

한 행은 기기 하나의 현재 관찰입니다. <code>unit</code>은 기기 결과를 찾는 이름이며, <code>signal</code>은 현재 측정값이고 0 또는 빈칸도 가능합니다. <code>panel</code>은 현재 상태를 담은 <code>(2,2,2)</code> 배열이며 축 순서는 행, 열, 채널입니다. **채널 0은 상태**(0=꺼짐, 1=켜짐), **채널 1은 대상**(0=배경, 2=센서)입니다. 배경의 상태 값은 의미가 없습니다. 이 숫자는 종류를 나타내며 숫자 차이가 센서 사이의 거리를 뜻하지 않습니다.

<code>label</code>은 나중에 확인한 <code>정상</code>, <code>점검</code>, <code>?</code> 중 하나이고 <code>?</code>는 미상입니다. 훈련 시에는 정답을 아는 행만 사용하고, 입력으로 쓸 빈 signal은 **알려진 훈련 행의 관측 평균**으로 채웁니다. 검증 정답은 모델을 정한 뒤 확인합니다. 새 기기의 정답은 주어지지 않습니다.

결과는 <code>sample_id,prediction</code> 헤더의 CSV입니다. 예측은 <code>정상</code> 또는 <code>점검</code>이며 요구 ID 순서는 **N7, N3, N1**입니다.

1. 어떤 항목이 언제 주어지는지, 목표·미상·연결용 ID를 적으세요. 학습에 쓸 ID, 관측 signal과 그 평균을 손으로 구하세요. 0과 빈칸은 어떻게 다른가요?
2. T2의 panel에서 <code>[0,1]</code>과 <code>[1,0]</code>의 뜻과 켜진 센서 수를 손으로 구하세요. 복사한 배열에서 배경의 상태만 바꾸거나 행과 열을 바꾸면 각각 무엇이 달라지나요? 코드로 확인하세요.
3. signal과 **panel에서 직접 만든 수치 특성 하나 이상**을 골라 의미·열 순서·shape를 적고, 타당한 학습 분류기를 스스로 선택해 알려진 훈련 행으로 fit하세요. 무엇을 배웠는지 값이나 구조로 설명하세요. 같은 수치 특성이라도 원래 관찰에서 잃을 수 있는 정보가 무엇인가요?
4. 별도 검증 예측·정확도를 구하고 작은 점수의 한계를 적으세요. 새로운 기기의 예측을 요구 순서의 CSV로 만들어 다시 읽고 헤더·행 수·ID·허용값을 검사하세요. 예측만 다른 순서로 옮기고 ID를 그대로 두면 왜 잘못될 수 있나요? 값이 우연히 같다면 겉으로 드러날까요?
5. signal **열 자체가 없거나** ID가 중복된 입력은 어떻게 알릴지 코드와 이유를 적으세요. 빈 값 한 칸을 대체하는 것과 구분하세요.

모델과 특성의 합리적인 선택은 하나만 있는 것이 아닙니다. 아래 입력 다음의 빈 칸에 직접 작성하고, 이유와 도움받은 내용을 남기세요.
"""

cells[30].source = """panel_examples = {
    "A": np.array([[[0,2],[1,0]], [[0,2],[0,0]]]),
    "B": np.array([[[1,0],[1,2]], [[0,2],[0,0]]]),
    "C": np.array([[[1,2],[1,2]], [[0,2],[0,0]]]),
    "D": np.array([[[1,2],[1,2]], [[1,2],[0,0]]]),
}
exercise_train = pd.DataFrame([
    ("T1", 0.0, panel_examples["A"], "정상"),
    ("T2", 2.0, panel_examples["B"], "정상"),
    ("T3", np.nan, panel_examples["C"], "점검"),
    ("T4", 4.0, panel_examples["D"], "점검"),
    ("T5", 6.0, panel_examples["D"], "?"),
], columns=["unit", "signal", "panel", "label"])
exercise_validation = pd.DataFrame([
    ("V9", 0.0, panel_examples["A"], "정상"),
    ("V4", 4.0, panel_examples["D"], "점검"),
    ("V7", 1.0, panel_examples["C"], "점검"),
], columns=["unit", "signal", "panel", "label"])
exercise_input = pd.DataFrame([
    ("N3", 3.5, panel_examples["D"]),
    ("N1", 0.5, panel_examples["A"]),
    ("N7", 3.0, panel_examples["B"]),
], columns=["unit", "signal", "panel"])
exercise_order = ["N7", "N3", "N1"]
print("훈련 / 검증 / 새 기기 행 수:",
      len(exercise_train), len(exercise_validation), len(exercise_input))
"""

cells[31].source = """내가 정리한 항목의 역할·시점, 훈련 ID와 대체 평균:

T2의 축·범주와 직접 계산한 특성, 같은 값이 되는 다른 관찰:

선택한 입력 열·모델 / 배운 값 / 검증 예측과 정확도:

CSV의 ID 순서·내용 확인과 오류 처리:

실행 뒤 달라진 생각 / 받은 도움(없음·힌트·예시·직접 설명):
"""
cells[32].source = "# 새 명세의 특성과 모델을 직접 선택해 작성하고 결과를 확인하세요."

cells[33].source += """
[IOAI 2026 Robot Chasing 국제 개인전 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/2_Robot_Chasing/statement.md)의 관찰은 (8,8,2) 배열 외에 로봇 번호·방향·문장 지시·들고 있는 물체를 포함합니다. 로봇마다 행동이 다를 수 있어 로봇 번호는 입력 단서가 될 수 있습니다. 행은 뒤섞인 독립 스냅샷으로, 이전 관찰·행동은 주어지지 않습니다. 출력은 입력과 같은 순서의 행동 코드 JSON입니다. 위의 (2,2,2) 잎·기기 격자는 별도 합성 연습이며 이 국제 문제 전체를 푼 것이 아닙니다.
"""
for i, c in enumerate(cells):
    new.append(c)
    if i == 12:
        new.extend([grid_intro, grid_code, grid_meaning, grid_count])
book.cells = new
nbformat.validate(book)

with tempfile.TemporaryDirectory(prefix="week01-deep-build-") as tmp:
    os.environ["IPYTHONDIR"] = tmp
    os.environ["MPLCONFIGDIR"] = tmp
    manager = InProcessKernelManager()
    manager.start_kernel()
    shell = manager.kernel.shell
    client = manager.client()
    client.start_channels()
    try:
        for i, cell in enumerate(book.cells):
            if cell.cell_type != "code":
                continue
            client.execute(cell.source, store_history=True)
            reply = client.get_shell_msg(timeout=120)
            if reply["content"]["status"] != "ok":
                raise RuntimeError(f"cell {i}: {reply['content']}")
            cell.execution_count = reply["content"]["execution_count"]
            cell.outputs = []
            while True:
                msg = client.get_iopub_msg(timeout=120)
                if msg["msg_type"] == "status" and msg["content"].get("execution_state") == "idle":
                    break
                if msg["msg_type"] in ("stream", "display_data", "execute_result", "error"):
                    cell.outputs.append(nbformat.v4.output_from_msg(msg))
            if any(o.output_type == "error" for o in cell.outputs):
                raise RuntimeError(f"cell {i} emitted an error")
    finally:
        client.stop_channels()
        manager.shutdown_kernel()
        shell._atexit_once()

notebook_text = nbformat.writes(book) + "\n"
html, _ = HTMLExporter().from_notebook_node(book)
output_dir.mkdir(parents=True, exist_ok=False)
with (output_dir / "week01_integrated.ipynb").open("x", encoding="utf-8") as stream:
    stream.write(notebook_text)
with (output_dir / "week01_integrated.html").open("x", encoding="utf-8") as stream:
    stream.write(html)
print("BUILT", len(book.cells), "cells", sum(c.cell_type == "code" for c in book.cells), "code cells")
