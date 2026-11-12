# 1주차 교안 재구성 및 실행 검증

기준은 `codex/week01-jupyter-lesson`의 `e3d3afdee8d2ad60141ca7a91b5b5bf3e7d3ec6d`다. 이전 통합 개선 후보 파일은 확인하지 못해 이 커밋에서 다시 구성했다. 기존 `week01_python_tables.ipynb`는 이전에 기록된 후보 SHA-256 `b239479f4572a01f0e2848043078b45f3cda6f60e02369da091a4f4a63651880`, 본문 교사용은 `f9bc7635a1ece9ba67b02020989e85902a97b59f896c4ce8e0ea15332b12c092`와 일치했다. 사용자 작업 전체의 복원이나 이후 별도 변경 부재를 증명하지는 않는다.

## 선정과 변경

[KOAI 2027 안내](https://kitpa.org/koai/2027)는 중등부에도 필기와 코딩을 요구한다. 연결된 [출제 기준](https://kitpa.org/koai/syllabus)은 확인 당시 IOAI 2026 기준이다. [IOAI 2025 Antique](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb)의 미상 라벨과 평가·제출 계약, [IOAI 2026 Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/2_Robot_Chasing/statement.md)의 독립 스냅샷·축·범주·ID는 필요한 선수 역량을 비교하는 국제 고등학생 문제다. 국내 중등 기출이나 이 축소 예제의 완성 결과로 보지 않는다.

최신 통합본은 고정식·학습 모델·훈련 전용 대체와 검증을, 본문과 교량은 평균·배열·행렬곱·토큰 조회·ID 검색을 이미 다룬다. 새 예제를 쌓기보다 기존 독립 기기 문제의 배열 공유와 검증 공개 순서를 우선 교정했다. 통합 그래프는 실제로 인식되는 한글 글꼴 대안도 추가했다. 더 많은 이론을 전부 1주에 넣거나 이후 학습이 완수됐다고 판정하지 않았다. 기존 필수 A–E와 교량 A/B를 포함한 학습량 및 독립 전이는 관찰이 필요하다.

최종 통합 노트북 SHA-256 `88d169a244b1f4c0caeb885bb0bd1627cacf74aa6eaebe6dbb69d3ea8f94adb2`, 통합 교사용 `fe584d8ccdd7e51169b3ab852c0bef8388f3d1ce7a5374615428d30dda3fc40b`, 검증 정답 CSV `eeda4512bdc920d3101c65fb8d594c9bc074c810bfea1d48f854ea3a8be3b6a6`, 재생성 HTML `fa84da786f42800817a9852369ed8548e580c3b052a94f8ab89bc24b0fa5e5c2`다.

## 실제 실행

- `python -B -m unittest discover -s tests`: 기존 시스템 회귀 271개 통과. 이 시험은 합성 시스템 계약 검사이며 교육 성취 평가가 아니다.
- 본문 `validate_week01.py --inprocess`: 사용자 교안 파일을 덮어쓰지 않도록 별도 복사본에서 실행. 본문 96셀 중 코드 31셀, 제공 함수·CSV·누락·병합과 별도 CSV 없는 경우 통과. 본문 노트북과 교사용 원본은 기준 커밋과 바이트가 같다.
- 최종 통합·본문·교량 코드를 각기 다른 프로세스의 in-process IPython 커널에서 위에서 아래로 실행: 코드 셀 22·31·16개, 오류 0개. 출력 수집기가 표준 출력의 부모 요청을 놓치지 않는지 별도 print로 확인했고, 통합 노트북의 표·기기 행 수·산점도와 빈 학생 답안을 확인했다. 통합 산점도 PNG의 한글 축·범례를 직접 확인했다. 실행본의 source·셀 ID·첨부는 원본과 같다.
- HTML은 실행 결과에서 생성했으며 통합·본문·교량·검증 CSV 상대 링크의 존재와 텍스트를 점검했다. 전체 HTML의 실제 브라우저 표시를 확인한 것은 아니다.
- [독립 기능 검토](review.md)는 실제 전후 입력, 11행·55쌍, 행별 변이, 검증 ID·라벨, 두 참고 분류기, 새 잎 입력과 보존을 검사했다. ID·값 오류 12종은 검토자 참조 코드에서 검사한 것으로 학생용 자동 채점은 아니다. [별도 커널 경로](route-results.json)에는 학생이 풀지 않은 빈 답안 대신 검토자 fixture를 쓴 부분이 명시돼 있다.

실행 가능한 재현 코드: [기기 검사](device_probe.py), [커널 경로](route_probe.py), [전체 노트북 실행](run_notebook.py). `run_notebook.py`는 입력 노트북, 출력 디렉터리, 이름(`integrated`, `tables`, `bridge`)을 인자로 받는다. 서로 다른 프로세스와 임시 Jupyter/IPython/Matplotlib 디렉터리를 사용해야 한다. 실행기에 출력 parent ID를 연결한 것은 in-process 환경에서 print가 다른 셀로 빠지는 현상을 막기 위한 것으로, 소켓 방식 커널을 대체했다는 뜻은 아니다.

## 상태와 제한

일반 소켓 Jupyter 커널의 smoke 실행은 로컬 네트워크 인터페이스 조회 후 `Operation not permitted`로 커널이 시작되지 않았다. 제한을 우회하지 않고 in-process 방식으로 실행했다. 일반 Jupyter/Colab과 전체 HTML 브라우저 표시, 실제 학생의 시간·도움·성취는 미검증이다. 정답 CSV와 교사용 해설은 공개 저장소에 있으며 접근 통제가 아니다.

기존 discovery 기록을 현재 교안으로 조회하면 `needs_work`이며 이전 산출물 변경, 열린 질문 8개와 큐 17개 등이 남는다. 이 기록은 과거 후보에 묶인 이력으로, 이번 코드 검사가 과거 요구 전체의 해결이나 교육 품질 승인을 뜻하지 않는다. 기존 본문 교사용 `teacher-notes.txt`는 검증 스크립트·결과가 동봉되지 않았다고 하나 두 파일이 이 저장소에 있다. 사용자 파일은 보존했고 이 불일치는 별도 정리가 필요하다.
