# 실제 외부 요구 discovery와 교안 대조 — 2026-11-11

기존 큐에서 출발해 새 공식 범위·문제·이론 원문을 읽고, `discover → read → trace → compare → next/report`를 실제 실행했다. **조사·비교 작업은 완료했으며, 과정 전체 완성이나 학생 성취는 입증하지 않았다.** 모든 현재 세션은 `needs_work`, `ready_for_review=false`다.

## 비교 단위와 결과

| 실제 입력 | 별도 실행 | 판정과 잔여 |
|---|---|---|
| 이전 보존 1주 원본과 기존 36-event 세션 | [baseline-wave-01](runs/baseline-wave-01/report.json), 45 events | 기존 열린 13개 요구를 지우지 않고 새 N01–N03을 추가했다. 총 17개 요구 중 큐 16개. 이전 D03의 국소 `covered`는 그대로다. |
| 실제 10주 HTML 계획 | [plan-wave-01](runs/plan-wave-01/report.json), 9 events | 새 요구 3개를 별도 대조했다. 활동 편성은 있으나 그 계획만으로 학습·독립 평가의 실제 제작을 보일 수 없어 모두 gap이다. 기존 14개 요구의 종료를 선언하는 세션이 아니다. |
| 새 실제 2주 노트북 | [week02-candidate-02](runs/week02-candidate-02/report.json), 48 events | 기존 14개 demand payload를 축소 없이 가져오고 새 3개를 더했다. 17개 중 N01만 이 단원의 자료 설계로 `covered`; 큐 16개. 아래 차원별 진전은 전체 요구 해소와 구별한다. |
| 새 실제 1주 보충 노트북 | [week01-bridge-02](runs/week01-bridge-02/report.json), 15 events | 원래 D01/D05/D07만 별도 대조했다. 행렬곱·ID 복원·lookup의 국소 진전은 있으나 원래 넓은 요구는 3개 모두 gap이다. 기존 1주와 2주를 합쳐 읽은 척하지 않았다. |

최종 `final-03` 조회에서 위 네 현재 세션은 바뀐 입력에 따른 freshness blocker가 없었다. 이전 1주 보충 `week01-bridge-01`은 저자가 원본을 바꾼 사실을 `artifact_changed`로 드러내며, 현재 세션으로 재사용하지 않는다. `next_action=expand_frontier`다. 명령의 exit 0은 유효한 기록·재생이라는 뜻이며 목표 완성 신호가 아니다. [최종 요약·무변경 증거](checks/final-03/integrity-and-execution-evidence.json)와 같은 폴더의 `*-current-summary.json`에서 실제 출력 요약을 바로 읽을 수 있다.

## 역할과 원본 결합

새 원문 독립 추출자는 실제 하위 에이전트 `/root/course_discovery/verify_new_scope`다. 범위·문제·이론을 직접 웹으로 읽고 요구를 전달했다. 검토자 `/root/course_discovery`는 그 기록과 선택한 원문을 재독하고 실제 교안을 별도로 판정했다. 10주 출처 문서의 저자는 `/root/ten_week_sources`와 `/root/source_problem_frontier`, 2주 저자는 `/root/week02_lesson`, 1주 보충 저자는 `/root/week01_bridge`다. 이 검토자는 그 교안을 작성하지 않았다. 역사적 요구의 `source-research-sol` 표기는 **이전 추출을 변경 없이 가져왔다는 출처**이며 이번에 그 에이전트가 새 검색을 했다는 뜻이 아니다. 역할명 문자열이나 해시 사슬은 신원·독립성·원문 진실을 인증하지 않는다.

- 기존 원본 보존: 이전 `reviews/discovery-loop-20261111/runs/session.json`의 파일 SHA가 유지됐다. 그 seed·이벤트·13개 열린 큐를 덮어쓰지 않았다.
- 10주 계획 원본 SHA-256: `a3a48fe01212b28368c34c46de2dee0c5d6a78ea7c5d37125b335891ae1f8254`.
- 2주 원본: `lessons/week02/week02_prediction_evaluation.ipynb`, SHA-256 `52b5c170ab2c83fc29327c302e9c77e34c58bce81061c7a167228d0cc67c36e3`.
- 최종 1주 보충 원본: `lessons/week01/week01_axes_linear_bridge.ipynb`, SHA-256 `6241f6bce0db5b2dfe40dc672a0706a09d7228d2aea451cd1a03b05847f910c4`.

