# 다른 checkout에서 재현하기

원래 case-configs의 절대경로와 실제 로그는 보존한다. rebase-case-configs.py는 동결 manifest의 repo_root를 읽어 notebook/oracle 필드만 새 repo-root 기준으로 변환하고 새 rebased-configs를 만든다. 원래 설정·log·기준·후보를 덮어쓰지 않는다.

같은 후보 SHA와 도구/입력/기대값을 가진 새 checkout에서 다음처럼 실행한다.

```sh
python -B reviews/week01-retrieval-20261111/independent/rebase-case-configs.py --repo-root /absolute/new/checkout --case full-bridge --case native-independent3d --case mutant-zero-silent
python -B /absolute/new/checkout/reviews/week01-retrieval-20261111/independent/execute_candidate_case.py /absolute/new/checkout/reviews/week01-retrieval-20261111/independent/rebased-configs/full-bridge.json
```

다른 두 설정도 같은 방식으로 각각 새 process에서 실행한다. native probe의 fixture/oracle 로딩은 해당 실행 cwd에서 이 independent 경로를 찾으므로 과거 workspace를 읽지 않는다. 실행기 자체도 새 checkout의 것을 사용해야 새 경로 안에 결과가 저장된다. 기존 runs/<id>와 rebased-configs가 있으면 덮어쓰지 않고 중단한다. 재시도는 증거를 보존한 별도 새 복제 위치에서 수행한다.

mutant-zero-silent의 기대 결과는 oracle_error / AssertionError / `candidate stated zero rejection did not occur`다. nonzero만으로 검출을 판정하지 않는다. 실제 zero→NaN과 임의ID 선택이 raw stdout에 있어야 한다.

`python -B relocation_smoke.py --python /path/to/venv/bin/python`은 independent 안의 최소 정확 자료 복제본에서 full-bridge 정상과 zero 오류를 실제 실행하고 relocation-results에 원시 결과/새 경로/파일SHA를 남긴 뒤 그 임시 복제본만 삭제한다. 공유 venv의 경로 이동 시험이며 전체 git clone·패키지 재설치·다른 OS/Colab 검증이 아니다.
