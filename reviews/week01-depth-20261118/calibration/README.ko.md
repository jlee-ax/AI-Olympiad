# 새 교안의 적정 깊이를 판정한 블라인드 비교

**교안 심의 11건에서 스킬을 받은 검토자와 받지 않은 검토자가 각각 11건을 모두 맞혔다. 이 표본에서 관측한 개선폭은 0%p다.** 두 검토자 모두 올바른 편집안을 고르고 새 입력의 결과를 구했으며, 구체적인 근거와 편집 결정을 제시했다. 별도의 도판 색인 요청도 양쪽 모두 원문 순서로 처리했다. [사전 고정한 조건](protocol.ko.md) · [팔 공개 전 개별 판독](blind-adjudication.json) · [NVIDIA 외부 비교 보고서](external/native-import/external_metrics.md)

## 무엇을 심의했나

2027 KOAI 중등부를 준비하는 10주 과정에서 Python 기초만 배운 학생을 상정했다. 새 사례에는 실제 학생용 활동을 본뜬 두 편집안, 그 주의 선수·목표·시간, 독립적으로 계산할 새 입력이 있다. 1주차 5건과 2·3·4·5·7·8주차 각 1건이다. 같은 집계 코드에 목적만 바꾼 1주차 두 건은 하나의 문제군이다. 따라서 서로 다른 교안 문제군은 10개다. 사례 문구·기준답·편집 원칙의 해시는 답변을 받기 전에 고정했다. [배부한 문제](blind/packets.json) · [동결 해시](frozen-sha256.json) · [기준답](answer-key.json)

