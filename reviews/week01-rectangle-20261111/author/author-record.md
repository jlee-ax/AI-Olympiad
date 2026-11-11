# 1주 공간 경계 · 작성 및 검증 기록

## 범위와 변경

기준 통합 노트북 `487379bf0c9c5fae5877d1eb5ec1414dedabbe2f2634a3827ae224f6e31bc568`의 기존 잎 격자 다음, 특성·모델 경로 안에 합성 공간 경계 완성 예를 연결했다. 원본 A의 reshape·전치·열별/행별 브로드캐스팅과 오류를 직접 수행한 뒤, 같은 숫자 T를 **통합본의 별도 커널에 다시 생성**해 독립 영역 함수를 작성하도록 했다. 입력 셀은 통합본 41, 빈 답안은 42이며 기기 문제의 빈 답안은 38이다. 셀 번호는 0부터 센다. 원본 A와 B–E, bridge A/B는 계속 수행해야 한다.

현재 산출물은 44셀·코드 21셀이다. 공간 응용은 기존 A에 더해지는 실제 수행이며, 중복된 질문 문구를 통합하고 이미 이해한 완성 설명을 반복 낭독하지 않더라도 기존 120분 수업과 이전 5~7시간 자습 추정 안에 들어간다고 판정하지 않는다. 학생용에는 시간 배정이나 운영 정보를 넣지 않았다. 교사용 원본 셀 번호는 안전 작업본의 89셀 기준이다. 보호한 사용자 작업본은 91셀이므로 같은 번호로 취급하지 않는다.

8×12 합성 격자의 `((2,4),(4,7))`은 2×3=6칸이고 6/96=1/16이다. 선택 원본값 하나가 0인 crop `[[0,29,30],[40,41,42]]`에서 비영 값은 5개여도 면적은 6이다. T는 2×3에서 한도를 4칸으로 **별도 약속**한다. 두 2×2 영역은 면적·shape가 같아도 좌표와 값이 다르다. 범위 밖 끝점은 NumPy 슬라이스가 조용히 잘릴 수 있으므로 순서·범위·면적을 먼저 검사한다. 빈 영역 거부는 이 합성 계약이다. 좌표는 참·거짓이 아닌 Python 정수라는 입력 전제와 실제 검사 범위를 분리했다. 원본 값 0과 선택 여부인 False를 구분하며, 기본 숫자 배열 슬라이스가 원본 값을 공유할 수 있음도 짧게 설명했다.

