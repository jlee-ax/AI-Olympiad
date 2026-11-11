# AI-Olympiad 시스템 검토·개선 결과 — 2026-11-11

기존 지침에는 그래프 연결, 과거 상태 조회, 검토·수정·재검토 절차가 이미 있었다. 실제 1주차 자료도 한 차례 이상의 검토와 수정이 있었다. 문제는 이를 자동 실행으로 볼 수 없고, 일부 연결·갱신이 실제 기록에 빠져도 기존 구조 검사만으로는 드러나지 않았다는 점이다. 새 구현은 누락과 오래된 바인딩을 함께 검사한다. **교안 전체 충분성이나 실제 학생 성취를 통과시킨 결과는 아니다.**

## 읽은 버전과 보존 범위

원격을 시작 시점과 마무리 직전에 확인했고 세 브랜치의 머리가 유지됐다.

| 대상 | 확인한 커밋 |
|---|---|
| main | `787079f4870068106500e5184ce457e95e6aa3f2` |
| 기존 contest-depth 스킬 브랜치 | `64f24aabdad2b1976740d88d4a0ba74a4ed89766` |
| 기존 Week 1 교안 브랜치 | `204743d94a4176ace81c64f138567c2cc12041d1` |

독립 브랜치 `codex/review-workflow-improvements-20261111`은 최신 main 위의 기존 contest-depth 두 커밋을 보존한 상태에서 시작했다. 미반영 변경이 있던 기존 작업본은 건드리지 않았고, 최신 교안은 별도 읽기용 작업본으로 확인했다. 학생용 노트북/HTML, 삭제된 lesson README, 사용자 변경 및 기존 검토 기록을 복원·덮어쓰지 않았다. main 병합, 자동 스케줄, 외부 유료 서비스, 개인 기기 작업, 제3자 연락은 하지 않았다.

최종 구현·독립 코드 검토에는 GPT-6.1 Sol Ultra 에이전트를 사용했다. 그 이전 예비 조사 결과는 원문·코드·실행 결과로 재확인했다. 현재 제공된 협업 모드는 Default/Plan이고 Goal 전환 인터페이스는 없다. **Goal 모드는 활성화되지 않았다.**

## 이행 누락과 설계 결함

| 발견 | 증거와 반증 가능한 범위 | 유형·중요도 | 조치 |
|---|---|---|---|
| 필수 학습 경로가 실제 그래프에 없음 | candidate-graph 12노드/21관계는 기존 검사에서 0 오류. 기존 지침이 요구한 출처→요구→선수→설명→평가→피드백 경로는 확인할 선언이 없다. 이것만으로 교안에 활동 자체가 없다고 결론내리지 않았다. | 이행 누락 + 구조 검사 범위의 결함, 높음 | 별도 7역할 경로·직접 연결·출처 위치/로컬 바이트 검사 추가. 실습도 별도 역할로 확인. |
| 옛 검토/상태가 새 노트북에 묶이지 않음 | 과거 상태의 artifact SHA는 `602c0c4e…`, 실제 최신 노트북은 `2506059c…`. 실제 상태 판정은 `pause / criteria_agreement_required`. 새 후보의 모든 검토가 갱신됐다는 근거가 없다. | 실행/갱신 누락, 높음 | 실제 파일·비교 기록·그래프·상태·recall을 결합 검사하고 오래된 재사용을 차단. 과거 수용을 새 후보로 위조하지 않음. |
| 메타데이터만 추가해도 판정이 바뀜 | 입력 fingerprint는 동일하지만 quality manifest 주석은 `quality_context_not_bound`, frozen rubric 주석은 `baseline_change_required`를 만들었다. | 기능 결함, 중간 | fingerprint와 동일한 canonical manifest 필드로 비교. 실제 id/revision/hash 변경은 계속 차단. |
| 불확실성의 부당한 전파 | unknown 하나가 모든 비교로 번지고, 숙제 시간 누락이 수업 시간 완전성까지 오염했다. | 기능/판정 범위 결함, 중간 | 비교별 unknown 범위 지원, 전역 문자열 호환 유지, 수업·숙제 시간 판정 분리. 전체 불확실성은 보존. |
| malformed graph 진단 중 비정상 종료 | lone Unicode surrogate를 포함한 중복 ID의 오류 출력에서 예외가 발생했다. | 기능 결함, 중간 | 안전한 진단으로 거부하고 CLI 회귀 추가. |
| 몇 개 비교의 개선을 전체 교안 보정으로 확대할 위험 | 실제 비교는 배열·함수·필기 형식·분산의 4개이며 전체 87개 셀을 포괄하지 않는다. | 검토 범위/보고 결함, 높음 | 전체 셀 범위표를 별도로 작성하고 미검토·미관찰을 명시. 스킬에는 전체 범위 기록과 결합 검사 호출만 최소 연결. |

기록으로는 모델이 내부적으로 지침을 읽었는지를 증명할 수 없다. 이미 쓰인 요구와 실제 산출물·명령 결과의 불일치를 확인했다. 스킬 문구를 먼저 늘리는 결론으로 시작하지 않았다.

## 구현과 실제 기능 검증

