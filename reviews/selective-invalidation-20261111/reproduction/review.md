# 선택적 재검토의 실제 기록 재현

최종 코드 입력은 quality.py `03f24f7e9b89979e30facf258f8c8f9f358b1aca2de876a1adae5e058f0fc96b`(v4), workflow.py `11dc7a916d00a3b67528b63f7d6b02a74e9b895972f7ce56ec540d245b54872b`, review_preflight.py `de09542da3c32f73f6f89a84709e63616fc8516f2ba6cbec08599443b5c878c5`다. 실제 기존 quality.json과 필요한 파일을 이 reproduction 경로 안에 복사해 동작을 비교했다. 기존 교안·lesson/user 원본·기존 기록·index·원격은 수정하지 않았다.

기능 결과와 실제 기존 승인 상태를 구분한다. 원 record에 stored passed=33/failed=1이 있지만, 현재 전체는 **uncertain/ready=false/discovery_missing**, policy.agreed=false다. baseline에서 최신 active20개 중17개는 context가 이미 stale였다. K06 table/array/visualise 세 claim만 현재 유효 passed여서 관련 셀의 실제 passed→uncertain 대조에 사용했다. 현재 workflow도 **pause/criteria_agreement_required**, quality.plan도 **pause/priority_policy_requires_agreement**, preflight는 **blocked**다. 새 해시·바인딩 캡처나 이번 하네스 테스트로 과거 합의·내용 승인·학생 성취를 생성하지 않았다.

## 기존 동작과 확인한 빈틈

`baseline-01/results.json`은 frozen baseline 코드 `bb7ee10c…`로 실제 복제 대조군2개와 변경14개를 실행한 결과다. 모든 사전 작성 기대 조건이 실제와 일치했다. 보다 자세한 구분은 `baseline-review.md`에 있다.

- 기존 object_fingerprint는 이미 실제 cell/HTML row, chain/explanation, upstream claim과 declared file path를 결합한다. 관련 table 셀08e374f4를 바꾸면 K06 table이 passed→uncertain이고 무관 array/visualise는 passed를 유지했다. 표시 output은 실제 공유하는 Python/array unit들에만 영향을 줬다. 미등록 셀·execution_count/metadata만 바꾸면 local FP는 유지되어도 전체 artifact/실행 SHA 게이트는 별도로 실패했다.
- 실제 PLAN은 path가 없고 평가 객체8개 closure 모두에 연결되지 않았다. week1 계획 변경은 K01/K03을 실패시키지만 개별 FP는 전혀 바꾸지 못했다. 복제 contract만 명시적으로 re-pin하면 구조 baseline은 pass여도 내용의 새 승인은 없다. PLAN에 전체파일 path+W1-table edge만 추가하면 무관 week10까지 W1-table을 무효화하므로 region 선택이 필요했다.
- 사용 source-read finding·공유 dependency 파일과 무관 source/file을 구분했다. review 근거 파일의 SHA가 바뀌면 `_evidence`가 local pass를 철회했지만 legacy K12의 context-only stale 목록은 해당 근거 사유를 표현하지 못했다.

## 후보 이력과 최종 대조

| 버전·기록 | 실제 대조와 결과 |
|---|---|
| v1 `9da63ab4…`, candidate-01 | 3대조군+16변경군 통과. 관련 week/scope/cell/source/evidence와 무관 week/CSS/script 등을 구분. 표 밖 전역 문단은 놓쳤음 |
| SHA guard, candidate-02 | 안내 v2 `4bce57…`와 실제 다음 코드 `613458…` 불일치를 실행 전에 감지. case 실행0, 미실행 기록 보존 |
| v3 `613458c1…`, finalcandidate-03 | 3대조군+19변경군 모두 기대 일치. 표 밖 전역 지시 및 보이는 글자가 같은 출처 href 변경도 감지. week10/scope60/CSS/script는 local current 유지 |
| v3→v4, finalsource-04 | v4의 실제 복제6군(control·사용 근거 bytes 변경·파일 누락·사용 read 변경·무관 read·무관 파일)에서 evaluate/plan/workflow/preflight 모두 통과. 동일 누락 입력에서 v3가 selective 진단을 잃던 실패도 별도 raw JSON 보존 |
| v4, final-cli-04 | 실제 원 record에서 K12/evaluate→plan→workflow→preflight 전파 등10체크 통과. 기존 pause/blocked와 원본 불변 유지 |

v1의 표 밖 문단 반례는 `candidate-findings/outside-plan-table/finding.json`에 남았다. 그 문단이 전역 평가 지시이며 원래 훈련 전용 규칙과 충돌한다는 판단은 검토자가 직접 읽어 내렸다. 해시가 의미를 추론한 것이 아니다. 초기 evidence-priority probe에서 K05가 변경 근거를 인용하지 않는다는 표적 선정 오류도 finding-01/02에 바로잡아 보존했다. 최종 후보는 실제 근거 파손을 review_required로 표시하면서 missing binding/impact 작업을 별도 병기한다.

