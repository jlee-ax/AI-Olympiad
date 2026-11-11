# 1주 통합 경로 · 작성 및 검증 기록

대상 후보: 통합 노트북 SHA-256 ca89cf21b31a82e51f083344f3d156e046ad1356d31c22ffd87607aeeddd4551, HTML f2d7d0fb5326e901335aa47350caba489bf64309e27f1befc866442f30883b28, 교사용 해설 d93a33f70a4db3e028f0f00a68c83c50270f73351c68987a2a71f721b69015d7. 기준이 된 기존 통합 노트북은 15ab0101edbca3c0c669e551cb723b401d168d9730523fa1ac1263a0d7538120이며 기존 본문·두 보충·사용자 미커밋 자료는 수정 대상에 넣지 않았다.

같은 화분의 합성 (2,2,2) 관찰을 행·열·범주 채널의 계약으로 읽고, 노란 잎 수를 한 화분의 관찰을 받는 함수로 추출하여 ID에 맞게 원래 표의 행에 붙인다. 물 결측은 훈련에서만 채우고 [물/10ml, 잎 수]로 실제 중심 분류기를 fit·검증한다. 평균과 제곱편차의 관계를 작은 계산으로 연결한다. 다른 채널 정의의 기기 명세는 학생이 특성·모델·검증·CSV를 직접 작성하는 빈 문제다. 이전 필수 A–E/bridge A·B의 위치와 준비·복귀 경로, 별도 Antique ZIP 계약 및 2–10주 선수 맵은 교사용 해설에 남겼다. 새 예제·남은 필수 과제의 실제 총시간과 학생 전이는 관찰하지 않았다.

## 실행 및 종료 처리 경과

첫 생성 시 모든 셀의 실행 후 작성자 실행기의 정리 코드가 shutdown_kernel() 다음에 manager.kernel.shell을 다시 참조해 AttributeError: 'NoneType' object has no attribute 'shell'가 발생했다. 이때 노트북과 HTML은 성공적인 전체 실행 및 정리 이후에만 쓰도록 되어 있어 새 후보가 저장되지 않았다. 커널 종료 전에 shell 참조를 보존하고 종료 후 해당 참조로 정리하도록 고쳤다. 이후 같은 빌더로 전체 실행과 저장에 성공했고, 독립 문제의 새 입력을 다듬은 뒤 같은 빌더를 다시 실행해 현재 SHA를 저장했다. 실행 중 Jupyter 라이브러리의 로컬 네트워크 인터페이스 열거가 권한 오류 경고를 내지만, 별도의 소켓 경로나 우회를 시도하지 않았다.

## 재현 명령

프로젝트 루트에서 아래 명령을 실행한다. 첫 명령은 결과 JSON을 새 author 폴더에 기록하며 교안·원본·사용자 미커밋 입력을 바꾸지 않는다.

    /workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B reviews/week01-deepening-20261111/author/validate_deepening.py --protected-worktree /workspace/scratch/d500e5cb2076/ai-olympiad-week01-integration --write reviews/week01-deepening-20261111/author/validation.json
    /workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B reviews/week01-integration-20261111/author/validate_followup_route.py --write reviews/week01-deepening-20261111/author/followup-route.json

다른 체크아웃에서 같은 Python 환경을 사용한다면 프로젝트 루트에서 다음 상대 경로 명령을 실행한다. 선택 인자를 생략하면 보호 작업트리 비교는 not_checked로 기록하며, 다른 체크아웃과는 독립적인 보호 작업트리의 경로가 있으면 --protected-worktree 뒤에 그 루트 경로를 명시한다.

    python -B reviews/week01-deepening-20261111/author/validate_deepening.py
    python -B reviews/week01-integration-20261111/author/validate_followup_route.py
    python -B reviews/week01-deepening-20261111/author/validate_portability.py

실제 검사는 Python 3.12.14, NumPy 2.5.4, pandas 3.1.1, scikit-learn 1.8.0, Matplotlib 3.11.2, Seaborn 0.13.2, nbformat 5.11.1, nbconvert 7.17.2, ipykernel 7.4.0, IPython 9.18.1, jupyter_client 8.10.0 환경에서 실행했다. 저장 PNG 바이트 비교는 폰트·렌더링 환경에도 의존한다. 다른 환경에서 동일 출력이 나온다고 가정하지 않는다.

후보 재생성 코드는 [build_deepening.py](build_deepening.py)다. 저장소의 이전 artifact-exact.ipynb를 SHA로 확인하고 읽으며, 필수 --output-dir로 지정한 **아직 존재하지 않는 디렉터리**에만 새 파일을 생성한다. 전체 in-process 실행·정리 후에 생성하며, 디렉터리가 이미 있으면 덮어쓰기 전에 실패한다. 저장소의 현재 교안 경로를 임의로 변경하지 않는다.

    python -B reviews/week01-deepening-20261111/author/build_deepening.py --output-dir /tmp/week01-new-output

