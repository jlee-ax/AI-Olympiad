# 1주 통합 교안의 별도 discovery 재개 기록

최종 notebook `lessons/week01/week01_integrated.ipynb`의 SHA-256은 `15ab0101edbca3c0c669e551cb723b401d168d9730523fa1ac1263a0d7538120`이다. 34셀 전체 source를 직접 읽고 새 단독 교안으로 비교했다. 이전 pipeline 19개 요구 payload와 5개 미조사 질문을 그대로 가져왔으며, bridge에만 있던 3개 질문도 원문 그대로 추가 보존했다. D01/D05/D07은 양쪽 payload가 같으므로 중복 요구로 늘리지 않았다. 원래 질문 ID는 이전 session에 남고, 새 frontier에 따른 ID 대응은 `runs/integrated-candidate-01/bridge-question-carryover.json`에 있다.

현재 `needs_work`, `ready_for_review=false`, 요구 19개·질문 8개·미해결 큐 17개다. `N01`, `P01`만 **자료 설계 범위에서** covered다. 57개 이벤트, 6회 source round이며 `next_action=expand_frontier`다. `elapsed_minutes=0`은 recorder가 별도 소요 시간을 보고하지 않았다는 뜻이지 실제 작업 시간이 0분이라는 측정이 아니다. 이 기록은 학생 성취·전체 10주 준비·기준 합의나 최종 승인으로 해석하지 않는다.

실제 원바이트·전 셀 source 투영·config·events·최종 session/report/manifest는 `runs/integrated-candidate-01/`에 있다. 이름의 candidate는 작성 당시 이름을 보존한 것이다. 이후 독립 검토도 같은 SHA를 최종 입력으로 확인했으며, 그 관계를 `final-review-status.json`에 별도로 기록했다. session/events/판정을 사후 덮어쓰지 않았다.

## 국소 진전과 잔여 범위

| 요구 | 실제 새 교안에서 확인한 것 | 남은 범위 |
|---|---|---|
| N01 | 새 기기 명세의 손계산·이유·자기 코드·도움 기록, 빈 답안 | 실제 학생의 독립 수행·도움·학습 효과는 미관찰 |
| P01 | 고정식과 실제 fit을 구별하고 훈련 전용 대체값·중심·훈련 변경에 따른 예측 변화를 실행. 새 열·라벨·ID 계약에서 학습 분류기를 선택하는 독립 과제 | 전체 Antique·숨은 평가·현실 성능 달성을 뜻하지 않음 |
| P02 | 실제 파일 result.csv 저장·재독, ID/허용값/순서. 새 과제는 입력과 다른 요구 순서 사용 | 두 무헤더 CSV의 공식 ZIP 계약은 설명과 선택적 옛 pipeline 링크만 있음. `submission_contract=gap` |
| D01/D03 | 축·reshape/전치·broadcast와 예측 시점/목표 제외를 더 명확히 연결 | Radar 입력/목표 축, 독립 의미 오류 코드 진단 등 원래 요구 전체는 미완 |
| D06 | 모든 관측 평균24와 훈련 평균20을 구별, train-only imputer fit과 validation transform | 원래 z 표준화·[0,2]/[100] 중심화·validation 변화 stress·누수/과대적합 독립 수정 전체는 미완 |
| N03 | unknown `?`와 정상/점검을 구별하고 알려진 훈련 행만 사용 | PU 관측 가정과 전체 반지도 학습은 미확인 |
| D02/D04/D05/D07–D10/D12/H01/H02/N02 | 현 교안과 후속 연결을 실제 확인 | kNN·label-index·정규화 검색·lookup/mask/loss/gradient·alias·가중평가·개발/추론 capability·Pixel 계약 등 원래 요구는 계속 큐에 남음 |
| D11 | 국내 2027 안내와 아직 IOAI2026 표기의 실라버스, 과거 국제 문제를 구분 | 국제2027 변경의 국내 적용성과 전문 차이는 미확정 |

P02가 이전 pipeline에서는 covered이고 통합본에서는 gap인 이유는 **비교하는 실제 파일 범위가 다르기 때문**이다. 기존 f64a… pipeline의 실제 두 CSV/ZIP 예와 판정은 그대로 남는다. 새 projection에 그 구현을 합친 것처럼 계산하지 않았다. /root/discovery_resume/state_structure_audit도 15ab… 전 셀과 요구를 별도로 읽어 이 구분을 점검했다. 단어 검색은 보조였고 전체 요구의 의미 판정은 사람이 수행했다.

