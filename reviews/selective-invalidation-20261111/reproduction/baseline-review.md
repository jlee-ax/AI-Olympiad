# 실제 기록 복제본으로 확인한 기존 동작

2026-11-11 작업트리 `ai-olympiad-review-invalidation`에서 기존 `tools/quality.py`를 먼저 `code-baseline/quality.py`에 보존했다(SHA `bb7ee10c793aa9916429a1dd77900fc59238738eb49632ba7ec44935e0770b30`). 실제 `reviews/week01/independent-transfer-20261111/quality.json`과 필요한 입력14파일을 각 복제 root로 복사해 대조군2개·변경14개를 실행했다. review context를 새로 써서 통과시키지 않았고 policy/과거 status를 바꾸지 않았다. 정확한 기대/실제와 입력/원본 SHA는 `baseline-01/results.json` 및 각 case의 `record.json`, `measurement.json`에 있다.

원래 record의 현재 전체 상태는 **uncertain, ready=false, discovery_missing**이고 policy.agreed=false다. stored review 33 passed/1 failed는 현재 전체 승인 수가 아니다. K12가 선택한 active20개 중17개는 이미 context stale이다. K06의 claim:table/array/visualise 세 개는 현재 fingerprint·근거가 맞아 `_review=passed`다. 따라서 table을 실제 유효 passed→uncertain 대조군으로 골랐다. 이 실험의 K10 `_review` 호출은 추가 fingerprint/helper probe일 뿐 실제 K10 기준의 research-cycle gate와 같지 않다. 기준의 실제 상태는 별도로 저장한 `criterion_statuses`에서 읽어야 한다.

| 복제본의 변경 | 실제 local fingerprint/상태 | 별도 전체 게이트 |
|---|---|---|
| week1 계획 행 | 객체24개 비교쌍 FP 전부 불변; PLAN은 평가 객체8개 closure에서 빠짐 | 원래 pin과 달라 K01/K03 fail |
| week10 계획 행 | 동일하게 FP 불변 | K01/K03 fail |
| week1 계획+복제 contract의 명시적 새 pin | 개별 FP 여전히 불변 | 구조 baseline pass. 합의나 내용 승인 생성 없음 |
| table claim 셀08e374f4 | table claim 및 unit의 관련6개 FP 변화. K06 table passed→uncertain; array/visualise local pass 유지 | 원 artifact·실행 SHA 불일치로 K01/K08 fail |
| 미등록 셀 | 선언 local FP 불변 | K01/K08 fail. 누락된 의미 의존을 자동 찾지 않음 |
| metadata/execution_count만 | local FP 불변 | raw artifact SHA가 달라 K01/K08 fail |
| 연결된 코드셀81129230의 표시 output | 해당 셀을 참조한 Python과 array unit의 FP만 변화 | raw artifact 게이트는 별도 fail |
| 사용 중 source-read finding | table claim/unit FP 변화 | 전체 상태는 원래 uncertain을 유지 |
| 미연결 source-read finding | local FP 불변 | 전체 승인으로 승격되지 않음 |
| review가 인용한 근거 파일 bytes | FP 불변이나 근거 SHA 검사가 세 K06 local pass를 uncertain으로 철회 | K12의 context-only stale ID 목록은 새 근거 사유를 표시하지 않음 |
| 무관한 새 근거 파일 | local FP·K06 pass 유지 | 선언되지 않은 영향의 의미까지 판단한 것이 아님 |
| 4unit이 공유하는 source-brief 파일 | 연결된4unit FP 변화, claim FP 불변 | 선언된 공유 의존의 영향이며 전면 무효화 아님 |
| PLAN 전체파일 path+W1-table edge를 명시한 대조군에서 week1 변경 | W1-table 판정4개 FP 변화 | raw 계획 binding 게이트는 별도 |
| 같은 대조군에서 무관 week10 변경 | W1-table 판정4개도 FP 변화 | 전체파일 path만 추가하면 선택성 부족 |

계획 관련 두 문제를 구분해야 한다. 실제 legacy PLAN은 `path`가 없고 closure에 연결되지 않아 영향을 관찰할 수 없다. 그러나 기존 `object_fingerprint`는 이미 셀/HTML 행, chain/explanation, upstream claim과 declared path의 실제 파일을 읽는다. 따라서 새 설계는 이 region 동작을 유지하면서 명시적인 계획 경로·영역·의존성과 누락 상태를 추가해야 한다. PLAN 미연결을 “무관함 확인”으로 돌려서는 안 된다.

`_review`는 근거 파일 SHA 불일치도 uncertain으로 바꾸지만 legacy K12는 context fingerprint만 요약한다. 새 표현은 실제 내용을 재검토해야 하는 경우와, 구 기록에 영향 범위 결합이 빠져 독립적으로 그 범위를 확인해야 하는 경우를 구분하는 편이 타당하다. old review의 stored status를 쓰거나 최신 stale 뒤에 과거 pass로 돌아가면 안 된다.

별도 읽기 감사자는 workflow와 preflight도 확인했다. `workflow.context_fingerprint`는 선언 manifest를 결합하며 실제 파일 freshness는 preflight가 검사한다. preflight의 전체 artifact·depth/graph/paths/semantic/source-catalog 결합은 local cell review보다 넓다. 현재 workflow는 criteria_agreement_required pause이며 reviews=[]다. 현재 preflight는 binding들이 맞아도 contest_depth_uncertain/discovery_missing/quality_not_ready/workflow_pause로 blocked다. local 선택적 재검토는 이런 전체 승인 게이트를 대체하지 않는다.

재현은 root에서 다음 명령을 사용한다. 결과 label은 기존 기록과 다른 새 이름이어야 한다. 모든 쓰기는 reproduction 경로 안의 실제 복제본에 한정된다.

```sh
python3 -B reviews/selective-invalidation-20261111/reproduction/reproduce_actual_record.py --label baseline-recheck-new-name
```

초기 실행 종료 시 원본 lessons/quality/workflow35개 파일과 git index SHA는 모두 동일했다. notebook의 변경된 코드를 실행하지 않았고, hash나 문자열이 의미 동치·학습 성취를 증명한다고 주장하지 않는다. 새 후보가 준비되면 해당 API를 동일 실제 복제본에서 추가 대조한다.