위 경로는 예시이며 이미 존재하면 다른 새 경로를 써야 한다. [이식성 결과](portability.json)는 실제 임시 로컬 clone에 현재 미커밋 후보 세 파일과 작성자 도구를 복사한 뒤 검증기·기존 후속 경로를 실행한 결과다. 같은 환경에서 빌더가 두 후보와 동일 SHA를 생성했고, 같은 디렉터리 재실행은 종료코드 2로 거부해 파일이 바뀌지 않았다. clone의 보호 작업트리 상태는 not_checked였다. 검사가 끝난 임시 clone과 출력은 삭제했다.

## 실제 결과와 검사 범위

[새 검증 결과](validation.json)의 아홉 검증군은 다음을 통과했다.

1. notebook schema와 독립 HTML 재생성 바이트 일치. 별도 fresh in-process 커널에서 38셀의 코드 18셀을 위에서 아래로 실행하고 저장된 텍스트·표 HTML·PNG 출력을 비교했다.
2. 독립 학생 답안은 주석만 있는 빈 코드 셀이고 출력이 없다. 교사용 CSV 예시 행이 학생 노트북·HTML에 노출되지 않았는지 검사했다.
3. 실제 CSV 열을 교안의 observed_mean에 전달하여 NaN·None·0·전부 미상·빈 입력·명시된 범위 끝을 확인했다. 평균·분산·axis·reshape·broadcast 예제도 수치와 오류를 확인했다.
4. 서로 다른 유효 객체/색 배치 256개의 각 배열을 **교안에서 실제 정의·실행한** count_yellow_leaf에 전달하고 별도 중첩 반복문 결과와 대조했다. 모든 경우에서 배경 색 변경 불변을 확인했으며 P02의 같은 shape 행·열 전치가 다른 한 칸 값을 만드는지도 확인했다.
5. 실제 교안의 훈련 X, 대체값·중심·검증 예측·변경 후 중심과 예측을 확인했다. 24개 훈련 행/라벨 공동 순열의 재학습 검사는 교안 함수를 재실행한 것이 아니라 **별도 중첩 반복문으로 특성을 재구성**해 SimpleImputer와 NearestCentroid를 새로 fit한 대조 실험이다. 짝지어지지 않은 라벨에서 중심이 달라지는지, 같은 shape라도 다른 ID에 이미지를 붙이면 잎 수가 달라지는지, 검증 값 변경이 이미 배운 상태를 바꾸지 않는지도 확인했다.
6. 산점도의 점·ID·축 단위, 메모리 CSV 및 교안의 실제 임시 CSV 파일 재읽기·정리를 확인했다. 부모 검토자가 현재 SHA에 저장된 PNG를 별도 추출해 한글 제목·축·장소 범례와 P01–P06 라벨이 읽히고 겹치지 않음을 육안 확인했다. HTML 전체의 브라우저 렌더링은 보지 않았다.
7. 새 기기 문제의 센서 조건을 별도 중첩 반복문으로 해석하고 교사용 예시의 훈련 대체값·중심·검증 및 실제 임시 CSV 파일을 확인했다. 가까운 중심과 깊이 2 결정 트리를 각각 fit하여 서로 다른 유효한 검증 예측을 확인했다. 누락 signal 열과 중복 ID 오류 검사는 **별도 교사용 참조 풀이**에 대한 것이며, 비어 있는 학생 코드가 이를 처리했다고 주장하지 않는다.

[후속 경로 결과](followup-route.json)는 기존 본문과 bridge를 각각 별도 새 Python 프로세스의 in-process 커널에서 열어 안내된 준비·입력·관련 제공 예제 코드를 실행한 결과다. 원본의 학생 답안과 bridge의 빈 답안은 실제 학생이 작성한 것이 아니며, 제공 코드 실행은 필수 과제 완료를 뜻하지 않는다. 두 검사 전후의 본문·bridge·원본 CSV 해시는 각각 같았다. 새 검사에서 원본 교안·두 보충과 명시적으로 전달한 보존 작업트리의 7개 파일 해시는 전후 같았다. 선택 경로를 전달하지 않은 다른 checkout에서는 보호 작업트리를 확인하지 않았다고 기록한다.

실제 학생의 독립 풀이·필요한 도움·수행 시간·학습 성과, 일반 소켓 Jupyter/Colab, HTML 전체 브라우저 표시, 숨은 시험·국제 과제 해결 여부는 검증하지 않았다. 별도 독립 검토와 discovery는 새 SHA에서 진행하며 이전 SHA의 판정이나 학생 성취를 복사하지 않는다.
