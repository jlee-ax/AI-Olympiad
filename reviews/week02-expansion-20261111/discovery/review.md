# 새 실제 교안의 discovery 재결합 — 2026-11-11

기존 discovery 기록을 직접 읽고 현재 상태를 조회한 뒤, 수정된 1주 보충·2주 본문·새 2주 보완본을 **각각 별도 새 baseline**에 결합했다. 아래 세션은 모두 `needs_work`, `ready_for_review=false`, `next_action=expand_frontier`다. 기록 재결합과 내용 대조는 완료했지만, 과정 전체 완성이나 학생 성취를 뜻하지 않는다.

| 실제 단독 산출물 | 새 세션 | 보존 범위와 현재 결과 |
|---|---|---|
| 최종 1주 보충본 | [week01-bridge-time-cleanup-01](runs/week01-bridge-time-cleanup-01/current-summary.json) | D01/D05/D07 원래 payload와 미조사 질문 3개 보존. 15 events, queue 3, 세 요구 모두 gap. |
| 최종 2주 본문 | [week02-main-time-cleanup-01](runs/week02-main-time-cleanup-01/current-summary.json) | 원래 17개 요구와 미조사 질문 4개 보존. 48 events, queue 16, N01 covered. D06 assessment uncertain. |
| 최종 2주 시계열·전처리 보완본 | [week02-temporal-final-02](runs/week02-temporal-final-02/current-summary.json) | 같은 17개 요구와 질문 4개를 보존한 별도 대조. 48 events, queue 16, N01 covered. D06 assessment met와 H01 learning/assessment met의 국소 진전을 기록했다. 넓은 D06/H01은 gap. |

각 폴더에는 최종 `session.json`, `report.json`, `manifest.json`, `config.json`, 모든 입력 event, 전이 기록, 원본 exact 사본, 전 셀 source 투영과 provenance가 있다. 중복 `session-NN.json`은 만들지 않았다. 최종 세션·config·events로 재생할 수 있으며, 압축 대상으로 삼을 대량 중간 상태가 없다.

## 실제 원본과 투영 결합

| 원본 | 최종 raw SHA-256 | 전 셀 source 투영 SHA-256 |
|---|---|---|
| `lessons/week01/week01_axes_linear_bridge.ipynb` | `1c3ccb5d79d5e6c0a1cb919fd9f8cfac723637b1dedac2d056fe45379ffd8847` | `3729f73ad7c8b83e14427d0b63602fa664ff7a37e8bbf1a675effe7f6b6a782c` |
| `lessons/week02/week02_prediction_evaluation.ipynb` | `9bb1ea5110b74ea1cf32fbc9ee9e9a5aadbceba2f750c2dfc2d6587e18954bdf` | `7972fbeb15f57f4cc4aa47ec0c48dbe2c764e5ec229104eac06aba5e9aca1627` |
| `lessons/week02/week02_temporal_preprocessing.ipynb` | `a830a15e8d2bf2cb91e17cd2e8b14172390fc7cea3a07539add3fe52a05b5865` | `40c7ff79b4bd98dcd368163851dfcffa504d6053657262a8dfc7d413402b3c62` |

보완본의 최종 전체 해시는 [projection-provenance](runs/week02-temporal-final-02/projection-provenance.json), 세 산출물의 현재 결합은 [최종 integrity](checks/final-02/integrity.json)에 있다. 투영은 모든 셀의 index·ID·종류·source를 순서대로 포함하며 출력과 metadata는 생략한다. PNG와 stream 출력까지 포함한 노트북 원바이트는 각 `artifact-exact.ipynb`에 보존했다. 검토자가 최종 1주 29셀과 2주 본문 25셀을 전부 읽고, 보완본은 전 셀을 읽은 중간판의 exact 사본과 최종 변경 셀을 직접 대조해 최종 19셀의 내용을 확인했다. 바이트 일치 검사는 이 대응의 기계적 부분을 확인할 뿐 의미 판단을 대신하지 않는다.

## 이전 상태를 보존하고 낡은 상태를 드러냄

[변경 전 실제 조회](prechange-current-state.json)에서 기존 최종 네 세션은 모두 `needs_work`였고 freshness blocker가 없었다. 수정 전 1·2주 노트북 원바이트를 `prechange-week01-bridge-exact.ipynb`, `prechange-week02-exact.ipynb`로 보존했다.

