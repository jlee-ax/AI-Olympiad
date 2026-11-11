# 후보 함수 호출 실행 준비

최종 후보 SHA 이전에는 후보 변경을 읽지 않는다. 현재 실행기는 이전 독립 검토의 일반 subprocess/커널 worker만 복제한 것이며 교안 source를 복제하지 않았다. 아직 후보 설정·어댑터는 연결하지 않았다.

최종 SHA 수령 뒤: (1) 실제 notebook/HTML/teacher의 SHA를 결합한다. (2) 전 셀 정상 control을 새 프로세스에서 실행한다. (3) 실제 정의된 행별 norm·정규화·점수/선택 함수를 호출하는 별도 oracle에 frozen 2D/3D/zero/tie/축/ID/scaling 입력을 넘긴다. 함수/셀 출처·최소 입력 어댑터·제거한 고정 예제 assert를 명시한다. (4) reference_retrieval.py의 검토자 구현과 실제 candidate 함수를 서로 다른 lane으로 기록한다. 후보 함수가 없는 기능을 검토자가 재구현해 후보 통과로 세지 않는다. (5) 실제 후보의 zero/tie 정책과 좁은 domain을 먼저 읽고 해당하는 기대/예외로 판정한다.

각 사례는 execute_candidate_case.py의 별도 subprocess에서 새 in-process kernel을 사용한다. 정상과 의도적 오류의 기대·실제·원시 stdout/stderr/실패 위치를 보존한다. 이전 결과를 덮어쓰지 않는 case ID를 쓴다. worker는 모든 쓰기를 이 independent 하위로 제한하고 runtime을 정리하며 notebook 원본 SHA 불변을 기록한다. notebook 단계의 파일 이벤트와 reviewer oracle 이벤트를 분리한다.

reference_retrieval.py는 후보를 읽거나 import하지 않는다. frozen 기대값에 맞춘 검토자 수학의 별도 구현이며 학생 성취·비공개 시험·교안 자체 실행이 아니다. 직접 루프와 math.fsum/sqrt를 사용하고 numpy/torch가 계산한 값을 정답으로 복사하지 않는다. 예: `python -B reference_retrieval.py --case independent-3d`.

후보 실행 상태: 아직 not_run. 실제 후보 어댑터·통합/bridge 새 셀 번호·선택한 실행 cell 목록은 후보 수령 후 새 파일로만 작성한다. 기존 동결 파일은 변경하지 않는다.
