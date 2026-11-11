# 후보 수령 후 실행 계획 · 현재 미실행

먼저 최종 notebook/HTML/teacher SHA를 받고 현재 source를 직접 읽는다. 사전 기준·입력·oracle을 후보 결과에 유리하게 고치지 않는다. frozen v1은 우연 노출된 역사적 자료라 독립 입력으로 쓰지 않으며 v2만 쓴다.

1. 최종 후보 완성 코드 전부를 새 subprocess의 fresh in-process 커널에서 실행하고 저장 출력과 실제 출력을 읽는다. 교안 코드·입력·학생 빈칸 및 기존 A–E/bridge A/B를 각각 식별한다.
2. 별도 프로세스에서 학생 안내대로 필요한 준비 셀만 실행해 T가 생성되고 기존 reshape·전치·행/열broadcast 문제 및 새 사각형 문제에 도달하는지 확인한다. 기억 속 변수에 기대거나 학생 빈칸을 완료로 세지 않는다.
3. 범용 함수가 있으면 실제 함수 호출을 adapter로 연결한다. 없으면 학생 지시를 따른 검토자 샘플 답안을 새 별도 파일로 작성한다. actual_candidate_callable과 reviewer_sample_solution_from_student_instructions를 혼합하지 않는다. loop/slice 등 타당한 대안을 수용한다.
4. 각 v2 입력을 별도 subprocess/커널에서 rectangle_probe.check_case에 적용한다. 모든 invalid 예외는 자동 통과가 아니라 pending_manual_traceback_review다. raw traceback이 의도한 계약 거부인지 읽고 판정한다. 정상·단일 오류와 원본 보존의 기대/실제를 새 로그에 기록한다. API를 바꾸는 adapter는 계약을 정규화할 뿐 틀린 좌표/배열을 정답으로 고치면 안 된다.
5. 사전 planned_single_faults를 실제 제공 코드/검토자 답안에 각각 한 오류씩 적용한다. 어느 코드가 변이 대상이고 누가 검출했는지 쓴다. 원시 실패·검출 못함·검토기 결함은 보존하고 수정판은 새 기록으로 만든다.
6. 이식성은 명시적 repo-root/새 output ID로 대표 정상·오류 경로를 별도 위치에서 확인한다. socket/browser 제한을 우회하거나 일반 커널 실행을 했다고 주장하지 않는다.

검토 코드는 아직 실행·import·compile하지 않았다. 이 문서와 oracle은 준비된 검증 방법이며 통과 결과가 아니다. 학생 성취·도움·시간·전체 Pixel/7–10주 해결 및 공개 teacher의 비공개성은 별도 관찰 대상이다.
