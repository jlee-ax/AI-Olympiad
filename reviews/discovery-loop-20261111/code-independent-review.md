# Discovery loop 독립 기능 검토 — 2026-11-11

검토 대상은 `tools/discovery_loop.py`와 그 기록을 읽는 준비 상태 경계다. 구현 담당과 별도 delegated reviewer가 읽기 전용 코드 검토 및 실제 로컬 파일을 읽는 합성 실험을 수행하고, 재현 사례를 구현 담당과 부모 task에 전달한 뒤 수정본을 다시 검증했다. 검토 대상의 사용자 교안·출처 원본을 수정하지 않았으며 커밋·푸시도 하지 않았다. 이 검토 기록 파일은 부모 task의 별도 승인으로 작성했다.

## 검토자 설정과 독립성

부모 task는 이 검토를 실제 별도 **Sol6.1Ultra** 설정의 delegated reviewer로 지정했다. **Grace가 수행한 검토가 아니며 Grace의 대체·동등성 검증으로 주장하지 않는다.** 설정명은 부모 위임 메시지의 명시를 따른다. 이 실행에서는 provider의 runtime model 식별값을 별도 API로 조회하지 않았으므로, 모델 설정명의 독립 인증까지 수행했다고 주장하지 않는다.

기능 결과의 근거는 아래 코드 SHA와 이 reviewer가 직접 실행한 사례다. 구현 작성자의 자체 회귀 결과를 독립 실험 결과로 전용하지 않았다. 최종 스모크는 테스트 모듈의 fixture/event 생성 helper를 불러왔지만, 합성 출처·교안과 demand 문구를 임의의 **tavren/orbel** 개념으로 바꾼 별도 시나리오를 실행했다. 사용자 예시인 matrix/embedding/stack을 통과 조건으로 사용하지 않았다.

## 검증한 코드

- 최초 실패 재현 SHA-256: `9c0516efa32966968fa7ada541196c9b9d2c7074110d8dd8745767401b11bc6b`
- 중간 재현·재검토 SHA-256: `b580e3328e1d08948f0cbb515e1dad9d7cb393c0fa7b07ac128dc74f4f00a514`
- 11개 generic smoke 대상 SHA-256: `2e4856ae4cfe300a21faa500a5485682d720bba3719f63225e2844e8ed476ad7`
- **최종 freeze 및 delta 독립 재검증 SHA-256: `2273d1e9a47aff0dc038f0379837c908cb84a559d3e31e3a026f5a7c189d0914`**

11개 generic smoke는 위 `2e4856ae…`에서 실행했다. 이후 source supersession 영향 전파와 next_action 우선순위 변경이 추가되어, 최종 `2273d1e9…`에서는 아래 delta 3개를 별도로 직접 실행했다. 최종 delta 실행 시작·종료 SHA와 문서 보완 직전 코드 SHA가 일치했다. 11개 전부를 최종 freeze에서 다시 실행했다고 주장하지 않는다. 이후 코드가 바뀌면 이 결과가 변경된 코드까지 자동 적용되는 것은 아니다.

실행 방식은 `python -B` 인라인 Python, 실제 `/tmp` 합성 파일과 `TemporaryDirectory`, `step`/`inspect`/`replay` 호출이었다. 읽기 receipt를 검사할 때도 실제 파일 내용을 사용했다. 소진 후 raw append 공격은 기존 seed와 이벤트 prefix를 수정하지 않고 새 이벤트와 올바른 hash chain만 덧붙여 검사했다. 최종 스모크 출력은 `TOTAL 11 PASS 11 FAIL 0`이었다. 초기 스모크 harness의 Python 문법 오타는 어떤 사례도 실행하기 전에 실패했으며, 수정 후 실행한 아래 11개 결과만 통과 수에 포함한다.

## 직접 수행한 generic smoke — 11/11 통과