최종 두 원본의 정확한 바이트 사본과 해시는 [원본 snapshot 목록](final-artifact-snapshots.json)에 보존했다. [1주 버전 후속 기록](bridge-version-followup.json)은 이전 `74f52475…`와 최종 `6241f6bc…`를 연결한다. 저자가 이전 원본을 수정하기 전에 exact raw 사본을 만들지는 못했으므로, 이전 버전은 SHA·전 셀 source 투영·영수증·이벤트·실행 출력으로 보존하며 이전 `.ipynb`의 출력/메타데이터까지 복원 가능한 사본이라고 주장하지 않는다.

각 후보는 원본 SHA와 모든 셀의 source를 순서대로 투영한 별도 텍스트 SHA를 함께 기록했다. 투영은 셀 ID·종류·원문을 포함하고 출력은 생략한다. 대응 관계는 검토자의 전 셀 읽기로 확인했으며 도구가 그 의미를 증명한 것은 아니다. 원본 노트북, 교사용 파일, 타인의 작업 파일과 git index를 수정하지 않았다. index는 첫 확인과 최종 확인의 해시가 같다. commit/push는 실행하지 않았다.

## 새 원문에서 생긴 요구

[출처 manifest](source-manifest.json)와 [읽기 메모](inputs/)는 원문 URL·버전·실제 읽은 범위·읽지 못한 범위를 명시한다. 도구는 **원문을 내려받은 원본이 아니라 이 의역 메모의 로컬 바이트**를 읽었다. 메모 해시는 원문 진위나 전체 조사 범위의 증거가 아니다.

