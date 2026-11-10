# pstack-codex 비교와 현재 설계에 반영할 부분

2026-11-10에 [ScriptedAlchemy/pstack-codex][port]의 `7f3b75256df824ca84a9b76b6bc202b967a221c2`(2026-11-09)를 읽었다. **독립적인 비공식 포트**이며 Cursor 또는 OpenAI의 공식 배포판이 아니다. 설치·포트 코드 실행·외부 서비스 변경 없이 공개 소스와 검증 보고서만 검토했다.

원래 출발점은 Lauren Tan의 pstack이다. 이 포트는 Codex 실행 환경에 맞추는 방법을 참고하는 보조 자료로 사용한다. 원본 절차와 출처를 이 포트로 대체하지 않는다.

## 비교 기준과 증거 수준

- 포트의 [UPSTREAM.json][upstream]은 원본 `236e5481d05cbadc315b374a5de54971858c27bb`, v0.15.36을 가리킨다. 우리 기준인 `c742dd61706fbacc1b95f1a20b7b988cf096ce6c`와 GitHub Git Trees API로 비교한 **pstack 하위 트리 해시는 모두 `4719e1c4b4c43bac85d4206a8b41dd2899769c1c`**였다. 두 기준은 pstack 내용이 같다.
- [PARITY.md][parity]는 모든 원본 파일에 유지·수정·대체 대응이 있다고 설명하면서, 파일 대응이 행동 동등성을 증명하지 않는다고 명시한다. [실제 parity 검사][parity-code]도 대상 파일 존재와 Git blob 해시를 확인한다. 이는 모델의 지시 준수, 재시작 복구, 서비스 성공률을 측정하는 검사가 아니다.
- [통합 검증 보고서][integration]의 최신 관찰 기록은 2026-10-23의 v0.15.32 대상이다. 현재 v0.15.36 전체에 대한 새 실서비스 검증으로 읽지 않는다. 아래 구현 확인 역시 실행 성공의 증거는 아니다.

## 유지할 원칙, 참고할 구현, 현재 제외할 기능

| 영역 | 읽은 실제 구현과 한계 | 현재 읽기 전용 제작 절차에 주는 시사점 |
|---|---|---|
| 지속 상태 | [CODEX.md][runtime]와 [Orchestrate][orchestrate]는 작업 목록과 `<repo>/.codex/pstack-runs/<run-name>/` 기록을 사용한다. 재시작하면 현재 branch/PR 상태를 확인하고 작업자를 다시 만든다. 이전 agent id는 영속 작업자 핸들이 아니다. | pstack의 인계·검증 원칙을 유지하고, 명시적인 상태 위치·내용 버전·재개 지점을 채택한다. 파일이 남았다는 사실을 작업자가 계속 실행 중이라는 뜻으로 해석하지 않는다. 현재 로컬 도구는 기록을 판독할 뿐 작업자를 실행하지 않는다. |
| 예약과 30분 | 런타임 계약은 현재 호스트가 제공하는 automation 스키마를 확인하고 저장 결과를 검증하라고 한다. detached sleep은 지속성이 아니다. 현재 포트는 PR/CI 이벤트 구독 대신 필요할 때 `gh`로 상태를 읽고, 가능한 경우 저장된 heartbeat를 사용한다. | 우리 30분은 승인된 실행 중 점검·인계 기준이다. 현재 환경의 예약 도구는 최소 1시간이므로 이 포트도 30분 자동 예약을 가능하게 하지 않는다. 이번 설계에서는 예약을 등록하지 않는다. |
| PR watcher | 포트와 원본의 `watch-pr/cli.ts`, `policy.ts`, `github.ts` 세 파일을 읽고 바이트 비교했으며 동일했다. [CLI][watch]는 단일 PR·스택·고정 큐, JSON/NDJSON, 기본 60초 조회·300초 전체 점검, 설정 가능한 timeout을 제공한다. 기본 timeout은 0으로 무제한이다. | 입력 검증·명시적 상태·제한된 대기라는 방법을 참고한다. 현재 수업 제작 절차에는 GitHub 조회나 PR 생성·병합 기능을 가져오지 않는다. 파일을 실행하지 않았다. |
| watcher 판정 | 중복 PR 번호는 거절한다. [정책 코드][watch-policy]는 충돌·리뷰·CI 등을 분류하고, 큐의 동일한 대기 보고를 억제한다. `--status-only`의 종료 코드 0은 상태 보고 성공이므로 JSON의 판정을 별도로 읽어야 한다. | 프로세스 성공, 검사 통과, 자료 완료를 분리한다. 중복 출력 억제는 외부 작업 중복 실행 방지와 다르다. watcher는 예약 서비스나 교육 적합성 검증기가 아니다. |
| Benny 기록 | [ledger.mjs][ledger]는 로컬 JSON 상태, cursor, report별 상태, 실행 lock, prepare/resolve를 구현한다. 임시 파일·fsync·rename으로 저장하며 외부 실행 전 의도를 기록한다. 확인되지 않은 의도는 재실행을 막는다. | 읽기 전용 planner에는 외부 작업 ledger가 필요하지 않다. 향후 실행 기능을 승인받으면 중복 키·모호한 결과 보존·재시도 전 확인을 참고할 수 있다. 외부 시스템의 exactly-once 보장은 아니다. |
| 모델 선택 | [모델 설정 스킬][models]은 역할별 `model @ effort`, 현재 실행 도구의 허용값, 누락 시 명시적 상속, 제한된 병렬 수를 사용한다. 전체 대화 fork와 모델 override가 충돌하면 필요한 문맥을 담은 새 fork를 요구한다. | 역할과 권한은 모델 이름과 분리한다. 사용자 선택과 실제 tool schema가 우선이다. GPT 계열의 서로 다른 이름을 독립 공급자나 독립 정답 근거로 표시하지 않는다. 현재 로컬 planner는 모델을 호출하지 않는다. |
| 경계와 권한 | 런타임 계약은 persona의 읽기 전용 문구를 독립적인 보안 경계로 보지 않으며, worktree를 cloud VM으로 부르지 않는다. 외부 연결과 자동화는 설치만으로 활성화되지 않는다. | 로컬 경로·권한·외부 쓰기 범위를 명시한다. 이 세션에서 금지된 `~/.codex/sessions` 읽기는 포트의 transcript 절차를 이유로 수행하지 않는다. 기존 사용자 제한이 우선이다. |

