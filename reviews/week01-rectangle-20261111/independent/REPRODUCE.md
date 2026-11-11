# 재현과 범위

원래 case-configs·동결 입력·raw 결과는 고치지 않았다. 새 checkout에서 rebase-case-configs.py는 baseline-manifest의 원래 repo-root를 기준으로 notebook/oracle 경로만 새 root로 바꾸고, 새 실행 ID/새 config를 만든다. 후보 SHA가 다르면 실행 전 중단한다. 현재 설치 환경의 Python을 `$REVIEW_PYTHON`으로 지정한다.

```bash
"$REVIEW_PYTHON" -B reviews/week01-rectangle-20261111/independent/rebase-case-configs.py --repo-root "$PWD" --run-prefix replay-001 --case portability-source-normal --case portability-source-error
"$REVIEW_PYTHON" -B reviews/week01-rectangle-20261111/independent/execute_notebook_case.py reviews/week01-rectangle-20261111/independent/rebased-configs/replay-001/portability-source-normal.json
"$REVIEW_PYTHON" -B reviews/week01-rectangle-20261111/independent/execute_notebook_case.py reviews/week01-rectangle-20261111/independent/rebased-configs/replay-001/portability-source-error.json
```

정상은 exit0/passed, 잘못된 상한 올림 어댑터는 exit1/oracle_error·ProbeMismatch와 invalid contract accepted가 기대다. 임의의 실행 오류를 이 검출로 세면 안 된다. 재실행 시 다른 run-prefix를 쓴다. 두 사례는 실제 최종 입력41/42 후 **검토자 샘플/어댑터**를 검사하며 학생 노트북에 없는 범용 함수를 실행했다는 뜻이 아니다.

실제 portability_smoke.py는 이 최소 입력/코드 묶음을 새 위치에 동일 바이트로 복사하고 대표 두 경로를 각각 새 subprocess/fresh in-process kernel에서 실행했다. 결과·명령/stdout/stderr는 portability-results.json 및 portability-raw에 남겼고 원본/복제본 SHA를 확인한 뒤 새 임시 복제본만 제거했다. 기존 olympiad-week1-cloud venv를 공유했으며 새 의존성 설치·모든 노트북/저장소의 새 위치 회귀는 하지 않았다.

주 기능 결과47건은 functional-results.json, 원시 값과 traceback은 runs, 초기/중간/최종 세 snapshot은 initial-inputs/candidate-387b-inputs/final-inputs다. 사전 입력 v1의 일부 우연 노출과 v2 교체는 exposure-and-replacement.md에 있으며, 실제 독립 입력은 v2만 사용했다. 공개 저장소 경로가 권한으로 숨긴 시험은 아니다. invalid-capture-attempt-01.json은 최초 검토기 실패이고 후보 기능 실패가 아니다.