- `tools/graph_paths.py`: 7역할, 방향이 맞는 직접 관계, 요구별 경로, 평가 지원 조건, 역할별 로컬 SHA·출처 위치 검사. 역할 이름이나 해시로 내용의 적절성을 추론하지 않는다.
- `tools/review_preflight.py`: 실제 노트북 바이트, 기록된 비교, 그래프 경로, active recall과 workflow 판정을 함께 읽는다. 세 검토 선언의 canonical manifests를 workflow 입력에 묶어 새 선언이 옛 aggregate review를 재사용하지 못하게 한다. 다른 비교의 정상 경로를 가져오는 것도 막는다.
- 기존 `workflow.py`, `contest_depth.py`, `validate.py`의 재현된 결함을 수정했다. 저장/작업 실행은 수동이며 [manual cycle](../../tools/MANUAL-CYCLE.md)에 단계·영수증·재개 조건과 한계를 명시했다.

[전체 회귀 로그](regression.log): **193개 통과** — depth 23, graph paths 31, quality 43, quality followup 36, joined preflight 9, legacy graph/API/CLI 12, workflow 39.

| 실행한 경로 | 기대·실제 결과 |
|---|---|
| 명시적 정상 경로 / 각 역할·관계 누락 / 반대 방향·관련 없는 경로 | 정상만 통과, 누락·오류는 gap/invalid |
| 독립 평가 조건·가시적 답·다른 검토자·실패/미실행 증거 | 조건별 차단. 선언은 신원·학생 독립성의 인증이 아님 |
| 저장 후 재조회 / 중복 기록 / 이미 완료된 동일 문맥 | recall은 active 자료를 반환하고 exact duplicate를 억제, 완료된 동일 문맥은 noop |
| 변경된 자료·스킬·출처·평가기준·검토 선언 | 옛 review/manifest 재사용 차단, fresh binding만으로는 수용되지 않음 |
| 체크포인트·중단·재개·정체·예산 | pause/stop을 보존하고 명시적 갱신 후 재판정. 자동 작업 없음 |
| 얕은 사례와 적정 단계의 기초 사례 | 기록된 gap/met와 scoped uncertainty를 구별. 의미 판정은 검토자 몫이며 아래 실제 자료 검토로 보완 |

[실제 기록 복제본 11개 사례](functional-results.json)도 모두 기대대로 동작했다. 원래 그래프는 형식 pass/경로 gap, 네 비교를 명시적으로 투영한 복제본은 경로 pass, 마지막 피드백 관계 삭제는 gap, 실제 노트북 바이트 변경은 stale, 정확한 바이트 복원은 pass였다. 이 경로 pass는 **네 비교의 기록 연결만** 확인한다. 실제 옛 workflow는 여전히 차단되며 pending criteria를 승인으로 바꾸지 않았다. 계산·축·함수 경계/150개 seeded 사례·분산 counterexample도 실제 교안의 검사 스크립트로 재실행해 통과했다.

[수정 전후 4개 코드 재현](code-regressions.json)은 고정된 `64f24aa` 구현과 현재 구현에 동일한 입력을 주었다. 메타데이터의 두 오차단, scoped unknown의 인접 정상 사례, 숙제 시간의 수업 판정 오염 모두 이전 실패→수정 후 기대 결과를 확인했다.

재현:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
python3 -B reviews/system-improvement-20261111/reproduce_code_regressions.py
# 204743d의 별도 checkout을 LESSON_ROOT에 지정한다.
python3 -B reviews/system-improvement-20261111/reproduce_real_cases.py --lesson-root "$LESSON_ROOT"
```

## 학습 목표에 대한 발견과 남은 일

[전체 1주차 검토](whole-week01-review.md)는 **87/87 셀을 한 번씩** 다뤘고 notes/key, manifest, 선수 명세, 두 도식과 다섯 저장 그림도 확인했다. 평균/분산의 정의·단위·누적 불변식, 축/분모, print/return, 결측과 0, 함수 명세와 동일 shape 반례는 실질적 강점이다. 적절한 기초 수업을 전체 대회 수준이 아니라는 이유로 탈락시키지 않았다.

남은 구체적 보완은 실제 traceback 진단/수정, 보지 않은 그래프·broadcasting 입력의 평가, merge 중복·미매칭/집계 count 경계 사례, 그 항목의 피드백과 새 재시도, 최종 학습 확인의 수업 내 배치와 필수 A–E 숙제 분량의 갱신이다. 이번 시스템 변경은 이 부족을 드러냈으며 **교안 내용을 모두 수정하거나 전체 충분성으로 승인하지 않았다.** 상세 셀 위치와 다음 행동은 전체 검토표에 있다.

[2027 공식 안내](https://kitpa.org/koai/2027)는 현행 범위/형식, [연결된 syllabus](https://kitpa.org/koai/syllabus)는 여전히 IOAI 2026 표기다. [2026 예시 공지](https://kitpa.org/files/36)와 [원본 PDF](https://kitpa.org/storage/c4016751-0e2c-4548-ab70-ecec994e8f8d.pdf)는 고등부 학습 참고용 예시다. 이를 2027 중등부 기출·난도 또는 1주차 완성 기준으로 사용하지 않았다. 1주차는 KNN 전체/4D PyTorch 조작 등을 평가하지 않으며 이것만으로 기초 교안의 결함이라고 판정하지 않았다.

현재 구현이 하지 않는 일: 자동 의미 이해, 공식 출처 인증/실시간 수집, 미선언 요구 발견, 실제 학생 성취·학습 효과 입증, 교사 보정, 최신 교안의 이번 실행에서의 전체 Jupyter 재실행/브라우저 레이아웃 검증, 작업자 실행·상태 writer·locking·인증된 append-only history·실시간 예산 측정·자율 수정/수용 루프. 실제 검토·수정·검증은 사람이 수행하고 기록하며, 코드가 그 기록의 정합성과 재사용 가능성을 점검한다.
