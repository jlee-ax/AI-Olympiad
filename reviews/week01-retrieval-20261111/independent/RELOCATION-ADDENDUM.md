# 경로 재현 보완 결과

기존 content-review.md·동결 파일·case-configs·원시 로그를 덮어쓰지 않고 별도로 보완했다.

명시적 repo-root로 notebook/oracle 경로를 새 설정에 rebase한 최소 정확 자료 복제본에서 full-bridge 전 셀 정상과 zero 거부 제거 오류를 각각 새 subprocess/커널로 실행했다. 정상은 passed, 오류는 의도한 `candidate stated zero rejection did not occur` AssertionError였다. raw 결과에 zero→NaN·임의ID42가 남아 있어 단순 nonzero 종료만으로 검출하지 않았다.

실제 새 경로·복사 파일 SHA·새 설정 SHA·stdout/stderr·원시 결과는 relocation-results에 있다. 원래 설정/source SHA 불변과 runtime/임시 복제본 삭제를 확인했다. 재현 방법은 REPRODUCING-ANOTHER-CHECKOUT.md, 도구는 rebase-case-configs.py 및 relocation_smoke.py다.

이는 공유 venv의 경로 재배치 기능 확인이다. 전체 git clone·깨끗한 의존성 설치·다른 운영체제/Colab의 시험은 아니다. 내용 검토 보고 SHA1955563b…를 보존했다.
