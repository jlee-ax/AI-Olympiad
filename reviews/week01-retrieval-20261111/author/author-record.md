# 1주 검색 심화 · 작성 및 검증 기록

## 범위와 근거

기존 통합본 ca89…과 검색 교량 09efa…을 읽고 각각의 필수 목표를 보존했다. 교량의 검색 완성 예제를 길이→행별 L2 정규화→원시 내적/코사인 점수표→위치·실제 ID로 재구성했다. 기존 필수 B의 같은 새 입력은 첫 질문에서 원시 내적 ID 8과 코사인 ID 53이 달라지므로 별도의 새 문제를 쌓지 않고 두 규칙을 비교한다. 본문의 제곱거리 최소화, 원시 내적 최대화, 코사인 최대화는 다른 질문이다. 명세가 원시 내적을 요구하는 경우도 유효하다.

행별 정규화는 검색 예제의 규칙이며 주교안 화분 분류에 끼우지 않는다. 분류의 P01=[0,0]은 유효한 입력이다. 작은 유한 검색 배열에 한해 0벡터, 비유한값과 계산 불가능한 길이는 명시적으로 거부한다. 양수 배율과 한 벡터의 음수 배율을 구분하고, 정확한 동률에서는 현재 후보 순서의 첫 위치라는 합성 정책을 설명한다. 2주 열별 훈련 표준화와 행별 길이 정규화는 다른 연산이다. 모든 유한 부동소수 범위를 보장하지 않는다.

통합 기기의 알려진 훈련 행만 사용하면 관측 평균 4, 입력 X=[[0,3],[3,1],[4,2],[9,0]]이다. 미상 행의 100까지 넣은 28과 다르며 주 화분 예제의 X와도 다르다. 미상 입력의 모든 사용을 금지하는 일반 규칙은 아니다. 새 독립 과제의 모델 선택, 입력 해석·축·범주·ID/CSV 및 빈 답안은 보존했다.