[IOAI 2025 Pixel 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Pixel/Pixel.ipynb)은 224×224, 최대 6.25%=0.0625=1/16, 즉 최대 3,136픽셀의 직사각형과 이미지 ID·좌표 JSONL 및 분류 정확도라는 별도 국제 개인전 계약이다. 전체 크기 mask는 좌표 검산의 중간 표현이다. 합성 좌표와 예산이 공식 문제의 해결, 숨은 채점기의 모든 정책, 국내 중등부 기출, 실제 모델 성능을 뜻하지 않는다. [NumPy 인덱싱 문서](https://numpy.org/doc/stable/user/basics.indexing.html)와 [Stanford CS231n NumPy 입문](https://cs231n.github.io/python-numpy-tutorial/)은 슬라이스와 축 이해의 참고다. 상세 비교는 [사전 원문·범위 기록](../source-prioritization.md)을 따른다. 실제 비전 모델과 3채널 구현은 후속 범위이며 이 예로 N02·D08 전체를 닫지 않는다.

## 산출물 SHA-256

| 파일 | SHA-256 |
|---|---|
| `lessons/week01/week01_integrated.ipynb` | `201e2de6ecf2a27f7a39e45744a162dfde6c26334a46370b77135ac0793047cb` |
| `lessons/week01/week01_integrated.html` | `c74c81f94996d0839ed2f5506e16746f2987c778e2fd266a614b4d607f977639` |
| `lessons/week01/week01_integrated_teacher.md` | `871bbc08dc9a678a2598c28ce9151cc74357e7d79ffe6fa5021fcfea9a814b51` |

## 후보와 검사 경과

첫 후보 notebook `f19f0dfecee8552fbfa6cae03fe92b0f1f606bba164d24a7c15ab3c84e428a6b`의 [초기 작성자 검증](validation-initial.json)은 보존했다. 독립 검토의 수식·코드 검토 및 부모 의견을 받아, `arange`, 불리언 마스크와 0, `zeros_like`, `astype(int)`, `copy`, `raise ValueError`의 목적과 완성 절차/학생 인자형 함수의 차이를 보충했다. 같은 위치 문제의 반복 문장을 합치되 각 경계와 실제 코드 검사는 유지했다. 가독성 후보 notebook `387b80845473172d35f9b7a979ca9f3098024b4b5c0c1b3a5df018144e16cba4`의 [검증](validation-readability.json)도 별도로 남겼다. 각 후보의 빌더와 validator 원문은 `build_initial.py`/`validate_initial.py`, `build_readability.py`/`validate_readability.py`로 보존했다.

부모가 공통 안내가 4번 목록 안에 렌더된 점을 발견해 [관찰 기록](rendering-note.md)에 남겼고, 첫 후보와 가독성 후보의 독립 snapshot 확보 후 빈 줄을 넣어 목록 밖 문단으로 렌더되게 했다. 저장 전 작성자 비교 스크립트의 변수 재사용 오류와 교안 미교체·수정 후 재실행은 [별도 기록](comparison-retry.md)에 있다. 이후 공식 비율·최대 칸 수를 한 문장으로 연결했다. 각 재생성에서 기존 코드와 저장 출력은 그대로임을 비교했다. 이 기록은 독립 검토의 내용 판정이나 학생 수행을 대신하지 않는다.

## 실행 결과와 재현

최종 후보의 실제 명령:

```bash
/workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B reviews/week01-rectangle-20261111/author/validate_candidate.py --protected-worktree /workspace/scratch/d500e5cb2076/ai-olympiad-week01-integration --write reviews/week01-rectangle-20261111/author/validation-final.json
/workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B reviews/week01-rectangle-20261111/author/validate_portability.py --write reviews/week01-rectangle-20261111/author/portability-final.json
```

[validation-final.json](validation-final.json)은 네 별도 subprocess의 fresh in-process 커널 결과다. 통합본 44셀의 코드 21셀을 위에서 아래로 실행하고 저장 텍스트·표·PNG와 새 HTML export가 같음을 확인했다. 별도 통합 커널의 T 재생성·빈 답안, 원본 89셀의 A 준비와 제공 셀·빈 답안, bridge A/B 준비와 실제 lookup/helper도 각각 분리해 실행했다. 빈 칸과 제공 셀의 실행은 학생이 푼 증거가 아니다.

교사용 문서에 실제 수록된 참조 함수를 추출해 T의 두 영역, 끝 경계, 한도 초과·범위 초과·음수·역순·빈 영역을 검사했다. 잘못된 경우는 배열 접근을 감시하는 입력으로 슬라이스 전에 거부됨을 확인했다. 다른 (3,4) 배열에서 0을 포함한 crop `[[0,7],[10,11]]`의 참 4칸과 비영 값 3개, 정확한 mask 위치·원본 불변도 검사했다. 이 숫자는 작성자의 참조 함수 검사이며 학생 코드나 독립 검토자의 숨은 입력이 아니다. 기존 화분의 실제 모델 fit·임시 디스크 CSV도 다시 확인했다.

후보·안전 작업본의 원본 notebook/HTML·bridge·기존 CSV와 선택 지정한 보호 작업트리의 7개 파일 SHA는 검사 전후 같았고, 보호 작업트리의 주차 README는 두 시점 모두 없었다. 학생 답안은 채우지 않았다. [portability-final.json](portability-final.json)은 임시 로컬 clone에서 저장된 이전 빌더와 기준 산출물을 이용해 최종 notebook/HTML을 같은 SHA로 재생성하고 전체 검증을 다시 실행한 결과다. 기존 출력 디렉터리와 기존 JSON 덮어쓰기를 거부하고 해당 파일이 변하지 않았음을 확인했다. clone 검사에는 보호 작업트리 경로를 주지 않아 그 부분은 `not_checked`다. clone과 임시 파일은 정리했다.

다른 checkout의 저장소 루트에서 같은 패키지를 준비한 뒤 다음과 같이 반복할 수 있다. 보호 작업트리 비교는 선택 사항이며, `--write`는 **아직 없는** 경로를 요구한다. 생략하면 표준 출력으로만 결과를 낸다.

```bash
python -B reviews/week01-rectangle-20261111/author/validate_candidate.py
python -B reviews/week01-rectangle-20261111/author/validate_portability.py
python -B reviews/week01-rectangle-20261111/author/validate_candidate.py --protected-worktree /path/to/protected-worktree --write /tmp/new-rectangle-validation.json
```

[build_candidate.py](build_candidate.py)는 지정한 이전 통합본의 정확한 SHA를 확인하고 존재하지 않는 출력 디렉터리에만 실행한 notebook과 HTML을 쓴다. 교사용 문서는 이 빌더가 생성하지 않으며 validator가 별도로 읽어 참조 함수를 검사한다. 아래 `/tmp` 경로는 아직 존재하지 않아야 한다. 이전 두 빌더와 저장된 기준 산출물이 checkout에 있어야 한다.

```bash
python -B reviews/week01-retrieval-20261111/author/build_candidate.py --output-dir /tmp/rectangle-previous-retrieval
python -B reviews/week01-sequence-20261111/author/build_candidate.py --bridge-baseline /tmp/rectangle-previous-retrieval/week01_axes_linear_bridge.ipynb --integrated-baseline /tmp/rectangle-previous-retrieval/week01_integrated.ipynb --output-dir /tmp/rectangle-previous-sequence
python -B reviews/week01-rectangle-20261111/author/build_candidate.py --baseline /tmp/rectangle-previous-sequence/week01_integrated.ipynb --output-dir /tmp/new-rectangle-candidate
```

실제 Python은 3.12.14, NumPy 2.5.4, pandas 3.1.1, Matplotlib 3.11.2, Seaborn 0.13.2, scikit-learn 1.8.0, nbformat 5.11.1, nbconvert 7.17.2, ipykernel 7.4.0, IPython 9.18.1, jupyter_client 8.10.0, pyzmq 27.3.0, traitlets 5.16.1이다. nbclient 0.11.0도 설치되어 있지만 이번 실행은 nbclient의 일반 소켓 커널이 아니라 `ipykernel.inprocess.manager.InProcessKernelManager`를 썼다. 출력·HTML의 바이트 일치는 라이브러리와 폰트에 의존한다. clone도 같은 설치와 폰트를 공유하므로 새 환경에서의 성공을 보장하지 않는다.

학생의 실제 시간·도움·이해·독립 성취, 일반 Jupyter/Colab 소켓 커널, 전체 HTML의 브라우저 시각 렌더링과 국제 문제 숨은 평가 성능은 미관찰이다. 도구에서 확인되는 작성자 정체성은 GPT-6 기반 Codex까지이며 세부 모델 식별자와 추론 노력 설정은 노출되지 않아 추정하지 않았다. 커밋·푸시는 하지 않았다.
