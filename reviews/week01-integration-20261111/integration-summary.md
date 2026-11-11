# 1주차 통합 교안과 검증

## 범위와 자료

학생 시작점은 [통합 노트북](../../lessons/week01/week01_integrated.ipynb)이다. [HTML](../../lessons/week01/week01_integrated.html)과 [교사용 해설](../../lessons/week01/week01_integrated_teacher.md)을 함께 제공한다. 10주 계획의 1주차 링크도 이 노트북을 가리킨다. 기존 본문과 두 보충은 보존하며, 학생이 통합본에서 필요한 선행 셀·필수 과제·복귀 순서를 찾을 수 있게 했다.

통합본은 하나의 합성 화분 표로 자료사전과 예측 시점 → 0과 결측·평균 → 배열과 그림 → 임의 고정식 → 훈련 자료로 배우는 모델 → 별도 검증 → ID와 CSV를 잇는다. 새로운 기기 표의 문자열 라벨·미상 라벨·다른 출력 순서를 학생이 직접 풀게 하며 답안은 비워 둔다. 기존 본문의 함수·새 CSV·집계/병합·두 라이브러리 그래프와 배열 과제, bridge의 필수 A/B는 남아 있다. 이들은 통합본 실행만으로 완료되지 않는다. 대상과 실제 위치는 [대응표](author/coverage-and-handoff.md)와 [독립 검토](independent/independent-review.md)에 있다.

기존 세 문서는 145셀/코드 53셀이고 새 중심 경로는 34셀/코드 16셀이다. 다만 남은 필수 연습을 합한 학습량이나 소요 시간이 이 비율로 감소했다는 뜻이 아니다. 이전 120분 수업과 자습 5~7시간은 이번 범위에 대한 실측이 아니다. 실제 학생의 시간·도움·이해와 전이는 관찰되지 않았으며 필요하면 수업 기간과 지원을 조정해야 한다.

[KOAI 2027 안내](https://kitpa.org/koai/2027)가 연결한 [출제 기준](https://kitpa.org/koai/syllabus)은 확인 당시 IOAI 2026으로 표시되어 있었다. [IOAI 2025 Antique](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb)와 [IOAI 2026 Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md)은 국제 개인전 원문이며 국내 중등 기출이라고 가정하지 않았다. Antique의 미상 입력 전체 활용과 두 무헤더 CSV/ZIP, Robot의 8×8×2 입력과 행동 예측은 이 입문 교안이 완수한 범위가 아니다.

## 실제 검증과 수정

- **초안 결측 오류:** 같은 CSV를 pandas로 읽으면 빈칸은 `NaN`인데 초안 함수는 `None`만 제외해 평균 24 대신 `NaN`을 냈다([수정 전](parent-review/initial-mean-regression.json)). 수정 후 동일 CSV, 0, `None`/`NaN`, 빈 목록과 전부 결측이 예상대로 작동했다([최종 재실행](parent-review/final-mean-regression.json)).
- **숫자 범위:** 다른 초안은 임의의 유한 수를 허용한다고 했지만 `[1e308,1e308]`의 합이 넘쳤다. 임의의 수를 모두 지원한다고 주장하지 않고 입력을 길이 10,000 이하, 관측값 ±1,000,000 이하로 명시했다. 지원 범위의 양·음 경계를 검증했다([전후 기록](discovery/overflow-contract-before-fix.json)).
- **실행:** 새 in-process 커널에서 34셀 중 코드 16개와 저장 출력을 확인했고, 학습된 평균·중심·검증 점수와 훈련 입력 변경에 따른 예측 변화를 대조했다. ID가 포함된 실제 임시 CSV의 쓰기·읽기·정리를 확인했다([실행 결과](author/integrated-validation.json)). 원본 필수 연습의 안내된 준비·제공 코드는 독립된 커널에서 재실행했다([결과](author/followup-route-validation.json)).
- **독립 검토:** 다른 검토자가 정해 둔 기준으로 코드와 새 입력을 독립 실행하고, 가까운 중심과 결정트리 두 모델을 실제 학습했다. 예측이 달라도 계약을 만족하는 경우를 수용했다. 새 subprocess 9개로 후속 경로를 확인하고, 누수·축·결측·ID·출력 등 13개 변이를 검사했다. 9개는 노트북의 자체 검사, 3개는 별도 의미 oracle, 1개는 노트북 실행과 숫자 검사만으로는 통과해 외부 물리 I/O 관찰로 구별했다. 원래 통과 결과를 덮어쓰지 않았다([근거와 한계](independent/independent-review.md)).
- **다른 원문:** Robot Chasing 계약을 바탕으로 새 합성 입력의 축·채널·허용 출력·순서에 대해 25개 기대값을 비교했다. 형식이 같아도 전치와 ID 오대응이 다르다는 것을 확인한 별도 검사이며 학생 전이를 입증하지 않는다([기록](transfer/review.md), [최종 교안 재대조](transfer/addendum-15ab0101.md)).
- **전체 회귀:** 첫 실행 255개 중 1개가 이전 계획 해시를 가리키는 미설정 템플릿 때문에 실패했다([로그](full-regression-initial.log)). 이전 계획·계약·템플릿을 보존하고 변경 사실을 명시한 새 버전으로 해당 참조를 갱신한 뒤 전체 255개가 통과했다([최종 로그](full-regression-final.log), [버전 기록과 기능 확인](plan-revision/revision.md)). 정책 합의나 예산을 만들어 넣지 않았다.

최종 노트북 SHA-256은 `15ab0101edbca3c0c669e551cb723b401d168d9730523fa1ac1263a0d7538120`, HTML은 `53b48bf8370cff4f97ace9f78cbf8c5b838f7c758a56b86ef82d474003470596`다. 그래프 이미지는 직접 확인했고 HTML은 저장본과 새 정적 변환이 같음을 확인했다. 일반 소켓 Jupyter/Colab 실행과 브라우저의 전체 HTML 화면은 환경 제한으로 검증하지 못했다.

## 보존과 기록의 해석

사용자의 별도 worktree에 남은 미커밋 교안·HTML·manifest·교사용 기록·검증 기록은 기존 해시와 일치한다. 새 미커밋 원문을 이번 검토에서 추가로 게시하지 않았고, 사용자가 삭제한 lesson README를 만들지 않았다.

과거 workflow는 `criteria_agreement_required` 중단 기록을 유지한다. 신규 계획의 구조적 baseline 통과는 예전 교안의 승인이나 새 교안의 학습 효과를 뜻하지 않는다. 계획 해시 변경이 모든 오래된 개별 검토에 자동으로 전파된다고 가정하지 않았고 새 자료에 별도 근거와 판단을 결합했다. [discovery 기록](discovery/review.md)은 출처·요구·후속 행동을 보존하되 연결·해시 검사가 내용의 의미나 학생 수행을 이해한 것은 아니라고 구분한다.