| # | 실행한 사례 | 최종 관측 결과 |
|---|---|---|
| 1 | overall `covered`인 비교에서 assessment 차원만 `gap`, 이후 실제 현재 교안으로 다시 `met` 비교 | gap 동안 `needs_work`; 재비교 후 `recorded_ready` |
| 2 | custom `mentions` 차원만 비교해 기본 학습·독립평가·선수 차원 대체 시도 | custom-only 비교가 `ValueError`; 기본 차원을 포함해 assessment gap을 기록하면 준비 상태 차단 |
| 3 | 알려진 미조사 질문을 기록한 뒤 빈 trace로 삭제 시도; 질문을 새 frontier로 확장 | 빈 trace 후에도 질문과 blocker 보존; 새 frontier를 추가하는 것만으로 준비되지 않음; 해당 frontier의 discovery/read/trace/compare 후 준비 상태 회복 |
| 4 | 실제 출처 bytes 변경; 새 source 버전 읽기·retrace·source 및 demand supersede·현재 비교 | 변경 직후 차단; 명시적 교체와 차원별 보존 검토 후 준비 상태 회복; 과거 stale read ID는 이력에 남음 |
| 5 | 실제 교안 bytes 변경 후 이전 비교 재사용 및 현재 bytes 재비교 | 변경 직후 차단; 현재 교안 receipt를 얻은 재비교 후 회복 |
| 6 | 같은 출처의 ID·attribution만 변경; 같은 bytes·범위를 새 read ID로 읽고 동일 demand를 새 ID로 trace; alias ID를 다른 내용으로 재사용 | 중복은 무진전으로 누적, demand 수는 1 유지; alias ID 재사용 거부; alias로 비교 참조 가능 |
| 7 | `pause → resume → 같은 내용의 새 pause`; paused 상태에서 현재 비교와 같은 새 ID compare 요청 | 두 번째 pause도 `paused`; paused compare 거부 |
| 8 | 마지막 예산 이벤트를 pause로 사용; 무진전 소진 뒤 JSON 재시작·resume 및 올바른 hash의 raw append | 소진은 `stopped`, 새 baseline 필요 안내; JSON roundtrip 후 카운터 유지; resume과 소진 뒤 raw append replay 모두 거부 |
| 9 | read 요청에 위조 receipt 주입; 이후 excerpt를 위조하고 이벤트 chain을 재계산 | `step`은 실제 source receipt로 대체; 재계산된 hash가 있어도 실제 bytes와 다른 excerpt는 준비 상태 차단 |
| 10 | 동일한 실제 later-placement receipt로 `scoped_foundation`과 `course` 평가 | foundation의 기록된 배치는 준비 가능; course는 `deferred_is_not_course_readiness`로 차단 |
| 11 | 기존 assessment gap이 있는 demand를 새 demand로 supersede; 매핑 생략 및 unresolved 매핑; 이후 `review_supersession` | 모든 기존 차원의 명시적 매핑 없이는 거부; unresolved는 차단; preserved 재검토 후 회복하며 이전 gap 비교와 두 번의 retirement review 이력 보존 |

## 최종 freeze delta 독립 재검증 — 3/3 통과

최종 코드 `2273d1e9a47aff0dc038f0379837c908cb84a559d3e31e3a026f5a7c189d0914`에서 `/tmp`의 tavren/orbel 출처·교안으로 다음 3개를 직접 실행했다. 실행 출력의 시작 `EXACT_CODE_SHA256`과 종료 `SHA_AFTER`가 같은 SHA였으며 `DELTA_TOTAL 3 PASS 3 FAIL 0`이었다.

| # | delta 실행 | 실제 관측 |
|---|---|---|
| D1 | 과거 source 파일 bytes를 그대로 보존하고 새 immutable source 버전을 별도 파일로 읽은 뒤 `supersede_source` | 기존 active demand에 `source_superseded_retrace_required`; 과거 bytes가 여전히 일치해도 재추적 필요 |
| D2 | retired source의 실제 old read receipt를 이용해 새 demand trace 생성 시도 | `Trace must use current source versions, not retired reads`로 거부 |
| D3 | fresh successor demand의 trace, 모든 기존 차원 매핑, 실제 교안 비교 완료 | 준비 상태 회복 |

중간 안내 SHA `b2056161…`를 기대한 첫 delta 시도는 코드 SHA guard에서 본문 실행 전에 중단했다. 그 결과를 테스트 통과로 세지 않았다. 구현 담당은 최종 `2273d1e9…`의 추가 차이가 next_action 우선순위이며 기록/schema/readiness 조건 변경은 아니라고 통보했다. 이 문서가 직접 실행을 확인하는 최신 delta 범위는 위 3개다.

## 최초 재현 실패와 수정 후 확인

아래 실패는 실제 실행으로 관측하고 구현 담당에게 직접 전달했다. 그 후 `2e4856ae…`의 11개 generic smoke에서 해당 경로를 다시 실행했고, 최종 freeze의 source supersession 변경은 위 delta 3개로 별도 확인했다.

