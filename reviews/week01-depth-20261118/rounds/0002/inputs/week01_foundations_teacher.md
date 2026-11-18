# 1주차 교사용 해설 · 반납함은 언제 붐빌까?

학생용 파일은 `week01_foundations.ipynb`이다. 예시와 독립 과제의 입력을 분리했다. 학생이 먼저 쓴 답, 실제 실행, 수정 이유를 함께 보면 무엇을 다시 가르쳐야 할지 판단할 수 있다. 세 CSV는 이 수업을 위해 만든 가상 기록이다. 원본 행 순서와 구역표 순서는 의도적으로 다르다.

## 수업 편성

|구분|분|내용과 관찰 지점|
|---|---:|---|
|이론|20|자료사전으로 한 행·시점·특성·정답을 짚는 데 5분, 두 기록으로 평균·분산·shape·축을 설명하는 데 15분. 분산은 차이와 단위까지만 함께 도입한다.|
|비코딩|20|U·V·W의 축별 손계산에 10분, 선택형 두 문항 3분·짧은 서술 4분·해설 3분. 수첩 세 행은 표를 읽을 때 구두로 짚는다.|
|코딩|80|Python 절차 추적·수정 20분. CSV 읽기·자료형·선택·결측·오류 40분. 배열과 Matplotlib 20분(배열 실행 5분, 그림 작성·원자료 연결 15분). 다섯 번째 Python 카드는 파일을 여는 장면에서 마저 확인한다.|

합계 120분이다. U·V·W는 먼저 종이에서 풀고 같은 입력을 배열 셀에서 확인한다. R1·R4는 기존 그림에서 행 두 개만 바꾸어 대조한다. 입력부터 그래프까지 새 절차를 쓰는 긴 과제는 수업 밖에 둔다.

필수 자습은 5~7시간 편성 안에서 6시간을 예상한다. 문법·배열 150분, 시각화 70분, 새 CSV 80분, 수학·새 세션 점검 60분이다. 활동을 목표별로 세면 Python 90분, 표 85분, 배열·수학 115분, 시각화 70분이다. 문법·배열에서 Python 90분과 배열 60분, 마지막 점검에서 배열·수학 55분과 표 5분을 쓴다. 예시 읽기, 새 입력 작성, 실패 수정, 설명을 포함한 편성 추정이다. 실제 학생 소요 시간은 학생별로 기록한다.

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

필기 답은 ㉡, ㉢이다. 오전의 실제 평균은 (4+0)/2=2권이다. 0을 빈칸으로 오인하면 4/1=4권으로 막대가 높아진다. R1·R4의 세로 막대는 [(2+4)/2, (4+2)/2, (6+0)/2] = [3, 3, 3]권이다. 앞서 가장 높았던 개관과 점심의 공동 1위가 세 구간 동률로 바뀐다. 같은 세로 한계 0~6권에서 읽는다. U·V·W 코드 검산은 `new_counts.mean(axis=0)` 및 `new_counts.mean(axis=1)`의 값과 shape를 모두 확인한다.

## 자습 배열과 수학

