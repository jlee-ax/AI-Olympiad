# 재배치 재현 확인

content-review.md의 재배치 미확인 상태를 이 새 기록으로 보완한다. 기존 보고서·원래 설정·실제 로그·후보 전 동결 자료를 덮어쓰지 않았다.

independent 내부의 다른 절대경로에 후보·실행기·필요 oracle/설정/manifest만 복사한 최소 자료 checkout에서, 명시적 repo-root로 notebook/oracle 경로를 새 설정에 rebase했다. 각 대표 사례는 다시 별도 subprocess/새 커널이었다.

- 전체 후보 정상: passed. 저장 텍스트/출력 타입과 실제 result.csv 물리 I/O 확인.
- 실제 집계 함수 독립 격자: passed.
- 물리 파일을 메모리 왕복으로 바꾼 변이: 기대한 `actual notebook physical file write/read missing: result.csv`로 거부됐다.

원본 후보/기존 설정 SHA 불변, 각 runtime 및 임시 복제본 정리를 확인했다. 실제 새 경로·복사 파일별 SHA·새 설정 SHA·stdout/stderr와 원시 결과는 relocation-results/에 있다. 복제본 삭제 후에도 재현 절차와 도구를 남겼다.

범위는 경로 재배치 기능이다. 공유 venv를 사용했으며 전체 git clone·깨끗한 의존성 설치·다른 OS/Colab의 검증은 아니다. 최종 후보 notebook ca89cf21…, HTML f2d7d0fb…, teacher d93a33f7…를 다시 확인했다.
