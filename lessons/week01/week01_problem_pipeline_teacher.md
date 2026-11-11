# 교사용 해설 · 낯선 문제에서 학습과 제출까지

이 문서는 독립 문제의 예시 답을 포함합니다. **공개 저장소에서 파일을 따로 둔 것은 접근 통제가 아닙니다.** 독립 수행 전에 교사가 별도 권한이 있는 위치나 다른 방법으로 해설을 배포·보관해야 합니다. 도움과 코드를 실제로 확인하지 않은 상태에서 학생이 독립 수행했다고 기록하지 않습니다.

## 편성과 범위

기존 1주 수업 120분의 블록을 늘리지 않습니다. 기존 필수 자습의 표·함수·배열·새 CSV 활동과 연결할 수 있는 보충이며, 다른 필수 성취를 이 자료로 대체했다고 가정하지 않습니다. 기존 5~7시간은 이전 범위의 계획 추정치이고 이 보충까지 포함한 실제 소요 시간·부담·완수 가능성·학습 성취는 관찰하지 않았습니다. 보충의 설명과 독립 수행을 추가하면 총 부담이 늘 수 있으며 기존 범위 안에 완료된다고 주장할 근거가 없습니다. 실제 시간을 기록하고 시간이 모자라면 미완료와 필요한 지원·추가 계획을 남깁니다.

재배치 후보: 본교안 배열 A의 축·특성 순서 설명과 축/ID 보충의 행 대응 설명을 함께 복습하고, 내적 E를 마친 뒤 이 자료의 거리·중심 계산으로 이어서 중복 설명을 줄입니다. 같은 자료사전의 ID·특성·정답 구분은 한 번의 점검표로 함께 확인할 수 있습니다. 다만 기존 A의 reshape·transpose·브로드캐스팅, E의 내적 새 입력, 새 CSV의 읽기·집계·병합·결측·dtype·그래프, 함수·독립 설명 등 기존 필수 목표와 결과물은 여전히 따로 확인해야 합니다. 합성 배열로 모델을 학습한 것만으로 새 CSV나 기존 독립 과제를 완료한 것으로 처리하지 않습니다.

본 교안은 미상 라벨을 포함한 국제 대회 전체 문제를 푸는 자료가 아닙니다. 학습 가능한 간단한 지도학습, 검증 경계, ID와 형식 계약의 연결만 다룹니다. 학생은 1주 본교안의 표·평균·함수 및 축/ID 교량을 먼저 접하고, 2주에서 분할·표준화·지표를 더 배웁니다. 3~10주의 학습이나 다른 모델에서의 독립 전이를 이 예제만으로 입증하지 않습니다.

## 예제의 수치와 오류 경로

- 알려진 라벨 T1~T4만 훈련 fit에 넣습니다. T5의 0은 미상으로 제외하며 −1로 바꾸지 않습니다. 이 단순화는 미상 입력까지 활용하라는 Antique 원문 과제를 충족하지 않습니다.
- 훈련 관측 평균은 texture (1+3+7+9)/4=5, color (1+3+5)/3=3. T2를 [3,3]으로 채운 뒤 −1 중심은 [2,2], 1 중심은 [8,4]입니다. T4 texture 9→11인 훈련 사본에 별도 fit하면 1 중심은 [9,4], 대체값은 [5.5,3]이지만 원래 모델은 바뀌지 않습니다. 같은 새 입력 [5.25,3]의 예측도 원래 1에서 변경한 모델 −1로 달라집니다. 비교용 변화는 검증을 보고 모델을 선택하는 과정이 아닙니다. 이는 fit이 고정 점수를 출력하는 것이 아니라 자료에서 매개변수를 배운다는 확인입니다.
- x=[6,3]의 두 제곱거리는 17과 5이므로 1입니다. 검증 예측 [-1,1,1,1], 실제 [-1,1,-1,1], 정확도 3/4입니다. 이 작은 예제는 현실 성능을 추정하지 않습니다. 검증 변화를 예측에만 사용하면 훈련 대체값·중심은 그대로입니다.
- A 입력 순서는 A08,A02,A05이고 예측은 [1,-1,-1]. 요구 순서 A05,A08,A02로 ID를 따라 배열하면 [-1,1,-1]. 순서가 잘못된 [1,-1,-1]은 길이와 허용 라벨이 같으므로 형식 검사만으로는 못 찾습니다. B 입력은 B09,B04에 [1,-1], 요구 순서 B04,B09에 [-1,1]입니다. ZIP 내부 두 파일과 헤더·행 수·라벨·ID 대응표를 비교합니다. 합성 ZIP은 임시 폴더의 submission.zip에 실제로 기록하고 다시 연 후 자동 삭제합니다. 원문의 submission.ipynb와 공식 입력·작업 경로를 실행하거나 대회에 제출한 것은 아닙니다. 대응표 자체가 오염되면 추가적인 행·ID 계보 검사가 필요합니다.
- 누락된 특성 열과 결측 셀은 다릅니다. 한 셀의 결측은 훈련 대체값을 적용하지만 열이 없으면 오류를 내고 데이터를 확인합니다. 입력 ID와 요구 순서·예측 대응표의 ID 결측(None, NaN, 빈 문자열) 또는 중복, 0 예측, 헤더, 행 누락, 같은 길이의 순서 오류를 실제 실행으로 거부합니다. ID 정렬 함수를 다른 코드에서 직접 호출해도 양쪽의 결측 ID를 거부합니다. 마지막 테스트 라벨이나 나중 검사 결과를 입력·fit·선택에 넣으면 누수입니다. 의도적으로 모델을 개선하기 전 공개 검증과 최종 테스트의 역할을 구별하게 합니다.

