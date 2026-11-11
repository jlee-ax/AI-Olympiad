# 보충 검사기 최소 안전 보정

최종 판정은 `temporal-final-summary.json`과 `temporal-final-results.json`이다. notebook b5f5 / HTML0b45 / teacher56c1 / validator60fb의 정확한 바이트를 `temporal-final-fixture/`에 고정한 뒤 26/26 회귀가 통과했다. 최종 fixture 이후 검사기 바이트는 바꾸지 않았다.

기본 `python validate_week02_temporal_preprocessing.py`는 기존대로 stdout JSON만 낸다. `--write /existing-parent/NEW.json`은 부모 디렉터리가 이미 있는 신규 파일만 배타 생성한다. 기존 파일/디렉터리/심링크와 심링크인 상위 경로는 실행 전에 거부하고 게시 직전에 다시 확인한다. 이전 덮어쓰기 호출자는 매번 새로운 보고서 파일명을 사용해야 한다. 기존 validation.json은 자동 갱신하지 않는다.

`-O`/`PYTHONOPTIMIZE`는 외부 모듈 import 전에 거부한다. 학생칸은 모든 태그 셀에서 정확히 하나인 코드 셀, 현행 주석 템플릿, execution_count=None, 저장 출력 없음이어야 한다. 실제 학생 성취나 공통 산출물의 완성도를 자동 평가했다고 보고하지 않는다.

notebook/HTML/teacher를 시작 시 바이트 스냅샷으로 읽어 검사하며, 결과 저장·stdout 출력 직전에 셋 중 하나라도 바뀌면 거부한다. 동시 사용자 변경은 덮어쓰거나 되돌리지 않는다. 신규 보고서의 쓰기 실패는 이번 실행이 만든 같은 inode 파일만 정리한다.

수치·시점·ROC 검증 블록은 원본과 바이트가 같다. 보고서는 저장 예제 출력·PNG와 학생칸 미실행 상태라는 관찰 범위만 적는다. 원래 저장 방식은 미검사이며 고정 과거 Jupyter 경고·previous_attempt를 제거했다. 브라우저 문구도 실제 시도한 것처럼 쓰지 않고 ‘이 검사기에서는 시각 검토를 수행하지 않음’으로 수정한 뒤 최종 fixture와 회귀를 고정했다.

수정 전 원본 및 옛 출력은 `temporal-baseline/`에 보존했다. 초반 teacherac2b fixture 회귀는 역사로만 남기고 최신 teacher56c1 근거와 구분했다. 초기 NEW JSON 테스트의 실패는 CLI의 마지막 빈 줄을 바이트 비교한 실행기 문제였으며 JSON 객체 비교로 정정했다.

검증은 승인된 기존 venv의 Python -B만 사용했고 설치·환경 변경·소켓 시도는 하지 않았다. 모든 실행은 임시 사본과 개별 캐시 경로에서 수행하고 실행기가 캐시를 정리했다. 별도 OS 격리가 아니므로 임의 Python의 절대경로 접근은 막지 못한다. 시각 렌더와 원격 MathJax, 학생 성취·시간은 미검증이다. 커밋·푸시는 하지 않았다.
