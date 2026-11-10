# 1주차 · Python과 표 데이터

[실행 출력이 저장된 노트북](week01_python_tables.ipynb)을 열면 한국어 설명, 수식, 배열 도식, 표와 그래프를 볼 수 있습니다. JupyterLab에서는 이 폴더를 내려받아 Python 3 커널로 열고 위에서 아래로 실행합니다. 노트북 하나만 옮겨도 동일한 CSV가 내장되어 있어 실행됩니다.

수업 대상은 코딩 기초가 있는 중학생입니다. 120분 수업은 이론 20분, 손풀이·필기 20분, 코딩 80분으로 구성했습니다. 별도로 표시한 필수 자습 5~7시간에는 배열 변형, 두 라이브러리 시각화, 새 CSV와 내적·재실행 활동이 있습니다. 자세한 문단은 다시 읽기 위한 설명도 포함하며, 실제 교실 소요 시간과 학생 이해는 아직 관찰하지 않았습니다.

평균·분산의 기호, 가정과 단위, 축을 줄이는 수식, 평균 알고리즘의 의사코드와 단계 추적을 코드 앞에 놓았습니다. 원본 표의 결측과 0을 구분하고, 그래프의 관찰 단위·집계·단위를 설명합니다. 예제 데이터는 모두 합성 자료입니다.

## 파일

- week01_python_tables.ipynb: 학생용 교안과 실행 예제, 빈 학생 답안 및 새 입력 과제
- week01_python_tables.html: 내려받아 볼 수 있는 렌더링 사본. 수식 표시는 MathJax 로딩에 의존할 수 있습니다.
- data/: 수업용 CSV와 열 이름·값을 바꾼 확인용 CSV
- teacher-notes.txt: 교사용 정답·오개념·시간 운영 메모. 독립 수행 시에는 닫아 둡니다.
- lesson-manifest.json: 시간·범위·미관찰 항목
- validation.json: 실행 방법, 출력 수, 계산·CSV·시간 검증과 화면 확인의 실제 범위
- validate_week01.py: 재실행·HTML 생성·수치 대조 도구
- provenance/: 수정하지 않은 승인 기준 파일 사본

기준은 main의 434fe5ad5d2300dba741c755bca8928177a2e098입니다. 승인 학생 계획의 SHA256은 96deb5e5e781bf39cc6bb5effe34d6d04a01ac65e13a3811c37f5a825714f7a9입니다. 공식 2027 공지가 연결한 실라버스는 확인 시점에 IOAI 2026으로 표시되므로 연도를 구분했습니다.

## 실행과 검증

Python 3, NumPy, pandas, Matplotlib, Seaborn, IPython 커널이 필요합니다. 별도 실행 검증에는 nbformat·nbclient·nbconvert도 사용합니다. 작성 환경의 정확한 버전은 validation.json에 기록했습니다.

JupyterLab의 Kernel → Restart Kernel and Run All Cells로 일반 환경에서 확인할 수 있습니다. 명령줄 검증은 이 폴더에서 다음과 같이 실행합니다.

~~~bash
python validate_week01.py
~~~

작성에 사용한 클라우드에서는 분리 커널의 ZMQ TCP·IPC 소켓이 제한됐습니다. 이 환경에서는 네트워크가 필요 없는 새 IPython 커널로 전체 실행했습니다.

~~~bash
python validate_week01.py --inprocess
~~~

자동 실행은 예제 코드와 계산 검증입니다. 학생 답안은 채우지 않고 성취 점수도 생성하지 않습니다. 시각 확인은 실행 성공과 별개이며 validation.json에 실제 관찰 범위를 남깁니다.

## 이후 개선 위치

교안 수정은 codex/week01-jupyter-lesson 브랜치의 lessons/week01/에서 이어갑니다. 회차마다 같은 브랜치에 변경 이유와 검증 결과를 커밋으로 남기고, 실패한 결과로 확인된 교안을 덮어쓰지 않습니다. 다른 작업이 진행 중이면 먼저 완료 상태를 확인하며, 강제 푸시는 하지 않습니다. 반복 실행 스케줄은 아직 만들지 않았습니다.

기존 skills/와 curriculum/의 원본은 수정하지 않았습니다. 한국어 문장 편집에는 [Humanizer-KO](https://github.com/IsaacEryn/humanizer-ko/blob/main/SKILL.md)의 사실·불확실성 보존과 상투적·장황한 표현 제거 원칙을 참고했습니다. 외부 스킬 설치나 AI 탐지 점수는 사용하지 않았습니다.
