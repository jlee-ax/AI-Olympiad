# 1주 문제→학습 모델→평가·출력 경로의 discovery 재개

기존 실제 상태를 재조회하고, 공식 원문을 새로 읽어 요구를 추가한 뒤, 최종 새 1주 교안과 수정 bridge를 **서로 다른 실제 artifact**에 결합했다. 현재 두 세션은 freshness blocker 없이 `needs_work`, `ready_for_review=false`, `next_action=expand_frontier`다. 이 작업의 기록·대조는 완료했으며 전체 과정 readiness와 학생 성취는 미확인 상태로 유지한다.

| 실제 산출물 | 현재 세션 | 결과 |
|---|---|---|
| 새 문제 해석→학습→예측→평가→파일 교안 | [pipeline-final-01](runs/pipeline-final-01/current-summary.json) | 원래 17개 요구+새 공식 출처 연결 P01/P02=19개, 미조사 질문 5개, 55 events. N01/P01/P02는 국소 자료설계 covered, 나머지 16개 요구는 큐 유지. |
| 축·ID bridge의 전방 링크 변경 | [bridge-navigation-01](runs/bridge-navigation-01/current-summary.json) | 원래 D01/D05/D07과 질문 3개 보존, 15 events, queue 3. 링크만으로 빠진 내용이 생긴 것으로 판정하지 않았다. |

[현재 실행 선택](current-run-selection.json)은 현재 두 세션과 보존된 `pipeline-candidate-01` 이력을 구별한다. 최종 원본·전 셀 투영·현재 보고서·기존 기록의 일치는 [최종 integrity](checks/final-01/integrity.json)에 있다.

## 과거 quality·workflow의 실제 재개 상태

재개 시 기존 `reviews/week01/independent-transfer-20261111`의 실제 bundle/state를 변경 없이 CLI로 읽었다. 그 artifact는 현재 기존 1주 원본 `ee8279b1…`와 일치한다.

| 실제 명령 | 결과와 의미 |
|---|---|
| quality evaluate | `uncertain`, `ready_for_review=false`. 실제 학생 결과·보정 등 미관찰과 기존 검토 불확실성을 유지한다. |
| quality plan | `pause / priority_policy_requires_agreement`. |
| workflow validate | `valid / structural_checks_only`. |
| workflow decide | `pause / criteria_agreement_required`. 과거 기준 합의를 새로 만들지 않았다. |
| joined preflight | exit 1, `blocked`: `contest_depth_uncertain`, `discovery_missing`, `quality_not_ready`, `workflow_pause`. |

[실제 명령·exit·stdout 해시·입력 해시](initial-state/manifest.json)와 같은 폴더의 원출력 JSON을 보존했다. 이 실행의 recall은 `--query` 없는 조회이며, 부모 스레드에서 별도 검색어로 결과 0을 확인한 조회와 혼동하지 않는다. 새 생산 작업의 권한은 이번 사용자 지시에서 왔고, 과거 상태의 기준 합의·수용 기록은 그대로다. 과거 pause를 통과나 동의로 바꾸지 않았다.

새 discovery는 새 노트북에 결합되므로 기존 1주 원본의 quality/workflow에 다른 artifact의 세션을 끼워 넣지 않았다. 새 P01/P02의 종합 graph/path·quality 수용 기록을 만들거나 전체 readiness를 선언한 작업도 아니다.

## 새 원문 읽기와 출처 연결

독립 추출자 `/root/discovery_resume/pipeline_source_extract`가 **새 교안이나 학생 답을 읽기 전에** 공식 웹 자료를 선택·재독했다. 검토자 `/root/discovery_resume`도 주요 원문 범위를 따로 읽고 실제 교안을 대조했다. 저자는 `/root/week01_bridge`다. 이 역할 분담과 바이트 사슬은 신원·객관성·원문 진실을 인증하지 않는다.

[독립 출처 payload](source-extraction/pipeline-source-payload.json)와 세 읽기 메모는 URL, 실제 읽은 범위, 동적 판본, 반대근거와 미확인 범위를 기록한다.