## 독립 문제 예시 답

새 명세는 0=정상, 1=점검, −1=미상입니다. R1~R4를 fit하고 R5는 이 지도학습 목표와 전처리 fit에서 제외합니다. 세 입력 열은 vibration, sound, heat이고 item은 ID, label은 훈련·검증 정답입니다. 알려진 훈련 관측의 공통 대체 평균은 [4,4,2]입니다. 학생이 가까운 중심 분류기를 선택한 경우에는 결측 대체 후 정상 중심 [1,3,1], 점검 중심 [7,5,3]입니다. 학생이 타당한 다른 모델을 선택하면 모델별로 배운 매개변수와 예측이 달라질 수 있습니다.

같은 중심 방법에서 검증 예측은 [0,1,1], 정답은 [0,1,0]이므로 정확도 2/3입니다. 같은 중심 분류기에서 입력 J3,J1,J2의 예측은 [1,0,0], CSV는 첫 줄 item,signal 다음에 J3,1 / J1,0 / J2,0 순서입니다. 다른 정당한 학습 모델의 다른 예측값은 0/1과 ID 대응 조건을 충족하면 일률 오답이 아닙니다. ID 없이 예측값만 뒤집으면 한 행의 정답이 다른 기기에 붙을 수 있습니다. 열 자체 누락이나 ID 중복은 오류로 거부하고, sound의 한 셀 결측은 훈련 sound 평균 4로 채웁니다.

예시 구현은 아래와 같습니다. 다른 모델을 사용하면 숫자는 달라질 수 있으므로, 훈련 경계·명세·정당한 검증 및 독립 작성 과정을 기준으로 확인합니다.

    cols = ["vibration", "sound", "heat"]
    known = exercise_train[exercise_train["label"].isin([0, 1])].copy()
    independent_model = Pipeline([("fill", SimpleImputer(strategy="mean")),
                                  ("classifier", NearestCentroid())])
    independent_model.fit(known[cols], known["label"])
    valid_pred = independent_model.predict(exercise_validation[cols])
    print((valid_pred == exercise_validation["label"].to_numpy()).mean())
    if exercise_input["item"].isna().any() or exercise_input["item"].duplicated().any():
        raise ValueError("item 결측 또는 중복")
    if any(name not in exercise_input.columns for name in cols):
        raise ValueError("필수 열 누락")
    out = pd.DataFrame({"item": exercise_input["item"],
                        "signal": independent_model.predict(exercise_input[cols])})
    csv_value = out.to_csv(index=False)
    reread = pd.read_csv(io.StringIO(csv_value))
    assert reread.columns.tolist() == ["item", "signal"]
    assert reread["item"].tolist() == exercise_input["item"].tolist()
    assert len(reread) == len(exercise_input) and set(reread["signal"]).issubset({0, 1})

학생이 명세에 맞는 서로 다른 구현을 만들면 일관된 ID·특성 순서, 예측 당시 가용성, train-only fit, 검증·최종 보류, 허용 출력, 예외 경로를 봅니다. 위 수치 자체를 다른 알고리즘의 유일한 정답으로 강제하지 않습니다.

## 공식 원문과 라벨 전이

2026-11-11 직접 확인: [KOAI 2027 공식 안내](https://kitpa.org/koai/2027)는 연결 [출제 기준](https://kitpa.org/koai/syllabus)을 중등부 1~4과목 전범위와 연결하며, 해당 출제 기준 페이지는 IOAI 2026으로 표시됩니다. [IOAI 2025 Antique 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb)은 각 분할 500표본, 5특성, 라벨 1/−1/0, 대회 중 직접 접근할 수 없는 검증·테스트, 미상 표본 활용, 정확도, submission.ipynb가 만드는 submission.zip 및 무헤더 submissionA.csv·submissionB.csv를 명세합니다. 이는 과거 국제 개인전 문제이며 KOAI 2027 중등부 기출·확정 출제 예측이 아닙니다. 원문 main은 변경될 수 있습니다.

[scikit-learn 반지도 학습](https://scikit-learn.org/stable/modules/semi_supervised.html)의 미상 표시는 −1입니다. Antique의 −1은 복제품이므로 그 라벨을 그대로 LabelSpreading/LabelPropagation에 넘기면 복제품을 미상으로, 실제 미상 0을 클래스 0으로 취급합니다. 가능한 명시적 매핑은 복제품 −1→0, 진품 1→1, 미상 0→−1이며, 모델이 예측한 0/1은 제출 전 −1/1로 되돌립니다. 이 교안은 매핑 직관만 설명하며 해당 반지도 모델의 타당성·학습·성능을 검증하지 않습니다.

지정 Python에서 새 in-process IPython 커널로 위에서 아래로 실행해 예제 표와 출력을 저장합니다. 일반 소켓 Jupyter·Colab 및 HTML 전체 시각 렌더링, 실제 학생 수행과 최종 숨은 테스트는 별도 확인 대상입니다.
