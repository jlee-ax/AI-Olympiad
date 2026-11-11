# 1주 통합 교안 · 범위와 검증 기록

## 학생 경로

주 진입점은 [통합 노트북](../../../lessons/week01/week01_integrated.ipynb)이며 [HTML](../../../lessons/week01/week01_integrated.html)과 [교사용 해설](../../../lessons/week01/week01_integrated_teacher.md)을 함께 제공한다. 통합 표 하나에서 행·ID·예측시점 → 관측 평균·분산 → 축·모양·그래프 → 임의 고정식 → 훈련 전용 대체·실제 fit → 검증·ID CSV → 새로운 기기 명세를 잇는다. 마지막 절은 남은 기존 필수 연습을 정확한 제목과 입력 준비 경로로 연결한다. 통합본 실행이나 새 문제 하나를 기존 필수 연습 전부의 완료로 판정하지 않는다.

학생은 통합본을 저장하고 기존 본문을 **별도 새 커널**에서 연다. ‘노트북 사용하기’ 아래 <code>from pathlib import Path</code>로 시작하는 준비 코드(본문 셀3), ‘7. CSV를 표로 읽기’ 아래 <code>csv_text =</code> 코드(셀27), ‘학습 확인’ 아래 <code>new_csv_text =</code> 코드(셀54)를 차례로 실행하고 지정된 문제와 관련 예제 셀로 이동한다. 원본 <code>sunlight_hours</code>와 통합본 <code>light_h</code>는 다른 자료다. 원본에 비해 P05 물20→10·높이10→14, P06 물60→50으로 바뀐 두 행도 섞으면 안 된다. 축·ID 교량은 또 다른 새 커널에서 준비 셀2와 독립 A/B 입력 셀21·25를 실행한 뒤 답안 셀23·27을 작성하고 통합본으로 돌아온다. 셀 번호는 교사용 0-based 위치이며 학생에게는 제목·코드 시작 문장으로 안내한다.

## 이전 자료와의 범위 대조

| 목표·근거 | 통합본의 경로 | 아직 남는 책임 있는 후속 |
|---|---|---|
| 89셀 본문의 행·특성·정답·CSV·결측(본문 셀4,26–37) | 통합 셀1–6의 CSV 읽기, 선택, 0/NaN, 실제 CSV 열을 함수에 전달 | 본문 셀42–44의 자료사전 확인 후 20ml 자료형 정리, 셀53–55·77–79의 다른 CSV·dtype·결측·집계·병합·미상/중복 키 |
| 평균·분산과 Python 상태(본문 셀5–8,16–25,47–48) | 통합 셀5–8의 분모·편차·분산과 반복·반환 | 본문 셀5–8 기호/유도, 14–25 필기·진단·traceback·함수 수정, 47–48 ddof와 NumPy/pandas 분모 차이, 과제 D 셀80–82의 관측 개수·평균 반환 |
| 축·reshape·broadcast 및 내적(본문 셀45–48,58–66,83–86) | 통합 셀9–12의 열/행 평균, 같은 shape 반례·broadcasting, 셀15–16 고정식 내적 | 본문 셀60–66 독립 배열·행/열 보정 및 오류, 셀83–86 다른 순서 수량·단가 내적과 새 세션 실행 |
| Matplotlib/Seaborn 및 새 그래프(본문 셀49–55,67–76) | 통합 셀13–14 산점도의 표 행·ID·단위와 인과 한계 | 본문 셀53–55 새 그래프 문제와 67–76 새 분산, Matplotlib/Seaborn 분포·범주 및 겹침 |
| 29셀 축·ID 교량 | 통합 셀9–12,15–16,25–26의 축·내적·ID 기초 | 교량 셀20–27 **필수 A/B**의 새 선형 변환·검색 점수·ID를 직접 작성. stack/lookup은 선택 교량 |
| 27셀 문제 해결 교안 | 통합 셀17–28의 train-only 대체, 학습 가능한 중심, 학습 변화, 검증, 메모리·임시 파일 CSV | 별도 교안 셀12–22의 상세 ID 오류와 ZIP/CSV 계약은 후속 심화. 세 특성의 별도 독립 문제를 통합본의 한 특성 문제와 자동으로 동일 성취로 간주하지 않음 |
| 보존 미커밋 91셀의 현재 본문과 다른 내용 | 예측시점·계수 단위·임의식·실제−예측은 통합 셀1,15–16; 장소별 다른 마커와 조건 차이·인과 한계는 셀13–14 | 보존판 파일·미커밋 변경은 그대로. 통합본이 원래 화분과 일부 숫자가 다른 합성 자료라는 설명 유지 |
| 2–10주 선수 연결 | 통합 마지막 절에 전처리·지표, 함수·거리·분산, shape·가중합, 표현·검색, 새 명세를 연결 | 후속 주차 구현·독립 수행은 이 통합본만으로 달성하지 않음 |

