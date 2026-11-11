# 1주 통합 교안 독립 검토

최종 후보 `15ab0101…`는 사전 고정한 내용·실행 기준을 충족했다. **현재 재현된 차단 결함은 없다.** 이는 합성 예제의 실행·계산·설계 검토이며 학생의 독립 성취·실제 부담·후속 10주 완수를 입증하지 않는다.

## 검토 입력과 기준 고정

- notebook: `lessons/week01/week01_integrated.ipynb` — `15ab0101edbca3c0c669e551cb723b401d168d9730523fa1ac1263a0d7538120`
- HTML: `53b48bf8370cff4f97ace9f78cbf8c5b838f7c758a56b86ef82d474003470596`
- teacher: `aafa8f3bbd6cc7b88131157d85a9ffa5d99d5e1b53db6abe2f021eaa2096bcdd`

새 후보가 없고 읽지 않은 2026-11-11 09:57:52 UTC에 `criteria-v1.md`와 `input-manifest-v1.json`을 고정했다. 해시는 각각 `405ba02653f5890d091ef3161a42a9f89dc8ecac44522e880b2be971bea06634`, `4ac9ea156f8b765cd035c52a3b506a3a365acbd910c044873d7fd5849e67fc7e`다. 기존 89셀 본문·29셀 bridge·27셀 pipeline 전체와 10주 계획을 읽었고, 별도 사용자 worktree의 실제 미커밋 변경도 읽었다.

계획의 1주 진입점 변경은 `criteria-addendum-01.md`로 허용 범위를 구분했다. 새 계획의 구 pinned baseline은 stale이며 기존 통과를 새 파일의 승인으로 옮기지 않았다. 이후 사용자 미커밋 원문을 새로 공개하지 말라는 부모 지시에 따라 이번 리뷰에 만든 원문 복제 3개만 제거했다(`privacy-copy-removal.json`, addendum 02). 기존 사용자 원본·기존 보존 사본은 그대로다. 이후 근거는 경로·SHA·필요 범위 요약만 사용했다.

## 내용·단일 학생 경로

같은 합성 화분 표가 CSV→관측 평균 함수→축/모양→산점도→고정 높이식→높이 12cm 이상 분류→훈련 전용 대체/중심 학습→검증→ID/실제 CSV로 이어진다. 첫 모델은 water_ml 한 열만 쓰는 기준 모델이다. 고정 계수의 높이 예측과 자료에서 배운 중심 분류를 구별하고, 연속 높이에서 이진 판정으로 질문이 바뀐 점도 설명한다. 따라서 단순 링크를 단 네 번째 보충 문서로 판단하지 않는다.

기존 필수 연습은 제거하지 않았다. 학생 cell33은 별도 새 커널·필수 준비 셀·해당 제목·작성 칸·복귀 위치를 안내한다. 상세 매핑은 `static-and-goal-mapping.json`에 10개 목표별로 남겼다.

| 필수 목표 | 통합본과 남은 실제 평가 위치(0-based 셀) |
|---|---|
| Python 상태·return·오류·새 함수 | 통합 5–6; 본문 14–25, 80–82의 진단·traceback·shifted_mean·recorded_mean |
| CSV·dtype·0/결측·더러운 값·새 열 | 통합 1–6; 본문 42–44의 `20ml`, 53–55의 새 CSV, 77–79 집계·병합·키 경계 |
| 평균·분산·원리·단위·분모 | 통합 5–8; 본문 5–8의 기호/유도, 47–48의 ddof, 67–68의 새 분산·이동/배율 |
| axis·reshape·전치·broadcast | 통합 9–12; 본문 60–66의 같은 shape 반례·행/열 보정·오류 |
| 그래프·분포·범주·해석 | 통합 13–14; 본문 53–55·67–76의 새 입력과 Matplotlib/Seaborn 실습 |
| 내적·순서·행렬 수축·ID | 통합 15–16·25–28; 본문 83–86과 bridge 20–27의 필수 A/B |
| 실제 fit·검증·새 명세 | 통합 17–32; 29–32의 문자열 라벨·미상 `?`·요구 ID 순서와 빈 학생 답안 |

