# Selective invalidation independent review

최종 core **03f24f7e…의 독립 기능 검토를 완료했다. 현재 재현된 차단 결함은 없다.** 실제 구 quality 기록은 여전히 failed/blocked이며, 이 결과가 새 의미 검토나 동의를 만들어 주지는 않는다.

## 고정한 입력과 범위

후보 열람 전 2026-11-11 10:54:40 UTC에 기준을 고정했다. `criteria-v1.md` SHA `4ae6bd20c6a5bceeac3992759321c5172e1fb905a2444da651c0ac0e393a913e`, `input-manifest-v1.json` SHA `e3bf430308b9d952188cff708d125aa2d44281d32c01b72d348570067b6ff057`. baseline commit은 `76b680d64548af5c87d0455008b25358af06a698`이다. 지역 내용 검토의 유지와 기존 전역 K01/K08/K14·joined catalog 차단을 구별하는 addendum도 후보 전에 남겼다.

검토한 최종 bytes:

- `tools/quality.py`: `03f24f7e9b89979e30facf258f8c8f9f358b1aca2de876a1adae5e058f0fc96b`
- `tools/workflow.py`: `11dc7a916d00a3b67528b63f7d6b02a74e9b895972f7ce56ec540d245b54872b`
- `tools/review_preflight.py`: `de09542da3c32f73f6f89a84709e63616fc8516f2ba6cbec08599443b5c878c5`

기존 코드를 직접 읽고, 서로 독립적인 2개 객체/주차/로컬 근거를 가진 **명시적 가상** 정상 control을 새로 작성했다. 동결한 old evaluator에서 K01–K16 정상 통과를 확인한 뒤 plan의 week1만 바꾸면 K01은 failed인데 해당 내용 검토 fingerprint와 K12는 그대로 통과하는 공백을 재현했다(`baseline-reproduced-gap.json`). 이 control의 review·동의·실행·학습자 기록은 소프트웨어 시험용 허구임을 명시했다. 실제 기록을 녹색으로 만들기 위해 갱신하지 않았다.

## 최종 독립 결과

`v4-matrix-results.json`: **31사례 모두 기대 결과 충족**. 각 사례는 새 subprocess·별도 복사 fixture에서 실행했고 caller bundle·fixture 파일의 검사 전후 동일성도 확인했다. 이 숫자는 기대한 오류 거부를 포함하며 31개 실제 교안/학습자 검토가 통과했다는 뜻이 아니다.

| 확인한 반례 | 실제 결과 |
|---|---|
| 관련 week1·scope02·밖의 전역 p 변경 | 선언된 소비 객체가 review_required. 관련 없는 독립 가지는 current. 공통 전역 문맥은 두 단위에 영향 |
| 무관 week9/scope60·CSS·미등록 셀·execution counter | 해당 내용 검토는 current 유지. 전체 artifact/pinned plan K01 등 별도 차단은 유지 |
| coding 셀·표시 output·지역 근거 bytes/버전/경로 변경 | 의존 가지의 명시 review_required, 독립 가지 유지 |
| source 파일·review evidence 누락/변경 | 해당 review와 경로를 명시. missing source에서도 evaluate/plan의 selective 목록 유지 |
| missing node/edge·미선언/끊긴 plan binding | invalid 또는 binding_required로 거부. 누락을 current pass로 바꾸지 않음 |
| symlink root escape | 안전하게 차단하며 영향 진단 유지. 대상 파일을 정상 근거로 읽지 않음 |
| shared/transitive source | 공유한 두 소비자에 전파. 무관한 전체 객체를 일괄 재검토로 지정하지 않음 |
| 무관 영역 변경 후 whole-file provenance pin 갱신 | 선택된 지역 내용 검토 유지. 실제 선택 영역과 선언을 기준으로 판정 |
| 새 current review append | 그 객체/기준의 최신 기록만 활성화, 이전 기록은 historical로 보존 |
| 최신 failed/uncertain/not_run/stale 및 retired append | 오래된 passed로 fallback하지 않음. retired 기록은 현재 객체를 불필요하게 거부하지 않음 |

`integration-v4-results.json`: 정상·누락 source·무관 catalog에 대한 **CLI 10개 조합**과 실제 구 quality의 evaluate/plan 4개를 확인했다.

- 정상 `evaluate`, `plan`, `review-context`, `workflow`, joined `preflight`의 명세 필드와 current 상태를 확인했다. `review-context`는 문맥 캡처이며 review를 추가하지 않는다.
- 기존 proposal이 있는 상태에서 source A를 삭제해 K11 context_error·K13 unavailable_contexts·plan context_status=unavailable을 실제 확인했다. evaluate/plan/workflow/preflight 모두 영향 A와 경로를 남기고 B는 current였다. workflow/preflight는 blocked였다.
- quality의 내용 검토에 쓰이지 않는 joined catalog 파일을 바꾸어, 내용 review가 current여도 preflight의 stale_declared_source 전역 차단이 유지됨을 확인했다.
- 실제 `reviews/week01/final-followup/quality.json`, `reviews/system-followup-20261111/current/quality.json`은 변경하지 않았다. 각각 evaluate=failed, plan=blocked, 최신 대상의 binding_required 16 / review_required 1 / current 3이 표시됐다. 이력 전체를 지우거나 재작성하지 않았다. exit0은 JSON 처리 성공이며 readiness 통과가 아니다.

