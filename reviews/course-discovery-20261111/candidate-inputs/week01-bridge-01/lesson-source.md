## Cell 0: 06c67cfc (markdown)

# 1주차 보충 · 표에서 점수와 ID까지

## 목표와 이용 방법

표의 행과 열에서 출발해 **같은 뜻의 값을 곱해 더하는 이유**, 행렬곱의 모양과 축, 결과 위치를 실제 ID로 바꾸는 방법을 연습합니다. 모든 숫자는 설명을 위해 만든 합성 자료입니다.

본 교안의 행·열, shape, 전치, 내적을 먼저 접한 뒤 사용합니다. 변수·리스트·함수를 써 보았다고 가정합니다. 먼저 예상과 이유를 적고 코드로 확인하며, 다르게 예상했다면 첫 단계부터 살펴보세요. Python 3와 NumPy만 필요합니다. Jupyter에서 위에서 아래로 Shift+Enter를 누르고 저장하세요.

**우선:** 1~3절, 5절의 검색과 ID, 6절 필수 문항. **선택 교량:** 4절의 stack·concatenate, 5절의 lookup과 6절 선택 문항은 관련 후속 단원 전에 다시 써도 됩니다. 후속 공식 범위의 필수 학습을 면제한다는 뜻은 아닙니다.

이 자료는 120분 수업 뒤, 계획된 1주차 필수 자습의 배열 A·내적 E와 연결하는 보충입니다. 기존 수업에 새 시간을 추가했다고 가정하지 않습니다. 중복 연습은 교사와 조정하되 기존 필수 성취를 생략하지 마세요. 기존 자습 5~7시간은 이전 범위의 추정치이며 이 보충을 포함한 실제 시간은 아직 모릅니다. 시간이 부족하면 미완료를 기록하고 보충 시간을 다시 계획합니다.


## Cell 1: 09b00247 (markdown)

## 1. 표를 숫자 배열로 옮기기

| 화분 ID | 빛 점수 | 물 점수 |
|---|---:|---:|
| P11 | 2 | 1 |
| P24 | 1 | 3 |
| P38 | 3 | 2 |

두 점수는 예제를 위한 단위 없는 숫자입니다. 한 **행**은 화분 한 개, 한 **열**은 정해진 특성 하나입니다. 숫자만 꺼낸 X에서 두 축은 각각 화분과 특성을 뜻합니다. ID는 숫자 특성이 아니라 행을 찾는 이름으로 따로 둡니다.

**먼저 예상:** X의 shape와 첫 행을 쓰세요. P24는 Python에서 몇 번째 위치의 행인가요? 특성 순서를 바꾸고도 원래 이름을 붙이면 어떤 문제가 생길까요?


## Cell 2: ba428b91 (code)

import numpy as np

plant_ids = np.array(["P11", "P24", "P38"])
X = np.array([[2, 1], [1, 3], [3, 2]])
print("X =\n", X)
print("shape:", X.shape, "/ 첫 행:", X[0])
print("위치 1의 ID:", plant_ids[1])
assert X.shape == (3, 2)


## Cell 3: e81d6244 (markdown)

첫 축 길이 3은 화분 수, 둘째 축 길이 2는 특성 수입니다. <code>X[1]</code>은 두 번째 화분 P24의 벡터 <code>[1, 3]</code>입니다. Python 위치는 0부터 셉니다. shape가 같아도 ‘빛, 물’ 순서가 ‘물, 빛’으로 바뀌면 같은 의미가 아닙니다.

### 두 벡터의 내적

첫 화분의 벡터 <code>[2, 1]</code>에 가중치 <code>[1, 2]</code>를 적용합니다. 첫 값은 빛에, 둘째 값은 물에 대응합니다. 같은 뜻끼리 곱해 더하면 <code>2×1 + 1×2 = 4</code>입니다. 일반적으로 길이 d인 u, w의 내적은 다음과 같습니다.

**u · w = u[0]×w[0] + … + u[d−1]×w[d−1]**

길이와 위치별 뜻이 모두 맞아야 합니다. 원소별 곱은 각 곱을 남기고, 내적은 그 곱들의 합 하나를 만듭니다.


## Cell 4: 5ebb633b (code)

one_plant = X[0]
weight = np.array([1, 2])
print("원소별 곱:", one_plant * weight)
print("내적:", one_plant @ weight)
assert one_plant @ weight == 4


## Cell 5: 39e31964 (markdown)

## 2. 한 행의 내적을 여러 행과 여러 출력으로

다음 변환은 학습된 모델이 아닙니다. 입력은 ‘빛, 물’ 순서이며 세 출력은 차례로 ‘빛’, ‘물’, ‘빛 + 물의 두 배’라는 계산 규칙입니다.

