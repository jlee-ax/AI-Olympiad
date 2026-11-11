# 1주 시퀀스 교량 · 작성 및 검증 기록

## 범위와 경계

이전 통합본 `b530a36ae4f0b4fe9237fb29d604dc288198df7027c85c2e99d1a2e6f2a41611`과 교량 `de5ba77f7cd1325769ca4af29a8fd9c851d14c8c83d5acb88a127bc277579ef0`을 기준으로, 기존 선택 lookup을 고정 표 조회 → 유효 위치의 개수·합·평균 → 기존 필수 검색 B의 질문으로 연결했다. 필수 A/B, 기존 통합 기기 문제, 원본 A–E와 후속 준비 경로는 유지했다. 교량과 통합 노트북, 각각의 HTML 및 교사용 안내만 교안에서 변경했다. 학생 답안은 빈칸으로 남겼다.

표 `(V,d)`와 ID `(B,T)`에서 조회값 `(B,T,d)`를 만들고, 이 합성 명세의 PAD ID 0인지로 `(B,T)` mask를 만든다. 평균은 유효 위치의 합을 유효 위치 수로 나눈다. PAD 행의 벡터 값과 무관하게 제외하며 실제 토큰의 영벡터는 개수에 포함한다. helper는 정수가 아닌 ID, 음수·상한 밖 ID 및 all-PAD를 거부한다. all-PAD의 평균은 없지만, 유효 영벡터의 평균 0은 정상이다. 그 결과를 코사인에 넣으면 방향이 없어 그 단계에서 별도 오류다. ID 0과 예외 정책은 이 합성 명세의 약속이다.

완성 예제는 `V=6, T=4, d=3`에서 유효 개수 `[2,3]`, 합 `[[2,2,2],[4,4,0]]`, 평균 `[[1,1,1],[4/3,4/3,0]]`이다. 필수 B는 다른 표와 ID를 주고 학생이 직접 Q를 만들게 한다. 정답 예시의 개수는 `[3,2]`, 합은 `[[6,9],[6,4]]`, Q는 `[[2,3],[3,2]]`다. 원시 내적 결과 ID는 `[8,90]`, 코사인 결과 ID는 `[53,90]`이다. PAD 값을 0으로 바꾸더라도 잘못 전체 길이 T로 나눈 Q는 `[[1.5,2.25],[1.5,1]]`이며 코사인 점수와 최종 ID는 옳은 결과와 같다. 따라서 개수·합·평균의 좌표를 확인해야 한다. 원래의 비영 PAD까지 평균하면 Q `[[3.25,5],[5,6.5]]`, 코사인 ID `[53,53]`이다.

고정 벡터의 평균은 토큰 순서를 바꾸어도 같으므로 이 표현으로 순서를 복원하지 못한다. 이는 모든 텍스트 모델의 성질이 아니다. 이 교안의 값은 고정 합성 표이며 학습된 임베딩, 토크나이저, attention 또는 공식 과제 완수가 아니다. 화분 분류에 검색의 행별 정규화를 넣지 않았다. 국제 문제와 전공 자료의 출처·선정 근거는 [사전 원문 대조](../source-prioritization.md)를 보라. 예컨대 [IOAI 2026 Potato 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/3_Potato/statement.md)의 어휘와 벡터 행 대응은 조회의 동기이며 별도의 숨은 표현과 상호작용 과제 전체를 풀지는 않았다. [Find the Order 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/1_Find_the_Order/statement.md)의 시간 순위 출력은 미해결 후속 전이다. 넓은 D07·D08 요구, 실제 attention과 3~10주 전체 구현·숙달을 완료로 판정하지 않는다.

## 최종 교안 SHA-256

| 파일 | SHA-256 |
|---|---|
| `lessons/week01/week01_axes_linear_bridge.ipynb` | `16b797de3935af5e25d6e297cdd8b4c72d7dbb32667ab36b9fb9df36965cd84d` |
| `lessons/week01/week01_axes_linear_bridge.html` | `86ca70620ded9e592a84fba218ab1fed635a6c6f3c451bad1c808fb89fc16030` |
| `lessons/week01/week01_axes_linear_bridge_teacher.md` | `298b385f2cb7dbd4cf2e1bc2aaaac61567638d67ef887eb4e533fbd2aa8eecc7` |
| `lessons/week01/week01_integrated.ipynb` | `487379bf0c9c5fae5877d1eb5ec1414dedabbe2f2634a3827ae224f6e31bc568` |
| `lessons/week01/week01_integrated.html` | `87ef29ccb2362ed6e9a5347d1deefe45d2dafe20537f926f6764ae1cfd567195` |
| `lessons/week01/week01_integrated_teacher.md` | `5004166eabc9231f46ce1c85aac6b08adb602a7d94b6376330101d23f15e4a12` |

