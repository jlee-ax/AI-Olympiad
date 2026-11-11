# 別 checkout에서 재실행

기존 case-configs와 raw 로그의 workspace 절대경로는 당시 실제 실행 위치이며 변경하지 않는다. 다음 절차는 **새 설정 파일만** 만든다.

1. 원하는 checkout에서 같은 notebook SHA와 independent 도구/동결 manifest·oracle·case-configs를 확보한다. 기존 venv 또는 기록된 패키지를 제공한다.
2. `python -B reviews/week01-deepening-20261111/independent/rebase-case-configs.py --repo-root /absolute/new/checkout --case full-candidate --case mutant-memory-replaces-physical`을 실행한다. 현재 폴더가 아닌 명시한 repo-root를 사용한다.
3. 새 `rebased-configs/`의 각 설정을 같은 checkout의 `execute_candidate_case.py`에 넘긴다. 예: `python -B /absolute/new/checkout/reviews/week01-deepening-20261111/independent/execute_candidate_case.py /absolute/new/checkout/reviews/week01-deepening-20261111/independent/rebased-configs/full-candidate.json`. 각 호출은 별도 프로세스와 새 커널이다. 실행기 경로도 새 checkout의 것을 사용해야 결과가 그 checkout independent 아래에 기록된다.
4. 변이의 nonzero는 raw 오류 원인을 읽어 의도한 검출인지 확인한다. `mutant-memory-replaces-physical`은 `actual notebook physical file write/read missing: result.csv`가 기대 결과다.

`rebased-configs/`와 `runs/<id>/`는 기존 결과를 덮어쓰지 않도록 이미 존재하면 중단한다. 반복 재현은 새 checkout/복제 위치를 쓰거나 기존 증거를 보존한 별도 실행 위치를 마련한다. 어떤 자동 삭제 명령도 사용자 원본이나 기존 로그에 적용하지 않는다.

`relocation_smoke.py --python /path/to/venv/bin/python`은 independent 내부의 임시 최소 자료 복제본으로 대표 정상·오류를 실제 실행하고 로그를 relocation-results/로 보존한 뒤 복제본만 삭제한다. 이는 전체 git clone이나 깨끗한 의존성 설치 검증이 아니다. 사용한 후보 SHA·새 경로·설정/파일 SHA·정리 상태를 summary.json에 기록한다.