| W의 행 | 출력 1 | 출력 2 | 출력 3 |
|---|---:|---:|---:|
| 빛에 곱할 값 | 1 | 0 | 1 |
| 물에 곱할 값 | 0 | 1 | 2 |

W의 한 **열**이 출력 하나에 쓸 가중치 벡터입니다. P11의 세 번째 출력은 X의 첫 행과 W의 셋째 열의 내적 <code>2×1 + 1×2 = 4</code>입니다. P24의 세 번째 출력도 직접 계산해 보세요.

| 배열 | shape | 축의 뜻 |
|---|---|---|
| X | (3, 2) | 화분, 입력 특성(빛·물) |
| W | (2, 3) | 입력 특성(빛·물), 출력 규칙 |
| Y = X @ W | (3, 3) | 화분, 출력 규칙 |

일반적으로 <code>(n, d) @ (d, m) → (n, m)</code>입니다. 가운데 두 길이 d가 같아야 같은 입력 특성을 하나씩 짝지어 곱하고 **그 축을 따라 더할** 수 있습니다. 왼쪽 행 축 n과 오른쪽 열 축 m은 결과에 남습니다. 식은 <code>Y[i, j] = Σ(k=0…d−1) X[i, k] × W[k, j]</code>입니다. i는 화분 위치, j는 출력 규칙 위치, k는 더할 입력 특성 위치입니다.

이 예제는 편향 없이 가중합으로 입력 벡터를 새 출력 벡터로 옮기는 **선형 변환**입니다. 같은 입력 특성 순서가 전제입니다. 가중치를 배우는 방법이나 결과의 타당성은 여기서 확인하지 않습니다.


## Cell 6: ae4dc17f (code)

W = np.array([[1, 0, 1], [0, 1, 2]])
Y = X @ W
print("X @ W =\n", Y)
print("shape:", X.shape, "@", W.shape, "→", Y.shape)
print("P24의 세 번째 출력:", Y[1, 2])
assert np.array_equal(Y, [[2, 1, 4], [1, 3, 7], [3, 2, 7]])


## Cell 7: bf96efdf (markdown)

### 모양 오류와 뜻 오류는 다릅니다

<code>W @ X</code>의 가운데 길이는 3과 3이어서 계산은 되지만 결과 행은 화분 행이 아닙니다. 가능하다는 것만으로 원하는 변환이 되지는 않습니다. 반면 <code>X @ X</code>는 <code>(3, 2) @ (3, 2)</code>에서 가운데 2와 3이 달라 실행할 수 없습니다. 예제는 오류를 잡아 이름만 출력하므로 전체 실행은 멈추지 않습니다.


## Cell 8: cb88ba54 (code)

print("W @ X는 실행 가능하지만 shape:", (W @ X).shape)
try:
    X @ X
except ValueError as error:
    print("X @ X:", type(error).__name__, "— 가운데 길이 2와 3이 다릅니다.")


## Cell 9: 25e2b1ff (markdown)

## 3. <code>*</code>와 <code>@</code>는 다른 질문입니다

아래 두 입력은 모두 shape가 <code>(2, 2)</code>입니다. 먼저 두 결과의 왼쪽 위와 오른쪽 아래 값을 예상하세요. <code>*</code>는 같은 위치끼리 곱합니다. <code>@</code>는 왼쪽 행과 오른쪽 열의 짝별 곱을 더합니다. 결과 shape까지 같아도 값과 의미가 다릅니다.


## Cell 10: e9bd32e9 (code)

A = np.array([[2, 1], [1, 3]])
identity = np.array([[1, 0], [0, 1]])
print("원소별 A * identity =\n", A * identity)
print("행렬곱 A @ identity =\n", A @ identity)
assert (A * identity).shape == (A @ identity).shape == (2, 2)
assert not np.array_equal(A * identity, A @ identity)


## Cell 11: d033f80f (markdown)

## 4. 선택 교량 · 묶음을 새로 만들까, 기존 축에 이을까?

이 절은 배열 축을 편하게 다룰 때 먼저 시도합니다. <code>stack</code>이 대회에서 항상 필수라는 뜻은 아닙니다.

first와 second는 각각 <code>(2, 3)</code>입니다. 행은 후보 하나, 열은 특성 세 개입니다.

- <code>stack([first, second], axis=0)</code>: 앞에 **새 묶음 축**, <code>(2, 2, 3)</code>. 묶음 × 후보 × 특성.
- <code>concatenate([first, second], axis=0)</code>: 기존 후보 행 축을 이어 <code>(4, 3)</code>.
- <code>concatenate([first, second], axis=1)</code>: 기존 특성 열 축을 이어 <code>(2, 6)</code>. 새 후보 네 행이 아닙니다.

