# 재현

원래 `case-configs/`의 notebook/oracle 절대경로와 실제 로그는 변경하지 않았다. 새 checkout에서는 `rebase-case-configs.py`가 동결 manifest의 원래 repo-root를 기준으로 두 경로 필드만 새 root로 바꾸고, 원래 설정·동결 입력·노트북·로그를 그대로 둔다. 새 실행 ID를 붙이므로 보존된 runs와 충돌하지 않는다. 정확한 후보 SHA가 다르면 실행 전에 중단한다.

새 checkout 루트에서 사용 가능한 의존성 환경의 Python으로 실행한다. `$REVIEW_PYTHON`은 그 실행 파일이고, NumPy/pandas/scikit-learn/Matplotlib/Seaborn/nbformat/IPython/ipykernel이 필요하다. 검토 실측은 기존 olympiad-week1-cloud venv를 공유했으며 새 패키지 설치 검증은 하지 않았다.

```bash
"$REVIEW_PYTHON" -B reviews/week01-sequence-20261111/independent/rebase-case-configs.py --repo-root "$PWD" --run-prefix replay-001 --case final-native-base --case final-mutant-wrong-T-denominator
"$REVIEW_PYTHON" -B reviews/week01-sequence-20261111/independent/execute_sequence_case.py reviews/week01-sequence-20261111/independent/rebased-configs/replay-001/final-native-base.json
"$REVIEW_PYTHON" -B reviews/week01-sequence-20261111/independent/execute_sequence_case.py reviews/week01-sequence-20261111/independent/rebased-configs/replay-001/final-mutant-wrong-T-denominator.json
```

첫 사례는 exit0/`passed`, 두 번째는 exit1/`oracle_error`와 `AssertionError ('values', 4)`가 기대다. 두 번째의 비정상 종료는 주입한 평균 분모 오류를 검출한 결과다. 예상치 못한 traceback을 같은 검출로 세면 안 된다. 다시 실행할 때 새 `--run-prefix`를 사용한다. 각 명령은 별도 subprocess의 새 in-process 커널이고 소켓 기반 커널을 쓰지 않는다.

`portability_smoke.py`가 실제로 새 경로의 최소 복제본에 동일 바이트의 최종 bridge, 실행기, 오라클, 동결 입력과 선택 설정을 복사하고 위 대표2건을 실행했다. `portability-results.json`의 파일별 SHA와 `portability-raw/`가 근거다. 원본/복제본 SHA를 재확인한 뒤 새 임시 복제본만 제거했다. 이것은 대표 helper 정상/오류 경로의 이식성 검증이며 전체 저장소/독립 설치/모든 notebook의 새 경로 회귀는 아니다.

`functional-results.json`은 주 검토33건의 기대·실제·raw 경로·검출 주체를, `CONTENT-REVIEW.md`는 사전12기준의 충족/부분 충족/미관찰을 기록한다. `reference-selfcheck-results-v1.json`은 교안 코드를 호출하지 않은 사전 참조 구현12건으로 별개다. 첫 A 오라클과 초기 내용 감사의 검토기 오류는 invalid adjudication과 원래 결과/스크립트로 남겼다. 학생 답안은 여전히 주석뿐이다.