- [국내 2027 안내](https://kitpa.org/koai/2027)와 [연결 syllabus](https://kitpa.org/koai/syllabus): 기법 선택·적용·출력 해석과 모델·전처리·평가의 연결을 확인했다. 연결 본문은 여전히 IOAI 2026 표기다. 독립 추출자의 국제 2027 PDF 열기는 HTTP 429였으므로 전체 변경과 국내 채택 관계는 미확인으로 남겼다.
- [공식 Antique](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb): statement raw L19–72, 실제 fit/predict L118–158, 제출 생성 L176–210을 읽었다. 학습된 모델 적용과 행에 대응하는 두 CSV·zip 계약을 새로 추적했다. baseline의 미상 0을 무작위 ±1로 바꾸는 부분은 휴리스틱이며 관측 정답이나 일반 반지도 해법의 정당화가 아니다.

새 요구 P01은 새 명세의 입력 가용성·훈련 자료·학습 상태·예측·평가를 이유와 코드로 연결하는 행동이다. P02는 행 대응·허용 라벨·지정 CSV/zip 구조를 보존하고 다시 읽어 점검하는 행동이다. 독립 새 표·read-back 평가를 요구한 부분은 공식의 숨겨진 미래 문항이 아니라 명시한 교육적 전이 설계다. 이 국제 과거 문제가 국내 중등 기출이거나 첫 주에 전체를 의무 구현하라는 뜻은 아니다.

프로그램은 원본 웹이 아닌 **실제로 저장된 의역 메모의 로컬 바이트**를 read 이벤트로 열었다. candidate-01은 새 frontier→discover→세 read→trace를 실제 실행한 다음 비교했다. final-01은 그 출처 연결과 19개 요구·5개 질문을 그대로 재생하고 수정된 실제 교안에 다시 compare했다. 수정 뒤 원래 웹 검색을 다시 했다고 주장하지 않는다. 원래 17개 payload와 기존 미조사 질문 4개는 삭제·축소·은퇴시키지 않았다.

## 직접 판정한 국소 진전과 남은 범위

기존 1주 원본은 표·평균·Python의 기초를 제공하고 스스로 모델을 학습하지 않는다고 밝힌다. 기존 bridge의 합성 내적 점수와 이전 2주의 고정 점수는 새 요구의 학습 분류기 근거로 재사용하지 않았다. 새 교안의 `fit`은 훈련 평균과 라벨별 중심을 실제로 배우며, 훈련값 변화가 배운 중심과 같은 입력의 예측을 바꾸는 것을 보여 준다.

| 요구 | 최종 교안에서 직접 확인한 내용 | 판정의 경계 |
|---|---|---|
| P01 | 허용 입력·ID·정답·미상 구분, train-only 대체와 NearestCentroid 학습, 손계산과 learned state, 훈련 변화에 따른 예측 변화, 별도 검증. 새 과제는 3특성·새 ID·0/−1 의미 반전·다른 출력 형식에서 타당한 분류기를 선택·fit하고 평가하도록 한다. | 자료설계 covered. 한 분류기 암기나 3/4 정확도로 실제 성능·학생 전이를 입증하지 않는다. |
| P02 | ID→예측 대응과 요구 순서, 무헤더 두 CSV, 실제 임시 `submission.zip` 쓰기·재개봉·삭제, 헤더/개수/라벨/같은 길이 순서/결측 ID 오류. 새 과제는 헤더 있는 `audit.csv`와 ID·0/1을 저장·재독하도록 한다. | 국소 계약·전이 설계 covered. 공식 데이터·숨은 평가·작업 환경·제출 수락이나 Antique 전체 해결은 검증하지 않았다. |
| N01 | 비코딩 이유·계산, 실행 예제, 다른 명세의 독립 작성 칸과 도움 기록을 각각 유지한다. | 학생 답안은 비어 있고 실제 독립 수행은 미관찰이다. |
| D02/D04/D05 | 중심 거리, 라벨 매핑 경고, 일반 ID/출력 대응은 관련 진전이다. | 원래 kNN 이웃·투표, 클래스 index/argmax/비연속 label round trip, 정규화된 검색 점수·공식 매칭 제약은 그대로 gap. 서로 다른 연산을 같은 것으로 합치지 않았다. |
| D03/D06/N03 | 예측 시점·train-only fit·검증 통계 불변·바뀐 미상 라벨 해석과 알려진 라벨만 쓰는 축소 경로를 다룬다. | 원래 shape 통과 대 의미 오류의 독립 대조, 표준화/평균 중심화 및 전체 누수·과대적합 평가, PU 관측가정 전체는 해소하지 않았다. |
| 기타 원래 요구 | 19개 전부를 해당 축과 실제 source span으로 비교했다. | mask·embedding lookup·softmax/loss·수치미분·Radar 가중 평가·추론 API 등 넓은 후속 요구를 유지했다. |

다른 분류기를 선택한 새 과제의 결과를 교사용 중심 분류기 숫자와 다르다는 이유만으로 오답 처리하지 않는 기준도 확인했다. 여러 파일을 합쳐 읽은 척하지 않았으며, 다른 단독 교안의 gap/uncertain을 이전 보존 baseline의 covered 취소나 회귀라고 판정하지 않았다.

## SHA 변경과 보존 이력

| 최종 실제 원본 | raw SHA-256 | 전 셀 source 투영 SHA-256 |
|---|---|---|
| `lessons/week01/week01_problem_pipeline.ipynb` | `f64a54c8f8eeb995fa8b85fc565836c5e66a97249f97177644cb15ad8f88997a` | `1eed14ba5df23994411ba0513bd24ac25f79d6627ab7d68a597496f14758929c` |
| `lessons/week01/week01_axes_linear_bridge.ipynb` | `09efa4d1a8ebf918dab7fc0b30f60f8130e817729d70cfe93cd7c60f15b5767f` | `45e99a9109db9b2da282d79eb95dbac1425ec08e303d9ce7dcb9d98de42a7821` |

각 run의 exact 노트북 사본에는 metadata·저장 출력까지 있으며, 별도 투영은 모든 셀의 index·ID·종류·source를 순서대로 담고 출력은 생략한다. 검토자는 기존 1주 89셀, bridge 내용과 마지막 링크 변경, 새 교안 전체 27셀 및 최종 수정 diff를 직접 읽었다. 코드가 셀 의미를 판정한 것은 아니다.

- 기존 bridge `1c3ccb5d…`의 exact raw를 [초기 사본](initial-week01-bridge.ipynb)으로 보존했다. 바뀐 것은 cell28의 전방 링크 한 줄이며 코드·실행 순서·저장 출력은 같았다. [이전 bridge stale 재현](previous-bridge-stale-after-navigation.json)은 원래 session/report를 덮어쓰지 않고 `artifact_changed`를 보인다. 새 bridge 세션은 원래 3개 요구와 질문을 그대로 유지한다.
- `pipeline-candidate-01`은 `94bc86e3…` 시점에 실제 생성·재조회했다. 이후 cell12의 ID 순서 보존 시점을 고친 `f64a54c8…`에서는 [candidate stale 재현](pipeline-candidate-01-stale-after-id-wording.json)을 추가했다. 그 한 Markdown source 외 모든 notebook 필드는 같았고, candidate session/report/raw와 [당시 검사](checks/candidate-01/integrity.json)를 보존한 채 새 final-01에 결합했다.
- [초기 1주 원본 사본](initial-week01-original.ipynb)의 SHA는 `ee8279b1af621c22da5094d765ea424171c5448527d931b943a6a30cb7c2f6b7`로 현재 원본과 같다. 기존 session·report·quality/workflow 파일도 초기 해시를 유지한다. 검사 시점 index SHA는 초기와 같은 `69172e45f585dd558ca872c017fff2d7079e0faa82bb1d83306ad87193f4020a`다.

이전 discovery의 `next_action`은 미조사 질문 우선순위 때문에 `expand_frontier`일 수 있다. 원본 최신성은 별도의 `artifact_changed`/receipt 결과와 함께 읽는다. 이전 2주 본문·보완본 세션은 현재 바이트와 일치하며, 변경된 bridge의 옛 세션만 최신 근거로 쓰지 않는다.

## 재현과 확인 범위

```sh
python3 -B reviews/week01-pipeline-20261111/discovery/verify_pipeline_discovery.py
python3 -B tools/discovery_loop.py report reviews/week01-pipeline-20261111/discovery/runs/pipeline-final-01/session.json --root .
python3 -B tools/discovery_loop.py report reviews/week01-pipeline-20261111/discovery/runs/bridge-navigation-01/session.json --root .
```

현재 두 세션의 `next/report/manifest` CLI 6회가 exit 0이었고 parsed report는 저장 report와 같았다. [명령·stdout SHA·바이트 수·보존/용량 검사](checks/final-01/cli-and-storage-integrity.json)에서 실제 재생 증거를 볼 수 있다. exit 0은 유효한 기록의 뜻이며 completion/승인 신호가 아니다.

[별도 독립 실행 검토](../independent/validation-results.json)와 [13개 변이 결과](../independent/mutation-results.json)는 같은 최종 SHA의 수치·ZIP·ID 경계·다른 모델 구현 등을 검증한 자료다. 그 실행은 학생 답·실제 성취가 아니다. 이 discovery의 재생/해시 검사, 수동 원문·교안 의미 판정, 별도 코드 실행과 학습 결과를 구별한다.

쓰기는 `reviews/week01-pipeline-20261111/discovery/` 안으로 제한했다. 기존 파일/index를 수정하거나 commit/push하지 않았다. 최종 config/session/report/manifest/events와 전이·원본 사본을 보존하고 중복 `session-NN` 상태나 `.pyc`/`__pycache__`/`.tmp`를 만들지 않았다. 큰 report stdout은 해시와 parsed 일치 결과만 남겨 중복 사본을 줄였다.

남은 과정 일은 원래 공식 범위 적용 관계·Pixel 세부 계약/환경·반지도/PU 깊이·후속 실제 주차 구현과 넓은 요구 대조다. 새 질문은 Antique 전체 반지도 학습·숨은 데이터·제출 수락·대회 성능의 미검증을 유지한다. 학생의 첫 응답·도움·재시도·낯선 문제 전이와 실제 수업 가능성도 관찰해야 한다. 새 연결 경로의 자료설계 진전과 이러한 미해결을 동시에 기록했다.