세 shape와 축 이름을 먼저 쓰세요. stack은 입력 shape가 모두 같아야 합니다. concatenate는 잇는 축을 제외한 나머지 축 길이가 같아야 합니다.


## Cell 12: 51e17d9e (code)

first = np.array([[1, 0, 2], [0, 1, 1]])
second = np.array([[2, 0, 0], [0, 2, 1]])
bundled = np.stack([first, second], axis=0)
joined_rows = np.concatenate([first, second], axis=0)
joined_columns = np.concatenate([first, second], axis=1)
print("새 묶음 축:", bundled.shape)
print("기존 행 축 연결:", joined_rows.shape)
print("기존 열 축 연결:", joined_columns.shape)
print("첫 묶음의 첫 후보:", bundled[0, 0])
try:
    np.stack([first[:1], second], axis=0)
except ValueError as error:
    print("서로 다른 모양을 stack:", type(error).__name__)
try:
    np.concatenate([first, second[:, :2]], axis=0)
except ValueError as error:
    print("잇지 않는 열의 길이가 다름:", type(error).__name__)
assert (bundled.shape, joined_rows.shape, joined_columns.shape) == ((2, 2, 3), (4, 3), (2, 6))


## Cell 13: bbd63f75 (markdown)

## 5. 여러 쌍의 점수에서 실제 ID 찾기

두 질문과 네 후보를 세 특성(둥글기·채움·밝기 점수)의 벡터로 나타냅니다. 점수들은 이미 주어졌다고 가정합니다. **큰 내적을 고르는 규칙은 이 합성 연습의 약속**입니다. 실제 유사도는 벡터의 크기, 정규화와 문제의 평가 규칙에 따라 달라집니다.

| 배열 | shape | 축의 뜻 |
|---|---|---|
| Q | (2, 3) | 질문, 세 특성 |
| G | (4, 3) | 후보, 세 특성 |
| G.T | (3, 4) | 세 특성, 후보 |
| S = Q @ G.T | (2, 4) | 질문, 후보 |

G.T는 G의 행과 열을 바꿉니다. S의 한 칸은 질문 한 행과 후보 한 행의 내적입니다. 첫 질문 <code>[1, 0, 2]</code>과 넷째 후보 <code>[0, 0, 2]</code>는 <code>1×0 + 0×0 + 2×2 = 4</code>입니다.

**먼저 예상:** 두 질문의 최댓값이 있는 0부터 세는 **열 위치**와 그 위치의 **후보 ID**를 따로 적으세요. ID의 숫자 크기는 점수가 아닙니다.


## Cell 14: 3950021e (code)

query_ids = np.array([103, 109])
candidate_ids = np.array([42, 7, 19, 35])
Q = np.array([[1, 0, 2], [0, 1, 1]])
G = np.array([[2, 0, 0], [0, 2, 1], [1, 1, 0], [0, 0, 2]])
scores = Q @ G.T
positions = np.argmax(scores, axis=1)
matched_ids = candidate_ids[positions]
print("점수표:\n", scores)
print("최댓값의 열 위치:", positions)
print("질문 ID → 후보 ID:", dict(zip(query_ids.tolist(), matched_ids.tolist())))
assert np.array_equal(scores, [[2, 2, 1, 4], [0, 3, 1, 2]])
assert np.array_equal(matched_ids, [35, 7])


## Cell 15: 2449ef26 (markdown)

첫 질문의 최댓값 위치는 3, 실제 후보 ID는 <code>candidate_ids[3] = 35</code>입니다. 둘째 질문은 위치 1, 후보 ID 7입니다. 이 예의 최댓값에는 동점이 없습니다. 동점이면 NumPy <code>argmax</code>는 첫 위치를 반환하지만 실제 과제에 동점 규칙이 있으면 그 규칙을 따릅니다.

### 같은 shape인데 ID가 바뀌는 반례

후보 행 순서를 바꿀 때 ID를 함께 바꾸지 않으면 점수표와 ID 목록의 shape는 그대로지만 이름표가 잘못 붙습니다. 아래에서 103과 109의 결과를 각각 비교하세요.


## Cell 16: ff882ec6 (code)

