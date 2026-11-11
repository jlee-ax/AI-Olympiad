> **판본 안내:** 아래 보충 `549c…`/`5695…`는 dtype 설명 전 후보입니다. 최종 `c35d…`/`f1ad…`와 재검증은 [dtype 추가 기록](dtype-addendum.md)을 참조하세요.

# 2주 최빈 기준 개정 — 작성자 실행 기록 (교사용)

독립 문제 해답과 검증 데이터가 포함됩니다. 학생에게 제공하지 않습니다. 범위는 `lessons/week02/`의 일곱 파일과 이 author 폴더이며, 커밋·푸시는 하지 않았습니다. 현재 내용 검토는 이 기록만으로 승인되지 않습니다.

## 대상 SHA-256

| 파일 (`lessons/week02/`) | SHA-256 |
|---|---|
| `week02_prediction_evaluation.ipynb` | `2eabca5db515279632f8c8e287564c08b486938c2fc8b1f96ff5a72ef2e61787` |
| `week02_prediction_evaluation.html` | `46fc2a995dae76a06a6c182d38429004a85822b5016075251be1aa20e44d1700` |
| `week02_temporal_preprocessing.ipynb` | `549cd18bfad99a720587b65b80a4de0b2402435cbdc95a0a5619e779f80f94e0` |
| `week02_temporal_preprocessing.html` | `5695b6c2adfd12dce7cf349a1ff9f0d448178b7b8c3c0ffb1507c9e94932c520` |
| `teacher-notes.md` | `2348b396701799328dbf5c8d586176debe29a010b2cc6bace7bf9acc10e75d36` |
| `week02_temporal_preprocessing_teacher.md` | `1c79ed6817542bf95738141676f62d137b6505981be0ccbfbea7a415f3dee925` |
| `build_week02.py` | `95d73cfb47f3cb2b24076693e082a66a9f131cb0d0f1ad9ec427a733d427ca17` |

원본 9개는 `baseline-*`으로 바이트 보존했습니다. 기존 `validation.json` SHA `182c796357a6cef40180e67fd707eef1b45cc70db3dfa446e111b0c4e97edf3e`은 산출물 해시가 없는 과거 기록, 기존 `week02_temporal_preprocessing_validation.json` SHA `f4ccd285b1dd861497c9e4b25700993fec89c7341486803337483701646f9936`은 이전 자료에 결합된 기록입니다. 둘 다 수정하지 않았고 새 판본의 승인 근거가 아닙니다. 이전 discovery의 양 노트북 `artifact_changed`/`needs_work` 판정도 보존했으며 새 승인으로 고쳐 쓰지 않았습니다.

## 구현과 기대값

본문의 A/B known 라벨은 -1과 +1이 2:2이므로 본문의 사람 지정 상수 -1은 최빈값 학습이 아닙니다. 보충 기존 B5/T1 평가에 별도의 훈련 B3/T1/미상 5를 연결해 알려진 라벨만 `fit`한 유일 최빈 B를 같은 여섯 검증 행에 예측합니다. 이 계약에서는 미상 0을 라벨 빈도에서 빼며, 이는 IOAI Antique의 반지도 학습용 미상 입력 활용을 금지하는 보편 규칙이 아닙니다. X와 y의 관계를 학습한 모델이라고 주장하지 않습니다.

T 양성에 대해 기준(기존 가)은 TP/FP/TN/FN=0/0/5/1, 정확도 5/6, 재현율 0, 정밀도 0/0 정의 불가, F1 0, 가중 정확도 1/2입니다. 기존 나는 1/2/3/0, 정밀도 1/3, 재현율 1, F1 1/2, 가중 정확도 4/5입니다. 검증 라벨만 B1/T5로 바꾸면 같은 fitted 기준의 예측은 고정이며 정확도는 1/6입니다. 0 보고 정책은 정의 불가를 바꾸지 않습니다.

기존 독립 6번에서 B1/T3/미상4 훈련 후 같은 B6/T2 검증에 고정한 최빈 기준은 T입니다. 기준/U/V의 정확도는 각각 1/4, 3/4, 5/8, 양성 재현율은 1, 0, 1, 가중 정확도는 4/7, 3/7, 11/14입니다. 최빈 기준은 TP/FP/TN/FN=2/6/0/0, 정밀도 1/4, F1 2/5이고, U의 정밀도는 정의 불가, V는 2/5 및 F1 4/7입니다. 선택할 지표와 동률은 목적에 달려 있습니다. 데이터 순서와 가중 분모 14를 유지합니다.

Robot 비교 문항은 실제 대회 분할을 재현하지 않는 두 합성 설계입니다. 동일한 두 ID의 새 조합 평가는 (가), 새 ID 평가는 (나)가 해당하며 주어진 새 조합 목표에는 (가)가 더 직접 맞습니다. 원문처럼 과거가 제공되지 않으면 두 경우 모두 과거 윈도를 입력할 수 없습니다.

## 실행·회귀와 제한