| 수정 전 관측 | 최초 관측 코드 | 11개 smoke 재검증 후 관측 |
|---|---|---|
| 새 출처 읽기·새 demand·supersede·비교를 끝내도 과거 `stale_source_read`와 이전 discovered source가 영구 blocker로 남음 | `9c0516e…` | 명시적 `supersede_source`와 demand 보존 검토 후 준비 상태 회복 |
| custom `dimensions=[mentions]`만 `met`이면 학습·평가·선수 요구가 있어도 `recorded_ready` | `9c0516e…` | custom 차원은 추가 차원이며 기본 필수 차원을 대체할 수 없음 |
| 미조사 질문을 기록한 후 다음 빈 trace에서 `uninvestigated=[]`로 지우면 준비 상태 회복 | `9c0516e…` | 알려진 질문은 보존되고 새 frontier의 실제 검토를 요구 |
| 동일 출처의 source ID만 변경하면 매번 `no_progress=0` | `9c0516e…` | canonical source identity로 중복 진전 차단; attribution 변경도 진전이 아님 |
| 전역 op/data 중복 억제가 두 번째 pause와 `met → gap → 이전과 같은 met` 재검토를 버림 | `9c0516e…` | 반복 상태 전환과 현재 효력에 대한 재비교 정상 작동 |
| demand alias ID를 새 내용으로 재사용하면 실제 demand와 alias map이 충돌해 새 demand가 영구 `comparison_required` | `b580e33…` | alias ID도 불변 namespace에 포함되어 재사용 거부 |
| 마지막 이벤트를 pause로 써 예산이 소진되어도 `paused / resume_with_reason`을 안내하고 실제 resume은 거부 | `b580e33…` | 소진 상태가 우선이며 `stopped / new_budget_requires_explicit_new_baseline` |
| 동일 source bytes·line span을 새 read ID로 읽고 같은 demand를 새 ID로 trace하면 demand 수가 1→4로 늘고 무진전은 계속 0 | `b580e33…` | literal read ID 대신 source identity와 실제 receipt 기반 중복 판정; 진전으로 인정하지 않음 |
| 무진전 소진 prefix 뒤에 새 demand trace와 compare를 valid hash로 append하면 최종 무진전이 0으로 되면서 `recorded_ready` | `b580e33…` | replay가 모든 prefix의 예산을 확인하여 소진 뒤 append를 거부 |
| 강한 기존 gap demand를 약한 같은-frontier demand로 매핑 없이 supersede하면 `recorded_ready` | `b580e33…` | 기존 모든 차원의 독립 reviewer 매핑·근거 필수; 이전·이후 행동과 prior comparison 보존; 의미 동치 자체는 reviewer 선언 |
| paused 중 같은 현재 비교를 새 ID로 요청하면 dedupe가 예외 없이 no-op 반환하여 새 회귀 계약과 불일치 | 수정 중간본 | 최종 SHA에서 paused 검사를 먼저 적용하여 거부 |

코드 검토 중 제기한 unresolved supersession의 후속 회복 경로 우려도 generic smoke 11번에서 검증했다. `review_supersession`으로 같은 old→successor 매핑을 다시 검토할 수 있으며, 최초 unresolved 이력을 삭제하지 않는다.

## 범위와 한계

- 이 프로그램은 브라우징·검색·의미 추론을 직접 수행하는 semantic agent가 아니다. 새 외부 요구를 찾아 읽고 추출하는 사람/모델의 작업을 유한·재생 가능한 이벤트와 후속 queue로 기록한다.
- read receipt는 이 프로그램이 연 **로컬 파일 bytes와 line 범위**를 확인한다. 읽기 이해, 실제 원격 URL과 로컬 파일의 일치, 출처의 진실성·공식성·최신성, reviewer 신원·독립성은 인증하지 않는다.
- 임의 합성 개념의 성공은 사용자 예시 문자열 하드코딩에 의존하지 않는 기록 경로를 확인한다. 실제 외부 지식에서 누락 역량을 자동으로 발견한다거나 전체 외부 universe를 빠짐없이 조사했다는 증거는 아니다.
- scope 적절성, `covered` 판단, 차원별 의미 동치, supersession의 `preserved` 근거는 사람/모델의 내용 판단이다. 차원 매핑과 이력이 있다고 실제 보존이 증명되는 것은 아니며, 거짓된 의미 판단은 별도 내용 검토가 필요하다.
- frozen seed와 hash chain은 연결된 review에서 선언 변경을 드러내지만, 인증된 identity나 외부 append-only 저장소를 제공하지 않는다. 호출자가 seed와 전체 history를 재작성하고 새 baseline·새 aggregate review로 재결속하는 행위 자체를 방지하지 않는다.
- 이벤트의 경과 시간은 기록된 minutes다. 실제 wall-clock 소요 시간이나 인간 작업 시간을 독립 측정하지 않았다.
- `scoped_foundation`의 deferred 배치는 현재 단계의 기록된 준비 상태다. 나중에 실제 수업을 했다는 증거, 전체 course 준비, 대회 충분성 또는 학습자 성취를 뜻하지 않는다.
- 이번 독립 작업은 사용자 교안·데이터 원본 수정, 커밋, 푸시, 배포를 수행하지 않았다. 모든 합성 변경은 임시 파일에서 이루어졌다.

## 전체 회귀 상태

**전체 regression 수치와 별도 실제-source heldout 결과는 부모/root의 최종 확인 대기다.** 이 문서는 직접 수행한 generic smoke **11/11**과 최종 freeze delta **3/3**을 구분해 기록한다. 다른 검사의 개수나 부모 task의 전체 통과 수를 이 문서에서 확정하지 않는다.
