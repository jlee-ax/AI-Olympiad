# 검토용 교량 후보 · 여러 벡터의 쌍별 점수와 ID

> 이 문서는 외부 요구 발견 → 교안 개선 후보 → 재검토 기능을 시험하기 위한 **초안**입니다. 1주차 필수 내용이나 전체 과정 배치를 승인한 문서가 아닙니다. 수업에 넣을지와 위치는 별도 검토가 필요합니다.

## 학습 범위와 선수 지식

대상은 변수·리스트·반복문·함수를 써 본 중학생입니다. 배열의 행과 열, shape와 축, 전치, 같은 순서인 벡터의 내적을 한 번씩 접했다고 가정합니다. 특히 내적은 같은 위치끼리 곱한 후 모두 더합니다. 아직 익숙하지 않다면 두 벡터를 종이에 적어 곱과 합을 먼저 연습합니다.

이 교량의 목표는 **두 벡터의 점곱 하나**에서 **여러 query(질문 대상)와 gallery(후보)의 모든 쌍 점수**로 옮겨 가고, 점수의 위치를 실제 ID에 연결하는 것입니다. 모델을 훈련하거나 이미지가 같은 장소에서 왔는지 판단하는 전체 방법은 다루지 않습니다. 실습 수치는 설명용 합성 자료이고 실제 대회 데이터가 아닙니다.

수식에서 나오는 기호를 먼저 정합니다. 아래 수식 번호는 1부터 세고, 뒤의 Python 인덱스는 0부터 셉니다.

| 기호 | 뜻 | 작은 예제에서 |
|---|---|---:|
| <code>n</code> | query 벡터의 개수(행 수) | 2 |
| <code>m</code> | gallery 벡터의 개수(행 수) | 4 |
| <code>d</code> | 한 벡터의 특성 수. 두 쪽에서 순서와 뜻이 같아야 함 | 3 |
| <code>i</code>, <code>j</code> | 각각 query, gallery의 번호 | <code>1≤i≤n</code>, <code>1≤j≤m</code> |
| <code>k</code> | 곱해서 더할 특성의 번호 | <code>1≤k≤d</code> |
| <code>Q[i,k]</code>, <code>G[j,k]</code> | 각각 i번째 query, j번째 gallery의 k번째 특성 | 수식 번호 |
| <code>S[i,j]</code> | i번째 query와 j번째 gallery의 점수 하나 | 수식 번호 |

기호는 외우기보다, 결과의 한 칸에 들어갈 두 행과 같은 위치의 특성을 손가락으로 짚어 봅니다.

## 기초에서 원리로

벡터 <code>[1, 0, 2]</code>와 <code>[0, 0, 2]</code>의 점곱은 <code>1×0 + 0×0 + 2×2 = 4</code>입니다. 여러 query 행과 gallery 행의 **모든 조합**에서 이 계산을 하면 다음 식이 됩니다.

$$
S_{ij}=\sum_{k=1}^{d} Q_{ik}G_{jk}.
$$

여기서 <code>i</code>와 <code>j</code>를 고정하면 query 한 행과 gallery 한 행이 정해집니다. <code>k</code>만 바꿔 같은 특성끼리 곱한 뒤 더해 점수 하나를 얻습니다. <code>i</code>, <code>j</code>를 각각 바꾸어 빈칸을 모두 채운 표가 점수 행렬입니다.

배열의 행으로 벡터를 놓았다면 <code>G.T</code>는 gallery의 행과 열을 바꿉니다. <code>Q @ G.T</code>는 <code>Q</code>의 각 행과 <code>G</code>의 각 원래 행 사이 점곱을 계산합니다. 여기서 <code>@</code>는 2차원 배열의 행렬곱이고 <code>*</code>는 원소별 곱입니다. 아래처럼 두 입력의 shape가 우연히 같아서 <code>*</code>가 오류 없이 실행돼도, 모든 쌍의 점수표가 나온 것은 아닙니다.

## shape 추적

