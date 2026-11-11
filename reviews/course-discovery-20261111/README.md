# 실제 과정 discovery 검토

시작: [사람이 읽는 최종 검토](review.md).

- [새 원문 manifest](source-manifest.json), [새 요구](new-demands.json)
- [기존 큐를 계승한 baseline](runs/baseline-wave-01/report.json)
- [실제 10주 계획 비교](runs/plan-wave-01/report.json)
- [실제 2주 원본 SHA 결합 비교](runs/week02-candidate-02/report.json)
- [실제 1주 보충 별도 비교](runs/week01-bridge-02/report.json)
- [최종 무변경·실행 증거](checks/final-03/integrity-and-execution-evidence.json)

모든 현재 상태는 `needs_work`다. 도구의 바이트 영수증·해시 사슬은 의미적 충분성이나 학생 성취를 보증하지 않는다. 기존 세션·원본 교안·타인의 작업·git index는 수정하지 않았으며 commit/push는 실행하지 않았다.

중복 중간 상태와 CLI report 영수증은 검증된 다섯 아카이브에 보존했다. 최종 session/report/manifest/이벤트와 출처는 펼쳐 있다. 압축 방법·전체 파일 목록·해시·복원 및 재현 명령은 review.md와 archive manifest에 있다.

1주 보충의 원본 변경 전·후 판정은 [버전 후속 기록](bridge-version-followup.json)에 있다. 이전 세션은 보존하며 `artifact_changed` 상태로 현재 후보와 구분한다. 최종 원본의 정확한 바이트 사본은 [snapshot 목록](final-artifact-snapshots.json)을 따른다.