공식 국내 안내가 연결한 실라버스는 IOAI 2026을 기준으로 삼는다. Python·데이터 처리·시각화는 실전, kNN·k-means·합성곱·손실 함수는 이론과 실전 항목이다. 날짜에 맞는 특징, 유효 토큰과 padding의 구별은 해당 주차의 처리·해석 과제에 맞췄다. 주차·분량·각 사례의 채택 결정은 이 과정의 편성 판단이다. [KOAI 2027 안내](https://kitpa.org/koai/2027) · [국내 출제 기준](https://kitpa.org/koai/syllabus) · [10주 과정표](../../../curriculum/student-plan.html)

| 심의 조건 | 두 검토자가 실제로 낸 판정 |
| --- | --- |
| 필요한 선수 설명을 지운 안 | 4주에는 거리순으로 이웃을 정렬한 뒤에 같은 점의 반을 찾아야 했다. 두 검토자는 두 개의 독립 정렬 목록을 기각하고, 새 질의에서 k를 1에서 3으로 바꿀 때 red에서 blue로 뒤집히는 이유를 설명했다. |
| 지나치게 깊은 필수 과제 | 7주에는 6×8 입력에서 유효 창을 세어 출력 2×3을 구했다. 두 검토자는 15분짜리 적용 활동에 추가한 특이값 증명을 필수 경로에서 뺐다. |
| 다른 표현으로도 충분한 수업 | 1주의 개별 관측 점그림 두 가지, 8주의 mask로 유효 행을 선택하거나 가중합으로 구하는 평균 두 가지를 모두 인정했다. 실제 0을 분모에 포함해 평균이 2로 유지됐다. |
| 두 쪽 모두 고쳐야 하는 수업 | 5주의 군집 색 옮겨 쓰기와 일반 수렴 증명 선결 조건을 모두 기각했다. 두 검토자는 한 번 배정·갱신한 중심 2와 10을 구하고, 좌표를 바꿔 손계산과 코드로 확인하는 활동을 제시했다. |
| 코드가 같고 보고 목적만 다른 수업 | 교실을 같은 확률로 뽑으면 방문 한 건을 추가해도 평균은 6→6분이다. 방문 건을 같은 확률로 뽑으면 4→3.6분이다. 두 검토자 모두 질문에 따라 반대편 코드를 골랐다. |

두 검토자는 새 대화에서 같은 순서와 과정 자료로 한 번씩 답했다. 같은 모델 설정(gpt-6.2-astra, max)을 요청했으며, 처치군만 개정 평가 스킬과 초보자 깊이 지침을 읽었다. 실제 서버 측 모델, 사용 토큰과 지연시간의 일치는 측정하지 않았다. 사례 제작자가 양쪽의 설명을 J·R로 읽은 뒤 개별 판정과 원문 해시를 고정했다. 이후 J가 대조군, R이 처치군임을 공개했다. [조건 공개 기록](arm-map.json) · [대조군 답변](reader-J.json) · [처치군 답변](reader-R.json)

## NVIDIA에서 실제로 실행한 단계

| 실행 | 결과 |
| --- | --- |
| 공식 원본 설치와 데이터 엄격 검사 | NVIDIA SkillEvaluator 1.0.1의 동결된 커밋과 uv.lock, Harbor 0.25.0을 사용했다. `tier3 validate --strict`의 5개 검사가 통과했다. 12개 사례에 기대 결과와 단언이 있었고, 내장 수량 조건인 10개·비호출 1개를 충족했다. [원본 리비전](https://github.com/NVIDIA/SkillEvaluator/tree/e3ede733f4d57578a1630b0579ea236b8cf8a727) · [실제 출력과 스킬 파일 해시](native-strict.json) |
| 당시 두 팔용 Harbor 과제 생성 | 원본 생성기가 12쌍, 총 24개 작업을 만들었다. 각 팔에 들어간 공통 파일 40개는 바이트 단위로 일치했다. 대상 스킬은 처치군에만 있고 정답·채점기는 verifier 영역에 있었다. 독립적인 사전 입력 심사 서명은 없어 프로젝트 표시는 `provisional`이다. 두 팔의 24개 실제 디렉터리마다 `material_revision`, `quality`, `workflow`, `discovery_loop`, `topic_depth`, `topic_depth_basis`가 해당 작업의 도구 폴더에서 로드됨을 별도로 확인했다. [준비 결과](native-preparation.json) · [공통 파일과 모듈 로드 확인](external/fixture-check.json) |
| Harbor 에이전트 실행 준비 진단 | 원본 `tier3 doctor`가 모델 공급자 미설정을 보고했다. Docker Compose 실행 파일이 없고 local 모드에서는 bubblewrap의 NETLINK_ROUTE 검사가 거부됐다. **네이티브 에이전트 실행 0회, 기본 모델 채점 0회**다. [런타임 진단](native-runtime.json) |
| 실제 외부 답변을 생성된 채점기로 재검산 | 공식 `custom_grader_runner.py --mode custom_only`로 실응답 24건을 재생해 선택·새 입력 필드가 모두 일치했다. 별도 대조에서는 오선택 0점, 오계산 0점이었다. 선택과 수치가 맞고 근거·편집이 빈 응답은 이 자동 점수에서 1점을 받았다. 의미 판독에서는 탈락하는 사례다. 독립 산식으로 새 입력 값 12개도 재계산했다. [실행 기록](external/replay.json) |
| 외부 측정치 합산 | 원본 `tier3 import-metrics`에 교안 11쌍의 실제 외부 판독 결과를 넣었다. 두 지표 모두 양쪽 1.0000, 짝 차이 0.0000이었다. 원본의 `executed_by_skillevaluator`는 false이고 공식 종합점수와 발행 판정은 부여되지 않는다. [원본 JSON](external/native-import/external_metrics.json) |

이번 점수의 대상은 주어진 활동의 적정 깊이를 판단하고 구체적 편집안을 내는 일이다. 사례는 비교 목적이 선명한 짧은 활동이고, 한 쪽당 하나의 검토 세션만 사용했다. 채점자가 문제 작성자이기도 해 대체 해석에 대한 다른 교육자의 확인은 포함되지 않았다. 양쪽 모두 만점을 받았으므로 어려운 활동에서의 효과·두 조건의 등가성·일반적인 수업 품질의 개선폭을 추정할 수 없다. 공개 후 같은 문제로 얻는 결과는 공개 개발 과제에 대한 결과로 취급한다.

## 배포 후보의 실행 환경 재검수

블라인드 답변을 받은 뒤 작업 흐름과 품질 검사가 수정되어 새 배포 후보에서 별도의 Harbor 작업 12쌍을 다시 만들었다. 당시의 공통 파일 40개와 검사 결과는 원래 경로에 보존했다. 배포 작업에는 일반 명령 안내서를 더해 공통 파일 41개가 들어간다. 24개 작업마다 프로젝트 도구 모듈 11개와 NVIDIA가 생성한 verifier 모듈 13개를 해당 작업 디렉터리에서 로드했다. 프로젝트 도구의 로컬 import 경로와 일반 안내서 링크를 확인했다. 신규 교안, 교사용 자료, 회차별 심의 및 풀이 파일은 공통 입력에서 제외했다. [배포 후보의 원본 엄격 검사](release-packaging/strict.json) · [작업 준비 결과](release-packaging/preparation.json) · [모듈·자료 해시](release-packaging/fixture-check.json)

배포 작업에서 원래 답변 24개를 같은 채점기로 다시 읽었을 때 개별 결과와 외부 지표 입력은 이전 결과와 바이트 단위로 일치했다. 공식 외부 지표 보고서에서는 생성 시각만 달라졌다. 이 확인에서 추가로 수집한 모델 응답은 0건이다. 원래 두 검토자에게 배부한 과정표·계약·처치 지침과 원래 의미 판정도 같은 해시를 유지한다. [이전·배포 파일 및 재생 비교](release-packaging/comparison.json)

## 재현

고정된 공식 원본에서 `uv sync --frozen --no-dev --no-editable --extra all`을 실행하고 해당 가상환경을 활성화한다. 공개된 KOAI 저장소의 이 리비전을 작업 디렉터리로 삼아 다음을 실행한다.

```sh
case_dir=reviews/week01-depth-20261118/calibration
storage=$(mktemp -d)
python -B tools/skill_evaluation.py prepare koai-evaluate "$storage/tasks" \
    --suite "$case_dir/native-suite.json" --pilot
python -B "$case_dir/reproduce.py" "$storage/tasks" "$storage/replay"
```

재생 도구는 동결된 입력·스킬·원본 Python 소스·채점기 해시를 확인하고 공통 자료를 기록된 당시 또는 배포 후보의 해시와 대조한다. 24개 작업의 프로젝트·verifier 모듈을 각각 격리된 Python 프로세스에서 읽는다. 새로운 임시 경로에 `replay.json`과 원본 외부 합산 보고서를 쓴다. 기관이 허용한 에이전트·judge 모델과 실제 작동하는 Docker 또는 격리된 local 실행기가 있는 경우에만 기본 지표를 포함한 네이티브 실험을 실행할 수 있다. 새 비교에는 공개 전 별도 심사를 거친 새 사례를 써야 한다. [NVIDIA 실행 안내](https://github.com/NVIDIA/SkillEvaluator/blob/e3ede733f4d57578a1630b0579ea236b8cf8a727/docs/tier3-run-reference.mdx) · [외부 측정치 가져오기 계약](https://github.com/NVIDIA/SkillEvaluator/blob/e3ede733f4d57578a1630b0579ea236b8cf8a727/docs/custom-graders.mdx#import-precomputed-custom-metrics)
