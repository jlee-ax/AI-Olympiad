# 1주차 배열·선형변환 보충본 독립 검토 — 2026-11-11

최종 학생용 29셀을 모두 읽고, 별도 새 in-process IPython 커널에서 13개 코드 셀을 전부 실행했다. 오류 출력 없이 통과했다. 이 13개에는 새 과제의 입력 정의 셀 2개와 주석뿐인 학생 답안 셀 2개가 포함되며, 학생이 독립 과제를 작성·실행했다는 뜻이 아니다.

최종 notebook SHA-256은 `6241f6bce0db5b2dfe40dc672a0706a09d7228d2aea451cd1a03b05847f910c4`, 교사용 해설 SHA는 `651038f80b4800f8efb72094823e497cfe5168985bc882e586b1c4dc12fcf9c0`이다. 둘 다 실행 전후 같았다. 초기판 SHA `74f52475ce1cd8bd80b61b8b4f064836f224912d2be5f46e39072b5a21080b45`의 검토와 lookup 반례는 `week01-bridge-results-initial.json`에 보존했다.

| 항목 | 독립 확인과 판정 |
|---|---|
| 기초와 축 수축 | 통과. 표의 개체×특성→내적→(n,d)@(d,m)→남는 n,m 축으로 점진적으로 설명한다. W의 열 하나가 출력 하나의 가중치라는 설명과 수식도 일치한다. 가중치를 학습한 모델이라는 주장은 없다. |
| 주 예제 | 통과. list/sum으로 X@W=[[2,1,4],[1,3,7],[3,2,7]]를 재계산했다. W@X는 (2,2)로 실행되지만 화분×출력이라는 목표 의미를 잃고, X@X는 가운데 길이2/3 불일치로 실패함을 확인했다. 같은 shape의 원소곱/행렬곱도 다른 값을 만든다. |
| 새 필수 A | 통과. 교사용 키 없이 별도 계산한 결과는 [[6,12],[5,3],[3,9]], 원소곱은 [[2,0],[2,3]]. 특성만 뒤집으면 첫 결과가6→9로 바뀌지만 X의 특성과 W의 대응 행을 함께 뒤집으면 원래 결과가 보존된다. bad_W의 모양 오류도 실제 ValueError다. |
| 새 필수 B·ID | 통과. 점수 [[4,6,3,2],[5,3,3,4]], 위치[1,0], ID[8,90], 관계61→8·22→90이다. 후보 순서[2,0,3,1]에서 새 위치[3,1], 올바른ID[8,90], ID를 옮기지 않은 오류[17,8]을 확인했다. 후보24순서×질문2순서=48회 공동 재배열에서도 ID 관계를 보존했다. |
| stack·concat | 통과. 주 예제의 새 축(2,2,3), 행연결(4,3), 열연결(2,6), 새 선택C의 (2,2,2)/(4,2)/(2,4)을 확인했다. (1,2)+(3,2)는 stack·열연결 실패, 행연결(4,2) 성공이다. |
| 열연결의 대상 의미 | 보완 후 통과. 초기판의 설명은 서로 다른 후보를 열로 붙여도 같은 후보의 특성 확장처럼 읽힐 여지가 있었다. 최종판은 F1/S1·F2/S2 및 선택C의 90/53·8/17이 인위적인 위치상 짝임을 밝히고, 같은 대상의 특성확장에는 행 ID·순서·열 뜻의 대응이 필요하다고 명시했다. |
| lookup 축·값 | 보완 후 통과. 초기판 B=T=d=2에서는 token_indices.T가 같은(2,2,2) shape와 기존 assert를 통과했다. 최종판은 입력(2,3)→출력(2,3,2), 전체 조회값과 [0,1]/[1,0] 대응을 출력·검사한다. 실제 전체값은 [[[1,3],[0,2],[2,1]],[[2,1],[1,3],[0,2]]]이다. 위치를 거꾸로 하는 같은shape 변이도 값 검사로 잡는다. 정수 lookup과 이미지 인코더 임베딩이 같은 실행은 아니라고 구별한다. |
| 의도적 오류 탐지 | 통과. 행렬곱 순서 반전, 모든쌍 대신 원소곱, argmax 축0, 위치+1을 ID로 사용, ID 없이 후보만 이동, stack 대신 concat, lookup 축 전치, 같은shape lookup 위치역순의 8개 변이를 각각 메모리 복사본에서 시험했다. 최종판은 모두 assert 또는 명시적 오류로 중단했다. 범용 의미 오류 탐지를 입증하는 것은 아니다. |
| 평가 독립성 | 학생 A/B 답안칸과 출력은 비어 있고 예제·교사용 키를 가리라고 명시한다. 새 숫자·새 차원의 근거리 전이 과제로서 계산과 ID 대응을 확인한다. 실제 첫 응답·도움·자기 수정·성취는 미관찰이다. 교사용 키와 검토자료는 같은 저장소에서 접근할 수 있으므로 파일 분리는 접근 통제가 아니다. |
| 120분·자습 | 통과(편성·한계). 기존20+20+20+40+20=120분을 늘리지 않고 보충은 수업 뒤 자습에 놓는다. 기존5~7시간 추정이 보충까지 포함한 검증된 시간이라고 주장하지 않으며, 새 총자습시간과 실제 중학생 완수가능성은 미추정·미관찰이다. 필수 기존 성취 생략으로 시간을 맞춘다고 하지 않는다. |

학생 코드와 출력, 교사용 해설을 대조해 현재 수치·축·ID 오류는 찾지 못했다. 출력은 작은 배열·표에 한정된다. HTML/인쇄의 실제 시각 렌더링, 일반 소켓 Jupyter 커널·Colab, 학생 독립 수행 및 실제 학습시간은 미검증이다. 소켓 기반 커널을 추가 시도하지 않았다. 검토 실행은 지정된 기존 venv의 Python3.12.14/NumPy2.5.4를 사용했다.

Restroom 공식 문제와 baseline을 직접 읽어 독립 query/gallery ID, 반환 gallery ID, 인코더 출력 연결·정규화 및 별도 순위 선택을 확인했다. 이 합성 최대 내적을 실제 대회 해결법이나 중등 기출로 취급하지 않은 점은 적절하다. 이 국소 보충은 4차원 batch/channel 축 조작, 실제 인코더·정규화·검색 평가, 전체 D01/D05나 10주 과정의 완료를 입증하지 않는다.

재현은 `python -B reviews/week02-independent-20261111/run_week01_bridge_review.py`이다. 원본을 읽어 검토 폴더에만 실행본·JSON을 남기고 자체 runtime을 정리한다. `week01-bridge-results.json`에는 해시·정확 계산·48개순열·8개변이 결과가, `week01-bridge-cell-evidence.json`과 `week01-bridge-executed.ipynb`에는 실제 실행 출력이 있다. 원본과 Git index는 수정하지 않았으며 commit/push하지 않았다.

직접 확인한 공식 근거: [NumPy matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html), [stack](https://numpy.org/doc/stable/reference/generated/numpy.stack.html), [concatenate](https://numpy.org/doc/stable/reference/generated/numpy.concatenate.html), [argmax](https://numpy.org/doc/stable/reference/generated/numpy.argmax.html), [PyTorch Embedding](https://docs.pytorch.org/docs/2.15/generated/torch.nn.Embedding.html), [IOAI2025 Restroom 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Restroom/Restroom.ipynb). 국내/국제2027 전체 실라버스 적용성은 이 기능 검토에서 새로 판정하지 않았다.
