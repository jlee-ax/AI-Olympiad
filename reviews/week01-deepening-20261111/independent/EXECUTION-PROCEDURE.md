# 준비한 독립 실행 절차

새 후보는 아직 읽지 않았다. 기준은 pre-candidate-criteria.md/FREEZE.sha256를 그대로 보존한다. 이 자료들은 부모가 최종 경로와 SHA를 알린 다음에만 사용한다.

1. 최종 파일 SHA를 새 실행 manifest에 기록한다. 후보 전 원본 SHA와 차이는 의미를 직접 읽어 해석한다.
2. 교안의 실제 관찰 집계·변환 함수를 독립 입력에 적용하는 lane과 검토자가 새 명세를 푸는 참조 lane을 분리한다. 전자는 정확한 셀/함수 출처와 어댑터를 기록하고 후자는 검토자 소유 코드임을 표시한다.
3. candidate-test-plan.json 각 case는 새 subprocess에서 시작한다. 전체 노트북/연결 과제에는 그 프로세스 안의 새 in-process 커널을 사용한다. 이전 셀/프로세스 상태를 재사용하지 않는다.
4. 정상 control을 먼저 실행한다. 기대값(reference-expectations.json), 실제 stdout/stderr/반환값, 판정과 한계를 별도 필드로 남긴다. 변이는 하나씩 넣고 감지하지 못한 경우도 보존한다. candidate-results.json의 pending을 성공으로 바꾸는 준비 동작은 없다. 실제 결과는 새 SHA별 실행 파일에 남긴다.
5. 3NN과 중심 모델은 V9에서 다르지만 둘 다 유효한 참조 답이다. 특정 알고리즘/동률 규칙을 학생 명세가 고정하지 않았다면 하나의 예측 벡터를 유일한 정답으로 채점하지 않는다.
6. 파일 검사는 교안의 파일명/실행 단계와 리뷰 참조 코드의 reviewer-answer.csv를 분리한다. 메모리만의 왕복을 물리 파일 저장으로 인정하지 않는다.
7. 기존 A–E/bridge 안내는 최종 후보의 실제 위치를 따른다. 준비/제공 코드 실행과 빈 학생 답안의 성취는 구분한다. 시간·학습자 성취·실제 비공개 테스트는 관찰하지 않았다.

준비 참조 자체의 검산: `python -B prepare_reference.py --case arithmetic`, `--case controls`, `--case physical_csv`를 각각 독립 subprocess로 실행한다. 이는 후보 교안 코드나 학생 답안의 시험이 아니다. physical_csv는 이 independent 경로 내부 임시 폴더만 쓰고 자동 정리한다.
