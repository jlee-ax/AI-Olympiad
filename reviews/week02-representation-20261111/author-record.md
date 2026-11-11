# 2주차 표현 선택과 F1 순서 — 작성자 기록

2026-11-11. 이 기록은 작성자의 자료 비교·유한 검산·실행 결과다. 독립 검토는 같은 디렉터리의 별도 기록을 확인한다. 학생이 혼자 해결한 답안, 실제 학습 성취, 받은 도움이나 수업·자습 소요시간은 관찰하지 않았다. 합성 예제의 성공으로 실제 성능이나 숙달을 주장하지 않는다.

## 변경 전 판단과 우선순위

현재 2주 본문은 분할, 전처리의 훈련 전용 fit, 평가 지표, 두 가지 예측 명세를 이미 다뤘다. 보충 2절의 `make_features`는 `recent`, `mean3`, `std3`를 계산하고 3절은 결측 대체·MinMax·one-hot을 설명했지만, 원시 자료의 어떤 정보가 표현에서 사라지는지, 목표가 바뀌면 같은 요약이 충분한지의 독립 판단은 구체적으로 요구하지 않았다. 보충의 고정 점수는 `recent`와 범주를 사용하며 `mean3`·`std3`는 사용하지 않는다. 바로 앞 독립 검토 또한 두 명세의 전처리와 후보가 고정되어 자유로운 표현 선택을 충분히 평가하지 못한다고 한정했다. 이에 이미 확장된 분할·AUC·최빈 기준·두 명세를 다시 늘리기보다 표현 선택을 기존 과거값 활동에 연결했다. 고급 모델의 자유 설계, 차원 축소·멀티모달 전 범위의 구현이나 학생 성취를 2주에 달성했다는 뜻은 아니다.

본문 9셀은 기존에 정확도·정밀도·재현율만 정의했지만 11셀이 F1을 계산하고 23셀이 F1을 출력했다. 보충 10셀의 설명을 먼저 읽지 않는 본문 순차 독자를 위해 9셀에 혼동행렬의 $F1=2TP/(2TP+FP+FN)=2/5$를 놓고 11셀 출력·검산에 연결했다. count 식의 분모가 0인 경우와 개별 정밀도 또는 재현율이 정의되지 않는 경우는 다르다. 예측 양성이 없지만 실제 양성이 있거나, 실제 양성은 없지만 양성 예측이 있다면 각각 개별 지표는 미정의여도 count F1은 0이다. TP=FP=FN=0일 때 count 식 F1은 미정의이며 라이브러리 보고값은 별도 정책이다.

## 직접 비교한 원문과 범위

