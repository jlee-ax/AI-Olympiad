# 후보 실행 준비와 증거 범위

최종 SHA를 받기 전에는 후보 변경을 읽지 않는다. reference_sequence.py는 후보/작성자 검증기를 import·읽지 않는 검토자 별도 구현이다. 기대값은 동결 JSON을 읽으며 count0에는 검토자 정책으로 zero placeholder+valid=False를 반환한다. 실제 후보가 명확한 오류를 쓰면 그 선언된 정책을 판정한다. 참조 코드와 후보 코드가 같은지로 학생 성취를 판정하지 않는다.

최종 후보 수령 후 실제 정의된 lookup·유효합·개수·mean 함수의 셀/이름/소스SHA를 새 adapter 기록에 묶는다. frozen V7/B2/T4/d3 입력을 **실제 함수에 직접** 넣는 lane, 검토자의 reference_sequence 계산 lane, 학생 빈칸/직접 수행 상태를 별도로 남긴다. 후보 helper가 없는 기능을 검토자가 대신 구현해 후보 통과로 세지 않는다.

execute_candidate_case.py는 각각 새 subprocess/새 in-process kernel에서 전체/선택 셀과 reviewer oracle을 실행하는 일반 도구다. 후보별 config·최소 adapter·cell 위치는 최종 SHA 후에만 새 파일로 만든다. 모든 쓰기는 이 independent 아래로 제한하고 runtime 삭제/원본 SHA 불변을 기록한다. 실제 notebook I/O와 reviewer I/O는 phase별로 나눈다.

정상 control을 먼저 검증한 뒤 한 오류씩 시험한다. 핵심은 V/T/d 뒤섞임, 무조건 mean(axis=1)의 T분모, PAD를 numerator만 제거, 영벡터 정상 토큰 누락, 반복ID deduplicate, 음수의 끝행 wraparound, 범위밖 clip, wrong-axis/broadcast, all-PAD를 진짜 평균0으로 주장, pooled zero를 무조건 cosine 성공으로 처리 등이다. 선언된 좁은 입력 범위와 API 정책을 존중한다.

기존 B의 새 실제 경로를 준비 셀부터 새 커널에서 재현한다. raw/cosine/ID/공동순열과 필수A/원본A–E·통합fit/검증/CSV, 다른 합리적 모델 허용·학생 빈칸 보존을 확인한다. 상세한 language model/attention/embedding 학습·FindOrder 또는 Pixel 해결을 이 예제 통과로 바꾸지 않는다. 별도 실제 학생 시간·도움·성취는 미관찰이다.

원래 로그·동결 자료는 덮어쓰지 않는다. 실패/기대 불일치나 harness 결함도 생긴 순서대로 별도 기록한다. 실행기 원본은 직전 retrieval independent의 일반 worker만 복제했으며 이전 oracle/사례나 교안 raw사본을 복제하지 않았다.