- 예시에서 둘째 행 첫 값은 8, shape ()이다. 둘째 행은 [8, 0, 4], (3,)이고 첫 두 열은 [[2, 4], [8, 0]], (2, 2)다. 뷰의 첫 원소를 바꾸면 원본 첫 행은 [2, 9, 6]이 되고 보관 열은 [4, 0]이다. 두 공유 검사는 각각 참·거짓이다.
- 구간 보정 후 예시는 [[3, 4, 8], [9, 0, 6]], 날짜 보정 후에는 [[3, 5, 7], [10, 2, 6]]이다. (2, 3)과 (2,)는 오른쪽 길이 3·2가 충돌한다.
- 재배열 후 예시는 [[2, 4], [6, 8], [0, 4]], 전치 후에는 [[2, 8], [4, 0], [6, 4]]다. [0, 1]은 각각 원래 [0, 1]의 4와 [1, 0]의 8이다. (4, 2)에는 원소가 8개 필요해 두 개 부족하다.
- D·E·F에서 F 점심은 5, shape ()다. E는 [3, 0], (2,)이고 점심 열은 [[4], [0], [5]], (3, 1)이다. `notice[:, 1]`은 (3,)이라 한 열짜리 2차원 조건을 충족하지 않는다. 첫 열 뷰로 고치면 원본 D의 개관도 11, 별도 사본에는 원래 1이 남는다. 새 복사본만 고칠 때 원본 D는 1이다.
- 독립 구간 보정은 [[1, 6], [3, 2], [2, 7]], 날짜 보정은 [[2, 5], [5, 2], [5, 8]]이다. 날짜 벡터는 (3, 1)이 되어야 한다. `notice.reshape(2, 3)[0, 1]`은 D 점심 4, `notice.T[0, 1]`은 E 개관 3이다.
- [0, 3, 6]과 [2, 3, 4]는 각각 합 9, 개수 3, 평균 3권이다. 차이는 [−3, 0, 3]과 [−1, 0, 1]이고 제곱합 18과 2를 3으로 나누면 6권²과 2/3권²이다. 첫날의 반납이 한 구간에 더 몰린다. 세 분류별 시간은 [6, 0, 4]초, 내적은 10초다. 시간표를 뒤집어 그대로 곱하면 [1, 5, 2]초/권이어서 일반과 대형의 시간이 뒤바뀌고 합 11초가 나온다. 순서를 일치시켜 10초를 회복한다.

```python
notice = np.array([[1, 4], [3, 0], [2, 5]])
for part in (notice[2, 1], notice[1, :], notice[:, 1:2]):
    print(part, part.shape)
working = notice.copy()
view = working[:, 0]
saved = view.copy()
view[0] = 11
print(working, saved, np.shares_memory(working, saved))
working = notice.copy()
saved = working[:, 0].copy()
saved[0] = 11
print(working, saved)
print(notice + np.array([0, 2]))
print(notice + np.array([1, 2, 3]).reshape(3, 1))
print(notice.reshape(2, 3), notice.T)
for day in ([0, 3, 6], [2, 3, 4]):
    print(np.mean(day), np.var(day, ddof=0))
print(np.dot([3, 0, 4], [2, 5, 1]))
```

## 병합과 두 그림의 예시

구역표 순서는 C→A→B다. 이름이 비어 있는 오른쪽 키는 먼저 제외한다. 왼쪽 기록의 미연결 여부는 `_merge`에서 확인하고 `record_id`를 유지한다. 원본에는 미연결 기록이 없다. 책장 예시에서 `left_on="shelf_tag"`와 `right_on="symbol"`이 서로 다른 키 이름을 대응시킨다. K1의 M은 1층과 연결된다. K2의 빈 표시는 오른쪽 빈 키와 합쳐지지 않아 K2가 미연결로 남고 9층이 붙지 않는다. 원본 여섯 행의 구역은 East, West, East, West, West, West다. R2는 B로 연결되므로 West다. East는 2행·관측 2·합 11·평균 5.5권이다. West는 4행·관측 3·합 12·평균 4권이다. R4의 0은 분모에 넣고 R5의 빈 하교 기록은 제외한다. 구역 합은 West가 더 크고 기록당 평균은 East가 더 크다. 합은 관측한 기록의 수도 반영한다.

원본 하교 권수 [7, 3, 4, 0, 9]를 경계 [0, 2, 4, 6, 8, 10]에 담으면 각 칸의 기록 수는 [1, 1, 1, 1, 1]이다. 정수 눈금 0과 1에서 다섯 범위가 모두 같은 높이이며 유일한 최빈 범위는 없다. 4 이상 6 미만에는 R3만 있다. 세로축 ‘기록 수’와 구역 막대의 ‘관측 기록당 권수’는 단위가 다르다. 히스토그램 칸 높이의 합 5는 하교 관측 수와 같다.

## 새 일지 독립 과제

