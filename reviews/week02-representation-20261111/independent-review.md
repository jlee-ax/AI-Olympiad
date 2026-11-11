# 2주차 표현·정보 손실 독립 검토

검토 결과: 아래 동결 후보와 유한한 입력 범위에서 추가 수정필수 결함을 발견하지 못했다. 시계열 요약에서 사라지는 순서 정보, 결측 대체와 값 변환의 차이, 예측 시점, 서로 다른 목표에 따른 표현 선택 및 F1을 정의한 뒤 사용하는 순서가 학생 자료와 교사용 해설에 연결된다. 실제 학생 성취나 소요 시간에 대한 판정은 아니다.

## 대상

| 파일 | SHA256 |
|---|---|
| 본문 `week02_prediction_evaluation.ipynb` | `6f79589e33574104bd8a471b008259f5b1d4847a19b8b8fc0c32a18418a5249e` |
| 보충 `week02_temporal_preprocessing.ipynb` | `ea847303906a48c98ae69f80cdaaa7a008e1ab31ad197ce69b3c0b7fdf2be326` |
| 본문 생성기 `build_week02.py` | `6fbc6e09e9e0b2efee6af8122f30e0972b0ca3add3ca4780bf0f366961fcf025` |
| 본문 HTML | `002bce623d581da096678f7bbd2edf3d36a5e4c81ae807ed2b1e7de1be05b612` |
| 보충 HTML | `7b343cb9aae34975bc9e64e7177f1ee6cda4252f1435f4adca91d9094a2bd49f` |
| 본문 교사용 `teacher-notes.md` | `29d27b076eb4316a8c437cd1b36ebc992be2a8daae528e686e6b163b955319e8` |
| 보충 교사용 `week02_temporal_preprocessing_teacher.md` | `c86f0d7af54016c642b8c17b704396147fa51d413fdb9b19a63a32995bc71716` |

본문 셀 번호는 0부터 센다. 본문 셀9는 F1의 count식과 분모 0을 제시하며 해당 예에서 2/5를 산출하고, 셀11은 0.4를 출력한다. 한 지표가 정의되지 않아도 F1 count식이 정의될 수 있다고 명시한다. 보충 셀2의 V/W는 본문의 최종 테스트 자리 표시 E/F와 무관한 별도 라벨 없는 합성 기록이다. 측정이 해당 예측 직후 도착한다는 가정 아래 두 함수가 측정 시각만 확인하며 지연 도착을 검사하지 않는다고 밝힌다. 보충 셀18의 M4 `[5,7,9]`, M′4 `[7,5,9]`는 각각 평균 7, 모집단 표준편차 √(8/3), 최근값 9로 같고 마지막 두 비결측 원본의 변화는 2와 4이다. 평균 6 이상 목표는 둘 다 양성이지만 변화 3 이상 목표는 서로 다르며 교사용 답도 같다. 별도 목표는 기존 사후 정답과 분리된다.

## 이 검토자가 직접 수행한 검사