## 예약·복구·학습 주장에 남는 한계

[Benny polling 계약][polling]과 설정에서 반복 cadence는 사용자가 승인한 호스트 지원 값이다. `triage_total_minutes: 30`은 한 신고의 처리 예산이며 30분 반복 예약이 아니다. `poll_seconds: 45`도 실행 중 읽기 간격이다. 기록 파일에는 스케줄러나 Slack/tracker 클라이언트가 없다.

ledger의 실행 lock과 명령별 transaction lock에는 자동 만료나 강제 해제가 없다. 이는 겹친 작업을 보수적으로 막지만, 프로세스가 죽은 뒤 자동 복구된다는 뜻은 아니다. prepare 이후 불확실한 외부 결과는 실제 서비스를 확인한 뒤 해결해야 한다. evidence 문자열이 있다는 사실만으로 외부 결과가 인증되지는 않는다. 로컬 fixture가 다루는 중복·복구와 실제 네트워크 중단 상황을 구별한다.

통합 보고서는 2026-09-17에 읽기 전용 GitHub PR 조회, 별도 CLI 프로세스의 ledger fixture, 실제 Codex persona·worktree·로컬 UI bridge 등을 관찰했다고 기록한다. 예약 검증은 **일시정지 heartbeat 생성 → 조회 → 삭제**였으며 시간에 맞춘 실행은 검증하지 않았다. Slack/tracker 전체 흐름, 실제 PR 병합, 임의 앱 재현, 무인 예약 전달은 해당 환경에서 확인해야 할 항목으로 남아 있다. 이 수치는 작성자 보고이며 이번 작업에서 재실행하지 않았다.

검토 중 [README][port]에는 삭제된 `orch`를 포함하는 테스트 명령이 남아 있었고, 현재 [package.json][package]은 `watch-pr`와 `check-plan.test.ts`만 지정한다. 문서의 설명이나 명령을 그대로 설치 절차로 승격하지 않고 정확한 revision의 실제 진입점을 확인해야 한다.

현재 적용할 것은 **호스트 기능 확인, 기록과 실행의 구분, 정확한 대상에 연결된 검증, 중복·불확실 상태의 보존**이다. pstack의 orchestrate·hillclimb·eval·correct·reflect가 핵심이고, 이 포트는 Codex에 옮길 때 생기는 차이를 설명하는 자료다. 포트 설치나 실행 기능 추가, 예약 활성화, 교육 효과 주장은 이번 비교의 산출물이 아니다.

[port]: https://github.com/ScriptedAlchemy/pstack-codex/tree/7f3b75256df824ca84a9b76b6bc202b967a221c2
[upstream]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/UPSTREAM.json
[parity]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/PARITY.md
[parity-code]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/scripts/parity.py
[runtime]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/CODEX.md
[orchestrate]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/skills/poteto-mode/playbooks/orchestrate.md
[watch]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/skills/poteto-mode/scripts/watch-pr/cli.ts
[watch-policy]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/skills/poteto-mode/scripts/watch-pr/policy.ts
[ledger]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/automations/benny/scripts/ledger.mjs
[polling]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/automations/benny/POLLING.md
[models]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/skills/setup-pstack/SKILL.md
[integration]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/INTEGRATION-TESTS.md
[package]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/skills/poteto-mode/scripts/package.json