[IOAI 2025 Restroom](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Restroom/Restroom.ipynb)의 baseline은 이미지 인코더 출력에 행별 L2 정규화를 사용한다. 원문은 같은 장소·반대 성별, 실제 훈련과 출력 계약도 요구하므로 합성 코사인 검색을 공식 과제 해결이나 국내 중등 기출로 제시하지 않는다. [IOAI 2026 Find the Order](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/1_Find_the_Order/statement.md)의 조각별 역순위는 이번 최댓값 위치→ID와 별개의 열린 과제다. [NumPy norm](https://numpy.org/doc/stable/reference/generated/numpy.linalg.norm.html)과 [scikit-learn cosine](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html)의 축과 정의도 참고했다.

## 대상 파일과 SHA-256

| 파일 | SHA-256 |
|---|---|
| lessons/week01/week01_axes_linear_bridge.ipynb | de5ba77f7cd1325769ca4af29a8fd9c851d14c8c83d5acb88a127bc277579ef0 |
| lessons/week01/week01_axes_linear_bridge.html | 347f2a86ae8ed1d4f1d1ac4b13ac62cf93805029d9f48b40a259ce11f4871fea |
| lessons/week01/week01_axes_linear_bridge_teacher.md | ebf6bc2040dbfa6f0708f8759872db475905b4a150125c1cde7a89e6b22771b9 |
| lessons/week01/week01_integrated.ipynb | b530a36ae4f0b4fe9237fb29d604dc288198df7027c85c2e99d1a2e6f2a41611 |
| lessons/week01/week01_integrated.html | a9aae8cb533a13e67d7c7ac71b23c14e3b29b65db71a291dd7b49e5ff8d87036 |
| lessons/week01/week01_integrated_teacher.md | 81a4f367b59d11d8b96c27606f893087f65a4637f2291f2466cabba42ea6172f |

## 생성 및 연결 수정 경과

최초 빌더는 같은 Python 프로세스에서 두 in-process 커널을 연속으로 실행했다. 첫 교량 뒤 통합본 첫 코드 셀에서 AssertionError가 났고 통합본 시작 실행 번호가 16인 상태가 관찰됐다. 두 노트북 모두 성공하기 전에는 노트북/HTML을 저장하지 않도록 했으므로 실패한 생성물은 저장되지 않았다. 각 노트북을 별도 subprocess의 fresh in-process 커널에서 실행하도록 고친 뒤 전체 실행과 저장에 성공했다. 각 프로세스의 Jupyter 라이브러리는 로컬 네트워크 인터페이스 열거 권한 경고를 냈지만 별도 소켓 경로나 우회는 시도하지 않았다.

이후 부모 검토자가 통합본에서 bridge의 함수를 재사용하는 데 필요한 선행 코드 안내가 빠졌음을 발견했다. 초안 통합본 b080…은 이에 따라 폐기하고, 5절 질문/후보 입력 코드 다음 정규화 함수 코드를 실행하고 완성 예제를 가린 뒤 B 입력으로 가도록 통합본과 교사용 위치 맵을 수정했다. 두 노트북 전체를 다시 독립 subprocess에서 실행했고 현재의 bridge de5b…와 통합본 b530…을 저장했다. 새 커널의 실제 실행 순서와 결과는 아래 검증에 포함했다.

## 재현 명령과 환경

현재 작업공간에서 보호 작업트리 7개 파일도 전후 비교한 실제 명령:

    /workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B reviews/week01-retrieval-20261111/author/validate_candidate.py --protected-worktree /workspace/scratch/d500e5cb2076/ai-olympiad-week01-integration --write reviews/week01-retrieval-20261111/author/validation.json
    /workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B reviews/week01-retrieval-20261111/author/validate_portability.py

다른 체크아웃에서 해당 Python 환경을 준비한 뒤 프로젝트 루트 기준으로 실행:

    python -B reviews/week01-retrieval-20261111/author/validate_candidate.py
    python -B reviews/week01-retrieval-20261111/author/validate_portability.py

선택 인자 --protected-worktree를 생략하면 보호 작업트리 비교는 not_checked로 기록한다. 검사는 Python 3.12.14, NumPy 2.5.4, pandas 3.1.1, scikit-learn 1.8.0, Matplotlib 3.11.2, Seaborn 0.13.2, nbformat 5.11.1, nbconvert 7.17.2, ipykernel 7.4.0, IPython 9.18.1, jupyter_client 8.10.0에서 실행했다. 저장 PNG 바이트 비교는 폰트·렌더링 환경에도 의존한다.

[build_candidate.py](build_candidate.py)는 저장소에 보존된 두 이전 artifact-exact.ipynb의 SHA를 확인해 읽고, 각 노트북을 별도 프로세스의 새 in-process 커널에서 실행한 뒤 명시한 **새 디렉터리**에만 HTML과 노트북을 쓴다. 존재하는 출력 디렉터리는 거부한다. 아래는 존재하지 않는 경로를 예시로 든 것이다.

    python -B reviews/week01-retrieval-20261111/author/build_candidate.py --output-dir /tmp/new-week01-retrieval

## 실제 검사

[validation.json](validation.json)은 네 별도 Python 프로세스의 fresh in-process 커널 결과다.

- 교량 33셀의 코드 15셀과 통합본 38셀의 코드 18셀을 위에서 아래로 실행하고 저장된 텍스트·표 HTML·PNG와 새 HTML export를 비교했다.
- **교안에서 실제 정의된** normalize_rows 및 cosine_scores를 별도 3특성 입력에도 호출했다. 행 길이·점수·선택 ID, 양/음 배율, 0/NaN/Inf/계산 불가능한 norm과 특성 차원 오류를 확인했다. 같은 shape의 행/열 순서 오류와 1차원 분모 broadcast 오용도 구별했다.
- 유일한 최댓값의 후보·ID 공동 순열 24개를 실제 함수에 넣어 ID를 확인하고, 별도 정확한 동률에서는 현재 행의 첫 위치 정책을 확인했다. B의 학생 입력은 작성자 참조 계산과 실제 함수로 검사했으며 학생의 빈 답안을 수행으로 세지 않았다.
- 주교안의 실제 분류 fit과 유효한 영벡터, 실제 임시 CSV 파일 재읽기·정리를 확인했다. 다른 기기의 평균·중심 분류기·결정 트리·ID/CSV 및 누락 열/중복 ID는 **교사용 참조 구현**을 검사한 것이지 학생 코드 실행 결과가 아니다.
- 통합본이 안내한 별도 bridge 커널의 코드 2→14→16→필수 입력 25/29 및 빈 답안 27/31을 실행했다. 기존 본문도 별도 새 프로세스에서 안내된 준비·입력·제공 예제만 실행했다. 빈 답안을 실행하는 것은 학생 성취가 아니다.
- 두 후보와 원본 교안·기존 보충·원본 CSV 및 선택 지정된 보호 작업트리 7개 파일의 SHA는 검사 전후 같았다.

[portability.json](portability.json)은 실제 임시 로컬 clone에 현재 후보와 작성자 도구를 복사한 뒤 두 산출물의 동일 SHA 생성, 존재하는 디렉터리의 덮어쓰기 거부, 전체 검증을 확인한 결과다. 이 clone에서는 보호 작업트리 경로를 주지 않아 not_checked로 기록했다. Python·라이브러리·폰트는 원래 환경과 같다.

이전 검증기와 로그는 이전 SHA의 증거로 남겼으며 이번 후보 검증으로 재사용하지 않는다. 실제 학생의 풀이 시간·도움·성취, 보통 소켓 Jupyter/Colab, 전체 HTML 브라우저 렌더링, 후속 주차 구현과 숨은 국제 과제 성능은 미관찰이다. 수업 120분 및 기존 5~7시간 자습 추정에 새 범위 전체가 들어간다고 주장하지 않는다.