finalsource-04는 원 source_read의 실제 `reading_receipt` 경로를 **복제 dependency node에만 명시**했다. 원래 record의 path 누락을 자동 수정하거나 이 receipt를 원출처 인증으로 취급하지 않았다. 실제 기존 candidate `correct-return-trace`와 전체 stored reviews는 복제본에서도 그대로다. 누락 때에는 해당 node/path/locator의 sha256:null/error, K11 claim별 context_error, K13 unavailable_contexts, plan의 기존 candidate context_status=unavailable가 남았다. 무관 K06 세 claim은 current였다. 동일 입력의 v3 evaluate/plan은 exit2이고 selective_review가 없었으며, v4는 명시적인 재검토 목록을 유지했다.

변경 없는 현재 범위를 만들기 위한 **mechanical capture probe는 별도 파일**이다. 실제 과거 review의 context 필드를 반사실적 대조로 캡처했을 뿐 record.reviews에 추가하지 않았고 내용 승인으로 사용하지 않았다. 실제 legacy unit은 binding_required이고, 명시 scope를 추가한 복제 record의 옛 review는 impact_confirmation_required였다. 빠진 scope/edge는 binding_required, 검출된 bytes/근거 파손은 review_required다. 이 구분은 기계적 진단이며 독립적인 내용 검토나 영향 확인 자체를 실행하지 않는다.

## 보존과 복구

반복 입력은 per-path SHA/size를 유지한 공유 content-addressed archive로 보존했다. **1,093개 입력 경로를69개 고유 byte content**로 표현한다. `archives/*-inputs.manifest.json`이 원래 경로→content member를 연결하고 `content-inputs-v2.index.json`이 모든 content를 검증한다. 원래4개 archive의22,397,198bytes는 새2,815,311bytes로 줄었다. 이전 압축 표현의 SHA/manifest는 `archives/representation-history/`와 `archive-deduplication-results.json`에 있다. 압축 wire 표현만 바뀌었고 입력 원바이트는 모두 보존됐다.

큰 CLI/inspection JSON103개도 exact per-file SHA/size의 `archives/inspection-outputs-v1.tar.gz`로 보존했다(29,281,508→1,867,580bytes). `inspection-outputs-v1.manifest.json`은 원래 출력 경로를 명시한다. 기대/실제 summary, version별 실패, report, code는 읽을 수 있게 남겼다. 예를 들어 finalsource의 전체 evaluate/plan/workflow/preflight JSON은 이 출력 archive에, 같은 입력에서 발생한 v3 failure JSON은 case 폴더에 그대로 있다. 저장 CLI JSON과 별도로 각 명령의 argv/exit/stdout SHA도 summary에 남는다.

복구는 extractfile(...).read() 후 **각 경로에 write_bytes**를 수행한다. extractall이나 filesystem hardlink 복구는 사용하지 않는다. 실제 restore에서 같은 내용의 두 case 파일이 서로 다른 inode이고 하나를 수정해도 다른 파일과 archive가 바뀌지 않음을 확인했다(`restore-independence-results.json`). 그 추가 임시 복제본은 검사 후 정리했다. `all-archives-final-verification.json`은 입력6군과 출력1군의 모든 원바이트 크기/SHA 검증 결과다.

root에서 archive 무결성만 재조회하려면:

```sh
python3 -B reviews/selective-invalidation-20261111/reproduction/archive_inputs.py verify
```

입력 control을 새 경로에 복원하고 현재 v4로 새 이름의 기능 대조를 수행하려면:

```sh
python3 -B reviews/selective-invalidation-20261111/reproduction/archive_inputs.py restore --group baseline-01 --destination replay-control --prefix cases/00-control/
python3 -B reviews/selective-invalidation-20261111/reproduction/check_candidate.py --label replay-v4-matrix --expected-quality-sha 03f24f7e9b89979e30facf258f8c8f9f358b1aca2de876a1adae5e058f0fc96b --baseline-control replay-control/cases/00-control
python3 -B reviews/selective-invalidation-20261111/reproduction/check_source_failure.py --label replay-v4-source --baseline-control replay-control/cases/00-control
python3 -B reviews/selective-invalidation-20261111/reproduction/check_cli_propagation.py --label replay-v4-cli
```

대상 이름은 항상 미존재 경로여야 한다. 원래 stdout의 저장 당시 절대 case 경로는 이력이며, 새 실행은 스크립트가 새 경로를 만든다. 특정 원 보고서 bytes만 보고 싶다면 `archive_inputs.py restore --group inspection-outputs --destination view-reports --prefix finalsource-04/cases/02-used-source-file-missing/`를 사용할 수 있다.

## 한계

source truth·의존성의 의미 적합성·아직 선언하지 않은 필수 관계는 해시가 입증하지 않는다. 현재 형식의 누락을 자동 “무관”으로 승인하지 않고 별도 작업으로 남기는 것이 이번 보완의 범위다. graph/path와 aggregate workflow의 전체 manifest·artifact 게이트는 local 선택적 판정보다 넓고 그대로 유지된다. 그 전체 무효화 구조를 이번 테스트가 선택적 내용 승인으로 대체하지 않았다. 학생 수행·학습 시간·학습 효과는 관찰하지 않았다. 검토자는 tools의 하네스 코드를 편집하지 않았고 지정 reproduction 경로에만 썼다. 원 교안·기존 기록35개와 검사 시점 git index SHA의 불변을 확인했다.