## 발견한 결함과 수정 재검증

v3 `613458c1…`에서는 선언 source가 사라졌을 때 `review_freshness`는 A=review_required/B=current였으나, ordinary evaluate의 K11 직접 fingerprint 예외가 전체 계산을 중단했다. CLI는 exit2/invalid_quality_input만 반환해 selective 목록이 사라졌다. symlink escape에서도 같은 연동 문제였다.

`candidate-v3-missing-source-reproduction.json`과 `v3-matrix-results.json`에 실패를 그대로 남겼다. v3 31사례 중 이 두 사례가 실패했고 다른 29개는 기대대로였다. v4의 K11/K13/plan 예외 처리와 unreadable binding 보완 후 같은 31개 및 CLI 연동을 다시 통과했다. v2→v3 writer 변경 때문에 SHA 전제조건에서 멈춘 시도도 `candidate-v2-precondition-failure.json`에 실행하지 않은 것으로 기록했다.

## 자동 검사가 증명하는 것과 남는 수동 판단

새 기능은 **선언된** plan week/scope/global structural context, artifact 지역, upstream 객체, local dependency와 review evidence가 현재 기록과 맞는지 확인한다. 누락 binding/legacy scope의 `binding_required`·`impact_confirmation_required`는 실제 내용 결함을 증명한 `review_required`와 구분한다. 같은 바이트인지, 선언된 경로가 달라졌는지, 최신 기록이 무엇인지가 자동 확인 범위다.

해시는 변경의 신호이지 의미 판정이 아니다. current freshness는 recorded_status=failed인 검토를 통과로 바꾸지 않는다. 유효한 다른 내용·새 규정의 실제 중요성·출처 진실성·검토자의 독립성·누락된 모든 외부 의존성·학생 성취는 자동으로 증명하지 않는다. 스타일/스크립트 등 제외된 구조와 애초 미선언 의존성도 별도의 의미 검토 대상이다. 서로 다른 기준·자료를 모두 다시 읽는 전면 재검토를 자동 처방하지 않는다.

수동으로 근거와 영향을 평가한 뒤 새 review를 append하는 책임은 남는다. 단순히 새 scope fingerprint/context_bindings를 복사하는 것은 평가·동의가 아니다. K01 전체 입력, K08 실행 영수증, K14 agreement 및 workflow의 aggregate manifest·전체 catalog 보호장치는 별도로 보존된다.

## 원본 유지와 정확한 근거 보존

독립 검토자는 이번 `independent/` 아래만 작성했다. 원본 tools/tests/docs·실제 review·교안·git index·remote에 변경 명령을 실행하지 않았다. 실제 구 bundle은 전후 SHA를 비교했고 가상 caller/history/file은 각 검사에서 불변을 확인했다. 원본 lessons는 HEAD와 같은 상태이며 실제 core도 최종 고정 SHA를 재확인했다.

부모 요청에 따라 큰 `inputs/`, `cases/` 복제본을 **삭제한 근거가 아니라 검증 가능한 archive 안에 보존**했다. raw matrix/실패 재현/CLI 요약·기준·보고서·재현 코드는 읽을 수 있는 파일로 남겼다.

- archive `evidence-cas.tar.gz`: 1,512,939 bytes, SHA `731d180e7f0082b60e8f43745b41f49a9c5f5d77518cf6bb63ff039087149da6`
- `evidence-archive-manifest.json`: 모든 원 path·kind·size·SHA·mode와 symlink target metadata. 원 regular 1,197 paths/41,886,800 bytes를 299 unique blobs로 보존했다.
- `archive-verification.json`: 전 path 동일 원바이트/SHA 복구, 모든 regular file의 독립 inode, 복제 하나를 바꿔도 다른 복제에 전파되지 않음을 확인했다. symlink 2개는 target metadata만 보존·검사했고 target을 따라 읽지 않았다.
- 복구된 v4 control에서 CLI를 실행해 원래 전체 JSON report와 동일함 및 ready 결과를 확인했다. 확인 후 중복 복구/원복제 트리만 정리했다. tar hardlink를 실제 파일 hardlink로 재생성하지 않는다.

복구 예(저장소 루트; destination은 아직 없는 이 independent 하위 디렉터리):

```bash
python -B reviews/selective-invalidation-20261111/independent/restore_evidence.py \
  --destination reviews/selective-invalidation-20261111/independent/restored
```

이후 `restored/inputs/v4-tools/quality.py`를 `--root restored/cases/v4-control/root`로 지정해 `restored/cases/v4-control/bundle.json`을 evaluate할 수 있다. `run_matrix.py`는 복구한 v4 snapshot 경로와 새 `--prefix`를 주어 재실행한다. archive의 case 결과는 당시의 exact 입력·raw output이며 성공/실패 상태를 재작성하지 않았다.