변경 후 이전 2주 `week02-candidate-02`는 bound SHA `52b5c170…`와 현재 `9bb1ea51…`의 차이를, 이전 1주 보충 `week01-bridge-02`는 bound SHA `6241f6bc…`와 현재 `1c3ccb5d…`의 차이를 **`artifact_changed`**로 보고한다. [첫 stale 재현](old-sessions-stale-after-time-cleanup.json)은 당시 관찰한 중간 수정 SHA를 보존하고, [최종 integrity](checks/final-02/integrity.json)는 최종 원본 SHA로 다시 조회한다. 두 기록은 각 시점의 관찰이다.

미조사 질문의 우선순위 때문에 낡은 세션도 `next_action=expand_frontier`를 반환한다. 따라서 next_action만 보고 원본 결합이 최신이라고 판단할 수 없다. `artifact_changed`가 별도로 존재하며 이전 세션은 바뀐 노트북의 현재 근거로 재사용하지 않았다.

새 보완본도 `774f3c48…` 시점에는 `week02-temporal-final-01`과 `checks/final-01`로 실제 기록·재조회했다. 그 뒤 가중점수의 합산 순서에 따른 부동소수 차이를 반영해 저자가 설명과 exact assertion을 고쳤다. 이전 세션·report·exact raw·final-01 증거는 그대로 두고 [artifact_changed 재현](temporal-final-01-stale-after-float-fix.json)을 추가했다. 최종 `a830a15e…`는 새 `week02-temporal-final-02`와 `checks/final-02`로 재결합했다. [현재 실행 선택](current-run-selection.json)은 세 현재 세션과 이 낡은 재결합 이력을 명시적으로 구별하며 원래 요구를 은퇴시키지 않는다.

기존 최종 네 세션의 파일 SHA와 그 이전 원래 36-event 세션 SHA `81d71bca932382b67c280daabc32cd3bcbfb6fd14ffa87a712679b8e5b85bdf2`가 보존되었다. 보존 1주 baseline과 10주 계획의 원본은 여전히 기존 결합과 일치한다. 원래 baseline의 D03 covered를 취소하거나, 단독 보완본의 gap을 이전 수업의 회귀로 해석하지 않는다.

## 내용 판정과 후속 범위

검토자는 `/root/discovery_resume`다. 기존 1주·2주 저자는 `/root/week01_bridge`, `/root/week02_lesson`, 이번 학생용 시간 문구 정리자는 `/root/student_time_cleanup`, 새 보완본 저자는 `/root/week02_substantive_lesson`이다. 이 검토자는 그 교안을 작성하지 않았다. 원래 추출자 `source-research-sol`과 `/root/course_discovery/verify_new_scope`의 demand payload·출처 메모를 그대로 가져온 것이며, 그 역할이 이번에 원래 외부 검색을 다시 실행했다는 뜻은 아니다.

| 보존한 원래 요구 | 직접 읽은 현재 진전 | 열린 부분 |
|---|---|---|
| 본문 D06 | train-only 평균·표준편차 식, 올바른 transform, 누수 반례, 새 표의 직접 작성이 유지되었다. | 독립 누수 대 과대적합 비교가 본문에는 없어 assessment uncertain. 시간 문구 제거만으로 이 평가를 닫지 않았다. |
| 보완본 D06 | 그룹·시점 계약, train-only 중앙값/minmax/범주 fit, 검증 입력 변경 후 통계 불변, 새 입력 코드 수정, 누수 대 검증 과대적합 독립 질문이 실제 있다. assessment met. | 원래 principle의 훈련 평균·표준편차 z 변환과 practice의 train-only 대 전체자료 평균 중심화는 이 **단독** 보완본에서 구현하지 않고 본문을 선수로 참조한다. 해당 차원은 gap으로 남겼다. |
| 보완본 H01 | 정답 의존 가중치, 모든 평가 행을 포함한 분모, 두 지표의 순위 역전, 새 1:4 표의 손계산·코드 전이가 있다. learning/assessment met. | 원래 Radar의 `w(-1)=1`, 그 외 50 및 비배경 label 2와 지정 예측벡터를 다루는 contract/practice는 학생용 보완본의 B/T 합성 계약에 없다. 원래 요구를 합성 이진 계약으로 줄여 종료하지 않았다. |
| 1주 D01/D05/D07 | 행렬곱 축과 순서, 임의 ID 복원·새 독립 문제, guided lookup 전체 값·반복 index·순서 반례가 유지된다. | reshape 대 transpose 좌표, 정규화/cosine와 공식 매칭 제약, V/L 구별과 독립 lookup B/L/H 전이는 여전히 후속 범위다. |
| 두 2주 산출물 N01 | 각자의 설명·손계산·코드 예제와 새 입력 독립 필기/코드·도움 기록 설계를 대조했다. | 국소 자료 설계의 covered이며 시험 충분성이나 학생의 실제 독립 성취를 보인 것은 아니다. |
| N02/N03 등 | 본문의 unknown-0 구별, 보완본의 시간·변환 계약 등 관련 진전은 산출물별로 남겼다. | Pixel 사각형/출력 계약, PU 관측가정, 나머지 넓은 원래 요구와 미조사 질문을 삭제하거나 은퇴시키지 않았다. |