- 지정된 가상 환경의 Python으로 본문 코드 셀 5·7·11과 보충 코드 셀 3·4를 메모리에서 실행했다. 각 셀의 저장 stdout과 새 실행 stdout이 일치했다. 이 범위에서 본문 2/5 출력 및 보충의 요약과 변화 예시를 확인했다. NumPy 2.5.4, pandas 3.1.1이었다.
- 후보가 쓰지 않은 독립 입력 P=`[2,8,5]`, Q=`[8,2,5]`를 같은 종류, 예측 시각 4, 개체 ID는 모델 입력이 아닌 계약에서 실제 `make_features`와 `last_observed_change`에 넣었다. 두 벡터의 최근값·평균·모집단 표준편차는 `[5,5,√6]`으로 같지만 변화는 각각 −3과 +3이다. 평균이 5 이상인 목표에서는 둘 다 양성이고 마지막 비결측 관측이 그 직전보다 큰 목표에서는 음성·양성이다. 동일 입력을 받는 결정적 규칙은 두 서로 다른 목표값을 구별하지 못하지만 변화 특성은 이 두 사례를 구별한다. 이는 임의의 모델이 새 자료에서 성공한다는 주장이나 성능 평가가 아니다.
- R=`[2,결측,5]`, S=`[결측,2,5]`는 최근값 5, 평균·표준편차 결측, 변화 +3으로 같아 결측 위치 정보는 변화까지 추가해도 복원되지 않는다. 관측이 0개 또는 1개면 변화 결측이고 두 값이 모두 5면 변화 0이다. 행 순서 섞기, 예측 시각 및 그 이후 값 변경에 대한 불변성과 중복 `(개체,시각)`의 두 함수 `ValueError`도 확인했다. 이 함수들은 지연 도착 시각을 검증하지 않는다.
- 보충의 실제 `ratio`·`rates` 함수에 독립 혼동 수를 넣었다. `(TP,FP,TN,FN)=(0,0,1,2)`는 정밀도 정의 불가·재현율 0·F1 0, `(0,2,1,0)`은 정밀도 0·재현율 정의 불가·F1 0, `(0,0,3,0)`은 F1 정의 불가이다. `(0,1,1,2)`는 정밀도와 재현율이 각각 0이어도 count식 F1이 0이다.
- 본문의 실제 훈련 파이프라인에 `[결측,4,2,6]`을 적용하면 처음 두 값은 모두 0으로 변환된다. 역표준화해도 원래 결측과 실측 4는 구별되지 않지만 실측 2와 6은 구별된다. 이는 대체와 스케일 변환의 서로 다른 정보 효과에 대한 해당 유한 사례다.
- 같은 가상 환경에서 본문 생성기의 `--check-source`는 25셀의 ID·종류·source 일치를 반환했다. 두 notebook을 `HTMLExporter`로 메모리에서 새로 내보낸 결과 각 저장 HTML과 바이트가 일치했다. 검사 전후 두 notebook 바이트도 변하지 않았다. 기본 Python에는 `nbformat`이 없어 첫 builder 검사는 실패했고 지정 가상 환경에서 다시 성공했다.

## 범위와 한계

[KOAI 출제 기준](https://kitpa.org/koai/syllabus)은 IOAI 2026 기준을 표시하고 피처 엔지니어링과 전처리의 실전, 지표·F1 및 ROC의 이론·실전을 열거한다. [IOAI 2026 Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md)은 위치별 그리드의 독립 snapshot이며 이전 관측을 제공하지 않는다. 별도의 [IOAI 2025 Radar](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Radar/Radar.ipynb)는 여러 공간 heatmap으로 좌표별 라벨을 예측한다. 어느 것도 이 합성 시계열을 실제 대회 문제나 국내 중등 기출로 만드는 근거가 아니다. [시계열 요약](https://otexts.com/fpp3/features.html), [시차와 rolling 특성 예제](https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html), [F1의 count식과 0분모](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html), [결측 표시](https://scikit-learn.org/stable/modules/impute.html#marking-imputed-values)도 대조했다.

기존 계획에는 2주 수업 120분, 필수 자습 6~8시간이 편성 추정으로 명시되어 있으며 현재 학생 실제 소요 시간은 확인 전이다. 새 활동은 기존 보충 1번에 통합하고 P6의 별도 통계 계산을 덜었지만, 설명과 코드 및 표현 선택이 추가되었다. 이 사실만으로 부담이 감소하거나 기존 편성 안에 완료된다고 결론 내릴 수 없다.

이번 검사는 위에 열거한 셀·함수와 산출물 대조에 한정된다. 노트북의 모든 셀 재실행, 실제 학생의 독립 답안·도움·성취·시간, 일반 Jupyter 커널, HTML 브라우저 시각 렌더 또는 진짜 최종 테스트의 확보는 검토하지 않았다. 공개 저장소의 교사용 해설은 접근 통제된 시험이 아니다.