`transfer-brief`와 `transfer-first-code`에서 그림 종류·열·가로와 세로 단위·한 표시의 뜻을 학생이 먼저 선택한다. `transfer-table`에 들어 있는 표·그림 실마리를 열기 전의 답과 도움 여부를 보존한다. 도움 후 완성한 결과는 구현을 평가하는 데 쓰고, 도움 없이 선택한 근거는 앞의 기록으로 판단한다. Python과 배열도 각각 첫 시도, 받은 도움, 실행 뒤 수정 내용을 대조한다.

공개한 새 입력만을 위한 예시 해설이다. 다른 코드로 같은 관찰 단위 및 오류 처리를 보이는 풀이도 인정한다. 아래 코드는 노트북에서 `data_dir`, `np`, `pd`, `plt`, `sns`를 불러온 뒤 실행할 수 있다.

```python
def attach_zones(frame, lookup):
    required = ["slip", "station", "morning_count", "pause_count",
                "meal_count", "closing_count"]
    for field in required:
        if field not in frame.columns:
            raise KeyError(field)
    for field in ["box_id", "zone"]:
        if field not in lookup.columns:
            raise KeyError(field)
    if frame["slip"].isna().any() or not frame["slip"].is_unique:
        raise ValueError("관찰 기록 이름을 확인하세요.")
    known = lookup.loc[lookup["box_id"].notna(), ["box_id", "zone"]]
    result = frame.merge(known, left_on="station", right_on="box_id",
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

new = pd.read_csv(data_dir / "foundations_returns_transfer.csv")
lookup = pd.read_csv(data_dir / "foundations_boxes.csv")
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

unmatched = new.copy()
unmatched.loc[unmatched["slip"] == "T1", "station"] = "Z"
unmatched.loc[unmatched["slip"] == "T2", "station"] = pd.NA
blank_key = pd.DataFrame({"box_id": [pd.NA], "zone": ["West"]})
with_blank = pd.concat([lookup, blank_key], ignore_index=True)
try:
    attach_zones(unmatched, with_blank)
except ValueError as error:
    assert error.args == ("구역을 찾지 못한 기록", ["T1", "T2"])
    print(type(error).__name__, error.args[1])
else:
    raise AssertionError("연결 근거가 없는 두 기록을 확인해야 합니다.")

assert len(attach_zones(new, lookup)) == len(new)
```

누락 열은 `KeyError('meal_count')`다. 처음 구역표 행 C를 복제하면 `MergeError`다. 검증 없이 붙이면 C가 붙는 T3·T6·T8이 각각 두 행이 되어 8행이 11행이 된다. T1의 반납함은 Z, T2의 반납함은 빈칸이다. 오른쪽 구역표에 빈 키와 West가 적혀 있어도 두 기록 모두 미연결이다. 왼쪽 병합 직후 두 행은 보존되며 함수는 실제 기록 이름 T1·T2를 알린다. 내부 병합으로 잃어버리거나 구역 빈칸을 임의로 하나의 구역에 넣는 풀이에는 어떤 학생 기록이 사라졌는지 찾게 한다.

```python
edges = [0, 3, 6, 9, 12, 15]
fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharey="col")
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
    zone_ax.set(title=f"Lunch >= {cutoff} books", xlabel="Zone",
                ylabel="Mean after-school books per observed record")
    print(cutoff, np.histogram(measured, bins=edges)[0].tolist())
fig.tight_layout()
plt.show()
```

두 히스토그램의 높이는 기준 4에서 [2, 1, 1, 0, 0], 기준 6에서 [2, 1, 0, 0, 0]이다. 첫 칸은 두 경우 모두 T4(0)·T8(1), [6, 9) 칸은 기준 4에서만 T1(7)이다. 0권은 실제 관측이어서 첫 칸과 관측 분모에 들어간다. T3의 미관측은 어떤 권수 칸에도 들어가지 않는다. `sharey="col"`로 두 분포끼리, 두 평균 그림끼리 눈금 범위가 같다.

