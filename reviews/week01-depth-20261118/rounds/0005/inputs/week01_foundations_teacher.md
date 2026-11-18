# 1주차 교사용 해설 · 표와 배열에서 무엇을 한 번씩 셀까?

학생용 파일은 `week01_foundations.ipynb`이다. 예시와 독립 과제의 입력을 분리했다. 학생이 먼저 쓴 답, 실제 실행, 수정 이유를 함께 보면 무엇을 다시 가르쳐야 할지 판단할 수 있다. 세 CSV는 이 수업을 위해 만든 가상 기록이다. 원본 행 순서와 구역표 순서는 의도적으로 다르다.

## 수업 편성

|구분|분|내용|
|---|---:|---|
|이론|20|관측 단위·시점·특성과 정답 5분, 배열의 모양과 축별 평균·분산 15분. 일반식의 한 기호를 실제 표의 행·열·단위에 대응시킨다.|
|비코딩|20|U·V·W의 손계산 10분, 선택형 둘 3분·짧은 서술 4분·해설 3분.|
|코딩|80|Python 진단·수정 20분, CSV 선택·결측·분모와 집계 40분, NumPy·Matplotlib 20분. 다섯 번째 Python 카드는 파일을 열 때 이어 확인한다.|

수업은 120분이다. 수첩의 세 행과 전체 표의 빈칸 목록을 두 번 훑는 대신 앞 세 행에서는 오전 빈칸 한 수만 확인한다. 같은 코드를 복제해 두 번째 수업 그래프를 그리던 자리를 비워, 승객·정류장의 비중 비교와 새 요구 풀이에 약 6~8분을 사용한다. 급히 답을 보여 주기보다 두 요청에서 같은 비중을 받는 대상을 먼저 듣는다. 새 자료로 그래프를 다시 만드는 필수 활동은 자습에서 수행한다. 시간 배분의 근거는 과정 원문의 이론 20분·비코딩 20분·코딩 80분이다. [과정의 1주차 편성](../../curriculum/student-plan.html#week-1)

|필수 자습 묶음|계획상 한도|실제 할 일과 예상 범위|
|---|---:|---|
|문법·배열|150분|함수 오류 복구, 인덱싱·공유·브로드캐스팅·모양 조작, 독립 경기표와 점수. 두 요청에 쓸 연산을 고르고, 기존 사본 정정에서 두 결과를 함께 재검산한다. 원본과 사본을 차례로 같은 값으로 고치는 이중 실험을 대신한다. 약 135~150분.|
|시각화|70분|두 라이브러리 그림, 첫 선택 근거, 기준 변경 해석. 약 60~70분.|
|새 CSV|80분|읽기·집계·병합·한 곳을 뺀 실제 ID 확인은 약 55분. 여러 고장 자료를 모두 만들어 보는 반복 대신 어려움이 생겼을 때만 쓰는 복구 여유 25분을 포함한다.|
|수학·새 세션 점검|60분|분산·단위·점수 손계산을 검산하고 새 세션에서 재실행한다. 약 50~60분. 같은 손계산을 두 묶음에 중복 산입하지 않는다.|

합계 편성은 360분이다. 공통 필수 활동 예상 범위는 **300~335분**이다. 식별자 복구 연습은 필요한 학생만 진행한다. 예시 추적·새 자료 확인 10~20분, 본교안 복귀 확인 3~5분으로 추가분 상한은 **25분**이고 전체 계획 상한은 **360분**이다. 도움이 필요하지 않은 학생은 공통 과제를 끝내면 된다. 실제 소요 시간과 남은 어려움을 따로 기록한다. 과정의 주당 필수 자습 5~7시간을 바탕으로 한 편성 추정이다. [과정 계획](../../curriculum/student-plan.html#week-1) · [W1 단원 명세](../../skills/koai-evaluate/references/unit-specifications.json)

## 사전 준비와 진단

Python 3, NumPy, pandas, Matplotlib, Seaborn 0.12 이상이 있는 Jupyter에서 노트북 폴더 또는 저장소 루트를 작업 폴더로 삼는다. 완성 답을 요구하는 칸에는 과제 입력과 기록 공간을 두었다. 의도적으로 실패하는 추적 문제에서는 실패 기록 자체가 관찰 자료다. Run All은 예제와 파일 경로를 점검한다. 풀이 증거는 학생이 새 입력 칸에 작성한 코드·설명에서 확인한다. 수식 표기 `(n,)`에서 쉼표는 축이 하나인 shape 표기다.

### Python 카드

|카드|기대 답과 확인|
|---|---|
|1. 대입|`books`는 3에서 5가 되어 다음 곱의 값은 10이다. `label`은 문자 그대로 `"books"`다.|
|2. 조건·반복|네 번 돈다. `hits`는 차례로 0, 0, 1, 1이다. `None`에서 두 번째 조건을 건너뛰고, 기준과 같은 3은 초과 조건을 만족하지 않는다.|
|3. 반환과 경계|포함 조건이면 관측값 3과 5가 통과한다. 반환값 2에 1을 더하면 3이다. 음수 기준은 비교를 시작하기 전에 `ValueError`다. `print`만 한 함수는 `None`을 반환해 이어지는 덧셈에서 `TypeError`가 난다.|
|4. 리스트|`codes[2]`는 `"B"`, `codes[1:3]`은 `["C", "B"]`. 잘라 만든 리스트의 첫 항목을 바꿔도 원래 첫 두 값은 `["A", "C"]`다. 이 예의 문자열 원소는 불변이다.|
|5. CSV와 오류|첫 줄은 여섯 열 이름, 둘째 줄은 `R1,A,2,4,6,7` 한 관측이다. 파일 열기에서 난 `FileNotFoundError`면 폴더·파일명을, 이미 읽은 표에서 난 `KeyError`면 실제 열 이름과 철자를 점검한다. `lunch_book`의 올바른 원본 이름은 `lunch_books`다.|

```python
def count_at_least(counts, limit):
    if limit < 0:
        raise ValueError("기준은 0 이상이어야 합니다.")
    hits = 0
    for books in counts:
        if books is not None and books >= limit:
            hits += 1
    return hits

assert count_at_least([3, None, 5, 0], 3) + 1 == 3
assert [count_at_least(example, 0) for example in ([], [0], [None])] == [0, 1, 0]
try:
    count_at_least([3], -1)
except ValueError as error:
    print(type(error).__name__)
```

`trace-example`에서 실제 예외의 마지막 두 프레임을 출력한다. `scan_batch`가 `count_over(values, 4)`를 호출했고, `count_over`의 `books > limit`에서 문자열 `"7"`과 정수 4를 비교해 `TypeError`가 발생한다. 단순 문자열 출력 대신 실제 호출 스택과 멈춘 연산이 일치하는지 확인한다. 실행 환경에서 보이는 파일명과 줄 번호는 달라질 수 있다.

`trace-independent`의 첫 시도에서는 `last_box(["B", "C"])`가 `len(codes) = 2`를 `code_at`에 전달한다. `code_at`의 `codes[position]`에서 유효 범위 0·1 밖의 2를 읽어 `IndexError`가 발생한다. 실패한 줄과 잘못된 번호가 생긴 호출 줄을 모두 짚게 한다. 빈 목록의 반환 약속을 지키는 수정 예시는 다음과 같다.

```python
def fixed_last_box(codes):
    if not codes:
        return None
    return code_at(codes, len(codes) - 1)

assert fixed_last_box(["B", "C"]) == "C"
assert fixed_last_box(["A"]) == "A"
assert fixed_last_box([]) is None
```

빈 목록은 길이 0·비교 0회·반환 0, [0]은 길이 1·비교 1회·반환 1, [None]은 길이 1·숫자 비교 0회·반환 0이다. `if books:`는 관측한 0을 탈락시킨다. 이 실패에는 `[0]`과 기준 0을 재입력하고 두 조건을 한 줄씩 읽게 한다. Python 카드 목표는 5개 중 4개다. 미달하면 실패한 유형에만 다른 입력을 주고 다시 작성·설명하게 한다. 단순한 출력 복사는 정답으로 세지 않는다.

## 수첩과 원본 CSV

수첩 세 줄에서 점심 5권 이상은 R1·R3이고 하교 권수는 7·4다. 오전의 관측한 0은 R2 한 칸, 빈칸은 R3 한 칸이다. R3을 0으로 채우면 책이 없었다는 측정이 생겨 분모도 바뀐다. 점심 끝에 수집을 마친 세 열은 사용 가능한 특성이며 하교 권수는 이후의 목표다. 기록 ID는 관찰 한 건, 반납함 ID는 여러 날짜가 공유하는 대상이다.

전체 표는 6행 6열이다. `record_id`·`box_id`는 문자열 계열, `open_books`·`lunch_books`는 정수 계열이다. 기본 CSV 추론에서 `break_books`와 `after_books`는 각각 빈칸 하나가 있어 실수 계열로 읽힌다. 설치 버전에 따라 문자열 자료형의 표시 이름은 다를 수 있다. `R3.break_books`와 `R5.after_books`가 미관측이다. 개관 4권 이상을 골라 출력할 열은 `record_id, open_books, after_books`이다. R2(8, 3), R4(4, 0), R5(6, 미관측)로 선택 3행, 하교 관측 2행이다. 선택한 행을 남긴 채 관측 열에서 분모를 세는지 확인한다.

```python
picked = returns.loc[returns["open_books"] >= 4,
                     ["record_id", "open_books", "after_books"]]
print(picked, len(picked), picked["after_books"].count())
```

## 축·분산·필기

R1·R2의 입력은 (2, 3)이다. 개관 열의 (누적합, 관측 수)는 (0, 0) → (2, 1) → (10, 2)로 변한다. 두 번째 행 다음에 멈춰 10/2=5권을 얻는다. 10/3은 열 세 개를 분모에 잘못 쓴 값이다. 열 합 [10, 4, 10]을 기록 수 2로 나누면 구간별 [5, 2, 5]권, shape (3,)이다. 행 합 [12, 12]를 구간 수 3으로 나누면 기록별 [4, 4]권, shape (2,)이다. R1 분산은 8/3권², R2는 평균 4에서의 차이가 [4, −4, 0]이고 제곱합이 32이므로 32/3권²이다. 평균만 같아도 수거 한 회에 8권이 몰린 R2의 변동은 더 크다.

|U·V·W 손계산|기대 답|
|---|---|
|1. 입력|3개 기록 × 2개 구간, (3, 2).|
|2. `axis=0`|열 합 [6, 15] ÷ 3 = [2, 5]권. 구간마다 하나, (2,).|
|3. `axis=1`|행 합 [9, 9, 3] ÷ 2 = [4.5, 4.5, 1.5]권. 기록마다 하나, (3,).|
|4. 한 행 추가|열별 출력 길이는 2로 유지된다. 행별 출력 길이는 3에서 4로 늘어난다. 새 행이 열 평균의 값은 바꿀 수 있다.|

목표는 네 문제 중 세 개다. 길이와 값의 변화를 구분해 듣는다. 분모가 바뀌었다면 종이에서 한 결과 칸에 참여한 원소를 동그라미 치고 그 개수로 다시 나누게 한다.

필기 답은 ㉡, ㉢이다. 오전의 실제 평균은 (4+0)/2=2권이다. 0을 빈칸으로 오인하면 4/1=4권으로 막대가 높아진다. U·V·W 코드에서는 `new_counts.mean(axis=0)` 및 `new_counts.mean(axis=1)`의 값과 shape를 모두 확인한다.

### 한 행과 같은 비중을 받는 단위

`weighting-principle`의 첫 표에서 0분은 실제 관측이다. 유효 승객 3명의 대기 합 18분을 3으로 나누면 6분이다. 관측이 있는 정류장 2곳의 평균 3분·12분을 같은 비중으로 모으면 7.5분이다. 관측 0건인 ‘다’는 평균이 미정이다. 모든 집단을 대표한다는 주장을 하려면 ‘다’의 측정이 필요하다. 모든 집단에 관측이 없으면 어느 방식도 평균을 정할 수 없다.

`class-transfer`에서 승객에게 한 장씩 주면 (3+3+9+12)/4 = 27/4 = **6.75분**이다. 정류장 대표에게 한 장씩 주면 ‘가’는 15/3=5분, ‘나’는 12/1=12분이고, 두 수의 평균은 **8.5분**이다. ‘다’에 0을 붙이면 실제 0분을 관측한 정류장이 새로 생긴 것처럼 분모가 3이 된다. 독립 풀이에서는 두 답의 단위가 모두 분이라는 사실과 누가 한 번씩 반영되는지를 함께 듣는다. 집단 관측 수가 같거나 집단 평균이 같으면 결과가 일치할 수 있어, 숫자 하나만으로 선택을 판정하기 어렵다.

```python
waits = pd.DataFrame({"stop": ["가", "가", "가", "나", "다"],
                      "minutes": [3, 3, 9, 12, np.nan]})
per_stop = waits.groupby("stop")["minutes"].mean()
assert waits["minutes"].count() == 4 and per_stop.count() == 2
assert waits["minutes"].mean() == 6.75 and per_stop.mean() == 8.5
assert pd.isna(per_stop["다"])
```

## 자습 배열과 수학

- 예시에서 둘째 행 첫 값은 8, shape ()이다. 둘째 행은 [8, 0, 4], (3,)이고 첫 두 열은 [[2, 4], [8, 0]], (2, 2)다. 뷰의 첫 원소를 바꾸면 원본 첫 행은 [2, 9, 6]이 되고 보관 열은 [4, 0]이다. 두 공유 검사는 각각 참·거짓이다.
- 구간 보정 후 예시는 [[3, 4, 8], [9, 0, 6]], 날짜 보정 후에는 [[3, 5, 7], [10, 2, 6]]이다. (2, 3)과 (2,)는 오른쪽 길이 3·2가 충돌한다.
- 재배열 후 예시는 [[2, 4], [6, 8], [0, 4]], 전치 후에는 [[2, 8], [4, 0], [6, 4]]다. [0, 1]은 각각 원래 [0, 1]의 4와 [1, 0]의 8이다. (4, 2)에는 원소가 8개 필요해 두 개 부족하다.
`array-lab`과 `array-independent`의 경기표에서는 학생이 예시를 가리고 두 요청의 출력 모양과 단위부터 정한다.

|요청|기대 출력과 그 근거|
|---|---|
|항목별 게시판|[[1, 3, 2], [4, 0, 5]], (2, 3), 단위 회. 원자료 E의 통과는 [1, 0]의 3회이므로 게시판 [0, 1]로 간다. `reshape(2, 3)`도 모양은 같지만 [0, 1]에 D의 경계선 횟수 4를 넣는다.|
|팀별 최종 점수|자료 열이 통과·경계 순서이므로 가중치는 [3, −2]점/회다. 팀별 항목 기여는 D [3, −8], E [9, 0], F [6, −10]점이다. 합은 [−5, 9, −4]점이고 모양은 (3,)이다. 규정 순서를 그대로 붙이면 [10, −6, 11]점이다. E는 통과만 3회여서 이 잘못된 부호를 쉽게 잡는다.|

`math-lab`에서는 실행 전에 두 결과를 각각 예측했는지 본다. F의 경계선 5→2회는 원자료 [2, 1]에서 게시판 [1, 2]로 간다. 게시판은 [[1, 3, 2], [4, 0, 2]]로 한 칸만 3회 줄고 모양 (2, 3)은 같다. F의 감점이 −10점에서 −4점으로 바뀌므로 총점은 −4점에서 2점으로 **6점 오른다**. 나머지 두 팀은 그대로여서 새 점수는 [−5, 9, 2]점, 모양 (3,)이다. 예측·정정 사본의 실제 재실행·설명이 두 요청 모두에 있어야 이 확인을 마친다.

손으로 열을 재배치하거나 반복문으로 항목별 기여를 더해도 좌표·순서·단위가 같으면 수용한다. 작업 대상이 팀이면 팀별 값이 남는다는 설명을 확인한다. 합에 가중치 수를 나눈 답은 총점 요구와 다르다.

- F 경계선 한 칸은 5회, shape ()다. E 한 행은 [3, 0], (2,)이고 경계선만 한 열로 고르면 [[4], [0], [5]], (3, 1)이다. 사본의 F 경계선만 5→2로 고치면 원자료 [2, 1]은 5로 유지된다. 원본 열의 뷰에서 고치면 초기 5를 보존할 수 없다.
- 항목별 보정 결과는 [[1, 6], [3, 2], [2, 7]], 팀별 보정 결과는 [[2, 5], [5, 2], [5, 8]]이다. 팀별 보정은 (3, 1) 모양으로 세 팀과 대응시킨다.
- P와 Q의 통과 횟수 합은 각각 9회, 관측 수는 3, 평균은 3회다. 평균과 차이는 [−3, 0, 3], [−1, 0, 1]이다. 제곱합 18·2를 3으로 나누면 각각 6회², 2/3회²이다. Q의 기록이 더 고르다.

```python
notice = np.array([[1, 4], [3, 0], [2, 5]])
printed_rule = np.array([-2, 3])
aligned = printed_rule[[1, 0]]
def outputs_for(records, weights):
    team_scores = np.array([np.dot(team, weights) for team in records])
    return records.T, team_scores

board, scores = outputs_for(notice, aligned)
print(board, board.shape, scores, scores.shape)
assert board[0, 1] == notice[1, 0] == 3
assert notice.reshape(2, 3)[0, 1] == 4
assert scores.tolist() == [-5, 9, -4]
for part in (notice[2, 1], notice[1, :], notice[:, 1:2]):
    print(part, part.shape)
corrected = notice.copy()
corrected[2, 1] = 2
new_board, new_scores = outputs_for(corrected, aligned)
print(new_board, new_board.shape, new_scores, new_scores.shape)
assert board.shape == new_board.shape == (2, 3)
assert scores.shape == new_scores.shape == (3,)
assert notice[2, 1] == board[1, 2] == 5
assert np.shares_memory(notice, notice[:, 1]) and not np.shares_memory(notice, corrected)
assert new_board[1, 2] == 2 and np.count_nonzero(new_board != board) == 1
assert new_scores.tolist() == [-5, 9, 2]
assert (new_scores - scores).tolist() == [0, 0, 6]
print(notice + np.array([0, 2]))
print(notice + np.array([1, 2, 3]).reshape(3, 1))
for trials in ([0, 3, 6], [2, 3, 4]):
    print(np.mean(trials), np.var(trials, ddof=0))
```

## 병합과 두 그림의 예시

구역표 순서는 C→A→B다. 이 CSV에서 빈 필드는 결측으로 읽고 이름은 문자로 읽는다. 이름의 양끝 공백을 제거해 남은 글자가 없으면 결측으로 통일한다. 숫자 열은 이 변환을 거치지 않는다. 이름이 비어 있는 오른쪽 키는 먼저 제외한다. 왼쪽 기록의 미연결 여부는 `_merge`에서 확인하고 `record_id`를 유지한다. 원본에는 미연결 기록이 없다. 책장 예시에서 `left_on="shelf_tag"`와 `right_on="symbol"`이 서로 다른 키 이름을 대응시킨다. K1의 M은 1층과 연결된다. K2의 빈 표시는 오른쪽 빈 키와 합쳐지지 않아 K2가 미연결로 남고 9층이 붙지 않는다. 원본 여섯 행의 구역은 East, West, East, West, West, West다. R2는 B로 연결되므로 West다. East는 2행·관측 2·합 11·평균 5.5권이다. West는 4행·관측 3·합 12·평균 4권이다. R4의 0은 분모에 넣고 R5의 빈 하교 기록은 제외한다. 구역 합은 West가 더 크고 기록당 평균은 East가 더 크다. 합은 관측한 기록의 수도 반영한다.

원본 하교 권수 [7, 3, 4, 0, 9]를 경계 [0, 2, 4, 6, 8, 10]에 담으면 각 칸의 기록 수는 [1, 1, 1, 1, 1]이다. 정수 눈금 0과 1에서 다섯 범위가 모두 같은 높이이며 유일한 최빈 범위는 없다. 4 이상 6 미만에는 R3만 있다. 세로축 ‘기록 수’와 구역 막대의 ‘관측 기록당 권수’는 단위가 다르다. 히스토그램 칸 높이의 합 5는 하교 관측 수와 같다.

## 새 일지 독립 과제

`transfer-brief`와 `transfer-first-code`에서 그림 종류·열·가로와 세로 단위·한 표시의 뜻을 학생이 먼저 선택한다. `transfer-table`에 들어 있는 표·그림 실마리를 열기 전의 답과 도움 여부를 보존한다. 도움 후 완성한 결과는 구현을 평가하는 데 쓰고, 도움 없이 선택한 근거는 앞의 기록으로 판단한다. Python과 배열도 각각 첫 시도, 받은 도움, 실행 뒤 수정 내용을 대조한다.

공개한 새 입력만을 위한 예시 해설이다. 다른 코드로 같은 관찰 단위 및 오류 처리를 보이는 풀이도 인정한다. 아래 코드는 노트북에서 `data_dir`, `np`, `pd`, `plt`, `sns`를 불러온 뒤 실행할 수 있다.

```python
def text_id(values):
    return values.astype("string").str.strip().replace("", pd.NA)

def read_returns(path):
    return pd.read_csv(path, dtype={"slip": "string", "station": "string"},
                       keep_default_na=False, na_values=[""])

def attach_zones(frame, lookup):
    required = ["slip", "station", "morning_count", "pause_count",
                "meal_count", "closing_count"]
    for field in required:
        if field not in frame.columns:
            raise KeyError(field)
    for field in ["box_id", "zone"]:
        if field not in lookup.columns:
            raise KeyError(field)
    slips = text_id(frame["slip"])
    if slips.isna().any():
        positions = [i for i, missing in enumerate(slips.isna(), 1) if missing]
        raise ValueError("기록 이름이 빈 입력 순번", positions)
    if not slips.is_unique:
        duplicates = slips[slips.duplicated(keep=False)].unique().tolist()
        raise ValueError("중복된 기록 이름", duplicates)
    observed = frame.assign(station=text_id(frame["station"]))
    right = lookup.assign(box_id=text_id(lookup["box_id"]))
    known = right.loc[right["box_id"].notna(), ["box_id", "zone"]]
    result = observed.merge(known, left_on="station", right_on="box_id",
                            how="left", validate="many_to_one", indicator=True)
    unknown = result.loc[result["_merge"] == "left_only", "slip"].tolist()
    if unknown:
        raise ValueError("구역을 찾지 못한 기록", unknown)
    missing_zone = result.loc[result["zone"].isna(), "slip"].tolist()
    if missing_zone:
        raise ValueError("구역 이름이 빈 기록", missing_zone)
    return result.drop(columns="_merge")

def summarize_returns(linked, cutoff):
    lunch = linked["meal_count"]
    selected = linked.loc[lunch.notna() & (lunch >= cutoff)].copy()
    grouped = selected.groupby("zone")["closing_count"]
    summary = grouped.agg(rows="size", observed="count", mean_books="mean")
    summary["sum_books"] = grouped.sum(min_count=1)
    return selected, summary[["rows", "observed", "sum_books", "mean_books"]]

new = read_returns(data_dir / "foundations_returns_transfer.csv")
lookup = pd.read_csv(data_dir / "foundations_boxes.csv", dtype={"box_id": "string"},
                     keep_default_na=False, na_values=[""])
print(new.shape, new.dtypes, new.isna().sum(), sep="\n")
print(new[["morning_count", "pause_count", "meal_count", "closing_count"]])
linked = attach_zones(new, lookup)
reversed_lookup = attach_zones(new, lookup.iloc[::-1])
pd.testing.assert_frame_equal(linked, reversed_lookup)
assert len(linked) == len(new)
print(linked[["slip", "station", "zone"]])
for cutoff in (4, 6):
    selected, summary = summarize_returns(linked, cutoff)
    print(cutoff, selected["slip"].tolist(), summary, sep="\n")
```

새 파일은 8행 6열이다. 문자열 계열 `slip`은 고유하고 `station`은 되풀이된다. 개관 `morning_count`는 정수 계열, 오전 `pause_count`·점심 `meal_count`·하교 `closing_count`는 기본 읽기에서 실수 계열이다. 빈칸은 T6의 오전, T7의 점심, T3의 하교에 하나씩 있다. 수량 단위는 모두 해당 구간의 권이다. 점심 끝에 개관·오전·점심을 알고 하교 반납량은 이후에 관측한다. `new.dropna()`로 모든 빈 행을 먼저 지우면 점심과 하교를 모두 센 T6까지 잃는다. 대응은 T1→West, T2→East, T3→West, T4→East, T5→West, T6→West, T7→East, T8→West다.

|점심 기준|구역|선택 행 수|하교 관측 수|하교 합(권)|하교 평균(권/관측 기록)|
|---|---|---:|---:|---:|---:|
|4 이상|East|1|1|0|0|
|4 이상|West|4|3|13|13/3 ≈ 4.33|
|6 이상|East|1|1|0|0|
|6 이상|West|2|2|6|3|

기준 4는 T1·T3·T4·T6·T8, 기준 6은 T4·T6·T8이다. 기준 4에서 T3은 적격이지만 하교 미관측이다. T4의 하교 0은 두 기준 모두 분모에 든다. 점심이 빈 T7은 하교가 12권이어도 점심 기준을 판정할 수 없다. 기준을 높이면 West에서 T1(하교 7권)과 T3(하교 미관측)이 빠져 분자는 13에서 6으로, 분모는 3에서 2로 줄어든다. East는 T4 한 건만 남아 평균이 0이다.

```python
try:
    attach_zones(new.drop(columns=["meal_count"]), lookup)
except KeyError as error:
    print(type(error).__name__, error)

duplicate = pd.concat([lookup, lookup.iloc[[0]]], ignore_index=True)
print(duplicate.loc[duplicate["box_id"].duplicated(keep=False), "box_id"])
try:
    attach_zones(new, duplicate)
except pd.errors.MergeError as error:
    print(type(error).__name__, error)

def expect_unmatched(frame, mapping, ids):
    original_frame, original_mapping = frame.copy(), mapping.copy()
    try:
        attach_zones(frame, mapping)
    except ValueError as error:
        assert error.args == ("구역을 찾지 못한 기록", ids)
        print("미연결 기록", ids)
    else:
        raise AssertionError("연결 근거가 없는 기록을 확인해야 합니다.")
    pd.testing.assert_frame_equal(frame, original_frame)
    pd.testing.assert_frame_equal(mapping, original_mapping)

unmatched = new.copy()
unmatched.loc[unmatched["slip"] == "T1", "station"] = "Z"
unmatched.loc[unmatched["slip"] == "T2", "station"] = ""
blank_key = pd.DataFrame({"box_id": [""], "zone": ["West"]})
with_blank = pd.concat([lookup, blank_key], ignore_index=True)
expect_unmatched(unmatched, with_blank, ["T1", "T2"])

from tempfile import TemporaryDirectory
from pathlib import Path

with TemporaryDirectory() as scratch:
    path = Path(scratch) / "blank_station.csv"
    path.write_text("slip,station,morning_count,pause_count,meal_count,closing_count\n"
                    "001,,0,2,3,4\n002,,1,0,4,0\n", encoding="utf-8")
    blank = read_returns(path)
    assert blank["closing_count"].tolist() == [4, 0]
    expect_unmatched(blank, with_blank, ["001", "002"])
    inferred = pd.read_csv(path, dtype={"slip": "string"})
    expect_unmatched(inferred, with_blank, ["001", "002"])

without_c = lookup.loc[lookup["box_id"] != "C"]
expect_unmatched(new, without_c, ["T3", "T6", "T8"])
assert len(attach_zones(new, lookup)) == len(new)
```

`transfer-faults`의 필수 검산에서는 뺀 반납함에 따라 A면 T2·T4·T7, B면 T1·T5, C면 T3·T6·T8이 영향을 받는다. 정상 구역표를 복구하면 처음의 8개 기록 이름이 모두 유지된다. 아래의 중복·양쪽 빈 키·빈 CSV 검사는 교사용 추가 검산이다.

누락 열은 `KeyError('meal_count')`다. 처음 구역표 행 C를 복제하면 `MergeError`다. 검증 없이 붙이면 C가 붙는 T3·T6·T8이 각각 두 행이 되어 8행이 11행이 된다. T1의 반납함은 Z, T2의 반납함은 빈칸이다. 오른쪽 구역표에 빈 키와 West가 적혀 있어도 두 기록 모두 미연결이다. 왼쪽 병합 직후 두 행은 보존되며 함수는 실제 기록 이름 T1·T2를 알린다. 반납함 열이 전부 빈 실제 CSV도 모든 입력 행의 기록 이름을 보고한다. 행 이름 자체가 빈 경우에는 자료의 첫 번째 관찰을 1로 세어 해당 입력 순번을 알린다. 내부 병합으로 잃어버리거나 구역 빈칸을 임의로 하나의 구역에 넣는 풀이에는 어떤 학생 기록이 사라졌는지 찾게 한다.

```python
edges = [0, 3, 6, 9, 12, 15]
fig, axes = plt.subplots(2, 2, figsize=(10, 6.3), sharey="col")
for row, cutoff in enumerate((4, 6)):
    selected, summary = summarize_returns(linked, cutoff)
    measured = selected["closing_count"].dropna()
    hist_ax, zone_ax = axes[row]
    sizes, _, _ = hist_ax.hist(measured, bins=edges, color="#216869", edgecolor="white")
    hist_ax.set_yticks(range(int(max(sizes)) + 1))
    hist_ax.set(title=f"Lunch >= {cutoff} books", xlabel="After-school books per record",
                ylabel="Number of records", xticks=edges)
    sns.barplot(data=summary.reset_index(), x="zone", y="mean_books",
                order=["East", "West"], errorbar=None, color="#956438", ax=zone_ax)
    zone_ax.set(title=f"After school | lunch >= {cutoff} books", xlabel="Zone",
                ylabel="Mean books per\nobserved record")
    print(cutoff, np.histogram(measured, bins=edges)[0].tolist())
fig.tight_layout(h_pad=1.6)
plt.show()
```

두 히스토그램의 높이는 기준 4에서 [2, 1, 1, 0, 0], 기준 6에서 [2, 1, 0, 0, 0]이다. 첫 칸은 두 경우 모두 T4(0)·T8(1), [6, 9) 칸은 기준 4에서만 T1(7)이다. 0권은 실제 관측이어서 첫 칸과 관측 분모에 들어간다. T3의 미관측은 어떤 권수 칸에도 들어가지 않는다. `sharey="col"`로 두 분포끼리, 두 평균 그림끼리 눈금 범위가 같다.

사서에게는 “측정한 기록 가운데 West 평균은 약 4.33권에서 3권으로 낮아졌고 관측 수도 3건에서 2건으로 줄었습니다. East는 한 건의 0권으로 두 조건에서 같습니다. 가장 자주 관측한 범위는 두 조건 모두 0 이상 3권 미만입니다” 정도로 답할 수 있다. 여덟 합성 기록을 비교한 결과다. 관찰한 장소·날짜를 넘어선 일반화나 점심 때문에 하교 반납이 변한다는 인과 해석을 뒷받침하지 않는다.

### 조건부 식별자 복구

본교안 `transfer-faults`에서 중복 원인이나 실제 미연결 기록 이름을 찾지 못했을 때 [식별자 연결 복구 연습](week01_foundations_repair.ipynb)을 연다. 다른 셀의 실행 상태나 추가 CSV 없이 시작할 수 있다. 예시에서는 B1의 두 구역이 충돌한다. 확인된 원본으로 위치표를 복구한 뒤 M07과 M12는 미연결로 남고 총 4행이 유지된다.

`repair-return`·`repair-fresh`의 독립 재검사에서 중복 키는 G2, 영향을 받는 방문은 J9다. 시설 원본을 사용하면 J6은 North, J9는 South, J2는 미연결이고 3행이 남는다. J2에 Top을 배정하면 양쪽 빈 이름을 같은 것으로 오인한 결과다. 확인 후 본교안 `transfer-faults`에서 앞서 뺀 곳과 **다른** 반납함으로 예상과 실제 ID를 대조한다. 이를 통과하면 원래의 두 그림 과제를 이어 간다. 도움이 필요하지 않은 학생에게 복구 노트북 실행을 요구하지 않는다.

## 학생 풀이를 볼 때

|학생이 보여 줄 것|특히 살필 흔적|막혔을 때 다시 물을 말|
|---|---|---|
|Python 반환값과 실패 설명|빈 목록, 관측한 0, 경계와 음수 기준을 자신의 함수로 실행|“화면에 보인 값과 다음 줄에 실제로 전달된 값은 각각 무엇이니?”|
|표·자료사전·병합|열 이름·시점·dtype·shape·열별 결측·고유 키, 뒤집은 구역표와 원래 구역표의 대응 일치|“어느 열을 기준으로 그 행을 빼야 했니? 원래 한 행이 합친 뒤 몇 행이 됐니?”|
|손계산과 배열|두 축의 값·모양·분모, 뷰와 복사의 대조, 오른쪽 축 정렬, 전치 좌표, 분산과 내적 단위|“그 출력 한 칸을 만들 때 읽은 원래 칸을 모두 가리켜 볼래?”|
|서로 다른 라이브러리로 만든 두 그림과 해석|실마리 전 학생이 고른 그림·열·단위와 도움 표시, 분포와 구역 비교의 다른 세로 단위, 두 기준의 재계산, 유효 관측 수와 한계|“이 막대 한 개에 실제로 들어간 기록 이름은 무엇이니?”|

고정된 구간의 출현 횟수를 정확히 담은 막대·점 그림, 구역별 관측 평균을 정확히 담은 막대·점 그림 등을 인정한다. 빈도 그림은 구간 경계와 건수, 구역 비교는 평균과 유효 관측 수의 해석을 갖춰야 한다. 두 그림이 같은 수량을 반복하거나 범주 빈도로 평균을 대신하면 해당 목표를 충족하지 못한다.

실제 학생의 독립 수행, 받은 도움, 재시도와 소요 시간은 교사가 수업 후 따로 기록한다. 채점할 때는 공개한 새 입력에 대한 답을 학생용 노트북에 미리 넣지 않는다.

## 자료와 참고 문서

과정 내 1주 편성과 실전 범위, 네 단원 목표의 근거는 저장소 내 원문에서 확인한다. [10주 학습 계획](../../curriculum/student-plan.html#week-1) · [단원 명세](../../skills/koai-evaluate/references/unit-specifications.json) · [KOAI 출제 기준](https://kitpa.org/koai/syllabus)

Python의 조건·반복·함수와 반환값은 공식 튜토리얼에 설명되어 있다. [Python 제어 흐름](https://docs.python.org/ko/3/tutorial/controlflow.html) · [오류와 예외](https://docs.python.org/ko/3/tutorial/errors.html)

배열 모양·축·전치, 뷰와 복사, 브로드캐스팅, 분산과 두 1차원 벡터의 내적은 NumPy 문서를 따른다. [NumPy 기초](https://numpy.org/doc/stable/user/absolute_beginners.html) · [가중평균의 합·분모](https://numpy.org/doc/stable/reference/generated/numpy.average.html) · [축 전치](https://numpy.org/doc/stable/reference/generated/numpy.transpose.html) · [뷰와 복사](https://numpy.org/doc/stable/user/basics.copies.html) · [브로드캐스팅](https://numpy.org/doc/stable/user/basics.broadcasting.html) · [분산](https://numpy.org/doc/stable/reference/generated/numpy.var.html) · [내적](https://numpy.org/doc/stable/reference/generated/numpy.dot.html)

CSV 읽기, 결측 검사, 키 병합과 그룹 통계는 pandas 문서에서 확인할 수 있다. [표 입문](https://pandas.pydata.org/docs/getting_started/intro_tutorials/index.html) · [CSV 읽기](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html) · [병합](https://pandas.pydata.org/docs/user_guide/merging.html) · [병합 키의 빈값 처리](https://pandas.pydata.org/docs/reference/api/pandas.merge.html) · [그룹 통계](https://pandas.pydata.org/docs/user_guide/groupby.html)

막대의 의미와 구간 경계는 두 라이브러리의 해당 함수 문서를 참고한다. [Matplotlib 히스토그램](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.hist.html) · [Seaborn 막대그래프](https://seaborn.pydata.org/generated/seaborn.barplot.html)
