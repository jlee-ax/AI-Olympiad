# 교안 내용 수정과 재검수

검수 대상은 교안의 설명, 선수관계, 문제, 정답과 코드다. 실제 학생 응답, 성취, 교실 소요시간은 수집 대상에서 제외한다. 학습효과를 주장하는 검수 결과는 그 주장을 고쳐야 한다. 수식이나 삽화의 개수에는 점수를 주지 않는다.

## 원문에서 수정할 내용 정하기

1. 교안의 목차를 보기 전에 공식 범위·문제와 필요한 전공 원문에서 목표 능력, 선수, 필요한 설명 깊이와 독립 과제를 추출한다. 발견 기록에 원문 위치와 적용 범위를 남긴다.
2. 교안 전체에서 해당 능력을 가르치는 위치와 평가하는 위치를 읽는다. 빠진 능력, 깊이가 부족한 설명, 실제 중복, 처음 등장하는 용어보다 앞선 사용을 찾아낸다. 올바른 기초도 기록한다. 핵심 공백이 확인되면 아직 단원 목록에 등록되지 않은 능력도 `quality.py plan`에 들어간다.
3. 발견 루프의 `compare`에 `edit`를 추가한다. 아직 편집안을 정하지 않았으면 계획기는 요구, 출처와 실제 위치를 붙여 `design_content_revision`을 선택한다. 근거나 판단이 불확실하면 원문 대조를 먼저 진행한다.
4. 하나의 편집안에 여러 행동을 묶을 수 있다. 설명을 덧붙일 때 길어진 만큼 무엇을 합치거나 덜 수 있는지도 비교한다. 각 행동에 `kind, before, after, reason, alternative, postcondition`을 기록한다. `before/after`는 노트북의 셀 ID 목록이다.

| 행동 | 수정본에서 확인할 결과 |
|---|---|
| `add`, `deepen`, `replace` | 필요한 내용이 생기거나 기존 설명의 조건·풀이가 달라진다. |
| `merge`, `remove` | 중복된 절이 실제로 줄고 필요한 능력과 독립 과제가 남는다. |
| `reorder`, `move` | 노트북 안에서 실제 순서가 바뀐다. 다른 주차로 보낼 요구는 발견 루프의 `deferred`로 목적 단원·담당·계획 근거를 남긴다. |
| `keep` | 정상 기초를 유지한다. 전체가 적절한 판정에서 편집 후보를 발행하지 않는다. |

`edit.routes`는 요구의 모든 차원 ID에 대해 `before`와 `after`를 기록한다. 선수·설명·과제처럼 순서가 있는 셀을 읽는 순으로 열거한다. 새로 발견된 결손에는 빈 `before`가 가능하다. 보존할 다른 능력에도 경로를 추가한다. 독립 검토자는 바뀐 교안 전체를 읽고, 선언이 실제 내용과 맞는지 확인한다.

## 실행

```sh
python3 tools/quality.py plan bundle.json --root .
python3 tools/workflow.py repair workflow.json --quality bundle.json --root .
python3 tools/material_revision.py apply workflow.json bundle.json patch.json candidates/lesson.ipynb --root .
python3 tools/material_revision.py verify workflow.json bundle.json patch.json candidates/lesson.ipynb --review review.json --root .
python3 tools/discovery_loop.py step discovery.json --event advance.json --root .
```

`repair`는 기존 승인·예산·기준본·변경 이력과 실제 발견 기록을 확인한다. `decide`는 최종 상태를 조회한다. 입력 번들과 사례는 같은 검토 기록의 manifest에 고정한다. 새 자료나 교안, 규칙 버전이 달라지면 현재 작업 키를 다시 얻는다. 계획에서 건너뛴 후보와 이유는 `skipped`에 남는다.