사서에게는 “측정한 기록 가운데 West 평균은 약 4.33권에서 3권으로 낮아졌고 관측 수도 3건에서 2건으로 줄었습니다. East는 한 건의 0권으로 두 조건에서 같습니다. 가장 자주 관측한 범위는 두 조건 모두 0 이상 3권 미만입니다” 정도로 답할 수 있다. 여덟 합성 기록을 비교한 결과다. 관찰한 장소·날짜를 넘어선 일반화나 점심 때문에 하교 반납이 변한다는 인과 해석을 뒷받침하지 않는다.

## 학생 풀이를 볼 때

|학생이 보여 줄 것|특히 살필 흔적|막혔을 때 다시 물을 말|
|---|---|---|
|Python 반환값과 실패 설명|빈 목록, 관측한 0, 경계와 음수 기준을 자신의 함수로 실행|“화면에 보인 값과 다음 줄에 실제로 전달된 값은 각각 무엇이니?”|
|표·자료사전·병합|열 이름·시점·dtype·shape·열별 결측·고유 키, 뒤집은 구역표와 원래 구역표의 대응 일치|“어느 열을 기준으로 그 행을 빼야 했니? 원래 한 행이 합친 뒤 몇 행이 됐니?”|
|손계산과 배열|두 축의 값·모양·분모, 뷰와 복사의 대조, 오른쪽 축 정렬, 전치 좌표, 분산과 내적 단위|“그 출력 한 칸을 만들 때 읽은 원래 칸을 모두 가리켜 볼래?”|
|별도의 두 라이브러리 그림과 해석|실마리 전 학생이 고른 그림·열·단위와 도움 표시, 분포와 구역 비교의 다른 세로 단위, 두 기준의 재계산, 유효 관측 수와 한계|“이 막대 한 개에 실제로 들어간 기록 이름은 무엇이니?”|

실제 학생의 독립 수행, 받은 도움, 재시도와 소요 시간은 교사가 수업 후 따로 기록한다. 채점할 때는 공개한 새 입력에 대한 답을 학생용 노트북에 미리 넣지 않는다.

## 자료와 참고 문서

과정 내 1주 편성과 실전 범위, 네 단원 목표의 근거는 저장소 내 원문에서 확인한다. [10주 학습 계획](../../curriculum/student-plan.html#week-1) · [단원 명세](../../skills/koai-evaluate/references/unit-specifications.json) · [KOAI 출제 기준](https://kitpa.org/koai/syllabus)

Python의 조건·반복·함수와 반환값은 공식 튜토리얼에 설명되어 있다. [Python 제어 흐름](https://docs.python.org/ko/3/tutorial/controlflow.html) · [오류와 예외](https://docs.python.org/ko/3/tutorial/errors.html)

배열 모양·축·전치, 뷰와 복사, 브로드캐스팅, 분산과 두 1차원 벡터의 내적은 NumPy 문서를 따른다. [NumPy 기초](https://numpy.org/doc/stable/user/absolute_beginners.html) · [뷰와 복사](https://numpy.org/doc/stable/user/basics.copies.html) · [브로드캐스팅](https://numpy.org/doc/stable/user/basics.broadcasting.html) · [분산](https://numpy.org/doc/stable/reference/generated/numpy.var.html) · [내적](https://numpy.org/doc/stable/reference/generated/numpy.dot.html)

CSV 읽기, 결측 검사, 키 병합과 그룹 통계는 pandas 문서에서 확인할 수 있다. [표 입문](https://pandas.pydata.org/docs/getting_started/intro_tutorials/index.html) · [병합](https://pandas.pydata.org/docs/user_guide/merging.html) · [병합 키의 빈값 처리](https://pandas.pydata.org/docs/reference/api/pandas.merge.html) · [그룹 통계](https://pandas.pydata.org/docs/user_guide/groupby.html)

막대의 의미와 구간 경계는 두 라이브러리의 해당 함수 문서를 참고한다. [Matplotlib 히스토그램](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.hist.html) · [Seaborn 막대그래프](https://seaborn.pydata.org/generated/seaborn.barplot.html)
