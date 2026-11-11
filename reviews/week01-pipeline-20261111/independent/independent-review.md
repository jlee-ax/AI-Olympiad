# 1주 문제 해석 → 학습 → 제출 교안 독립 검토

최종 후보 **통과, 현재 차단 결함 없음**. 이는 아래 합성 입력의 실행·수치·명세 검토 결과이며 학생의 독립 성취나 대회 문제 해결을 입증하지 않는다.

- 학생 notebook: `lessons/week01/week01_problem_pipeline.ipynb`, SHA-256 `f64a54c8f8eeb995fa8b85fc565836c5e66a97249f97177644cb15ad8f88997a`
- HTML: `28308deb024292977cd22a2931801ff242f010e5b6e8b4de01fa4e01e3a4bfd3`
- teacher: `646c9e4bbd6b631864f2e802b3cfb9f38da39ee6b7db79cef6a431ee6a7eb589`
- 기존 bridge: notebook `09efa4d1a8ebf918dab7fc0b30f60f8130e817729d70cfe93cd7c60f15b5767f`, HTML `45bc5fe99f90b7bd4dd39ef67557b87c227f263e59e20c54fa1d44764a07239b`

## 기준과 입력의 사전 고정

`criteria-v1.md`와 `input-manifest-v1.json`은 새 교안 경로가 없고 내용을 읽지 않은 2026-11-11 08:52:03 UTC에 고정했다. 기준 SHA는 `164f0e760ba368641bfe8030f140233cc22a0b5e8b60305e6837ed98bd137993`, manifest SHA는 `874370699ae93ab91b4450939896561b38676f8e1f072c4b2f88b096af56e459`다. 부모의 물리 ZIP 쓰기·자유로운 분류기 요구는 원 기준을 덮어쓰지 않고 `criteria-addendum-01.md`에 추가했다. 교사용 키를 읽기 전에 `manual-centroid-oracle-v1.json`에 별도 목록·합·분수 손계산을 저장했다.