통합본 cell33의 원래 본문 필수 연습·bridge A/B 안내는 실제 참조 파일 SHA와 준비/입력 셀 위치로 별도 결합했다(`context-binding.json`). 평균·분산 유도/ddof, Python 진단/함수, dirty CSV·집계/병합, 새 배열·그래프·내적·bridge 과제는 아직 학습자가 풀어야 한다. 선택적 detailed pipeline과 lookup을 필수 과제 완료로 세지 않는다. 새 통합본의 코드 실행 한 번으로 이 외부 과제나 주차를 완료 처리하지 않는다.

`source-demand-evidence-next.json`은 19개 각각의 **source URI/local receipt → 원래 payload/trace → 실제 셀 span/차원 판정 → queue → 수동 다음 조치**를 연결한다. 원래 source_locations 문자열의 의미 적합성이나 다음 교육 조치는 코드가 도출한 것이 아니다.

## 출처와 코드 검사의 경계

기존 source trace/read를 payload 변경 없이 새 session에서 실제 로컬 재독했다. 이전 독립 추출자의 원문 읽기 기록을 재사용한 것이며 새 자동 검색으로 표시하지 않았다. 추가로 이번 검토자가 [KOAI 2027 안내](https://kitpa.org/koai/2027), [국내 실라버스](https://kitpa.org/koai/syllabus), [Antique 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb)을 web 도구로 다시 열어 해당 범위를 직접 확인했다. 별도 `official-source-corroboration.md`는 읽은 범위·한계를 기록한다. 이는 교안을 읽은 뒤의 수동 재확인이므로 새 독립 source 추출이라고 주장하지 않는다.

| 단계 | 실제 코드가 검사하는 것 | 수동 판단·미보장 |
|---|---|---|
| 초기화/replay | seed digest·hash chain·불변 ID·유한 budget | frontier가 외부 세계를 충분히 표집했는지 |
| read | 로컬 정규 파일의 줄·전체/발췌 SHA receipt | 원출처 진위·upstream 최신성·변환 의미 |
| trace | 같은 frontier의 선행 read ID, 필수 필드/차원, 질문 보존 | source_locations의 의미·요구 추출의 타당성 |
| compare | 모든 요구 차원, 실제 projection receipt, 추출자와 다른 reviewer 문자열 | 진짜 독립성·교육적 충족·학생 성취 |
| inspect/next | 현재 artifact/receipt freshness, 미해결 질문/큐, 일반 다음 상태 | 어느 후속 내용이 충분한 수업인지 |
| 이 폴더 검증기 | payload19·질문8 보존, 셀 투영, 57개 이벤트 재실행, CLI/API 일치, 별도 context SHA | 의미 판정의 자동 증명·기준 합의·종합 승인 |
| joined preflight | 같은 artifact/discovery manifest 및 covered-demand graph path 등 | 이 기록만으로 새 aggregate 심사가 만들어지지 않음 |

구조의 근거는 `tools/discovery_loop.py`의 read/trace/compare/replay/inspect, `tools/review_preflight.py`의 동일 artifact·discovery gate, `tools/quality.py:825`의 agreement fingerprint다. core inspect는 추가 context manifest를 자동 추적하지 않는다. 이 폴더의 검증기가 계획/계약/템플릿·연결 파일을 따로 검사한다.

## 계획 변경과 이전 pause의 보존

구 계획 SHA `a3a48fe01212b28368c34c46de2dee0c5d6a78ea7c5d37125b335891ae1f8254`는 원래 계약 pin 및 HEAD 원바이트와 일치했다. 부모가 새 진입 링크와 옛 시간 추정의 미실측 표시를 바꾸면서 구 pin과 충돌한 실패는 `../plan-revision/before-rebind.json`에 남는다. 부모의 명시적 `curriculum-v2-week01-integrated`는 구 계획/계약을 별도 snapshot으로 보존하고 현재 계획 SHA `cbe69f862ae76a87cd69233889c7fd6698e38ac34eb4d385f2b825722daeabb5`에 새 pin을 만들었다. 주/60개 주제·시수·기준 필드는 보존됐다.

부모의 실제 기능 결과는 **구 snapshot pass → 새 계획+구 pin fail → 새 revision pass → 후속 bytes 변조 fail**이다. 현재 새 baseline pass는 일정/해시 구조 검사다. 구 미설정 quality 템플릿도 HEAD 바이트 snapshot으로 보존되었고 새 템플릿은 revision/artifact revision/SHA만 바뀌었다. policy/budget/reviews는 불변이고 agreed=false다. 구 템플릿은 현재 계획에서 binding 실패, 새 템플릿은 `priority_policy_requires_agreement` pause다. 이 전이는 새 교안의 내용 통과가 아니다.

직접 재조회한 기존 workflow는 validate=valid/구조만, recall 기본6개·`week1 pipeline` 쿼리0개, decide=`pause/criteria_agreement_required`다. recall은 active record.text의 AND 부분문자열 검색으로 의미/파일/웹 검색이 아니다. 기존 quality는 원래 ee827… 본문에 결합된 `uncertain/ready=false/discovery_missing`, plan은 `priority_policy_requires_agreement`다. K12에 원래 stale 리뷰들이 남는다. agreement fingerprint는 계획 SHA와 contract revision을 포함하지 않으므로 같은 fingerprint를 새 내용 동의로 읽지 않는다. PLAN이 모든 개별 review의 의존 폐쇄에 있지 않아 모든 옛 review가 자동 stale되는 구조도 아니다. 현재 개별 원본 notebook SHA가 유지된 pipeline/bridge 리뷰와 새 통합본의 판단은 별도로 남겼다.

10주 계약의 60주제는 여전히 scheduled_only다. 실제 lessons에는 1주 4개·2주 2개 notebook이 있고 3–10주 notebook은 없다. `context-binding.json`에 조회 시점의 경로 목록과 선수 연결을 기록했다. 2주 split/지표, 3–5주 회귀·손실·거리, 6주 tensor/학습, 7–9주 표현·검색, 10주 새 계약으로 이어지는 설명은 후속 실제 교육/전이의 증거가 아니다. 이전 2주의 고정 점수 실행도 학습 모델로 계산하지 않았다.

## 결함 이력·검증·재현

09da… 후보의 함수가 유한한 `[1e308,1e308]`에서 기대 평균1e308 대신 inf를 내는 것을 실제 함수 AST만 분리 실행해 찾았다. 저자 수정이 먼저 시작되어 그 후보 전체 raw snapshot은 이 폴더에서 확보하지 못했다. `overflow-contract-before-fix.json`은 당시 SHA·읽은 함수·입력·기대/실제·원바이트 확보 한계를 명시한다. 수정은 임의 실수의 overflow 알고리즘 해결이 아니라 정상 입력을 길이≤10,000·관측값±1,000,000·bool 제외로 좁힌 계약 정정이다. `overflow-contract-after-fix.json`은 중간31b…에서 범위 내 경계6개를 확인한 기록이며, 최종15ab…의 같은 계약/함수는 독립 검토가 재실행했다. 범위 밖1e308은 여전히 보장하지 않는다.

동일 최종 SHA의 별도 독립 검토는 새 subprocess kernel에서 34셀/16코드·제공 후속 경로9개·오류 변이13개를 확인했고 차단 결함 없음으로 기록했다(`../independent/final-summary.json`). 물리 CSV를 메모리로 바꾼 변이는 교안/수치 oracle 실행을 통과했고 별도의 단계 구분 I/O oracle만 거부했다. 이를 교안 자체 검사 성공으로 합치지 않았다. 학생 답안·일반 Jupyter/Colab·브라우저 전체 HTML·보호된 최종 테스트·실제 학생 소요 시간은 확인되지 않았다.

`checks/integrity-02.json`은 보호 이력45개·context21개·git index 불변, 원바이트/투영, 57개 입력 이벤트를 처음부터 다시 실행한 완전 상태 일치, report/next/manifest의 실제 CLI와 API 일치를 확인한다. 첫 integrity-01은 caller event와 자동 receipt/hash가 추가된 event를 직접 비교한 검증기 오류를 그대로 남겼고, 수정 근거는 `checks/verifier-correction.json`에 있다. session/events/report는 수정하지 않았다. 초기 recorder의 counterevidence 타입 오류로 종료한 미완성 시도는 `build-attempts/`에 per-file byte/SHA 검증 가능한 압축으로 보존했다. 중간 session 복제·runtime·cache는 남기지 않았다.

repo root에서 다음은 읽기만 수행한다.

```sh
python3 -B reviews/week01-integration-20261111/discovery/verify_integrated_discovery.py
python3 -B tools/discovery_loop.py report reviews/week01-integration-20261111/discovery/runs/integrated-candidate-01/session.json --root .
python3 -B tools/discovery_loop.py next reviews/week01-integration-20261111/discovery/runs/integrated-candidate-01/session.json --root .
python3 -B tools/workflow.py decide reviews/week01/independent-transfer-20261111/workflow.json --quality reviews/week01/independent-transfer-20261111/quality.json --root .
```

다음 실제 notebook 바이트가 바뀌면 이 session은 원바이트 불일치로 stale이 되어야 한다. 이전 파일을 유지하고 새 run·새 exact snapshot·새 비교를 만들어야 한다. 이번 검토자는 지정 discovery 폴더에만 썼고 다른 파일·git index·commit·push·원격을 변경하지 않았다.