## 초기 후보에서 설명 보강까지

처음 후보 `f3f739cf…`의 전체 실행·복제본 결과는 [validation.json](validation.json)과 [portability.json](portability.json)에 그대로 남겼다. 독립 검토와 부모 의견에 따라 함수 앞에 유효 mask → `np.where` → 위치 축 합 → 개수로 나눔을 핵심 계산으로, `dtype=object`·`errstate` 및 유효성 검사를 보조 보호로 구분하는 한 단락을 추가했다. 두 노트북을 다시 별도 프로세스로 실행해 최종 후보를 만들었다. 코드와 학생 데이터는 변경하지 않았다.

[initial-final-comparison.json](initial-final-comparison.json)은 최종 교량의 이 단락만 제거해 초기 notebook SHA `f3f739cf…`를 정확히 재구성하고, 차이가 0부터 센 Markdown 셀 23뿐이며 코드·저장 출력이 같음을 확인한다. 두 검증 결과의 파일별 SHA를 비교했을 때 교량 notebook·HTML 외의 통합본, 양쪽 교사 안내, 원본 자료와 보호 파일도 같았다. 초기 결과는 최종 SHA에 대한 결과로 덮어쓰거나 재사용하지 않는다.

## 실제 실행과 재현

[validation-explained.json](validation-explained.json)은 최종 후보에 대한 다음 실제 명령의 결과다. 네 검증군을 각각 별도 subprocess의 fresh in-process 커널에서 실행했다. 과거 검색 교안 작성 때 관찰한 동일 프로세스 커널 상태 재사용 문제를 피하기 위해 이 방식을 유지했다. 소켓 경로나 환경 정책 우회는 시도하지 않았다.

```bash
/workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B reviews/week01-sequence-20261111/author/validate_candidate.py --protected-worktree /workspace/scratch/d500e5cb2076/ai-olympiad-week01-integration --write reviews/week01-sequence-20261111/author/validation-explained.json
/workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B /tmp/week01-sequence-portability-explained.py
```

같은 의존성을 설치한 다른 체크아웃의 저장소 루트에서 후보 검사를 반복하는 명령은 아래와 같다. `--protected-worktree`는 선택이며 생략하면 해당 비교를 `not_checked`로 기록한다. `--write`에는 **아직 존재하지 않는** 경로를 주어야 하며, 생략하면 JSON을 표준 출력에만 쓴다. 기존 기록을 덮어쓰지 않는다.

```bash
python -B reviews/week01-sequence-20261111/author/validate_candidate.py
python -B reviews/week01-sequence-20261111/author/validate_candidate.py --protected-worktree /path/to/optional-protected-worktree --write /tmp/new-week01-sequence-validation.json
```

환경은 Python 3.12.14, NumPy 2.5.4, pandas 3.1.1, Matplotlib 3.11.2, Seaborn 0.13.2, scikit-learn 1.8.0, nbformat 5.11.1, nbclient 0.11.0, nbconvert 7.17.2, ipykernel 7.4.0, jupyter_client 8.10.0이다. 저장 PNG와 HTML의 바이트 수준 일치는 폰트와 도구 버전에도 의존한다.