1주 본교안 89셀, 배열 bridge 29셀, 2주 기존/시계열 교안, 10주 계획 및 [KOAI 2027 안내](https://kitpa.org/koai/2027), [연결 실라버스](https://kitpa.org/koai/syllabus), [Antique 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb)·공식 채점 코드, sklearn 문서를 읽었다. 본교안·2주 두 파일·계획·기존 teacher의 사전 해시는 유지됐다. 새 자료가 기존 2주의 고정 `z>=1` 또는 합성 시계열 점수를 학습된 분류 모델로 잘못 묘사하지 않는다.

## 실제 실행과 계산

`run_pipeline_review.py`를 지정 venv Python에서 실행했다. Python 3.12.14 / NumPy 2.5.4 / pandas 3.1.1 / sklearn 1.8.0. 일반 소켓 커널 대신 새 **in-process 커널**에서 27셀 중 코드 12셀을 순차 실행했고 모든 저장 출력과 다시 계산한 출력이 일치했다. 빈 학생 코드칸도 주석뿐인 AST·빈 출력임을 확인했다. 실행 사본은 `independently-executed.ipynb`, 기계 판정은 `validation-results.json`이다.

| 핵심 시나리오 | 독립 확인 결과 |
|---|---|
| 실제 훈련 | 알려진 T1~T4 평균 `[5,3]`, 중심 −1=`[2,2]`, +1=`[8,4]`가 분수 구현과 일치. T4 특성 또는 T3 라벨을 바꾸어 별도 fit하면 같은 `[5.25,3]` 예측이 +1→−1로 달라진다. |
| 미상과 fit 경계 | 주 예제 0은 미상, 독립 문제 −1은 미상. 미상 행 특성 극단 변경과 검증 특성·라벨 변경은 원래 fit 통계·중심을 바꾸지 않는다. 알려진 라벨만 사용하는 단순화는 공식 Antique의 미상 입력 활용 요구와 구분된다. |
| 특성·ID·정답 | 이름으로 정한 특성만 선택. 열 순서 변경과 label/나중 검사 열 추가가 예측에 끼어들지 않는다. A/B 공동 행순열 12가지에서 ID별 예측과 요구 순서가 유지된다. |
| 누락 ID | None/NaN/pd.NA/빈 문자열/공백의 요구 ID·예측 ID·실제 입력 경로 20건을 거부. 정상 문자열·정수 ID는 허용. 이전 helper 단독 누락 ID 허용 결함이 수정됐고, 실제 `predict_pairs` 경로와 helper 단독 경계를 각각 검사했다. |
| 파일 경계 | 실제 임시 `submission.zip`의 디스크 쓰기·재읽기를 계측했고 동일 바이트를 확인했다. 두 무헤더 한 열 CSV 이름·라벨·개수·ID 대응 순서가 일치한다. 종료 후 파일·임시 디렉터리가 제거됐다. 공식 서버 제출이나 원문 submission.ipynb 실행은 하지 않았다. |
| 오류 출력 | 순서만 다름·헤더·index/추가 열·행 누락/추가·0/확률·파일명·추가/중복 ZIP 구성원·비ZIP 11건을 별도 ZIP 생성기로 주입해 거부했다. |
| 형식과 성능 구분 | 상수 −1 출력도 형식은 통과한다. 오염된 대응표와 일치하게 만든 CSV는 형식 검사만으로 발견되지 않는다. 별도 모델/ID 계보 oracle은 이를 검출했다. 학생 설명도 이 한계를 밝힌다. |
| 독립 새 명세 | 3특성의 알려진 R1~R4 평균 `[4,4,2]`, 선택적 중심 `[1,3,1]`/`[7,5,3]`, 검증 `[0,1,1]`·2/3, J3/J1/J2 예측 `[1,0,0]`가 손계산·교사용 예시 코드와 일치한다. |
| 여러 타당한 모델 | 중심 분류와 Gaussian Naive Bayes를 각각 훈련. 검증 예측은 `[0,1,1]`와 `[0,1,0]`으로 달라도 각각 자기 모델의 학습값과 0/1 계약에 따라 처리한다. 두 모델 모두 실제 `audit.csv`를 써서 헤더 `item,signal`·입력 ID 순서·3행·허용값을 재읽기 확인했다. 작은 표의 2/3·3/3은 현실 성능 비교가 아니다. |

`check_new_contract.py`는 새 CSV 계약 반례 7건과 예전 라벨 mask를 그대로 복사하는 반례 1건을 별도로 검출했다(`new-contract-results.json`). 교사용 들여쓴 예시 코드도 실제 실행해 수치·직렬화 결과를 대조했다. 교사용 예시의 재읽기는 StringIO이며, 물리 audit.csv 재읽기는 **검토자의 별도 구현**에서 확인한 것이다. 학생이 이 과제를 수행했다는 증거로 사용하지 않는다.

## 소스 변이 13건과 검토 harness 교정

유효 결과는 **`mutation-results.json`**이다. 변이마다 별도 Python 프로세스를 시작해 새 in-process 커널에서 실행했다. 각 입력은 `mutation-inputs/`에 보존했다. 변경 전 부분·변경 내용·실패 셀과 원인을 JSON에 기록했다.

- 미상 0을 음성으로 학습, 정답을 특성에 포함, 훈련/검증 혼합 fit, 평균 대신 상수 대체, 훈련 라벨 뒤집기: 셀 5의 통계·중심 검사에서 검출.
- 검증 재fit: 셀 11, ID 대신 위치 순서: 셀 15, 양쪽 누락 ID 검사 제거·0 출력 허용: 셀 21에서 검출.
- 금지 헤더와 ZIP 파일명 오류: 셀 17에서 검출.
- bool을 정수 예측으로 허용하는 변이와 물리 파일 쓰기·읽기를 메모리로 바꾸는 변이는 교안만 실행해서는 통과한다. 각각 **독립 bool oracle**과 **디스크 I/O 계측**이 검출했다. 교안의 자체 assert가 모든 오류를 잡는다고 주장하지 않는다.

초기 harness는 한 Python 프로세스에서 여러 in-process 커널을 순차 생성해 display singleton이 이전 커널을 참조했다. 그때 13건 모두 변이가 작동하기 전 셀 3에서 `AttributeError: NoneType.outputs`로 실패한 결과는 **무효**다. 원본을 `invalid-harness-v1-mutation-results.json`, `invalid-harness-v1-validation-results.json`로 보존했고 `invalid-harness-v1-status.json`에 machine-readable 무효 사유를 적었다. 초기 실패를 교안 검출 성과로 세지 않는다. 별도 프로세스 재검증 결과에는 그 오류가 없으며 실제 변이 위치 이후의 검사 실패만 채택했다.

## 내용·학습 범위·기존 검토의 적용 범위

학생 자료에는 수업/자습 시간 배정·실측·교사 운영 편성 문구가 없다. Shift+Enter, 예측을 먼저 적기, 오류를 예상하기, 독립 문제를 가리고 풀기는 학습 지시로 유지됐다. 예측 시점·훈련 전용 fit·선택 후 최종 테스트·결측 셀과 누락 열의 구분도 유지됐다. ID 순서를 ‘읽기 전에’ 보관한다는 문구는 검토 중 ‘읽은 직후 정렬·변형하기 전에’로 수정됐고 최종 SHA 전체를 다시 실행했다.

선수는 표·평균·Python·행/ID 대응이며 행렬곱/stack/lookup을 필수로 요구하지 않는다. 중심·거리의 수학은 평균과 제곱합으로 따라갈 수 있다. 다만 ZIP, 집합·사전, lambda, 예외 처리까지 초심자가 독립 구현하는 부담은 크다. 제공 helper의 실행·추적과 학생의 독립 구현은 같은 성취가 아니다. teacher는 기존 120분 블록과 기존 필수 목표를 유지하되 이 보충까지 기존 5~7시간에 완료된다는 근거가 없고 총 부담 증가 가능성이 있음을 명시한다. **실제 학생의 수행 시간·이해·독립 전이는 미관찰**이다.

학생 문제와 teacher 모두 다른 타당한 학습 분류기를 허용한다. 특정 중심 예측과 다르다는 이유만으로 오답 처리하도록 하지 않는다. 독립 학생 칸·출력은 비어 있고 공개 학생 HTML에 교사용 독립 답을 넣지 않았다. 그러나 공개 teacher 파일 분리는 접근 통제가 아니다. 실제 보호된 최종 숨은 테스트는 생성·실행하지 않았다.

Antique의 5특성·각 500표본·미상 입력 활용·정확도·공식 제출 규칙과, 교안의 자체 제작 2특성·알려진 라벨 지도학습 및 독립 3특성 문제를 명확히 구분한다. 과거 IOAI 문제를 국내 2027 확정 문제로 취급하지 않는다. 반지도 도구의 −1 미상 sentinel로 옮길 때 Antique의 −1→0, 1→1, 0→−1 및 예측 역대응도 올바르다.

기존 bridge 변경은 마지막 Markdown 셀의 새 pipeline 링크 한 줄뿐이다. 사전 고정 Git HEAD와 모든 코드·출력 셀이 동일했고 원래 문장도 보존됐다. 두 HTML은 현재 notebook을 다시 export한 결과와 바이트 단위로 일치했다. 이전 bridge 전체 파일 SHA 리뷰는 새 파일 SHA와 다르므로 그대로 재사용하지 않는다. **계산·코드·출력에 대한 이전 근거는 변화가 없고, 이번 링크/HTML 변경만 새 SHA로 추가 확인**했다.

## 한계와 재현

일반 소켓 Jupyter·Colab, 브라우저 전체 시각 렌더링은 확인하지 않았다. HTML export 일치·본문과 표의 정적 출력 읽기는 확인했다. 합성 입력의 수치·코드 실행은 실제 학생 성취·일반화·대회 준비 완료를 뜻하지 않는다. 독립 문제의 일부 클래스 내 일정한 heat 값에 대한 sklearn 표준편차 경고가 있으나, 기본 uniform-prior Euclidean 중심 예측은 손계산과 일치한다. Jupyter의 네트워크 인터페이스 탐색 경고도 남았으며 소켓 커널을 시작하거나 제한을 우회하지 않았다.

재현 명령(저장소 루트):

```bash
/workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B reviews/week01-pipeline-20261111/independent/run_pipeline_review.py
/workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B reviews/week01-pipeline-20261111/independent/check_new_contract.py
```

작성·실행은 지정 리뷰 폴더 안에서만 했다. runtime/history.sqlite, 임시 submission.zip/audit.csv와 캐시를 정리했다. 복제 HTML을 남기지 않았다. 교안 파일·기존 리뷰·git index를 수정하거나 commit/push하지 않았다. 남은 실행 차단 요인은 없다.