| 요구 | 새 원문과 실제 읽기 | 새로 드러난 행동 |
|---|---|---|
| N01 | [KOAI 2027 안내](https://kitpa.org/koai/2027), L90–100·120–140·218–234; 연결된 [국내 기준](https://kitpa.org/koai/syllabus), L72–196 | 비코딩 이유·계산과 코드 구현을 각각 평가하고, 기법의 사용 시점과 출력 의미를 설명한다. 실제 미래 문항의 세부 난도를 추정하지 않는다. |
| N02 | [IOAI 2025 Pixel](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Pixel/Pixel.ipynb), raw L28–90, 추가 L94–96 | 반열린 사각형의 픽셀·면적, 6.25% 예산, 각 이미지의 지정 출력 계약을 함께 점검한다. 새 좌표의 경계·예산 초과 사례를 독립 평가한다. |
| N03 | [IOAI 2025 Antique](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb), raw L19–72; [CS229 Summer2019 PS1](https://cs229.stanford.edu/summer2019/ps1.pdf), 문제2 인쇄 pp5–6, L195–354 | 미상과 확정 음성을 구분하고 허용된 특성·라벨을 보존한다. 관찰 라벨과 참값을 구별하며 특정 PU 관측모형을 일반 미상 라벨에 자동 적용하지 않는다. |

`main`은 고정 upstream commit으로 핀하지 못한 동적 원문이다. CS229의 일정한 양성 관측확률·거짓 양성 부재 가정이 Antique에 성립한다고 원문이 보장하지 않는다. 그 확률 유도를 중학생 1·2주 필수로 승격하지 않았다. 국내 2027 안내가 연결한 본문은 여전히 IOAI 2026 기준이고, 공식 국제 2027 PDF는 링크 확인 후 직접 열기·클릭 모두 HTTP 429였다. **최신 PDF 전체 차이·국내 채택은 미검증**으로 남겼다.

## 실제 교안 의미 판정

| 원래 요구를 유지한 대조 | 실제 관찰된 진전 | 남긴 누락·불확실성 |
|---|---|---|
| 2주 D06 | 평균·표준편차 식, train-only fit, 같은 통계의 transform, 별도로 표시한 누수 반례, 새 표의 직접 구현. 선수·학습·원리·실습 차원 met. | 원래 독립 평가에는 누수와 과대적합의 구별도 있다. 검증 적응은 설명하지만 독립 비교 문항은 없으므로 assessment uncertain, 전체 uncertain. |
| 2주 H01 | 전체 행 정확도와 개체별 정확도 평균을 새 불균형 예제로 계산한다. | 원래 Radar의 정답 의존 가중치와 지표별 순위 역전은 다르다. 관련 분모 토대가 H01 전체를 해소하지 않아 gap. |
| 2주 H02 | 공개 개발 라벨과 숨은 추론 라벨의 가용성을 구분한다. | Concepts의 추론 API 부재 탐지·의존성 제거·오프라인 산출물 재구성은 없으므로 gap. |
| 2주 N01/N03 | 실제 비코딩·코드·새 입력 평가·도움 기록은 N01의 이 단원 국소 설계를 충족한다. 미상 0과 음성 -1을 구분하고 독립 새 n3 처리 이유를 묻는다. | N03의 CS229 관측가정·상수 alpha 반례 독립 평가는 없어 assumptions uncertain. 미상 구분의 진전과 고급 관측모형 충분성을 구별한다. |
| 2주 N02 | 배열·비율 선수가 있다. | 사각형 경계·면적 예산·JSONL 과제는 없고 실제 후속 주차 자료를 확인하지 못했다. gap은 이후 과정의 잔여이며 2주에 모든 비전 내용을 넣으라는 뜻이 아니다. |
| 1주 보충 D01 | 행렬곱의 수축 축, 행·특성·출력 축, shape는 맞지만 뜻이 틀린 순서 반례를 구현했다. | 원래 reshape 대 transpose 좌표 비교와 모델 입력·정답 축 전이는 이 단독 보충본에 없어 gap. |
| 1주 보충 D05 | QGᵀ 점수표, 임의 ID 복원, 행을 섞고 ID를 그대로 둔 오류, 새 입력 독립 과제는 실제 존재한다. practice met. | norm·단위 정규화 cosine, 공식 identity/gender matching 제약은 없다. 원래 넓은 요구는 gap. 합성 최대 내적이 공식 정답 알고리즘이라는 주장은 하지 않는다. |
| 1주 보충 D07 | 최종판은 전체 lookup 벡터 출력, (2,3)→(2,3,2), 반복 index 대응과 같은 shape의 순서 반례를 추가했다. 학습·실습 차원은 met으로 진전했다. | V/L 축 차이와 새 B/L/H·반복 index 전체 값의 **독립** 과제는 없다. 선택 C는 후보 ID 의미를 강화한 stack/concatenate이며 lookup 평가가 아니므로 gap. |

2주 세션에서 D03이 uncertain인 것은 **다른 단독 산출물**의 평가다. 이전 보존 1주의 D03 covered 기록을 취소하거나 회귀라고 판정한 것이 아니다. 새 노트북에서 미실시된 과제를 줄여 적거나 기존 요구를 은퇴시키지 않았기 때문에, 코드와 설명이 진전돼도 넓은 큐는 남는다. 10주 배치는 [별도 출처·선수 검토](../course-reconstruction-20261111/independent-ten-week-source-audit.md)의 제안이며 후속 3–10주 실제 제작·수업·무도움 성취가 아니다.

## 실제 실행과 실패 이력

- [2주 실행 기록](runs/week02-candidate-02/execution-output.json): fresh in-process IPython에서 8개 코드셀, 오류 0; 훈련 행·그룹 분리·대체값 4와 잘못된 9·검증 입력 변경 후 학습 통계 불변·혼동행렬·정밀도 0분모 정책·행/개체 점수·ROC의 8개 별도 수치 점검 통과.
- [1주 보충 실행 기록](runs/week01-bridge-02/execution-output.json): 13개 코드셀, 오류 0; 선형변환·섞인 ID 복원·반복 lookup 대응의 3개 별도 유한 점검 통과.
- 학생 답안은 만들어 넣지 않았다. 2주 독립 코드 칸은 실제 AST 문장 수 0이다. 원본의 빈칸 플래그를 그대로 믿는 검사가 아니다. 학생 답·도움·완료 시간·학습효과는 모두 미관찰이다.
- [첫 2주 실행 실패](runs/week02-candidate-01/run-failure.json): discovery 보고서는 저장됐으나 필요 없는 `nbformat` 배포 메타데이터 조회에서 `PackageNotFoundError`가 발생해 실행 결과 저장이 중단됐다. 그 기록은 보존했고 사용하지 않는 조회를 제거한 새 `week02-candidate-02`에서 완결했다. 첫 실패 projection의 잠정 저자명은 `/root/week02_author`였지만 실제 canonical 저자는 `/root/week02_lesson`이며 최종 실행에 바로잡았다.
- 두 번째 실행 stdout의 `covered:[]`는 report 내부 위치를 잘못 조회한 **표시 오류**였다. 저장된 event/report는 처음부터 N01 covered였고 변조하지 않았다. 출력 코드를 고쳤으며 최종 CLI 요약은 실제 `comparisons`에서 N01을 확인한다.

## 재현과 압축 보존

현재 파일을 검증하는 읽기 전용 명령:

```sh
python -B tools/discovery_loop.py next reviews/course-discovery-20261111/runs/baseline-wave-01/session.json --root .
python -B tools/discovery_loop.py report reviews/course-discovery-20261111/runs/week02-candidate-02/session.json --root .
python -B tools/discovery_loop.py report reviews/course-discovery-20261111/runs/week01-bridge-02/session.json --root .
python -B reviews/course-discovery-20261111/archive_snapshots.py verify
python -B reviews/course-discovery-20261111/archive_snapshots.py verify --tag bridge
python -B reviews/course-discovery-20261111/archive_snapshots.py verify --tag cli-reports
python -B reviews/course-discovery-20261111/archive_snapshots.py verify --tag bridge-final
python -B reviews/course-discovery-20261111/archive_snapshots.py verify --tag cli-reports-final
```

원본이 같은 SHA인 경우 **새 실행 이름**을 써서 다시 생성할 수 있다. 이미 있는 실행 폴더를 덮어쓰지 않는다.

```sh
python -B reviews/course-discovery-20261111/run_review.py baseline --run baseline-replay-02
python -B reviews/course-discovery-20261111/run_review.py plan --run plan-replay-02
python -B reviews/course-discovery-20261111/run_candidate.py --run week02-replay-03 --expected-sha 52b5c170ab2c83fc29327c302e9c77e34c58bce81061c7a167228d0cc67c36e3
python -B reviews/course-discovery-20261111/run_bridge_review.py --run week01-bridge-replay-03 --expected-sha 6241f6bce0db5b2dfe40dc672a0706a09d7228d2aea451cd1a03b05847f910c4
```

이 스크립트는 기록된 실제 웹 읽기를 다시 검색하지 않는다. 새로운 원문·판본을 확인하는 일은 별도 행위이며 기존 메모만 재생해서 최신 자료를 재확인했다고 말할 수 없다.

| 보관본 | 보존 내용 | 원본 → 압축 바이트 |
|---|---|---:|
| [state-snapshots.tar.gz](state-snapshots.tar.gz) | 118개 `session-NN.json`, 실패 실행의 중간 상태 포함 | 40,640,766 → 3,759,466 |
| [state-snapshots-bridge.tar.gz](state-snapshots-bridge.tar.gz) | 1주 보충의 추가 16개 중간 상태 | 500,900 → 45,945 |
| [cli-report-replays.tar.gz](cli-report-replays.tar.gz) | `checks/final-01/02`의 중복 CLI report stdout+parsed JSON 7개 | 21,590,781 → 3,679,903 |
| [state-snapshots-bridge-final.tar.gz](state-snapshots-bridge-final.tar.gz) | 최종 1주 보충의 추가 16개 중간 상태 | 515,038 → 46,931 |
| [cli-report-replays-final.tar.gz](cli-report-replays-final.tar.gz) | `checks/final-03`의 중복 CLI report 영수증 5개 | 11,214,818 → 1,883,501 |

각 manifest(`snapshot-archive-manifest*.json`, `cli-report-archive-manifest*.json`)에 모든 상대 경로·원래 바이트 수·개별 SHA와 archive SHA를 남겼다. 정렬 경로, USTAR, uid/gid/mtime 0, 고정 mode, 빈 gzip 이름·mtime 0, level9로 원래 바이트를 재직렬화 없이 압축했다. 완성 아카이브의 모든 파일을 다시 읽어 원래 해시·길이·목록을 확인한 뒤 **그 목록의 중복 펼침 파일만** 제거했다. 최종 `runs/*/session.json`, `report.json`, `manifest.json`, 이벤트·실패 이력·출처·투영·현재 요약은 그대로 펼쳐 있다. 임시 `.tmp`/`.pyc` 파일은 없다.

`checks/final-01`은 1주 보충 추가 이전, `final-02`는 최초 보충까지 포함한 시점, `final-03`은 최종 보충과 그 이전 세션의 stale 판정까지 포함한 최종 조회다. 이전 판정을 숨기거나 수정한 파일이 아니라 각 시점의 실제 세션을 CLI로 다시 읽은 영수증이다. 권위 있는 판정은 `runs/*/report.json`과 이벤트 사슬이며, CLI report 중복 영수증은 아카이브에서 원바이트로 복원할 수 있다. 개별 내용을 읽으려면 `tar -xOf <archive> <manifest의 상대 경로>`를 사용한다. 기존/현재 report의 의미 차이는 교안 산출물·선택 범위·요구 보존 여부이며, 압축이 의미를 바꾸지 않는다.

## 남은 실제 일

국내/국제 2027 적용 관계와 HTTP 429로 못 읽은 최신 PDF 차이를 확인한다. Pixel 경계·출력 세부 허용, 실제 모델/추론 환경과 시간·대회 데이터 성능은 미검증이다. 후속 실제 주차 교안에서 원래 넓은 요구를 이어서 비교하고, 독립 새 입력의 학생 답·도움·시간 기록을 수집해야 한다. 자동 상태 검사, 수동 원문 의미 판정, 실제 학습 목표 달성은 계속 별개로 남는다.