본문과 보완본은 서로 연결해 사용할 수 있지만, 여기의 discovery scope는 각각 한 실제 노트북이다. 여러 파일을 합쳐 읽은 척하거나 새 결합 산출물을 만들지 않고, 원래 17개 요구를 각 산출물에 독립 비교했다. 보완본 D06 gap은 본문+보완본의 학습 연결이 나빠졌다는 뜻이 아니다. 과정의 종합 readiness나 이 연결의 실제 수업 효과는 별도 근거가 필요하다.

보완본 검토 중 실행 환경 `scikit-learn>=1.2`와 ROC 첫 `+∞` 설명의 불일치를 발견해 [공식 API 문서](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html)의 version 1.3 변경 설명(L682–685)을 직접 읽었다. 저자가 최종판의 환경을 1.3 이상으로 고쳤다. [발견 기록](auxiliary-roc-version-check.json)과 [최종 해결 기록](auxiliary-roc-version-resolution-final.json)을 따로 보존했다. 이 좁은 호환성 확인은 원래 공식 범위·문제·이론 조사 전체를 다시 검색한 일이 아니다.

## 재현과 확인 한계

저장소 루트에서 다음 읽기 전용 명령으로 현재 상태를 다시 볼 수 있다.

```sh
python3 -B reviews/week02-expansion-20261111/discovery/verify_discovery.py
python3 -B tools/discovery_loop.py report reviews/week02-expansion-20261111/discovery/runs/week01-bridge-time-cleanup-01/session.json --root .
python3 -B tools/discovery_loop.py report reviews/week02-expansion-20261111/discovery/runs/week02-main-time-cleanup-01/session.json --root .
python3 -B tools/discovery_loop.py report reviews/week02-expansion-20261111/discovery/runs/week02-temporal-final-02/session.json --root .
```

최종 세 세션에 대해 `next/report/manifest` CLI를 각각 실행한 9개 호출이 exit 0이었다. CLI report의 parsed JSON은 저장된 권위 report와 모두 같았다. [실제 CLI·답안 공란 증거](checks/final-02/cli-and-answer-integrity.json)에 명령·stdout SHA·원바이트 길이·비교 결과를 남겼고, receipt가 큰 전체 report stdout을 중복 저장하지 않았다. exit 0은 유효한 재생의 뜻이며 완성 신호가 아니다.

검사기는 세 최종 원본의 exact 사본·전 셀 투영·현재 SHA, 모든 demand payload·미조사 질문 보존, 현재 report 일치와 freshness blocker 부재를 확인했다. 원문 검색과 의미 판정은 코드가 수행하지 않았다. 학생용 답안 공란 4개는 실제 AST 문장 수 0이며 학생 답을 채워 넣지 않았다. 이 discovery 역할의 재생 확인과 [별도 독립 코드 실행 검토](../independent/temporal-review-results.json), 학생의 학습 성취는 서로 다른 증거다. 독립 검토자의 최종 10개 정상 시나리오·14개 소스 변이 결과는 그 별도 JSON의 책임 범위다.

이 검토자의 쓰기는 `reviews/week02-expansion-20261111/discovery/` 안으로 제한했다. 기존 세션·노트북·교사용 파일·git index를 수정하지 않았고 commit/push를 실행하지 않았다. 최종 index SHA는 변경 전과 같은 `3d5a4b43568f538f5a4967581232c0dd709631feb14d389192b02ffd8ac0b300`이었다. `.pyc`, `__pycache__`, `.tmp`는 없다.

남은 과정 작업은 기존 미조사 질문인 국내/국제 2027 적용 관계·최신 PDF 차이, Pixel 세부 계약과 실제 환경, 완전한 반지도/관측모형 내용, 학생의 독립 전이·도움·성취 관찰 등이다. 후속 실제 주차의 교안 제작과 원래 넓은 요구 대조도 계속 필요하다. 이 기록은 그 범위를 축소하지 않는다.