합성 예제에서 query는 2개, gallery는 4개이고, 각 벡터에는 순서가 같은 특성 3개가 있습니다. ID는 사람이 각 행을 다시 찾는 표식이며, 숫자의 크기가 유사도는 아닙니다.

| 단계 | shape | 각 축의 뜻 |
|---|---|---|
| <code>Q</code> | <code>(n, d) = (2, 3)</code> | query 행, 특성 열 |
| <code>G</code> | <code>(m, d) = (4, 3)</code> | gallery 행, 특성 열 |
| <code>G.T</code> | <code>(d, m) = (3, 4)</code> | 특성 행, gallery 열 |
| <code>Q @ G.T</code> | <code>(n, m) = (2, 4)</code> | query 행, gallery 열 |

2차원 행렬곱의 일반 계약은 <code>(n, d) @ (d, m) → (n, m)</code>입니다. 가운데 두 길이 <code>d</code>가 같아야 하고, 이 축에서 짝별 곱을 더합니다. 바깥 길이는 결과에 남습니다. <code>Q @ G</code>는 <code>(2,3) @ (4,3)</code>이므로 가운데 3과 4가 달라 실행할 수 없습니다. shape가 같더라도 양쪽 특성의 의미와 순서가 맞는지는 따로 확인해야 합니다.

아래 예제의 수식 <code>S[1,4]</code>는 첫 query <code>[1,0,2]</code>와 넷째 gallery <code>[0,0,2]</code>의 점수 4입니다. Python에서는 <code>scores[0,3]</code>입니다. 이 점수의 열 위치 3은 gallery ID 3이 아니라, 같은 순서의 <code>gallery_ids[3]</code>인 35입니다.

여러 묶음을 합칠 때도 축을 확인합니다. 이미 각각 <code>(2,3)</code>인 두 묶음은 <code>concatenate(..., axis=0)</code>로 기존 행 축을 이어 <code>(4,3)</code>이 됩니다. <code>stack(..., axis=0)</code>은 새 묶음 축을 만들어 <code>(2,2,3)</code>이 되며, 입력 묶음의 shape가 같아야 합니다. 반면 <code>concatenate(..., axis=1)</code>은 기존 열 축을 이어 <code>(2,6)</code>이므로 이 예제에서 gallery 네 행을 만드는 방법이 아닙니다. 연결할 축 이외의 길이도 맞아야 합니다.

## 작은 코드

다음은 점수 계산과 ID 복원만 보여 줍니다. 각 ID는 배열의 같은 위치에 있는 벡터의 이름입니다. 이 예제에서 각 행의 최댓값에는 동점이 없습니다. <code>argmax</code>는 각 행의 가장 큰 점수 **위치**를 반환합니다.

<!-- 실행 예제 시작 -->
~~~python
import numpy as np

query_ids = np.array([103, 109])
gallery_ids = np.array([42, 7, 19, 35])
Q = np.array([[1, 0, 2],
              [0, 1, 1]])
G = np.array([[2, 0, 0],
              [0, 2, 1],
              [1, 1, 0],
              [0, 0, 2]])

scores = Q @ G.T                         # (2, 3) @ (3, 4) -> (2, 4)
positions = np.argmax(scores, axis=1)     # gallery 열 위치 [3, 1]
matched_ids = gallery_ids[positions]      # 실제 gallery ID [35, 7]
matches = dict(zip(query_ids, matched_ids))

chunks = [G[:2], G[2:]]
stacked = np.stack(chunks, axis=0)        # (2, 2, 3): 새 축
joined_rows = np.concatenate(chunks, axis=0)  # (4, 3): 기존 행 축
joined_columns = np.concatenate(chunks, axis=1)  # (2, 6): 기존 열 축

print("점수:\n", scores)
print("query ID -> gallery ID:", matches)
print("stack / 행 연결 / 열 연결:",
      stacked.shape, joined_rows.shape, joined_columns.shape)
~~~
<!-- 실행 예제 끝 -->

