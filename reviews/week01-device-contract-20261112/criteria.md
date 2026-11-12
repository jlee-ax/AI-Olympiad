# 1주 독립 검토 사전 기준

대상은 원격 기준 e3d3afdee8d2ad60141ca7a91b5b5bf3e7d3ec6d와 이 체크아웃의 저자 최종 후보이며, 작성자의 최종 해시를 받기 전에 이 기준을 정했다. 별도 사용자 미커밋 전체의 보존을 이 확인으로 주장하지 않는다.

1. 원본 실제 기기 입력 코드를 실행해 T2→N7 및 T4→V4/N3 변이 전파를 재현한다. 후속 후보는 11개 행의 배열 55쌍과 템플릿 간 메모리 공유가 없고 각 변이가 나머지 10행에 영향을 주지 않는지 확인한다. 원래 모든 관찰 숫자·행·라벨 값은 보존한다. 표 deep copy의 중첩 ndarray 한계와 각 배열 복사의 효과를 따로 확인한다.
2. 학생의 처음 보는 검증 입력에는 정답이 없고 선택·ID별 예측 기록 후 별도 정답에 접근하도록 하는지, 공개 저장소 파일 분리가 접근 통제가 아님을 분명히 하는지 확인한다. 정답은 ID별 기존 V9 정상·V4 점검·V7 점검과 일치해야 한다. 검증을 이용한 모델 선택과 제공되지 않은 별도 최종 테스트를 구분한다.
3. 학습에 알려진 라벨만 쓰고 평균을 훈련 관측에서 구하도록 하는지, 0과 결측·ID 순서·패널 범주와 축에 관한 설명을 보존하는지 확인한다. 정답 예시 모델을 유일한 답으로 강제하지 않고, 검토자만 별도 코드에서 다른 합리적 모델·새 입력으로 교사용 수치를 확인한다. 학생의 빈 답안은 건드리거나 성취 결과로 처리하지 않는다.
4. 본문·교량·2주차의 사용자 파일과 통합 교안의 관련 없는 기존 셀 ID·순서·핵심 내용을 보존한다. 최근 본문은 96셀이므로 과거 89/91셀 번호가 현재 위치로 오인되지 않는지 확인한다. 동시 작업과 원격 HEAD 갱신은 부모가 재확인한다.
5. 1주 교안의 이론·실전 연결과 기존 독립 A–E·교량 A/B의 부담을 함께 살핀다. 실제 학생 이해·소요 시간·도움과 3–10주 성취는 미관찰이며, 자동 코드 실행으로 이를 입증했다고 판단하지 않는다.
6. KOAI 2027의 중등 이론·코딩 안내와 연결된 IOAI 2026 기준을 구별한다. 국제 개인전 Antique와 Robot Chasing은 선수 역량 비교 자료로만 취급하고 국내 중등 기출이나 1주 문제의 실전 완수로 부르지 않는다. [KOAI](https://kitpa.org/koai/2027), [범위](https://kitpa.org/koai/syllabus), [Antique](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb), [Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/2_Robot_Chasing/statement.md), [pandas 복사](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.copy.html), [scikit-learn 누수](https://scikit-learn.org/stable/common_pitfalls.html).

기능 및 내용 판단과 일반 Jupyter/Colab·HTML 사용자 환경 검증은 별개다. 원격 쓰기는 독립 검토자가 수행하지 않는다.
