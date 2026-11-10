# Workflow state contract · v1

이 계약은 pstack의 제한된 개선 루프를 KOAI 설계 작업에 적용하기 위한 작은 상태 검사기다. **기록된 조건과 참조의 일관성을 검사하며, 작업을 실행하거나 기록의 진실을 인증하지 않는다.** 기존 그래프 검사기와 독립적으로 작동한다.

pstack에서 가져온 방법상의 출발점은 [autonomous-run의 완료 조건과 반복 기록](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/poteto-mode/playbooks/autonomous-run.md), [hillclimb의 측정 기준 고정](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/poteto-mode/playbooks/hillclimb.md), [orchestrate의 작성자와 검토자 분리](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/poteto-mode/playbooks/orchestrate.md), [session-pickup의 이전 주장 재확인](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/poteto-mode/playbooks/session-pickup.md)이다. Lauren Tan의 원본을 위 고정 커밋으로 명시하며, 여기의 Python 코드는 별도로 작성했다. 이 연결은 교육 효과에 대한 실험적 검증을 뜻하지 않는다.

## 실행 범위

```sh
python3 -B tools/workflow.py validate templates/workflow.json
python3 -B tools/workflow.py decide templates/workflow.json
python3 -B tools/workflow.py fingerprint examples/workflow.json
python3 -B tools/workflow.py recall examples/workflow.json --query 'synthetic evidence'
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

네 명령은 지정한 JSON 파일만 읽고 JSON 결과를 표준 출력에 쓴다. `--query`는 `recall`에서만 사용한다. 파일 생성·수정, 검색망 접속, 셸 실행, 스케줄 등록, 수업 생성, PR 또는 병합 기능은 없다. 조회와 판정을 반복해도 입력은 바뀌지 않는다.

`validate`는 구조와 참조를 검사한다. `fingerprint`는 아래 세 지문을 계산한다. `recall`은 유효한 기록에서 대체된 항목과 정확한 중복을 제외하고 검색한다. `decide`는 `pause`, `blocked`, `continue`, `noop`, `stop`과 이유 코드를 반환한다. 모든 결과의 `authority`는 `advisory_only`다. 유효한 입력의 종료 코드는 판정 결과와 관계없이 0이고, 입력/구조 오류는 2다. 따라서 종료 코드 0은 다음 작업에 대한 허가나 통과 증명이 아니다. 명령행 사용법 오류는 argparse의 오류 출력과 종료 코드 2를 따른다.

[기본 양식](../templates/workflow.json)은 구조상 유효하지만 합의·기준·예산이 미정이므로 `pause / operator_agreement_required`다. [예시](../examples/workflow.json)는 `synthetic: true`인 가상 상태다. 예시의 승인, 해시, 통과, 검토자와 예산은 모두 테스트용 선언이며 실제 실행 권한이나 수행 이력이 아니다. 가상 예시의 해시는 가상 식별 문자열에서 만든 값이다.

## 상태와 근거

| 필드 | 계약 |
|---|---|
| `schema_version`, `synthetic` | 버전은 정수 1. `synthetic`은 가상 자료 여부이며 불리언이다. |
| `scope` | `task_kind`는 `design`, `lesson_production`, `recurring` 중 하나. 뒤의 두 종류는 각각 `lesson_production_allowed`, `recurring_allowed`가 true로 명시되어야 조언 판정을 받을 수 있다. 두 플래그의 기본값은 false다. 플래그를 켜도 실행 기능이 생기지 않는다. |
| `agreement` | `operator_agreed`, `operator_id`, `criteria_agreed`, `criteria_fingerprint`, `budget_fingerprint`. 실제 사용자 요청을 근거로 사람이 기록해야 하며 문자열·불리언 자체는 승인 인증이 아니다. |
| `context` | `inputs`, `skills`, `rubric`, `evaluator`, `references`, `artifact`, `author`, `required_checks`, `finish_condition`. 처음에는 비어 있거나 null일 수 있지만 진행 판정 전에는 설정해야 한다. |
| `frozen` | 고정한 `rubric`, `evaluator`, `references`, `required_checks`, `finish_condition`. 기준 변경은 새 비교 실험/기준선에서 명시적으로 처리한다. |
| `limits` | `checkpoint_minutes` 기본값 30. `max_iterations`, `max_elapsed_minutes`, `max_no_progress`는 미합의 시 null이고, 진행 전에는 양의 정수로 합의해야 한다. 예시의 3회·90분·2회는 검증된 최적값이나 기본 운영 정책이 아니다. |
| `usage` | 호출자가 보고한 `iterations_used`, `elapsed_minutes`, `no_progress_count`, `minutes_since_checkpoint`. 음수가 아닌 정수다. 검사는 실제 경과 시간이나 외부 작업을 계측하지 않는다. |
| `stop` | `requested`, `reason`, `goal_claimed`. 명시적인 정지에는 이유가 필요하다. 목표 달성 주장은 최신 필수 검사와 별도 검토가 통과한 경우에만 완료 판정에 쓰인다. |
| `sources` | 출처 카탈로그: `id`, `uri`, `revision`, `sha256`. 링크를 열거나 원문을 내려받지 않는다. 같은 출처의 새 버전도 원기록을 보존할 수 있도록 새 식별자로 기록한다. |
| `records` | 보존할 `id`, `kind`, `text`, `created_at`, `source_refs`, `supersedes`. `kind`는 `evidence`, `decision`, `observation`, `skill`. 최소 한 개의 출처와 원문 위치가 필요하다. |
| `reviews` | `id`, `context_fingerprint`, `author_id`, `reviewer`, `checks`, `conclusion`, `reason`. 결론은 `accepted`, `changes_requested`, `abstain` 중 하나다. 같은 지문의 검토가 여러 개면 배열에서 마지막 것을 적용한다. |
| `history` | 완료된 시도의 `id`, `context_fingerprint`, `outcome`, `reason`. `outcome`은 `accepted`, `rejected`, `no_progress`. 단순 조회나 합의 대기는 완료된 시도가 아니므로 여기에 추가하지 않는다. |

버전 명세(manifest)는 `id`, 비어 있지 않은 `revision`, 소문자 64자리 `sha256`으로 구성한다. `inputs`, `skills`, `references`는 명세 목록이고 `rubric`, `evaluator`, `artifact`는 단일 명세다. `context.references`는 카탈로그의 같은 ID·버전·해시와 일치해야 한다. 실제 자료를 다룰 때는 작업자가 실제 파일/원문의 내용 해시를 기록해야 한다. 도구는 선언된 해시의 형식을 검사할 뿐 해당 바이트의 존재나 일치를 확인하지 않는다.

`author`와 `reviewer`는 각각 `id`, `model_family`를 가진다. `source_refs`의 각 항목은 `source_id`와 비어 있지 않은 `locator`를 가진다. `checks`의 각 항목은 `id`, `status`, `evidence_record_ids`를 가진다. 검사 상태는 `passed`, `failed`, `not_run`이다. 통과를 뒷받침하는 ID는 모두 현재 유효한 **`kind: evidence`** 기록이어야 한다. `decision`, `skill`, `observation`만으로 통과를 뒷받침할 수 없다.

## 지문과 재사용

`context_fingerprint(state)`는 작업 맥락의 단일 지문이다. 명시된 작업 범위와 권한 플래그, 입력·스킬·산출물의 ID/버전/해시, 작성자, 고정 측정 항목, 활성 기록의 종류·내용·출처 위치, 실제로 참조한 출처 카탈로그를 정규화하여 SHA256으로 묶는다. 명세 목록 순서를 바꾸어도 같고, 스킬 버전만 바뀌어도 달라진다. 활성 기록에 실제 새 내용이 추가되면 달라진다.

정확히 같은 종류·문장·출처 위치를 가진 중복 기록은 ID나 작성 시각만 달라도 같은 기록으로 취급한다. 동일한 출처 참조의 반복이나 정의되지 않은 장식용 메타데이터는 새 근거로 세지 않는다. 이는 의미상 중복이나 모순을 판별하는 기능이 아니다. 바꿔 쓴 문장, 서로 다른 출처 ID, 누락된 의존성은 사람의 검토가 필요하다. 이 작은 상태 파일에 선택해 넣은 맥락만 다루며, 관련 자료를 모두 찾았다는 보장은 없다.

검토·완료 기록·사용량 자체는 맥락 지문에 넣지 않아 기록 추가가 자기 자신을 무효화하지 않게 한다. 대신 현재 지문과 일치하는 마지막 검토를 다시 확인한다. 새 실패나 검토 거절은 과거 완료 기록보다 우선한다. 검토가 유효하게 통과했고 같은 지문에 대한 완료 기록이 이미 있으면 `noop / no_new_evidence`다. 입력이 바뀌면 기존 검토와 완료 기록을 재사용하지 않는다.

`criteria_fingerprint(state)`는 고정 측정 항목을, `budget_fingerprint(state)`는 `scope`와 `limits`를 묶는다. 합의에 기록한 값이 현재 값과 달라지면 중단하여 새 합의를 요구한다. 세 값은 `fingerprint` 명령으로 확인할 수 있다. 계산된 값을 합의 필드에 복사하는 행위만으로 실제 동의가 생기는 것은 아니다.

공식 대회 범위, 평가기 또는 루브릭을 바꾸려면 기존 실험 기록을 보존하고 새 상태 파일/기준선에서 `context`와 `frozen`, 관련 합의 및 검토를 새로 설정한다. 현재 CLI는 이전 파일과의 변경 이력을 인증하지 않으므로 기존 `frozen`을 조용히 덮어쓰지 않는 작업 규율은 별도로 지켜야 한다.

## 대체와 검색

`supersedes`는 앞에 있는 기록 ID만 가리킬 수 있다. 원기록은 삭제하지 않는다. 같은 선행 기록을 두 후속 기록이 각각 대체하는 분기는 오류다. v1에서는 이미 잘못 만든 분기를 후속 조정 기록을 추가하는 방식으로 복구할 수 없다. 대안들은 `supersedes`가 없는 관찰 기록으로 유지하고, 검토 후 하나의 후속 기록이 현재 기록과 대안들을 명시적으로 대체하도록 한다.

검색에서는 대체된 기록과 그 정확한 복사본이 오래된 답을 되살리지 않도록 제외한다. 수정이 다시 뒤집혀야 한다면 현재 수정 계보의 기록을 명시적으로 대체하는 새 기록을 남긴다. 무관한 기록을 대체하는 방식으로 이미 수정된 내용을 되살리는 것은 오류다. `recall`은 활성 기록의 `text`에서 공백으로 나눈 검색어를 대소문자 구분 없이 모두 포함하는 항목을 반환하고 출처 상세 정보를 붙인다. 벡터 검색, 의미 검색, 자동 요약 또는 자동 삭제는 하지 않는다.

검토가 대체된 근거를 계속 가리키면 해당 검사는 `stale`로 표시하며 통과로 계산하지 않는다. 통과라고 적었지만 근거가 없거나 근거 종류가 잘못되면 `unsupported`, 필요한 검사 자체가 없으면 `not_run`이다. 모든 참조가 존재한다는 것과 주장이 참이라는 것은 다르다.

## 판정과 운영 순서

1. 상태의 구조·참조를 검사한다. 불완전한 JSON, 비유한 숫자, UTF-8로 표현할 수 없는 단독 서로게이트도 구조 오류로 보고한다.
2. 명시적인 정지 요청, 운영자·기준 합의, 작업 범위, 설정된 맥락을 확인한다.
3. 고정 기준선과 현재 측정 항목, 기준 합의 지문을 대조한다.
4. 유한한 예산과 범위·예산 합의 지문을 확인한다. 완료 기록 수는 반복 횟수의 하한이며, 마지막 수락 이후의 거절/무진전 기록 수는 정체 횟수의 하한이다. 한도에 도달하면 `stop`이다.
5. 마지막 점검 이후 보고 시간이 30분 기본값에 도달하면 `pause / checkpoint_due`다. 이는 사용자가 요청한 점검 간격이며 최적성 주장이 아니다. 실행 중인 일을 강제로 종료하는 타이머도 아니다. 외부 작업자는 안전한 지점에서 증거와 사용량을 기록하고 점검해야 한다.
6. 현재 지문의 마지막 검토를 확인한다. 작성자 ID와 검토자 ID가 같으면 차단한다. 같은 모델 계열이면 경고한다. 문자열이 다르다는 사실로 실제 사람/에이전트의 독립성이나 다른 모델 사용을 인증할 수는 없다.
7. 현재 필수 검사가 모두 근거를 갖추어 통과하고 검토가 수락된 때만 완료 주장, 중복 `noop`, 또는 예산 내 `continue`를 판단한다. 새 실패는 `blocked`로 드러낸다.

`continue`는 한정된 다음 단계의 제안이다. 외부 실행 권한을 부여하거나 다음 호출을 예약하지 않는다. 체크포인트를 확인한 작업자는 사용량을 정확히 반영하고 `minutes_since_checkpoint`를 재설정할 수 있지만 총 사용 시간·횟수와 이전 기록은 보존해야 한다. 코드가 파일을 쓰지 않으므로 실제 기록 보존과 인계는 승인된 작업자가 상태 파일을 별도로 저장하여 수행한다.

Python API의 `validate_state(state)`와 `decide(state)`는 구조 오류를 결과로 돌려준다. `context_fingerprint`, `criteria_fingerprint`, `budget_fingerprint`, `measurement`, `recall_records`는 먼저 검증한 상태를 받는 순수 조회 함수다. 공개 CLI는 항상 구조 검증 후 조회한다.

## 검증의 경계

합성 테스트는 지문 변경, 오래된 검토 거절, 실제 근거 종류, 실패·미실행 구분, 작성자/검토자 ID 분리, 기준선 고정, 중복 무작업, 대체 검색, 유한 예산, 체크포인트, 읽기 전용 동작과 잘못된 JSON 처리를 확인한다. **출처의 진실, 검사의 실제 수행, 동의의 진위, 기록의 불변성, 실제 경과 시간, 검토자의 독립적 판단, 학생의 학습 효과 또는 반복 개선의 효능은 입증하지 않는다.** 테스트 통과를 수업 준비 완료나 연구 가설의 검증으로 해석하지 않는다.
