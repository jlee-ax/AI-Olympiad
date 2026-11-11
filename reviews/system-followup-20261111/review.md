# 독립 검토 후 재작업 결과 — 2026-11-11

직전 구현의 네 결함을 재현해 수정했다. **선언된 로컬 자료 전체 확인**, **최신 스킬·실제 교안의 결합 실행**, **문제별 내용 검토의 별도 연결**, **단독 workflow의 중복 JSON 키 거부**가 구현·검증됐다. 전체 회귀 **228개**, 실제 1주차 기록 복제본 **21개 시나리오**가 통과했다. 실행 성공은 교육적 수용이 아니다. 최신 K01–K16 결과는 여전히 `uncertain`, `ready_for_review: false`다.

이 보고서는 앞선 시스템 검토의 후속 보정이다. 기존 main `787079f`, 스킬 `64f24aa`, lesson `204743d`와 사용자 변경을 보존했다. 원본 교안 브랜치와 그 작업본은 수정하지 않았다. 자동 스케줄·main 병합은 하지 않았다. GPT-6.1 Sol Ultra 구현·독립 검토를 사용했다. Goal 모드는 제공되지 않아 활성화되지 않았다.

## 수정 전후

| 결함·실제 재현 | 수정과 정상 대조 | 실제 결과/남은 한계 |
|---|---|---|
| preflight가 active recall의 source만 읽음. 실제 `source-register`는 선언·context reference에는 있으나 recall에는 없고, 예상 SHA `4286e627…`와 실제 `234f1a9e…`가 달랐는데 누락됨. superseded review 파일의 변경·삭제도 놓침. | 모든 source catalog의 로컬 URI를 검사한다. context-only·미사용·과거 source도 포함. file URI는 root에 가두고 잘못된 URI/누락을 차단한다. catalog 자체도 aggregate review의 입력 manifest로 묶는다. | 실제 복제본의 drift는 `stale_declared_source`; 변경한 과거 파일은 stale, 지운 파일은 unreadable. 변경 없는 과거 고정 바이트는 pass. 외부 URI는 미검증으로 표시하며 온라인 진실을 인증하지 않는다. |
| 최신 quality.py를 lesson checkout root에 바로 적용하면 최신 theory spec 등 파일이 없어 함께 실행되지 않음. | 최신 tools/skills/specs와 lesson의 curriculum/lessons/reviews를 새 외부 작업본에 정확한 해시로 복제한다. 기존·입력 내부 출력 경로와 symlink를 거부하고 원본/복제 기준을 실행 전후 확인한다. | 최신 baseline, 옛 bundle 평가, 새 커널 전체 실행, 최종 내용 검사, 현재 artifact-bound bundle 평가가 모두 exit 0. 원본 변경 0, 예상 밖 복제 파일 변경 0. 이것은 OS 보안 sandbox가 아니라 검토된 코드의 복제 실행 환경이다. |
| 그래프의 7역할과 해시가 맞아도 네 문제의 feedback이 모두 일반 복습 c85를 가리켜 문제별 해설이 아님. | 형식 결과와 별도로 현재 graph/spec/evidence에 묶인 검토 기록을 요구한다. key·feedback·independent assessment의 각 내용 판단과 근거를 구분하고, 누락/old/gap/uncertain은 preflight를 차단한다. | 일반 복습 연결은 형식 `declared_path_complete`, 내용 `gap`. 실제 교사용 문제별 해설을 연결하면 피드백 gap은 해소되지만 분산의 독립 평가 설계는 `uncertain`. 학생 독립 수행은 모두 미관찰. |
| 단독 workflow CLI가 `json.loads` 기본 파서로 중복 키를 허용. root/nested/Unicode-escaped 키의 모순 입력을 네 명령 모두 exit 0으로 받았고 decide가 continue. | 모든 CLI 명령이 공유하는 strict object-pairs 파서가 중복을 거부한다. API는 변경하지 않는다. | 같은 입력은 exit 2, `blocked / unreadable_state`, 안전한 duplicate-key 진단. 정상 인접 JSON·CLI/API 일치·입력 불변도 통과. |

새 실행 도구도 독립 검토를 받았다. 테스트 중 발견한 오래된 실행 receipt 재사용, bool/int 혼동, 다른 artifact에 실행 pass를 붙이는 문제, 나중 명령이 artifact/receipt를 바꾸는 문제를 수정했다. 복제된 옛 receipt를 삭제하고 새 timestamp·현재 hash·정확한 정수 count·실행 방식·필수 assertions·source projection·빈 학습자 코드 범위를 확인한다. 이후 변경은 pass를 무효화한다. 현재 도구는 실행 flag 없이 notebook/key 코드도 실행하지 않는다.

## 실제 최신 결합 실행과 현재 기록

[실행 receipt](combined-run.json)는 5개 실제 명령이 정상 완료됐음을 기록한다. 준비된 workspace에는 tool layer 60파일, lesson layer 83파일이 있었다. 실제 공급된 코드를 새 in-process 커널에서 실행하고 standalone CSV fallback까지 확인했다.