order = np.array([2, 0, 3, 1])
G_shuffled = G[order]
correct_ids = candidate_ids[order]
new_positions = np.argmax(Q @ G_shuffled.T, axis=1)
right = correct_ids[new_positions]
wrong = candidate_ids[new_positions]  # 행만 섞고 ID는 그대로 둔 실수
print("이전/새 G shape:", G.shape, G_shuffled.shape)
print("새 점수의 열 위치:", new_positions)
print("ID도 같이 이동:", right)
print("ID를 그대로 둔 오류:", wrong)
assert np.array_equal(right, [35, 7])
assert np.array_equal(wrong, [19, 35])


## Cell 17: 36acbf6f (markdown)

행과 ID는 항상 같은 순서로 옮기고, 제출할 때 요구된 질문 ID 순서도 확인합니다. <code>위치 + 1</code>이 실제 ID라는 규칙은 따로 주어졌을 때만 쓸 수 있습니다. 길이뿐 아니라 **각 위치가 누구를 가리키는지** 확인해야 합니다.

### 선택 교량 · lookup과 임베딩

색인으로 숫자표의 한 행을 찾는 것을 lookup이라고 합니다. 토큰 인덱스는 이 표에서 **0, 1, 2번 행**을 가리키며, 다른 데이터의 임의 ID와 자동으로 같지는 않습니다. ID 41처럼 별도 이름을 쓰면 ID→행 위치 대응표가 먼저 필요합니다.


## Cell 18: d81386f3 (code)

table = np.array([[0, 2], [2, 1], [1, 3]])
token_indices = np.array([[2, 0], [1, 2]])
looked_up = table[token_indices]
external_id_to_row = {41: 2, 87: 0}
print("인덱스 (묶음, 위치):", token_indices.shape)
print("조회 결과 (묶음, 위치, 벡터):", looked_up.shape)
print("ID 41을 대응표로 찾아 얻은 벡터:", table[external_id_to_row[41]])
assert looked_up.shape == (2, 2, 2)


## Cell 19: 5cd8c35a (markdown)

입력 인덱스가 <code>(B, T)</code>, 표의 각 벡터 길이가 d이면 출력은 <code>(B, T, d)</code>입니다. B는 묶음 수, T는 묶음 안 인덱스 수입니다. PyTorch Embedding은 이와 같은 정수 인덱스 lookup을 제공하는 층입니다. 여기의 숫자표는 학습하지 않았습니다. 이미지 인코더가 이미지에서 만든 출력 벡터도 임베딩이라 부르지만 그것이 곧 정수 인덱스 lookup이라는 뜻은 아닙니다. 인코더 실행·표현 학습은 후속 주차에서 다룹니다.


## Cell 20: 4ac3bb9a (markdown)

## 6. 낯선 입력으로 혼자 풀기

**먼저 앞의 완성 예제와 별도 교사용 해설을 가리세요.** 아래 자료는 새 합성 입력입니다. 답을 적은 뒤 코드 셀에 직접 작성하고 실행하세요. 답을 복사하거나 빈 셀을 실행한 것은 독립 수행이 아닙니다.

### 필수 A · 새 선형 변환

행은 세 학생의 활동 점수 a, b입니다. W_new의 두 열은 각각 새 점수 규칙입니다.

1. X_new와 W_new 및 <code>X_new @ W_new</code>의 shape와 각 축의 뜻을 적으세요. 모든 결과를 손으로 구하고, 두 번째 행 첫 점수에 어떤 곱을 더했는지 쓰세요.
2. <code>X_new[:2] * W_new</code>와 <code>X_new[:2] @ W_new</code>는 둘 다 <code>(2, 2)</code>입니다. 각각의 값을 구해 왜 다른지 설명하세요.
3. <code>X_new @ bad_W</code>는 왜 안 되나요? <code>X_new[:, ::-1] @ W_new</code>는 실행되더라도 첫 행 첫 결과가 왜 달라지나요? a, b 순서를 가중치와 연결해 설명하세요.
4. 아래 빈 코드 셀에 두 연산과 shape를 직접 작성해 손계산을 확인하세요. 오류는 이유를 먼저 쓴 뒤 필요하면 예제처럼 잡아서 확인하세요.


## Cell 21: ec433d3b (code)

# 독립 문제 입력: 각 행은 학생 한 명, 열 순서는 a, b입니다.
X_new = np.array([[1, 4], [2, 1], [0, 3]])
W_new = np.array([[2, 0], [1, 3]])
bad_W = np.ones((3, 2), dtype=int)


## Cell 22: f2068453 (markdown)

내 예상·계산과 축의 뜻:

모양 오류와 순서 오류를 구분한 이유:

실행 뒤 달라진 생각 / 받은 도움(없음·힌트·예시·직접 설명):


## Cell 23: 7b96a39e (code)

# 필수 A: 자신의 확인 코드를 작성하세요.


## Cell 24: 2442117e (markdown)

