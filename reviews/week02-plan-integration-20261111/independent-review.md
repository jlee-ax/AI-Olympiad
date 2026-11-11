# 2주 학습 계획 개정의 독립 검토

검토자: /root/plan_independent_review. 이 기록은 요청받은 계획 개정과 합성 예시의 정합성을 독립적으로 확인한 것이다. 정확한 모델 ID는 확인할 수 없어 기재하지 않는다.

**판정:** 아래에 명시한 범위에서 최종 계획 개정이나 합성 예시를 막을 새 결함은 확인하지 못했다. 이 판정은 기존 1주 검토의 재승인, 실제 학생의 성취, 후속 교안 완성 또는 최종 테스트의 준비를 뜻하지 않는다.

## 직접 확인한 대상

- 학생 계획: curriculum/student-plan.html — SHA-256 c60063bf1c55b957f4b6271a0796d5301d9f209de28a91d468c0c20e72fa0133
- 계약: curriculum/contract.json — a84c4fa7e363050bad0d6c204d583384e6d37474b9295dd2f3797a3272276c99
- 미설정 품질 템플릿: templates/quality.json — 976dc0a9047041c4a97e0a1b9dbfda210b51c08dd8773e87d31fa4338df73f8a
- 저장소 루트 README.md — 609310eef6e5c3669ec66eb545765abfb9ed121d6e8bcebbc17449915ecb52c8
- 2주 교사 해설: lessons/week02/teacher-notes.md — 265b54be1f423704332dd4b0f62817d3ce4d38b12e009710856b047e486dec46
- 합성 품질 예시: examples/quality.json — 45b0c265b178f63dd436780d821deb8692483c41e69c3536d225be928ef08c11
- 합성 workflow 예시: examples/quality-workflow.json — 8610f8a3a11f6ed61cc2436eb5bb92282645b9cb9a090c25489cd6d90dcee0c0
- 합성 맥락 검토: synthetic-context-review.md — fa2b9de88433e1505a1e094b77579502f5ecec9a948a3f7eb2c68a1da91e67cb

위 SHA는 실제 파일에서 계산해 전달받은 값과 대조했다. 검토 과정에서 위 파일을 수정하지 않았다.

## 분할 원칙과 반례

기존 학생 계획의 무조건적인 개체 묶음은 2주 교안의 서로 다른 원본 기록 X와 Y로 알려진 기기의 새 설정을 평가하는 명세와 충돌했다. 최종 계획은 처음 보는 개체를 평가할 때 개체별 분할을 요구하고, 알려진 개체의 새 설정이나 미래를 평가할 때는 같은 ID가 양쪽에 있을 수 있되 이것이 새 개체 일반화의 근거가 아님을 밝힌다. 같은 기기의 행이 서로 독립이라는 주장도 아니다.

- 새 기기의 성능이 목적일 때 A/B를 훈련, C/D를 검증으로 두는 것은 그룹 분리의 예다. 같은 기기의 A1과 A2를 훈련과 검증에 나누면 이 목적을 충족하지 못한다.
- 알려진 기기들의 기존 설정 X로 학습하고, 같은 ID의 별도 원본 기록 Y를 검증하는 것은 새 설정이라는 별개의 목표를 평가할 수 있다. 같은 ID가 사용됐다는 사실만으로 무효가 아니지만, 중복과 정보 제공 시점 등은 여전히 확인해야 한다.
- 알려진 센서의 미래를 예측할 때 예측 시점에 실제로 도착한 과거 관측은 평가 입력의 허용 문맥으로 사용할 수 있다. 아직 도착하지 않은 관측이나 미래 정답은 사용할 수 없으며, 과거 문맥을 전처리 fit 자료나 같은 예측 대상의 복제로 혼동하지 않는다.
- 훈련에 없는 검증 사례와 그 복제본을 각각 검증과 최종 테스트에 넣으면 최종 평가가 오염된다. 최초 후보의 훈련과의 중복만 금지한 문구로는 이 반례가 남았지만, 최종 계획은 같은 예측 대상 사례의 복제·증강·파생본이 훈련·검증·테스트의 서로 다른 분할을 넘나들지 않도록 한다. 허용된 과거 문맥 전체를 무조건 금지하지도 않는다.

