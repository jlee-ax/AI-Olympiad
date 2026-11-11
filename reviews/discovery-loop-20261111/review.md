# 외부 요구 발견과 교안 개선 루프 — 2026-11-11

## 확인한 원인

기존 지침에는 원문 읽기와 반복 검토가 있었으며 실제 교안에도 유의미한 검토·수정이 있었다. 그 사실과 별개로, 실행기는 **이미 등록된 주장·목표의 바깥에서 새로운 요구를 받아들이는 단계가 없었다.**

1. `quality.py` K11은 현재 claims에 대해 마지막 research_cycle을 확인하고, plan은 현재 unit/claim ID의 발견만 작업 후보로 만든다. 원문을 읽었어도 등록되지 않은 개념은 이 큐에 들어오지 않는다.
2. contest-depth는 target.goals와 comparisons, graph/preflight는 그 비교의 경로를 확인한다. 이를 만족하는 것과 외부 문제의 요구를 충분히 찾아냈다는 것은 다른 판단이다.
3. 실제 이전 1주차 깊이 기록은 축·함수·필기형식·분산의 네 비교였다. 전체 셀 검토도 기존 셀별 설명과 과제의 빈틈을 중심으로 수행됐다. 넓은 syllabus ID의 배치나 코드 실행 성공으로 행렬 수축, 검색 ID 복원, label decode 등의 구체 역량까지 확인할 수는 없다.
4. 상태·자료 바이트 정합성의 기존 개선은 재사용 오류를 막지만 무엇을 더 읽고 어떤 새로운 요구를 등록할지는 실행하지 않았다. 과거 보고서도 이 한계를 명시했다. 내부적으로 모델이 스킬을 읽지 않았다는 주장은 이 증거로 입증할 수 없다.

[기준 코드 재현](legacy-results.json)은 원격에 존재하는 `c3579c47`의 inspector를 고정해 실행했다. 좁은 합성 정상 기록은 recorded_met이고, 등록되지 않은 외부 요구 목록을 추가해도 보고서는 동일했다. 같은 요구를 target.goal로 직접 등록하자 missing comparison이 드러났다. 이는 기존 선택 범위 검사가 거짓이라는 뜻이 아니라, 사용자가 요구한 **범위 발견과 확장 기능이 없었다는 재현**이다. 실제 네 비교의 불확실성도 그대로 보존했다.

## 이번 구현

[discovery_loop.py](../../tools/discovery_loop.py)는 `init → discover → read → trace → compare → 다음 작업`을 저장·재생하는 실행 가능한 상태 전이를 제공한다. 새 출처와 문제에서 요구·선수·원리·실습·평가를 등록하고, 새 질문을 frontier로 계속 확장할 수 있다. 발견된 출처는 읽기와 요구 추적 없이 완료되지 않는다. 실제 로컬 파일의 바이트·행 범위를 열어 영수증을 생성하고, 변경된 자료/교안/후속 배치의 영향과 재검토를 표시한다.

미조사 질문은 후속 빈 기록으로 없어지지 않는다. 새로운 ID를 붙인 동일 출처·읽기·요구는 실질적 진전으로 세지 않으며, 이전 요구를 바꿀 때는 기존 차원별 이관 판단과 gap 이력을 보존한다. 학습·평가·선수 차원은 사용자 정의 차원으로 제거할 수 없다. 외부 범위의 관련성이 불명확하면 연구 항목으로, 적절한 기초 이후에 다룰 내용은 배치 근거와 함께 남길 수 있다. 후속 배치는 전체 과정의 달성으로 간주하지 않는다.

실제 quality readiness, quality plan, 직접 workflow decide와 joined preflight에 discovery gate를 연결했다. 실제 교안 완료 경로에서 탐색 기록을 생략해 과거의 좁은 통과를 재사용할 수 없다. 명시적인 legacy 검사는 과거 기록의 검사이며 readiness가 아니다. 관련 스킬에는 이 실행 진입점만 최소 연결했다. 기존 K01–K16 기준을 유리하게 고치거나 실제 동의·학생 결과를 생성하지 않았다.

독립 코드 검토에서 새 구현의 초기 결함도 재현·수정했다. 동일 출처를 새 ID/읽기 ID로 포장한 진전, 필수 평가 차원 생략, 미조사 질문 소거, 반복 pause/재판정 누락, 예산 소진 후 replay 부활, 출처 변경 후 복구와 요구 약화 이관 문제가 포함된다. [별도 검토 기록](code-independent-review.md)은 최초 실패와 수정 후 확인, 검증 코드 SHA를 구분한다.

## 실제 외부 조사와 반복 실행

[구조화된 조사](source-research.json)와 [출처 요약](source-research.md)은 공식 범위, 실제 IOAI 세 문제군, 기술 계약 및 대학 강의 자료 **12개 primary 문서**에서 14개 요구 후보를 도출했다. 이는 제한된 조사 표본이다. 문서 수가 범위의 완전성이나 학습 효과를 보장하지 않는다.

새 요구에는 KNN 명세의 거리→이웃→투표, label encode/decode, 검색 행렬 위치→실제 ID, train-only preprocessing, embedding lookup 축, attention mask 의미, softmax·수치 안정화 등이 있다. 행렬곱·embedding·stack을 미리 필수로 고정하지 않았다. 실제 Restroom baseline은 cat을 사용하므로 stack 자체가 대회 필수라는 결론을 내리지 않았다.