[IOAI 2025 Antique 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb)은 5특성, 미상 라벨 활용, 두 무헤더 CSV와 ZIP을 요구한다. 통합본은 별도 1특성 합성 지도학습과 헤더·ID CSV다. [IOAI 2026 Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md)은 독립 snapshot에 image (8,8,2), robot_id, 방향·mission·carrying을 주고 다음 action을 묻는다. 과거 관측·행동은 제공하지 않는다. 행·축·예측시점 선수의 전이 근거일 뿐 두 국제 과제나 국내 2027 출제의 완수를 뜻하지 않는다.

## 분량과 미관찰

통합본은 34셀(코드 16)이다. 기존 89셀 본문, 29셀 축 교량, 27셀 문제 해결본의 주요 설명을 한 서사로 다시 구성했지만, 셀 수 차이로 학습시간 절감이나 완주를 추정할 수 없다. 기존 수업 120분과 이전 범위에서 제시된 1주 자습 5~7시간에 통합본·남은 필수 연습이 들어간다는 관찰 근거는 없다. 실제 학생의 풀이 시간·도움·이해·독립 전이 및 재배치 가능성을 확인하고, 부족하면 미완료를 기록하고 지원과 기간을 다시 정한다.

고정식을 학습 모델로 오인하지 않도록 구분했으며, 독립 과제에서 다른 타당한 분류기 선택을 허용한다. 작은 합성 검증 1/2나 실행 성공은 실제 성능·대회 합격의 증거가 아니다. 별도 교사용 해설 파일은 공개 저장소에서 비밀이 아니므로 독립 평가 전에 별도 접근 통제가 필요하다.

## 실행과 재현

지정 venv Python 3.12.14 / NumPy 2.5.4 / pandas 3.1.1 / scikit-learn 1.8.0에서 새 in-process 커널로 통합 전체 셀을 실행한다. 별도의 두 Python 프로세스·in-process 커널로 원본 준비·후속 의존 셀과 bridge 준비·독립 입력을 실행한다.

    /workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B reviews/week01-integration-20261111/author/validate_integrated.py --write reviews/week01-integration-20261111/author/integrated-validation.json
    /workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B reviews/week01-integration-20261111/author/validate_followup_route.py --write reviews/week01-integration-20261111/author/followup-route-validation.json

[통합 결과](integrated-validation.json)는 실제 CSV의 NaN·None·0·빈 입력과 정상 범위 경계, 훈련 행/라벨 공동 순열, 학습 상태와 예측 변화, 실제 임시 CSV 왕복, 빈 학생 답안, 저장 출력과 산점도를 확인한다. [후속 경로 결과](followup-route-validation.json)는 학생 답을 대신 풀지 않고 안내된 준비·입력 및 관련 예제 셀의 실행 의존성을 확인한다. 저장된 [산점도](integrated-scatter.png)는 ID·단위·범례가 보이는지 직접 열어 확인했다. HTML은 새 export와 일치시키되 브라우저 전체의 시각 렌더링과 일반 소켓 Jupyter/Colab은 환경 제한으로 확인하지 않았다. 기존 자료와 사용자 미커밋 파일의 해시는 검증 전후 동일하다.
