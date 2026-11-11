# 1주 교안 심화와 시스템 통합 검증

## 범위와 근거

기존 lesson 브랜치의 최신 상태에 시스템 개선 53c7077을 순방향 통합했다. 개선 커밋과 직전 lesson 사이에 교안 변경은 없었고, 분리된 작업트리에서 기존 사용자 미커밋 파일의 원래 해시 6개가 변하지 않았음을 확인했다. 사용자가 삭제한 lesson README는 복원하지 않았다. main은 이번 작업에서 병합하지 않았다.

[공식 출제 기준·전공·올림피아드 원문 대조와 10주 선수관계](sources-and-scope.md)의 선택에 따라, 새 요구는 낯선 명세의 필드·시점·범주·축을 해석해 수치 특성, 실제 학습, 검증, 출력으로 잇는 첫 주의 독립 연습이다. 국제 고등학생 대상 Robot Chasing과 Antique의 전체 해결이나 국내 중등 기출로 주장하지 않는다. 기존 단일 특성 모델도 유효한 기초였다. 새 통합본은 기존 필수 A–E와 bridge A/B 경로를 유지한다.

[작성 기록과 재현 명령](author/author-record.md)은 정규 checkout용 새 검증기와 별도 안전 빌더, 첫 실행기의 종료 오류 및 수정, 실제 clone 검사 범위를 명시한다. 구 `reviews/week01-integration-20261111/author/validate_integrated.py`는 이전 15ab 후보의 수치·단일 열에 맞춘 역사적 검증기다. 현재 ca89 후보는 [validate_deepening.py](author/validate_deepening.py)로 검사한다. 기존 `tools/lesson_validation.py`도 다른 원본 교안을 대상으로 하므로 현재 통합본의 검사 결과로 취급하지 않는다.

## 실행과 독립 내용 검토

통합 직후와 교안 변경 후 각각 시스템 전체 271개 테스트가 통과했다. [실행 기록](integration/post-lesson-regression.json)의 log를 보라. 예제 quality와 workflow의 통과·계속 결과는 합성 사례이며 교안의 승인이나 학생 성취가 아니다. 이전 discovery의 도구 및 산출물 문맥이 달라진 결과는 [실제 조회 기록](system-context/review.md)에 보존했다. 예전 요구 19개·질문 8개·미해결 큐 17개 및 합의 대기 pause는 변경하지 않았고, 새 품질 bundle이나 graph 승인·새 discovery session을 만들었다고 주장하지 않는다.

새 노트북 38셀 중 코드 18셀을 새 in-process 커널에서 실행하고 저장 출력과 HTML을 비교했다. [작성자 검증](author/validation.json)은 실제 교안 함수에 256개 유효 격자를 적용했고 배경 변경, 같은 shape 전치, 훈련 fit과 ID 대조, 실제 임시 CSV를 확인했다. 별도 구현으로 훈련 행/정답 24개 공동 순열을 검증했다. 원본과 bridge의 안내된 준비·제공 코드를 별도 새 프로세스에서 실행했다.

[독립 내용 검토](independent/content-review.md)는 정상 12건과 실제 교안 코드에 가한 의도 오류 8건을 실행했다. 네 오류는 교안 자체 assert가, 네 오류는 별도 검토 oracle이 검출했다. [변이별 기대·실제와 검출 주체](independent/mutation-adjudication.json), 생략 없는 실행 결과가 `independent/runs/`에 있다. 학생의 빈 답안을 검토자의 참조 풀이 또는 제공 코드 실행으로 대체해 완료 처리하지 않았다.

## 한계

학생 독립 수행·도움·수행 시간·성취, 3–10주 전체 실물 교안과 숙달, 실제 대회 해결은 미관찰이다. 1주에 기존 수업·자습 시간 추정이 그대로 맞는다고 결론내릴 수 없다. 일반 소켓 Jupyter/Colab과 HTML 전체 브라우저 렌더링은 실행 환경의 제한으로 확인하지 못했다. 저장된 PNG는 제목·축·범례·ID를 직접 시각 검토했다.

자동 생성 HTML의 NumPy 출력 줄 1곳에 공백이 있고, 문맥 검증용 교안 source 투영 파일 끝에 빈 줄이 있어 `git diff --check`가 두 항목을 보고한다. 생성 출력과 기록된 바이트의 정확한 일치를 위해 보존한 표시상의 차이이며 기능 오류는 아니다.

독립 검토 설정의 절대경로는 원래 로그를 보존한 채 별도 재설정 절차로 보완했다. 다른 위치의 최소 복제본에서 대표 정상 2건과 물리 파일을 메모리로 바꾸는 오류 1건이 기대대로 판정됐다. 전체 환경 재설치 검증은 아니다. [경로 보정 기록](independent/RELOCATION-ADDENDUM.md)