또한 [국내 연결 실라버스](https://kitpa.org/koai/syllabus)는 IOAI 2026 표기이고, [국제 IOAI 2027 원문](https://ioai-official.org/wp-content/uploads/2026/11/IOAI_Syllabus.pdf)은 기술 환경 및 강화학습 항목을 포함한다. 국제 최신 내용을 국내 KOAI 2027 확정 범위나 초보 1주차 필수로 자동 승격하지 않았다. 적용성은 미해결 조사로 남겼다.

[실제 루프 실행](actual-loop-results.json)은 보존된 91셀 교안의 source projection과 원본 SHA를 연결했다. 12개 요구의 비교 이후 구현에 직접 전달하지 않은 H01/H02를 새 frontier로 추가하고, 다음 탐색 질문으로 확장했다. 총 **36개 이벤트를 매번 JSON 저장·재시작**했으며 14개 요구 중 13개가 현재 과정 큐에 남는다. 남은 공식 문제군과 후속 실제 교안의 조사 의무도 `next-wave`에 남아 있다. D03의 좁은 입력/정답·시점 설명 설계가 기록됐다고 다른 과제군 전이나 과정 충분성을 통과시키지 않았다.

원문 검색·의미 추출은 실제 조사 에이전트가 브라우저 도구로 수행했다. reducer가 읽는 `reading-note-*.md`는 그 직접 읽기의 **기록·요약**이며, CLI가 원본 웹 문서를 새로 읽거나 공식성을 인증했다는 뜻이 아니다. 원격 main/stable 자료의 향후 변화도 자동 감시하지 않으며 새 버전이 수집되면 로컬 비교가 다시 열린다.

## 보정과 반증 결과

| 실제 확인 | 결과와 범위 |
|---|---|
| [전체 회귀](regression.log) | 255개 통과, 종료 0. 새 discovery 기능 27개 포함 |
| [독립 기능 공격](code-independent-review.md) | 일반 임의 개념으로 11개 공격과 최종 변경분 3개 확인. 사용자 예시 키워드에 의존하지 않음 |
| [새 요구 두 개](heldout-results.json) | Radar weighted score에서 일반 정확도 순위와 가중 점수 순위가 역전되는 새 입력을 계산. 별도 Concepts 문제의 추론 단계 API 부재도 네트워크 호출 없이 정상/오류 제어로 확인 |
| [교량 후보 실행](candidate-check.json) | Terra가 만든 별도 후보에서 직사각형 행렬곱, 원소별 곱 오용, 수축 축 불일치, stack/concat, 순서·ID 대응과 새 입력 과제 등 8개 검사 통과 |
| [개선 전후와 새 누락](bridge-cycle-results.json) | 원래 교안은 해당 좁은 교량 요구의 gap, 후보는 scoped recorded_ready, 독립 과제 영역을 제거한 오류 사본은 assessment gap. 전체 과정 D05는 계속 미해결 |
| [CLI 실제 상태](cli-results.json) | 새 누락 큐 재조회·manifest 재생 성공. 실제 과거 workflow의 기준 미합의는 pause로 유지 |

H01은 개발 요구와 Radar 자료를 공유하므로 요구 단위 holdout이며 새 출처군 holdout은 아니다. H02는 다른 생성 문제군에서 왔다. 루프는 실제 검토자가 기록한 gap을 보존한다. 프로그램이 원문 의미를 자동 이해해 그 gap을 스스로 판정했다고 주장하지 않는다.

[검토용 교량 후보](candidate-bridge.md)는 실제 lesson 브랜치의 교안 교체본이 아니다. 원리·수식·shape·코드·새 문제·피드백으로 이어지는 작은 수정 경로를 시험한 산출물이다. 단원 편성·시간·후속 자료 전체를 승인하지 않았고, 이 하나의 보정으로 전체 교안이 충분해졌다고 보고하지 않는다. 교사용 해설을 숨기는 것은 전달 조건이며 이 Markdown이 이를 강제로 집행하지는 않는다.

## 보존과 한계

기존 lesson worktree의 미커밋 5개 파일과 실행 로그 1개는 [보존 해시](preserved-inputs.json)와 일치한다. 원본 노트북 SHA `733c0093b44f30d31354567331c2c39ee325ed074e7a6368bb1f2e96f0c174c0`을 유지했다. 이번 변경은 개선 브랜치에만 반영하며 main이나 lesson 브랜치를 수정하지 않는다.

시스템 구현·조사에는 GPT-6.1 Sol Ultra를, 검토용 교육 후보에는 GPT-6.1 Terra Max를 지정했다. 별도 코드 검토도 다른 Sol 에이전트가 수행했다. 도구에는 Grace 모델/리뷰어 선택 항목이 없으므로 **Grace 검토는 수행했다고 주장하지 않는다**. 모델 설정은 위임 구성 근거이며 런타임 식별을 별도 인증한 것은 아니다.

검색과 의미 판단을 자동 실행하는 무인 에이전트·스케줄러, 전체 외부 지식의 완전성 증명, 서명된 변경 불가 이력, 실제 학생 독립 수행·학습 효과는 구현·검증 범위 밖이다. 작업을 계속하면 남은 조사/교안 요구를 큐에서 이어갈 수 있지만, 전체 교안의 재구성 및 실제 후속 주차 교안의 생산·검토는 아직 끝나지 않았다.

재현 명령:

```sh
python3 -B -m unittest discover -s tests
python3 -B reviews/discovery-loop-20261111/reproduce_legacy.py
python3 -B reviews/discovery-loop-20261111/run_real_discovery.py
python3 -B reviews/discovery-loop-20261111/check_heldout.py
python3 -B reviews/discovery-loop-20261111/run_bridge_cycle.py
# 기존 환경에 NumPy가 필요하다.
python3 -B reviews/discovery-loop-20261111/candidate-check.py
```