정확한 문제 숫자를 유지하는 것과 목표를 보존하는 것은 구분했다. 학생이 아직 수행할 함수·새 CSV·그래프·배열·bridge A/B 과제를 실제 모델 fit 한번으로 완료 처리하지 않는다. 평균·분산의 긴 유도는 원문 필수 경로로 남는다. 핵심 34셀만으로 전체 1주 독립 과제가 완료되는 자료는 아니다.

새 본문은 34셀/16코드, source 16,804자다. 기존 세 파일 source는 각각 37,130/12,227/17,175자다. 이는 **주 설명 경로를 다시 쓴 크기 비교**이며 총 학습량이 그 비율로 줄었다는 계산이 아니다. 남은 필수 연습·오류 수정·스스로 작성량을 합한 실제 시간은 모른다. teacher는 기존 120분·5–7시간이 새 범위의 완료 근거가 아니며 총 부담·지원 필요가 미관찰임을 밝힌다.

학생 notebook/HTML에는 시간 배정·교사 운영·실측 문구가 없다. 실행 방법·예상/이유·오류 탐색·도움 기록은 학습 지시로 남는다. 2주 fit/지표, 3–5주 함수·거리·분산, 6주 shape/가중합, 7–9주 ID/표현·검색, 10주 새 계약의 재사용처를 설명하며 후속 실습 완료로 세지 않는다.

## 전체 실행·독립 계산·다른 모델

각 사례는 **별도 Python subprocess의 새 in-process 커널**에서 실행했다. 같은 프로세스에서 여러 커널을 재생성하지 않았다. worker는 쓰기/삭제 경로를 이번 independent 폴더로 제한하고 원본 source SHA를 확인한다. 일반 소켓 커널·브라우저 file URL 정책은 우회하지 않았다.

최종 34셀 중 코드 16셀을 순차 실행해 저장 표·문자 출력·PNG와 일치함을 확인했다(`cases/candidate-15ab-main-oracles/result.json`). 학생 cell32는 주석뿐인 AST와 빈 출력이며, 빈 셀 실행은 학생 과제 수행으로 세지 않았다.

독립 list/Fraction 계산과 새 입력 bank로 다음을 확인했다.

- CSV 관측 물 0/20/40/10/50의 평균 24. None·NaN·0·빈 목록·전부 미상·길이 10,000·±1,000,000 경계에서 명세대로 작동한다. 입력을 변경하지 않는다.
- 높이 평균 10·분산 8/3, 축 평균 [11/3,11/3]/[2,3,6], reshape/전치의 실제 값이 맞다. 새 배열에서도 축·배치·행/열 broadcast·실패 shape를 독립 계산과 대조했다.
- 훈련 P01~P04의 대체값은 20, 중심은 10/30이다. 검증 P05/P06의 예측 [0,1], 실제 [1,1], 정확도 1/2다. 전체 관측 평균 24를 fit에 사용하지 않는다.
- P04 훈련 물 40→60이면 대체값 80/3·양성 중심 130/3, 같은 25ml 예측이 1→0이다. 훈련 y 변경도 학습 중심과 예측을 바꾼다. 검증 특성·정답 변경은 원래 fit 상태를 바꾸지 않는다.
- 한 특성의 훈련·추론을 함께 ml→L로 바꾸면 가까운 중심이 유지된다. 여러 특성의 상대 척도 문제와 구분했다.
- ID별 예측·CSV 헤더·행 수·순서를 확인했다. 형식이 맞는 상수 출력도 있을 수 있어 형식 통과와 모델 provenance/성능을 따로 검사한다.