2·4주 공통 분류 자료는 새 개체 평가이므로 그룹 분리를 유지한다. 교사는 아직 실제로 준비되지 않은 별도 최종 테스트를 구성해 선택 담당자가 보지 못하게 보관하고, 4주 수업과 필수 자습의 선택을 마치고 고정한 뒤 한 번 평가하도록 되어 있다. E/F는 실제 테스트가 아니라 자리 표시다. 자료가 없으면 미완료라는 문구도 있다. 이 검토에서 보관 장소, 별도 자료 또는 실제 접근 제한을 만들거나 검증하지 않았다.

8주 자습은 새 생성 틀 평가에서 동일 문장 및 생성 틀별 문장을 묶는 기존 필수 분할 연습을 유지한다. TF-IDF·BERT·전체 미세조정과 PEFT 등의 원래 학습 활동과 편성 시간도 계약상 보존되었다. 다른 문제의 분할은 그 목표와 명세에 맞춘다는 설명을 추가했다.

## 원문 및 학습 부담

직접 확인한 [KOAI 2027 안내](https://kitpa.org/koai/2027)는 중등부를 포함한 1~4과목 범위와 필기 3시간·코딩 3시간을 설명하고, 연결된 [국내 실라버스](https://kitpa.org/koai/syllabus)는 IOAI 2026 기준으로 표기되어 있다. [IOAI 2026 Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md)은 같은 여섯 로봇의 학습과 공개 평가, 독립 snapshot, 이전 관측 미제공과 로봇별 평가를 명시한다. 이는 별도의 국제 문제이지 2주 합성 명세 또는 국내 중등 기출이 아니다.

[scikit-learn의 교차검증 문서](https://scikit-learn.org/stable/modules/cross_validation.html)는 새 그룹 일반화와 시간 구조에 맞는 평가를, [누수 방지 문서](https://scikit-learn.org/stable/common_pitfalls.html)는 훈련 데이터에만 학습형 전처리를 fit하는 원칙을 설명한다. [Stanford CS229 강의노트](https://cs229.stanford.edu/main_notes.pdf) 9.3절은 검증 자료를 이용한 모델 선택의 원리 근거이며, 수업 시간이나 학생의 수행 시간에 대한 실측 근거는 아니다.

2주 수업 120분과 필수 자습 6~8시간은 유지된 편성이다. 학생 계획은 6~8시간이 현재 본문과 보충 교안에 대한 실제 학생 소요 시간이 확인되기 전의 추정임을 명시한다. 계획의 10주 수업·필수 자습 총량도 편성 추정이며 학생 이해·도움·독립 수행을 측정한 것으로 해석하지 않는다.

## 진입 링크

2주 계획의 본문과 보충 노트북은 원격 브랜치의 실제 두 노트북을 각각 가리킨다. GitHub 연결 도구로 본문·보충의 노트북 및 HTML 파일 네 개가 해당 브랜치에 존재함을 확인했고, 각각의 원격 Git blob SHA가 로컬 파일의 Git blob SHA와 일치함을 계산했다. 두 노트북의 서로를 가리키는 상대 경로도 같은 로컬 디렉터리에서 대상이 존재한다.

GitHub의 HTML blob은 렌더된 웹 페이지가 아니라 소스 보기였다. 노트북 blob에는 Preview와 원본 다운로드가 표시됐지만 웹 추출에서는 preview가 Loading 상태여서 내부 링크 클릭과 시각 렌더를 확인하지 못했다. README는 계획 HTML을 내려받아 브라우저에서 열도록 안내하지만, 이 검토에서는 다운로드와 로컬 브라우저 렌더 또는 사용자의 Jupyter 실행을 실제로 시험하지 않았다.

## 계약·이력과 1주 영향

현재 계획의 SHA는 계약 baseline과 미설정 템플릿 artifact pin에 모두 일치한다. v2 계획·계약·템플릿 snapshot의 SHA는 각각 cbe69f862ae76a87cd69233889c7fd6698e38ac34eb4d385f2b825722daeabb5, 977460b110c75a89c08731c59f045e53168ff36dc8896ca6b0bdf4b3057a4b54, 0b74c8fb3f3e5e71fa776535230e3d6fa980d828b9a57195343cb25f6d729097이다. v3 계약은 v2 계획과 계약 snapshot을 supersedes로 참조하고, v2 계약은 기존 v1 이력으로 이어진다.

v2와 v3를 직접 비교했을 때 1주 행은 원바이트가 같고, 영역 해시가 바뀐 곳은 예약된 #plan-context와 #week-2, #week-4, #week-8이다. 계약의 주별 시수·자습 배열과 60개 항목, 이론·실전 표기는 같고, 템플릿 정책과 기존 리뷰 배열도 같다. quality.baseline의 읽기 전용 실행은 10주·주당 120분·60개 예정 항목에 대해 passed를 반환했다. 이는 구조·pin 검사이지 교육적 합격이 아니다.

#plan-context는 별도 HTML 행 ID가 아니라 식별되지 않은 표 행과 표 밖 가시 내용을 묶는 예약 선택자다. 이를 결합한 검토는 공통 원칙 변경의 영향을 받을 수 있다. 반면 모든 실제 1주 검토가 자동으로 stale이 된다고 단정하지 않는다. 기존 1주 quality bundle은 명시적인 plan_dependency_ids가 없는 legacy 기록이고, 1주 통합 discovery의 별도 context-binding은 계획·계약·템플릿의 전체 SHA를 보관하며 별도 검증기가 이를 확인한다. core discovery가 그 추가 manifest를 자동 추적한다는 뜻은 아니다. 기존 기록은 보존되며 변경된 공통 맥락의 영향은 별도 확인이 필요하다.

기준 commit 190eecaa의 GitHub blob과 현재 로컬 바이트를 직접 대조한 범위에서는 1주 통합 노트북, 1주 discovery의 context-binding·최종 상태·보고서, 이전 1주 quality bundle이 일치했다. 공유 quality-specification, 두 evaluator와 test_quality.py도 기준 blob과 일치했다. 이것은 열거한 파일에 대한 확인이며 사용자 1주 worktree 전체를 조사했다는 뜻이 아니다.

공유 skills/references/quality-specification.md에는 현재 계획을 과거 SHA 96deb5e5e781bf39cc6bb5effe34d6d04a01ac65e13a3811c37f5a825714f7a9로 설명하는 오래된 문구가 남아 있다. 이 SHA는 실제로 보존된 lessons/week01/provenance/student-plan.html에 해당한다. 공유 specification과 결합된 이력을 보존하기 위해 이 검토에서는 그 파일을 수정하지 않았고, 안내 정정은 열린 항목이다.

## 합성 예시의 선택적 재검토

v2 예시 snapshot과 실제 파일을 재귀 비교했다. quality.json은 과거 12개 리뷰를 그대로 보존하고 K02·K05·K09·K15·K16에 대한 synthetic 리뷰 5개를 추가했다. 다른 변경은 예시 revision과 계획 의존성의 revision/SHA뿐이다. quality-workflow.json은 과거 3개 리뷰, agreement와 history를 보존하고 예시 bundle 결합을 갱신했으며 synthetic workflow 리뷰 1개를 추가했다. 두 예시의 이전 snapshot도 기준 commit의 원본 Git blob과 일치했다. 새 기록은 가상의 축 평균 통제와 맥락 검토를 나타내며 실제 수업·학습자 결과나 사용자 승인이 아니다.

직접 읽기 전용으로 평가한 결과, 과거 합성 예시를 현재 계획과 결합하면 위 5개 unit 리뷰는 #plan-context 변경으로 review_required, K06 claim은 current, ready_for_review는 false였다. 최종 합성 예시의 quality CLI는 exit 0, 16개 체크 passed, synthetic true 및 ready_for_review true를 반환했다. workflow CLI도 exit 0과 synthetic continue/verified_candidate_within_budget를 반환했다.

파일을 바꾸지 않고 메모리의 영역 결과만 대체한 반례에서는 전역 평가 문구가 변하면 새 5개 리뷰가 review_required가 되고 K06은 current였다. 무관한 #week-3 행만 바꾸면 5개 리뷰와 K06은 current였다. 이는 영역 freshness 함수의 선택성을 확인한 것이며 실제 파일을 바꾸고 계약 pin을 갱신하지 않았을 때 전체 baseline 검사가 통과한다는 뜻은 아니다.

## 범위와 한계

이 검토자가 실제 실행한 검사는 SHA·원격 Git blob 비교, HTML 영역 및 계약 비교, quality.baseline, 합성 예시 quality/workflow CLI, 그리고 위 메모리 반례다. 전체 unittest, 새 노트북 커널 실행, 브라우저 시각 검토, 학생 답안·소요 시간·학습 효과, 숨겨진 최종 테스트의 생성·보관은 이 독립 검토에서 수행하지 않았다. 원문을 확인한 것은 위에 열거한 위치와 요지에 한정하며, 과거 국제 문제를 국내 시험이나 학생 성취로 바꾸어 주장하지 않는다.