- 교량은 35셀 중 코드 16셀, 통합본은 38셀 중 코드 18셀을 각자 위에서 아래로 실행했다. 재실행한 텍스트·표·PNG 출력은 저장된 출력과 같았고, 두 HTML은 현재 노트북을 `HTMLExporter`로 내보낸 결과와 같았다.
- 별도 교량 커널에서 준비 2 → 검색 입력 14 → 정규화 16 → lookup 입력 22 → lookup/평균 함수 24 → A 입력 27과 빈칸 29 → B 입력 31과 빈칸 33을 실행했다. 숫자는 교사용 0부터 세는 셀 위치이며 학생 안내는 제목과 코드 첫 문장으로 찾도록 했다. 이 경로에서 B의 `query_new`가 미리 주어지지 않음을 확인한 뒤 실제 helper로 Q를 구성했다.
- 실제 교안의 `lookup_and_masked_mean`에 교안과 다른 `(V,B,T,d)=(6,2,3,4)` 입력을 넣어 조회값·마스크·개수·합·평균을 검증했다. 비영 PAD, 정상 영벡터와 반복 ID, PAD 값 변경·추가, 순서 교환, 음수·상한 밖·실수·bool ID, all-PAD·비유한 표와 정상 영평균 다음의 코사인 오류를 시험했다. 필수 B의 Q·점수·ID·잘못된 T 분모도 실제 helper와 교사용 해설을 대조했다. 실제 `normalize_rows`와 `cosine_scores`는 다른 3특성 입력, 양/음 배율, 축과 shape 오류, 0/비유한값, 24개 후보·ID 공동 순열과 동률 정책을 검사했다.
- 통합본의 실제 화분 모델 fit, 영 입력, 임시 CSV 저장·재읽기와 삭제를 확인했다. 독립 기기 문제의 다른 훈련 X, 평균, 중심 모델·트리 및 결과 CSV/ID와 오류는 **교사용 참조 구현**의 검사다. 교량 A/B와 기기 문제의 학생 답안은 비어 있으며 학생 코드나 성취로 세지 않았다.
- 원본 89셀 노트북의 별도 커널에서 후속 경로의 준비·입력과 제공 예제만 실행했다. 해당 경로의 학생 작성 답을 수행한 것은 아니다. 후보 6개, 원본 노트북·문제 해결 보충·CSV 및 선택 지정한 보호 작업트리 7개 파일의 SHA는 검사 전후 같았다. 보호 작업트리의 주차 README는 현재 없다.

[portability-explained.json](portability-explained.json)은 임시 로컬 clone에 미커밋 후보 6개와 도구를 복사하고, 저장소에 보존된 이전 빌더와 기준 산출물로부터 이전 노트북을 만든 뒤 [새 빌더](build_candidate.py)를 실행한 결과다. 두 노트북·두 HTML의 SHA가 현재 후보와 일치했고, 기존 출력 디렉터리와 기존 JSON을 덮어쓰려는 시도는 거부되었으며 해당 파일은 변하지 않았다. 검증기의 보호 경로는 지정하지 않아 `not_checked`다. 임시 clone은 정리되었다. 같은 Python·패키지·폰트를 공유하므로 다른 설치 환경에서의 실행을 입증하지 않는다. 최종 실행의 임시 wrapper는 후보 6개와 도구를 바깥 임시 clone에 복사한 뒤 그 안에서 저장소의 [validate_portability.py](validate_portability.py)를 실행하고, 결과를 새 이름으로 기록했다. 이 스크립트는 `author/portability.json`을 배타적으로 새로 만들므로, 재실행 시 기존 기록이 없는 임시 복제본에서 수행해야 한다.

새 빌더는 위의 두 이전 노트북을 인자로 받아 정확한 SHA를 먼저 확인하고, 존재하지 않는 출력 디렉터리에만 작성한다. 다음 경로는 존재하지 않는 출력 위치의 예시다. 기존 수업 파일을 덮어쓰는 명령이 아니다.

```bash
python -B reviews/week01-retrieval-20261111/author/build_candidate.py --output-dir /tmp/new-week01-retrieval-baseline
python -B reviews/week01-sequence-20261111/author/build_candidate.py --bridge-baseline /tmp/new-week01-retrieval-baseline/week01_axes_linear_bridge.ipynb --integrated-baseline /tmp/new-week01-retrieval-baseline/week01_integrated.ipynb --output-dir /tmp/new-week01-sequence-candidate
```

후보 편집 전에 별도 검토 기준과 독립 새 입력이 동결되었으며, 과거 검색 교안 검증 기록은 과거 SHA에 대한 기록으로 남겼다. 이 작성자 검증과 교사용 참조 계산은 독립 검토나 학생 수행을 대신하지 않는다. 실제 학생의 학습·도움·소요 시간, 수업 120분과 이전 자습 추정 안에서의 가능성, 보통 Jupyter/Colab 커널, HTML 전체의 브라우저 시각 렌더링, 국제 문제의 숨은 평가 성능은 미관찰이다.