새 기기 문제는 `정상/점검/?`, signal 한 특성, 출력 `sample_id,prediction`, 요구 순서 N7/N3/N1으로 바뀐다. 알려진 T1~T4만 사용한 평균 2, 선택적 중심 정상=1·점검=3, 검증 2/3과 teacher 예시 CSV가 일치했다. 별도 reviewer 구현에서 가까운 중심과 결정트리를 각각 실제 fit하고 CSV를 써서 재읽었다. 추가 입력 signal=1.5에서는 중심은 정상, 트리는 점검으로 서로 다른 예측을 내며 각 학습 구조와 계약에 따라 수용된다. teacher는 중심 예측을 모든 모델의 정답으로 강제하지 않는다. 이 reviewer 구현은 학생의 빈 답안을 채우거나 학생 수행 증거로 사용하지 않았다.

## 후속 경로 9개

`followup-path-results.json`에 각 파일 SHA·원본 셀·입력·oracle·프로세스 결과를 남겼다. 원본 준비 3→27→54와 각 과제 제공 코드를 새 subprocess에서 실행했다. 원래 `sunlight_hours`·합성값을 다시 만들고 통합본 `light_h`·변경값과 섞지 않았다.

| 별도 실행 경로 | 결과와 남은 학생 작업 |
|---|---|
| Python 진단/함수 | 준비 및 제공 함수 실행 통과; shifted_mean 작성 미수행 |
| 통계/ddof | NumPy·pandas 분모 비교 실행 통과; 새 손계산 미수행 |
| dirty CSV | `20ml` 입력 준비·원본 보존 통과; 학생 정리 코드 미수행 |
| 과제 A | reshape/broadcast 제공 예제 실행 통과; 빈 61·66 미수행 |
| 과제 B | Matplotlib·Seaborn 제공 그림 실행 통과; 학생의 새 분포/범주 그림 미수행 |
| 과제 C | new_plants/site_notes 입력 준비 통과; 학생 집계·병합·키 반례 작성 미수행 |
| 과제 D/E | 빈 함수 칸·제공 내적 예제 실행 통과; 새 함수/단가 순서 풀이 미수행 |
| bridge A | 준비2·입력21·빈23 실행 통과; 학생 새 변환 풀이 미수행 |
| bridge B | 준비2·입력25·빈27 실행 통과; 학생 새 검색/ID 풀이 미수행 |

## 변이 13건과 물리 I/O의 별도 판정

정상 대조군이 통과한 뒤 각 변이를 새 subprocess에서 실행했다. 원본 입력과 실패 결과를 보존했다(`mutation-inputs/`, `mutation-results.json`).

- 교안 자체 검사 9건: NaN 누락 처리 제거, 실제 0 제외, 전부 미상 평균0, 전체 행 fit, target 입력, 훈련 y 뒤집기, 훈련 변화 무시, 출력 순서 오류, reshape를 전치로 사용.
- 독립 수치/의미 oracle 3건: 검증에서 imputer 재fit, ID를 둔 채 예측만 뒤집기, CSV index 추가. 이 변이들은 교안 셀 실행만으로는 통과하며 검토자의 별도 검사가 잡는다.
- 외부 물리 I/O oracle 1건: 실제 result.csv 쓰기/읽기를 StringIO로 바꾸기. **노트북과 숫자 oracle은 통과했다.** 그러므로 raw result는 `status=passed` 그대로 보존했다. 이것을 교안 자체가 잡은 실패로 세지 않는다.

물리 변이는 `physical-io-followup.json`에서 후속 판정했다. 별도 새 대조군은 `phase=notebook`, 파일명 `result.csv`의 write/read가 있었다. 메모리 변이는 같은 단계의 result.csv 이벤트가 0건이었다. 두 경우 reviewer oracle이 만든 `reviewer-answer.csv`의 write/read는 `phase=reviewer_oracle`로 구분해 **학생 예제 파일 I/O 근거에서 제외**했다. 첫 raw 결과 SHA `51644b134ab2062d1872f999070d283673132dd71478ca9146c588c3d2d92beb`는 후속 전후 동일했다. 외부 판정이 요구한 물리 계약 위반을 검출한 것이며 notebook 실행 실패가 아니다.