- **27/27 코드 셀, 오류 0.** 빈 학습자 코드도 실행 셀 수에 포함되며 답을 채우거나 채점하지 않았다.
- 입력 notebook SHA `2506059c…`, 실행 후 SHA `7b933976…`. source·attachments·셀 ID/type는 동일하고 일부 표/그림 출력 바이트가 달라졌다. [비교 기록](current/artifact-comparison.json)과 [실행된 감사용 notebook](current/week01_python_tables.ipynb)을 보존했다.
- [최신 K01–K16 결과](current/quality-result.json): K01/K08 등 실제 artifact·실행 바인딩은 pass. K02/K04/K15는 not_run; K05/K09/K12/K14/K16은 uncertain. 전체는 uncertain/검토 수용 불가. 옛 content review를 현재 pass로 자동 승격하지 않았다.
- [현재 bundle](current/quality.json), [새 실행 영수증](current/execution-receipt.json), [실행 workspace 파일 해시](current/workspace-manifest.json)를 저장했다. 이 bundle의 상대 경로는 결합 workspace 기준이다. 저장된 감사용 notebook은 원래 lesson 경로를 덮어쓴 것이 아니다.
- 실행 뒤 독립 검토자가 새 notebook의 task/response/feedback와 실제 teacher key를 다시 읽고 새 SHA에 묶인 [현재 내용 검토](current/graph-semantic-review.md)를 별도로 만들었다. 분산의 독립 평가 불확실성을 유지한다.

원본 보존 확인은 실행 시점에 수행됐다. 그 후 거짓 양성 가능성이 있던 **테스트 하나만** 강화하고 전체 회귀를 다시 실행했다. [바이트 비교](current/final-tool-parity.json)는 실제 실행한 제품 도구·스킬과 최종 제품 파일이 동일함을 확인한다.

## 기능 테스트 근거

[전체 회귀 로그](regression.log): **228/228** — contest depth23, graph42, combined workspace13, quality43, quality-followup36, joined preflight16, legacy graph/API/CLI12, workflow39, strict-JSON4. JSON4개 테스트는 파일/표준입력과 네 명령을 조합한 144회 실제 CLI 호출을 포함한다.

[실제 복제본 21개 결과](functional-results.json)는 원본 graph 형식 pass/경로 gap, 누락 feedback edge, 바이트 stale/복원, 원래 state 차단, source-register drift, 정상 historical source·변경·삭제, 일반 feedback의 내용 gap, 실제 key로 고친 뒤 남는 uncertainty를 확인한다. 원래 pending criteria나 실제 학생 결과를 조작해 pass로 만들지 않았다.

새 workspace13개 테스트는 정상 fresh receipt, 24개 잘못된 receipt field, 누락된 새 receipt, 오래된 receipt, 원본/복제 변경, 도구·기준 파일 추가, 후속 notebook/receipt 변경, 다른 artifact 경로를 검사한다. 임시 fixture의 정상 pass는 도구 동작의 대조군이며 실제 학습 성과가 아니다.

재현 방법은 [결합 workspace 문서](../../tools/lesson-validation.md), [preflight](../../tools/review-preflight.md), [현재 내용 gate](../../tools/graph-paths.md)를 참고한다. 원본 lesson을 commit `204743d`로 고정하고, 새 외부 output 경로와 notebook 의존성이 설치된 Python을 지정한다. 도구는 의존성을 설치하지 않는다.

## 남은 한계와 실제 다음 일

- 실제 source-register의 옛 예상 바이트 불일치는 **발견·차단**했다. 옛 기록을 임의로 재해석하지 않았으므로 기존 workflow는 여전히 blocked/pause다. 과거 source는 실제 해당 버전 바이트를 보존하거나 새로운 source/record와 현재 검토로 갱신해야 한다.
- [문제별 내용 검토](graph-semantic-review.md)는 네 비교만 다룬다. 분산의 복합 과제에서 독립 수행을 판별할 별도 prompt/response·지원 조건이 불충분해 uncertain이다. 앞선 [87셀 전체 검토](../system-improvement-20261111/whole-week01-review.md)의 traceback·새 broadcasting/graph/merge probes·숙제 계획 과제도 남는다.
- 코드가 locator의 교육적 의미를 자동 판정하거나 reviewer 신원을 인증하지 않는다. 현재 semantic 판단은 근거 파일과 정확한 범위에 묶인 사람/에이전트 검토 기록이다. key가 맞다는 사실은 피드백이 전달되거나 학생이 독립 해결했다는 사실이 아니다.
- 새 커널 실행은 공급된 예제·assertions의 기술 검증이다. 브라우저 레이아웃, 교사 calibration, 실제 학생 답·소요 시간·유지·전이·효과는 검증하지 않았다. 2026 예시는 고등부 학습 참고용이며 2027 중등부 난도로 확장하지 않는다.
- 복제 workspace는 원본에 쓰지 않도록 구성하고 바이트 변경을 감지하지만 악성 코드에 대한 OS 접근 통제는 아니다. 네트워크/파일 권한을 철회하는 sandbox, 자율 작업자, writer/locking/인증 ledger, 반복 스케줄러를 구현했다고 주장하지 않는다.