### 필수 B · 순서를 바꾼 검색 결과

<code>query_new</code>와 <code>gallery_new</code>의 행은 같은 순서의 두 특성을 가진 벡터입니다. 한 질문에 대해 모든 후보의 내적을 구하고 가장 큰 점수의 후보를 고르세요. 이 데이터의 각 질문은 최댓값이 하나입니다.

1. 점수표의 shape와 모든 값을 구하세요. 각 질문의 **위치**와 실제 **후보 ID**를 따로 쓰고, 관계를 질문 ID → 후보 ID로 적으세요.
2. 후보 행을 <code>[2, 0, 3, 1]</code> 순서로 옮기세요. 후보 ID도 똑같이 옮겼을 때 각 질문의 새 위치와 실제 ID를 쓰세요.
3. 후보 행만 옮기고 ID를 옮기지 않으면 두 질문의 어떤 잘못된 ID가 나오나요? shape가 같아도 틀린 이유를 설명하세요.
4. 점수표, 위치, 올바른 ID를 구하는 코드를 직접 쓰고 출력으로 확인하세요.


## Cell 25: 07c93362 (code)

q_ids_new = np.array([61, 22])
g_ids_new = np.array([90, 8, 53, 17])
query_new = np.array([[1, 2], [2, 1]])
gallery_new = np.array([[2, 1], [0, 3], [1, 1], [2, 0]])


## Cell 26: 619d5445 (markdown)

내 점수표와 위치 / ID:

순서를 바꾼 뒤 위치 / ID 및 ID만 남긴 오류:

실행 뒤 달라진 생각 / 받은 도움(없음·힌트·예시·직접 설명):


## Cell 27: 54646dc1 (code)

# 필수 B: 자신의 확인 코드를 작성하세요.


## Cell 28: 2882691e (markdown)

### 선택 C · 묶음 만들기

<code>gallery_new[:2]</code>와 <code>gallery_new[2:]</code>로 stack(axis=0), concatenate(axis=0), concatenate(axis=1)을 실행하기 전에 결과 shape와 축의 뜻을 적으세요. <code>gallery_new[:1]</code>과 <code>gallery_new[1:]</code>은 어떤 연산이 실패하고 어떤 행 연결이 가능한지도 이유와 함께 예측하세요. 별도 코드 셀을 만들어 확인합니다.

## 다음 단계

10주차 새 문제에서는 입력·출력·평가 규칙을 다시 읽고 열과 ID의 의미를 먼저 적습니다. 이 자료의 1주차 선수는 3주차 가중합, 6주차 층별 shape, 7~9주차 인코더 표현·검색, 10주차 낯선 입력 해석으로 이어집니다. 후속 모델 구현, 분할·학습·평가, 대회 문제 해결을 이 노트북 하나로 완료했다고 볼 수는 없습니다.

## 자료와 범위

- [1주차 본 교안](week01_python_tables.ipynb): 표·axis, 전치, 내적. [10주 학습 계획](../../curriculum/student-plan.html): 기존 수업 및 자습 편성.
- [IOAI 2025 Restroom 공식 문제와 baseline](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Restroom/Restroom.ipynb)은 후보 번호·순서와 벡터 점수를 검토하는 계기입니다. 실제 baseline은 이미지 인코더 출력 연결·정규화와 별도의 선택 규칙을 사용합니다. 이 단순 합성 내적의 최댓값 규칙은 공식 정답이나 대회 해결법이 아닙니다.
- [NumPy matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html), [stack](https://numpy.org/doc/stable/reference/generated/numpy.stack.html), [concatenate](https://numpy.org/doc/stable/reference/generated/numpy.concatenate.html), [argmax](https://numpy.org/doc/stable/reference/generated/numpy.argmax.html), [PyTorch Embedding](https://docs.pytorch.org/docs/2.15/generated/torch.nn.Embedding.html).
- [KOAI 2027 안내](https://kitpa.org/koai/2027)에 연결된 [국내 실라버스](https://kitpa.org/koai/syllabus)는 조사 당시 IOAI 2026 기준 표기였습니다. 별도 [IOAI 2027 원문](https://ioai-official.org/wp-content/uploads/2026/11/IOAI_Syllabus.pdf)의 국제 항목을 국내 2027 확정 범위나 1주차 필수로 자동 취급하지 않습니다. 확인 기록: [source-research.md](../../reviews/discovery-loop-20261111/source-research.md), 2026-11-11. 최신 공지를 다시 확인하세요.

교안의 숫자와 문제는 자체 제작 자료입니다. 실제 학생의 소요 시간·이해·도움 없이 푼 결과는 아직 관찰하지 않았습니다.