## 이전 후보의 실패와 수정

09da… 후보는 전체 코드 실행은 통과했지만 ‘임의 유한 수’ 함수 계약이 `[1e308,1e308]`에서 inf를 내는 결함이 있었다. 저자 수정이 시작돼 옛 SHA 직접 재현의 전제조건이 실패한 사실도 `candidate-09da-overflow-precondition-failed.json`에 보존했다. 당시 전체 실행에서 캡처한 원문 셀2/5/6을 별도 입력으로 묶어 결함을 재현했다. derivative의 별도 SHA·원본 실행과의 관계·raw oracle_error는 `candidate-09da-overflow-source-binding.json`과 사례 폴더에 남겼다. 옛 후보를 승인한 것으로 기록하지 않았다.

15ab…는 수치 알고리즘의 전 범위 overflow를 해결한 것이 아니라 **정상 입력을 길이 0~10,000·관측값 ±1,000,000·bool 제외로 제한해 계약을 바로잡았다.** 새 범위 경계는 실제 검증했다. 1e308 입력은 새 계약 밖이며 여전히 보장하지 않는다. 이전의 필수 dirty/원리/ddof 매핑, 다른 노트북 준비 셀·복귀, 단위 설명·후속 주차 연결도 수정됐다. 기존 코드와 저장 출력은 원문 대조 결과 동일했다.

## 진입 경로·범위·보존·남은 한계

현재 계획의 1주 링크가 통합 notebook을 가리키며 로컬 대상과 후속 세 링크가 존재한다. 계획 변경은 1주 진입점과 옛 시간 추정 한계 안에 있고 2–10주 나머지 내용은 같다. 이는 원격 공개 배포를 확인하거나 수행했다는 뜻은 아니다. 기존 3교안·2주 파일·보존 사용자 원본 6개는 사전 SHA와 일치했다.

정적 HTML은 fresh export와 바이트 단위로 같고, 저장/새 산점도 PNG도 같다. 산점도 PNG는 직접 열어 ID·좌표·범례·단위·표식·글자/축 범위를 확인했다. 브라우저 전체 HTML 배치·일반 Jupyter/Colab은 미검증이다.

[KOAI 2027 안내](https://kitpa.org/koai/2027)가 연결한 [실라버스](https://kitpa.org/koai/syllabus)는 확인 시 IOAI 2026 기준이었다. [Antique 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb)의 5특성·미상 입력 활용·무헤더 CSV/ZIP과 이번 교육용 합성을 구별한다. teacher의 [Robot Chasing 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md) 연결도 현재 제공 snapshot의 8×8×2 범주 채널·ID/방향/지시/운반 물체와 과거 입력이 없는 조건을 읽는 선수 설명이다. 이번 교안이 그 모델/국제 과제를 구현했다고 하지 않는다.

공개 teacher 파일 분리는 접근 통제가 아니며 실제 보호된 최종 숨은 테스트는 생성·실행하지 않았다. 학생의 독립 코드·설명·도움·실제 소요 시간·후속 전이는 관찰하지 않았다. 합성 코드의 실행 통과나 정상/오류 변이 검출을 이런 성취로 바꾸어 주장하지 않는다.

재현은 이 폴더의 `execute_case.py`를 사용한다. `run_followup_paths.py`, `run_mutations.py`, `check_static_and_mapping.py`에 exact 입력·SHA·명령이 있다. 기존 case 이름 덮어쓰기는 거부하므로 재실행할 때 새 case 이름 또는 격리된 새 리뷰 디렉터리를 사용한다. 각 case의 source/실행 notebook·raw result·stdout/stderr를 확인할 수 있다. worker의 이전 계측 버전도 `execute_case-before-phase-audit.py`로 보존했다.

runtime·history.sqlite·pyc·실제 임시 CSV와 생성 HTML 사본을 남기지 않았다. 이번 허용 independent 경로만 작성했고 교안·다른 검토 경로·git index·commit·remote는 수정하지 않았다.