패치에는 선택된 `work_key`, 실제 `author`, `operations`를 넣는다. `insert`는 새 ID·셀 유형·본문·앞에 놓을 셀 ID(`before`, 끝이면 null)를, `replace`는 기존 ID와 새 본문을 받는다. `move`와 `remove`는 기존 ID로 동작한다. 생성 위치의 부모 디렉터리는 미리 존재해야 한다. 생성기는 필수 경로, 계획 밖의 셀과 노트북 메타데이터를 대조해 별도 후보 파일을 원자적으로 만든다. 같은 내용의 재시도는 기존 파일을 재사용한다.

검토자 기록에는 `candidate_sha256, work_key, reviewer, checks`가 필요하다. 검토자는 편집자와 구별되며 각 `action:0` 등 행동과 `route:learning` 등 경로, `new_input, boundary, regression`에 대해 판정·실제 셀·관찰·해시가 맞는 근거를 적는다. 새 입력과 경계 검사에는 각각 다른 입력의 `case_id`를 붙인다. 해당 근거 JSON에는 수정본 해시와 `cases` 목록의 `id, input, expected, actual`이 들어간다. 코드는 기대값과 실행 기록을 대조한다. 검토자의 신원, 원문 의미나 선언한 실행의 진실성은 별도로 판단한다.

`advance_lesson` 이벤트에는 공통 `reason`과 `workflow_path, quality_path, patch_path, candidate_path, review_path, revision`을 준다. 검증을 다시 통과한 후보만 새 기준본이 된다. 원본과 사건 이력은 보존한다. 새 산출물에 대한 원문 대조와 최종 검수가 남는다. 실제 배포는 독립 검토가 현재 산출물과 일치하는지 `decide`에서 확인한다. 명령의 출력 JSON을 새 이력 파일에 저장한다. 덮어쓰기 리다이렉션으로 입력 파일을 출력 대상으로 쓰면 안 된다.

## 검수 목적별 판정

- K02는 범위를 선택한 개념 도입 단원에 한해 후속 실습의 주차·단원·과제와 모든 실전 주제 ID를 확인한다. `continuation`의 다음 주차 `plan_locator`도 단원의 계획 의존성에 묶는다. 전체 범위 완료에는 현재 실습 근거가 필요하다. 실제 코드 셀을 담은 교안에는 실행 검사가 적용된다.
- K04는 선수별 `id, task, expected, support_before_use`와 독립적인 K04 내용 검토를 확인한다. 지원 기록의 `before_unit, locator, first_use`는 실제 단원과 위치를 가리켜야 한다. 같은 셀 안의 설명 순서와 타당성은 검토자가 읽는다. 과거 학생 응답만 있는 기록은 설계 근거를 보완한다.
- K15는 교안 검수의 결론에 학생 효과를 끌어들였는지 확인한다. 평가기 자체의 검증은 `python3 tools/quality.py qualify qualification.json --root .`에서 수행한다. 분야, 서로 다른 작성·검토자, 평가기 코드 해시, 실제 파일 근거가 있는 정상·오류 대조, 명시한 허용값을 사용한다. 같은 평가기 버전·분야의 결과는 여러 교안에 재사용할 수 있다.
- 필수 원문의 미해결 요구는 완료를 막는다. 부가 탐색은 배경 자료만 사용하는 질문에 `purpose: background`와 `scope_reason`을 명시한다. 그곳에서 실제 요구가 발견되면 해당 요구도 비교한다. 무관하다고 판단한 필수 자료는 직접 읽고 추출한 결과가 비어 있을 때 별도 검토자가 `exclude_probe`로 근거를 남긴다. 필수 자료에서 파생된 주변 질문에는 원래 읽기 근거와 별도 검토자의 범위 판단을 담은 `exclude_question`을 쓴다. 원문이 바뀌면 질문이 다시 열린다. 추출자 자신의 제외 판정이나 필수 질문의 배경 전환은 허용되지 않는다.

실행 가능한 전 과정 예시는 저장소의 기능 검사에 있다. [교안 수정과 재개 검사](../tests/test_material_revision.py)