<code>scores</code>는 <code>[[2,2,1,4],[0,3,1,2]]</code>이며, 결과는 query 103 → gallery 35, query 109 → gallery 7입니다. <code>Q * G[:2]</code>는 두 shape가 모두 <code>(2,3)</code>이어서 오류 없이 실행되지만 결과도 <code>(2,3)</code>인 원소별 곱입니다. 열마다 모든 query와 gallery를 비교하는 점수표는 아닙니다.

행 순서를 섞는다면 해당 벡터와 ID를 **함께 같은 순서**로 옮겨야 합니다. 예를 들어 gallery 행을 <code>[2,0,3,1]</code> 순서로 바꾸면 ID도 같은 순서로 바꾸고, 새 점수 열 위치를 새 ID 배열에서 찾아야 합니다. query를 섞을 때도 마찬가지로 query ID를 함께 옮깁니다. 요구되는 제출 순서가 따로 있으면 마지막에 query ID를 기준으로 그 순서에 맞춥니다. 순위를 나타내는 0부터의 위치에 무조건 1을 더해 ID를 얻는 것은 ID가 순서대로 1부터 빈칸 없이 주어지는 등의 조건이 확인된 경우에만 가능합니다.

### 임베딩이라는 두 쓰임

임베딩은 대상을 숫자 벡터로 표현한 결과를 가리키기도 합니다. PyTorch의 <code>nn.Embedding</code>은 **정수 인덱스로 표의 행 벡터를 찾는 lookup 층**입니다. 예를 들어 인덱스 입력이 <code>(B,T)</code>이고 벡터 길이가 <code>d</code>이면 출력은 <code>(B,T,d)</code>입니다. 여기서 B는 묶음 크기, T는 각 묶음의 인덱스 수입니다.

반면 이미지 **encoder 출력 임베딩**은 이미지 자체를 모델에 넣어 얻은 벡터를 뜻합니다. 공식 Restroom baseline은 시각 encoder의 출력을 모아서 정규화합니다. 이미지 encoder 출력이 곧 <code>nn.Embedding</code>의 정수 인덱스 lookup이라는 뜻은 아닙니다. 이 짧은 자료는 두 용어와 shape의 연결만 보여 주며 임베딩 학습, 모델 훈련 또는 검증 단원을 완성하지 않습니다.

## 삭제된 평가 영역
이 오류 control에는 새 입력 평가가 없습니다.

## 별도 검토: 과제 예시 답안

> 교사용 검토 영역입니다. 실제 독립 평가 전에는 학습자에게 이 영역과 아래 확인 코드를 숨깁니다. 이 과제는 독립 평가를 *위해 설계*되었으나 실제 학습자 응답이나 독립 수행은 아직 관찰하지 않았습니다.

정답 예시: shape는 <code>(2,2) @ (2,3) → (2,3)</code>, 점수는 <code>[[4,2,3],[2,4,3]]</code>입니다. 첫 query와 셋째 gallery는 <code>1×1 + 2×1 = 3</code>입니다. 원래 위치는 <code>[0,1]</code>이고 ID는 <code>[81,6]</code>입니다. 두 배열을 지정된 순서로 함께 섞으면 query 순서는 27,12, 새 gallery 위치는 <code>[2,1]</code>, 관계는 27 → 6, 12 → 81로 보존됩니다.

<code>q @ g</code>의 가운데 길이 2와 3은 다릅니다. <code>q * g[:2]</code>는 shape가 <code>(2,2)</code>인 원소별 곱이며 세 gallery와 모든 쌍을 내지 않습니다. 두 1차원 행을 stack하면 <code>[[0,2],[2,0]]</code>, shape <code>(2,2)</code>이고, concatenate하면 <code>[0,2,2,0]</code>, shape <code>(4,)</code>입니다. 두 <code>(1,2)</code> 행을 <code>axis=1</code>로 연결하면 열을 이어 <code>(1,4)</code>입니다.