- [KOAI 2027 공식 안내](https://kitpa.org/koai/2027)의 중등부 시험 안내는 필기·코딩과 출제 기준 전반을 설명한다. 연결된 [국내 출제 기준](https://kitpa.org/koai/syllabus)은 페이지에 IOAI 2026 기준으로 표기되어 있으며 1과목의 특성 엔지니어링에 슬라이딩 윈도·통계량·one-hot·PCA·임베딩을 실전 항목으로 열거한다. 이론 O와 실전 O의 공식 구분을 변경하지 않는다.
- [KOAI 2026 예시문항 안내](https://kitpa.org/files/36)와 연결된 [예시 PDF](https://kitpa.org/storage/c4016751-0e2c-4548-ab70-ecec994e8f8d.pdf)의 24~25번은 각각 특성 방법과 가변 길이 전처리의 범위를 보여준다. 공지대로 이 예시는 고등부 수준의 학습 참고이며 정답은 공개되지 않았다. 문항 원문은 학생 자료에 복제하지 않았다.
- [IOAI 2026 Robot Chasing 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md)은 8×8×2 범주형 격자, 방향, 명령, 든 물체를 입력으로 다음 행동을 예측한다. 이전 행은 이용할 수 없는 독립 snapshot이다. 위치·명령의 관계와 예측 시점의 제공 정보가 표현 선택에 중요하다는 대조이지 보충의 시계열과 동일한 계약은 아니다.
- [IOAI 2025 Radar 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Radar/Radar.ipynb)은 여섯 신호 heatmap과 정답 지도를 구별하며 위치별 사람을 분할한다. 공간적으로 다른 입력을 하나의 전역 평균으로 합치면 원래 위치를 되살릴 수 없는 상황이 생길 수 있다. 이것은 설계상 추론이지 원문이 특정 모델이나 평균 방식의 실패를 입증했다는 말이 아니다. 두 국제 과제는 국내 중등 기출이 아니다.
- [scikit-learn 시계열 지연 특성 원문](https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html)은 과거 시차 값과 rolling 통계를 함께 구성한다. [Dive into Deep Learning의 pooling 원문](https://d2l.ai/chapter_convolutional-neural-networks/pooling.html)은 공간을 줄이고 작은 위치 이동에 대한 민감도를 낮추는 목적을 설명한다. 어느 한 표현이 모든 목표에서 항상 최선이라는 근거는 아니다. 외부 stable/main 문서는 바뀔 수 있다.

## 학생 활동과 부담

보충의 worked 예제 V/W는 서로 다른 `[1,3,2]`, `[3,1,2]`가 `recent=2`, 평균 2, 모집단 표준편차 $\sqrt{2/3}$으로 같고 마지막 두 비결측 원본 관측의 차이는 -1/+1임을 수식과 실제 `make_features`, `last_observed_change` 실행으로 확인한다. 두 기록은 본문의 E/F 최종 테스트 자리 표시와 무관한 별도 합성 기록이며 target 라벨은 제공하지 않고 함수가 라벨을 읽지 않는다. 같은 요약을 받는 결정적 규칙은 충돌한 두 입력을 다르게 분류할 수 없지만, 평균만으로 정의된 목표에는 평균이 충분할 수 있다. 두 원본 관측이 부족하면 차이는 결측이고, 시간 간격을 나누지 않았으므로 변화율이 아니다. 결측된 시각 자체는 차이만으로 복구하지 못할 수 있다.

기존 독립 1번에서 P6의 별도 평균·표준편차 손계산을 덜고, 같은 활동 안에서 M4 `[5,7,9]`와 M′4 `[7,5,9]`를 두 목표로 비교한다. 두 기록의 세 요약은 `[9,7,√(8/3)]`이고 차이는 2/4다. 평균 6 이상 목표는 둘 다 양성이고, 변화 3 이상 목표는 음성/양성이다. 사후 이상 라벨과는 별개의 합성 목표다. 학생이 새 표와 코드를 직접 만들고 표현·이유와 결측/시점 경계를 설명한다. 기존 N/Q·P7의 과거 문맥, 다른 번호, 빈 독립 답안 칸을 보존했다. P6의 반복 계산을 빼더라도 표현 비교·새 표·코드가 추가되므로 전체 작업량이 감소했다고 단정하지 않는다. 원래 편성의 수업 120분과 별도 필수 자습 6~8시간은 실측이 아니다.

보충 3절은 중앙값 대체가 관측 4와 대체된 결측을 합칠 수 있다는 점, 결측 표시의 목적, clip하지 않은 MinMax의 순서 보존과 clipping의 충돌 가능성을 연결한다. 3주 회귀, 4주 거리·스케일, 5주 PCA, 6주 텐서·학습, 7주 위치·pooling, 8주 텍스트 순서·마스크, 9주 오디오, 10주 새 명세 적용은 보충의 다음 학습 경로로만 명시했다. 후속 교안 완성이나 전체 공식 범위의 완료를 주장하지 않는다.

이 합성 기록의 측정은 해당 시각 예측 직후 도착한다고 가정한다. `make_features`와 새 차이 함수는 측정 시각만 검사하며 실제 도착 지연은 구현하지 않았다. 지연 자료에는 별도 도착 시각 검사와 입력 계약이 필요하다. 공개 저장소의 교사용 답안은 비공개 시험이나 실제 접근 통제를 보장하지 않는다.

## 고정 입력 SHA-256

| 파일 | SHA-256 |
|---|---|
| `lessons/week02/week02_prediction_evaluation.ipynb` | `6f79589e33574104bd8a471b008259f5b1d4847a19b8b8fc0c32a18418a5249e` |
| `lessons/week02/week02_prediction_evaluation.html` | `002bce623d581da096678f7bbd2edf3d36a5e4c81ae807ed2b1e7de1be05b612` |
| `lessons/week02/build_week02.py` | `6fbc6e09e9e0b2efee6af8122f30e0972b0ca3add3ca4780bf0f366961fcf025` |
| `lessons/week02/teacher-notes.md` | `29d27b076eb4316a8c437cd1b36ebc992be2a8daae528e686e6b163b955319e8` |
| `lessons/week02/week02_temporal_preprocessing.ipynb` | `ea847303906a48c98ae69f80cdaaa7a008e1ab31ad197ce69b3c0b7fdf2be326` |
| `lessons/week02/week02_temporal_preprocessing.html` | `7b343cb9aae34975bc9e64e7177f1ee6cda4252f1435f4adca91d9094a2bd49f` |
| `lessons/week02/week02_temporal_preprocessing_teacher.md` | `c86f0d7af54016c642b8c17b704396147fa51d413fdb9b19a63a32995bc71716` |
| `reviews/week02-representation-20261111/check_representation.py` | `6864a373fe558f363118eca6b0b495db3d469f63f9e39a2d6a449ba297129186` |

## 실행과 한계

저장소 루트에서 `PY=/workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python`을 사용했다. 아래 각 검증은 위 고정 노트북 SHA에 대한 결과다.

- `$PY -B -m unittest discover -s tests -q`: 종료 0, **271 tests, 97.472초, OK**, 실패나 경고 출력 없음. 이는 저장소 회귀 테스트의 실행 시간이며 학생 시간과 무관하다.
- `$PY -B lessons/week02/build_week02.py --check-source lessons/week02/week02_prediction_evaluation.ipynb`: 25개 본문 셀의 ID·종류·source 일치.
- `$PY -B lessons/week02/teacher_validate_week02.py --inprocess`: 종료 0, 본문 25셀과 8개 코드 셀의 순차 실행 및 기존 유한 검산 통과. 결과 이후 로컬 네트워크 인터페이스 권한 경고와 IPython 종료 시 readonly SQLite traceback이 stderr에 나타났다. 종료 0이 경고 부재를 뜻하지 않는다. 이 검사기는 새 두 명세의 학생 답을 채점하지 않는다.
- `$PY -B lessons/week02/validate_week02_temporal_preprocessing.py`: 종료 0, 보충 순차 실행·기존 계산·저장 stdout 일치·빈 독립 셀 확인. 임시 IPython/Matplotlib 디렉터리를 사용했으며 stderr는 비었다. 학생 답안은 채점하지 않는다.
- `$PY -B reviews/week02-representation-20261111/check_representation.py`: 본문 F1 실제 코드·세 분모 경계, 실제 보충 함수의 새로운 P/Q와 M/M′, R/S 결측 위치, 관측 부족 대 실제 변화 0, 원본 셔플·예측 시각 및 미래 제외·동일 시각 중복·라벨 변화와 출력 순서, 중앙값 충돌·결측 표시·MinMax clipping, 지연 도착 미구현의 반례를 통과했다. 새로운 P/Q는 각각 `[2,8,5]`, `[8,2,5]`로 공통 요약 `[5,5,√6]`, 차이 -3/+3이다. 새 검사는 학생 코드를 받거나 평가하지 않는다.
- `$PY -B lessons/week02/teacher_validate_contracts.py`: 기존 두 명세의 교사용 수치 참조와 유한 경계 통과. `$PY -B reviews/week02-integration-20261111/author/check_candidate.py`: 4주 후보의 두 그룹 fold와 각 fold fit, 전체 8행 재적합, 기존 보충 검증·무라벨 예측의 유한 회귀 통과. 4주 교안 완성이나 실제 학습 성취를 뜻하지 않는다.
- `nbconvert.HTMLExporter().from_notebook_node(...)` 결과와 저장된 본문·보충 HTML이 각각 바이트 단위로 일치했다. `git diff --check` 통과. 전체 브라우저 시각 확인과 오프라인 MathJax 가용성은 확인하지 않았다. 보충 디렉터리의 기존 validation JSON은 이전 판본에 결합된 기록이므로 이 후보의 검증 보고서로 취급하지 않는다.

독립 검토 및 실제 학생의 수행·시간 관찰은 별도다. 임시 디렉터리는 OS 보안 격리가 아니며 신뢰한 노트북만 실행했다.
