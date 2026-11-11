# 2주차 명세 전이 교안 — 작성자 기록

이 기록은 작성자의 유한 검산과 실행 결과입니다. 실제 학습자 답안·학습 성취·소요 시간, 숨은 최종 테스트의 확보 여부를 입증하지 않습니다. 독립 검토 결과는 [별도 검토 기록](independent-review.md)에 있습니다.

## 변경과 범위

본문 6절의 단일 M/N 과제를 다른 평가 목표를 가진 두 합성 명세로 교체했습니다. 새 개체의 미래와 알려진 기기의 새 설정은 분할 단위가 다릅니다. 두 문제 모두 예측 가능 입력, 훈련 전용 변환, 동일 검증 행의 후보 비교, 목적 지표 선택과 고정 후 무라벨 연습을 연결합니다. 보충 6절에 이미 있던 목적별 Robot 비교와 반복 분할 설계는 본문으로 통합했고, 보충의 과거 특성·ROC·가중점수·최빈 기준 연습은 남겼습니다. 보충의 동률 여부는 선택 전에 학생에게 알려주지 않도록 문구를 고쳤습니다. 1주, 10주 계획, 기존 사용자 작업과 원격은 건드리지 않았습니다.

본문 독립 문제는 1,529→2,541자, 보충 도입·분할 비교는 1,558→1,026자이며 두 부분 합계는 3,087→3,567자입니다. 보충의 무라벨 입력 안내는 657→676자입니다. 새로운 독립 선택과 구현은 늘었으며 글자 수는 난도나 실제 소요 시간의 대용이 아닙니다. 120분 수업과 별도 필수 자습 6–8시간은 기존 편성이고 실측하지 않았습니다.

## 입력과 원문

- 본문 SHA-256 `8edc5014f9d80f8cc0813153471cd5878b73023e9e3b4903a23d8e44688f9577`; 보충 SHA-256 `4852a81b3cd19d40e3baba5447b68f6a5765402e17edf658f9c5b84e1a669ba0`.
- 생성기 `8d2e1754e07c4e0da8f8f80f489c047111a983bd52e77ee45ac94462747b6653`; 교사용 본문 해설 `8c9f005ea78669f6b9c97face48c940a3a96a79e98e580e945386ed3f2747a9a`; 참조 검산기 `2fd86ccbdfa9cd65dc1e1f4efeb79141ef057c75b4d625bc0ebeeb559a9b46c6`.
- 본문 HTML `5e2f5a41b7f26ccf673529900ffa586f6a62af347296e13aeced41cbb5c86319`; 보충 HTML `30e27e99936beb934797148baf9646e5abb5ff8caa3da78eeb97cf550517f49f`; 보충 해설 `04fe73baac6f6a46874991ff5fa469834820a6fe28f1f1fcc95dd7b14e11213a`; 본문 기존 검사기 `d89bbd7c3262d22fa994ad1b93d62cfcef77ff31e958102a30ae4db63ccb6fc8`.
- [KOAI 2027](https://kitpa.org/koai/2027) 중등 시험 안내, 연결된 [IOAI 2026 표기의 국내 실라버스](https://kitpa.org/koai/syllabus), [IOAI 2026 Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md), [scikit-learn 그룹·시간 분할](https://scikit-learn.org/stable/modules/cross_validation.html), [누수 방지](https://scikit-learn.org/stable/common_pitfalls.html), [Stanford CS229 모델 선택](https://cs229.stanford.edu/notes2020spring/cs229-notes5.pdf)을 직접 확인했습니다. 국제 기출은 국내 중등 기출이나 새 합성 명세의 실제 분할로 제시하지 않습니다.

계획의 평가 원칙 29행, 2주 자습 40행, 4주 교차검증 52행은 반복 개체를 분리하는 범용 문구여서, 알려진 기기의 새 설정을 대상으로 같은 ID를 양쪽에 두는 명세 나와 표현상 충돌할 수 있습니다. X/Y는 같은 원본의 복사·증강이 아닌 별도 원본 snapshot이며 동일 기기의 기록 사이 상관은 남을 수 있습니다. 이 기록은 계획을 바꾸지 않으며 목표별 분할 문구의 후속 재검토를 열린 항목으로 남깁니다.

## 실행과 한계

저장소 루트에서 `PY=/workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python`으로 다음을 실행했습니다. 임시 실행 공간을 사용했고 기존 보고서나 교안을 덮어쓰지 않았습니다.

최종 본문 SHA `8edc5014f9d80f8cc0813153471cd5878b73023e9e3b4903a23d8e44688f9577`에 대해 생성기·참조 검산·본문 실행을 문구 수정 후 다시 실행했습니다. 보충 SHA는 앞선 실행과 같습니다.

- `$PY -B lessons/week02/build_week02.py --check-source lessons/week02/week02_prediction_evaluation.ipynb`: 통과, 25셀의 ID·종류·source 일치.
- `$PY -B lessons/week02/teacher_validate_contracts.py`: 통과. 실제 학생 과제 표의 입력을 읽고 별도 산술 및 scikit-learn fit을 비교했습니다. 가의 평균 2.5·표준편차 √19/2와 정확도 선택 K, 나의 평균 3·표준편차 √5와 재현율 선택 R, 고정 후 무라벨 예측 [-1,-1]·[1,-1]을 확인했습니다. 양성 0의 미정의, 알려진 클래스 0과 별도 미상, 관측 후 늦게 도착한 값, 훈련 fit 경계도 유한 사례로 확인했습니다. 학생 코드를 받거나 채점하지 않습니다.
- `$PY -B lessons/week02/teacher_validate_week02.py --inprocess`: 종료 0, 본문 코드 순차 실행·기존 본문 및 과거 M/N 대조 통과. 이 검사기는 새 두 명세의 학생 답을 채점하지 않습니다. 성공 결과 후 기존과 같은 로컬 네트워크 인터페이스 권한 경고와 IPython 종료 시 readonly SQLite traceback이 stderr에 발생했습니다.
- `$PY -B lessons/week02/validate_week02_temporal_preprocessing.py`: 종료 0, 보충 코드 순차 실행·저장 출력과 재실행 일치·빈 독립 코드칸 확인. 학생 답안을 자동 채점하지 않습니다.
- `$PY -B -m unittest discover -s tests -q`: 앞선 본문 SHA `813f7ea5ef20f38e06f974787857e191db30f0aa905a377fa3e053e57ca96984`에서 271개 통과(92.400초). 이후 본문 Markdown의 원본 구분 문장과 교사용 기록만 바꾸었으며 최종 판본에서 전체 271개를 다시 실행하지는 않았습니다. 현재 두 노트북의 모든 코드 셀 ID·source는 기존 HEAD e73c166과 일치하고 tests 경로도 변경되지 않았음을 별도 비교했습니다.
- 두 노트북을 `nbconvert.HTMLExporter().from_notebook_node(...)`로 내보낸 결과는 저장된 HTML과 각각 정확히 일치했고 저장된 오류 출력은 0개였습니다. 전체 브라우저 시각 확인과 오프라인 MathJax 확인은 수행하지 않았습니다.
- `git diff --check`: 통과.

이전 발견·검토 기록은 이전 자료 SHA에 결합되어 있으므로 현재 후보에 대한 자동 승인이 아닙니다. 공개 저장소에 교사용 답안이 있으므로 실제 접근 제한이나 비공개 평가가 준비된 것으로 말할 수 없습니다.