<!-- 검토 답안 코드 시작 -->
~~~python
exercise_scores = q @ g.T
exercise_positions = np.argmax(exercise_scores, axis=1)
exercise_ids = g_ids[exercise_positions]
q_order = [1, 0]
g_order = [2, 0, 1]
shuffled_scores = q[q_order] @ g[g_order].T
shuffled_positions = np.argmax(shuffled_scores, axis=1)
shuffled_ids = g_ids[g_order][shuffled_positions]
stacked_vectors = np.stack([g[0], g[1]], axis=0)
joined_vectors = np.concatenate([g[0], g[1]], axis=0)
joined_features = np.concatenate([g[:1], g[1:2]], axis=1)
~~~
<!-- 검토 답안 코드 끝 -->

피드백은 정답 숫자만 보지 않습니다. 한 점수에 곱해진 같은 순서의 특성, 곱셈에서 사라지는 축과 남는 축, 원소별 곱과 전체 쌍의 차이, 새 위치를 ID 배열에 연결하는 근거, stack과 연결 축의 차이를 각각 설명할 수 있는지 확인합니다.

## 기존 교안과의 대조 및 배치 제안

아래 관찰은 보존된 <code>inputs/lesson-source.md</code>의 직접 대조이며, 과정 전체의 다른 자료에는 해당 내용을 다루는 부분이 있을 수 있습니다.

| 이미 있는 내용 | 이 후보가 잇는 미포함 내용 |
|---|---|
| Cell 9·11: 2차원 shape, 축과 평균을 줄이는 과정 | 두 행렬의 수축 축 일치와 <code>(n,d) @ (d,m)</code>으로 모든 쌍의 점수 계산 |
| Cell 60·62: 전치와 reshape의 차이 | gallery를 전치한 열이 원래 어떤 gallery 행인지 추적 |
| Cell 85·86: 1차원 내적, <code>*</code>와 <code>@</code>의 차이 | 직사각형 쌍별 점수표와 위치 → 실제 ID 복원, query·gallery 순서 변경 시 동반 정렬 |
| Cell 85·87: 새 벡터의 내적 연습 | 새 행렬·ID 입력으로 위 흐름과 연결 축을 함께 설명하는 독립 과제 |

자료에는 <code>stack</code>과 <code>concatenate</code>의 새 축/기존 축 비교 및 임베딩 lookup과 encoder 출력의 구분도 없습니다. 이는 관찰된 **공백**이지 1주차에 넣어야 한다는 결정이 아닙니다. 배치는 벡터 내적과 2차원 축·전치를 익힌 뒤, 검색 또는 이미지 표현을 다루는 후속 단원 직전에 작은 교량으로 검토할 수 있습니다. 주차·필수 여부·시간 배분은 미결정입니다.

## 근거와 검증 범위

- [IOAI 2025 공식 Restroom 문제와 baseline](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Restroom/Restroom.ipynb): query와 gallery는 각각 독립적으로 번호가 매겨지고 섞이며, 목표는 같은 화장실의 반대 성별 아이콘입니다. baseline은 encoder 출력들을 이어 정규화하고 행렬곱 후 <code>topk_idxs[:, 1]</code>을 선택합니다. 그 두 번째 순위가 언제나 목표를 만족한다는 보장은 문제 설명에서 나오지 않으며, 이를 정답이나 최적 규칙으로 가정하지 않습니다. 이 후보의 합성 점수에서 최대값을 택한 것은 위치→ID 연습일 뿐 대회 문제의 해결책이 아닙니다.
- NumPy 공식 문서: [matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html), [stack](https://numpy.org/doc/stable/reference/generated/numpy.stack.html), [concatenate](https://numpy.org/doc/stable/reference/generated/numpy.concatenate.html).
- PyTorch 공식 [Embedding](https://docs.pytorch.org/docs/2.15/generated/torch.nn.Embedding.html) 문서: 인덱스로 표를 조회하는 층과 입출력 shape. 문서 조회일 2026-11-11.

이 후보의 코드와 예시 답안에 대한 기계적 검사는 별도 <code>candidate-check.py</code>와 <code>candidate-check.json</code>에 기록합니다. 이는 학습자 이해도, 실제 독립 응답, 이미지 모델의 정확도 또는 전체 교안의 충분성을 증명하지 않습니다.