- 두 학생 노트북을 각각 별도 fresh in-process kernel에서 위에서 아래로 실행해 저장했습니다. 본문 25셀/코드 8셀, 보충 25셀/코드 10셀입니다. 독립 답안은 AST가 비고 저장 출력이 없으며, 보충 답안 셀은 미실행입니다. 본문의 원래 주석 답안 셀은 빈 상태에서 실행 카운트가 있습니다. 같은 실행본에서 HTMLExporter로 내보낸 텍스트가 해당 HTML 바이트와 정확히 일치합니다. [대상 및 동기화 검산](artifact-audit.json).
- [실제 학생 함수 새 입력 13건](majority-validation-final.log), [재현 코드](check_majority.py): 훈련 빈도 반전/미상 다수, 검증 정답만 교체한 뒤 기존 fitted 상태·예측 불변, 입력 값 변화, tie·빈 known·허용되지 않은 값의 오류, Boolean 거부 및 수치 0.0 허용, known 한 클래스의 fit·`classes_`/확률 열, worked 및 독립 지표가 통과했습니다. 이 검사는 실제 학습자 응답을 채점하지 않습니다.
- [기존 본문 검사](main-validation-final/validation.json)와 [보충 검사](temporal-validation-final.json)는 별도 실행·사본에서 통과했으며, 보충 보고서의 notebook·HTML·해설 SHA가 위 대상과 일치합니다. 본문 보고서는 input SHA와 별도 생성한 세 산출물의 SHA를 구분해 기록합니다. 기존 검사기는 새 최빈 과제 응답을 자동 채점하지 않으며 본문 검사기는 AUC 및 4주 CV를 보장하지 않습니다.
- [AUC 별도 회귀](auc-validation-final.json)는 쌍 순위·사다리꼴·라이브러리 결과의 기존 7개 유한 사례, 동점·역순·전체동점, 미상 제외, 한 클래스, 임계값 동시 이동과 F1 변화를 계산했습니다. [4주 별도 유한 회귀](week04-regression-final.json)는 그룹 교집합 없음, 각 4행의 양 클래스, fold 평균 3과 16/3, k=3, 실제 모델 fit/predict 및 전체 8행 재fit 상태를 확인합니다. 4주 교안 완성이나 실제 성능을 입증하지 않습니다.
- [생성기 검사](builder-checks.json)는 본문 셀 ID·종류·소스 동기화, 재생성 결정성, 기존 파일·폴더·심링크·없는 부모 거부, 안전한 import, 실패한 부분 쓰기 정리를 확인했습니다. [저장소 단위 회귀](unit-tests.log)는 271개 통과했습니다. 이는 특정 학생의 성취 판정이 아닙니다.
- 최초 원본 반영 전 작성자 harness는 본문 주석 답안 셀의 실행 카운트까지 `None`이어야 한다고 잘못 요구해 중단됐습니다. 당시 원본 7개에 쓴 것은 없었고, 빈 AST와 저장 출력 없음이라는 실제 조건으로 고친 후 반영했습니다. 최초 후보의 Boolean을 0과 혼동하는 경계는 원본 반영 전에 수정하고 재실행했습니다.
- 본문 validator는 두 실행 모두 JSON상 통과와 종료 코드 0을 반환한 **뒤**, 정리된 임시 IPython runtime의 history 종료 과정에서 `sqlite3.OperationalError: attempt to write a readonly database` traceback을 기록했습니다([최종 로그](main-validation-final.log)). 내부 임시 runtime 정리 후 history 종료 처리가 남은 것으로 보이며 상대경로 문제라는 앞선 추정은 철회합니다. 예제 셀 오류는 0개이나, 이 종료 경고는 해결된 것으로 취급하지 않습니다. 인터페이스 탐색 시 `Operation not permitted` 경고도 있었고 일반 소켓·브라우저 차단을 우회하지 않았습니다. HTML과 오프라인 MathJax의 전체 시각 검토는 하지 않았습니다.

기존 보충 독립 6번을 대체·확장하고 worked 코드 셀 하나를 추가해 필수 수행 단계와 글은 증가했습니다. 기존 6번을 포함하는 셀의 문자는 608→1102자, 기존 worked 설명 셀은 1017→1951자이며 문자 수는 난도나 시간을 뜻하지 않습니다. 실제 학생의 이해·성취·도움·소요시간은 관찰하지 못했습니다. 작은 표본의 지표는 실제 성능 추정이 아닙니다.

## 원문

[scikit-learn DummyClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyClassifier.html)의 최빈 전략·`classes_`/`predict_proba`와 [IOAI 2026 Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md)의 같은 로봇, 독립 snapshot, 과거 미제공, 익숙한 구성 요소의 새 조합 가능성을 확인했습니다. KOAI 2026 예시는 고등부 학습 참고이며 IOAI는 국제 문제입니다. 실제 대회 분할을 합성 질문에 덧씌우지 않았습니다. 실행환경은 Python 3.12.14, scikit-learn 1.8.0, NumPy 2.5.4, pandas 3.1.1, Matplotlib 3.11.2입니다. 노트북은 scikit-learn 1.3 이상을 요구합니다.
