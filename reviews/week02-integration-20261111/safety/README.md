# 2주 본문 검증기 안전성 후보

수정 범위는 `lessons/week02/teacher_validate_week02.py`와 이 디렉터리의 신규 증거뿐이다. 이전 품질 기록은 변경하지 않는다. 1주 파일 및 다른 작성자의 본문/보충 notebook·생성기·교사용 문서는 수정하지 않는다.

## 사용법과 이전 호출자 이전

- `python lessons/week02/teacher_validate_week02.py` 또는 `--inprocess`: 메모리에서 실행·HTML 렌더를 확인하고 stdout JSON만 출력한다. 학생 입력 notebook, 인접 HTML, 기존 validation.json을 갱신하지 않는다.
- 새 산출물은 `python lessons/week02/teacher_validate_week02.py --inprocess --output-dir /existing-parent/NEW`로 요청한다. 부모는 이미 있는 일반 디렉터리이고 NEW 자체는 없어야 한다. 기본 입력이면 NEW에 `week02_prediction_evaluation.ipynb`, `week02_prediction_evaluation.html`, `validation.json` 세 파일을 생성한다. 기존 파일/디렉터리/심링크, 경로 중 심링크, 입력을 포함하는 겹친 경로는 거부한다.
- `--notebook PATH`는 신뢰된 self-contained 입력 복제본용이다. 출력 notebook/HTML 이름은 입력 파일명/같은 stem이다.
- 이전에 `--inprocess`만으로 배포 파일 세 개를 재생성했던 호출자는 새 `--output-dir NEW`를 명시하고 결과를 검토해야 한다. 같은 폴더 덮어쓰기는 지원하지 않는다. 실행 cwd가 입력 폴더에서 임시 폴더로 바뀌어 상대 파일에 의존하는 notebook은 이 계약의 대상이 아니다.

## 범위와 한계

현재 2주 worked example은 A/B의 알려진 네 행(a1,a2,b1,b2), 대체 평균4/scale√2, 의도적 누수 평균9를 유지한다. G/H는 별도 4주 후보 확장이며 이 검증기의 숫자를 임의로 바꾸거나 의무화하지 않는다. 독립 연습의 교사 유한사례 검사와 실제 학생 답안/성취는 다르다.

사전검사는 학생 칸이 정확히 하나이고 원래 주석 템플릿이며 저장 출력이 없음을 커널 실행 전에 확인한다. 기존 comment-only cell의 execution_count=7은 허용한다. AST만으로 빈칸이라고 판단하지 않는다.

일반 상대경로 쓰기 및 IPython/Jupyter/Matplotlib 캐시는 임시 cwd/설정 경로에 두고 정리한다. **이는 별도 OS 보안 격리가 아니다. 임의 Python notebook은 절대경로로 입력이나 다른 파일에 접근할 수 있다.** 이 검사기는 신뢰된 notebook 전용이며, 악성/비신뢰 notebook의 절대경로 접근 차단이나 무쓰기 보장을 주장하지 않는다.

회귀 검사는 임시 복제본에서만 실행한다. 원래 작업본의 검사기 실행으로 배포 파일을 갱신하지 않는다. 결과와 raw traceback, 파일 SHA/소스·ID 보존 검사는 `results.json`과 `run_regressions.py`를 참조한다.

보고서의 이전 `test_labels_and_scores_in_student_notebook: false`는 임의 입력에 대한 실제 검색 결과가 아니었다. 이제 미검사를 뜻하는 `null`과 설명 필드를 반환한다(기존 boolean 소비자는 이전 필요). 별도 `teacher_qa_removed_from_artifacts: true`만 실제 셀 제거 후조건에 근거한다. `-O`/`PYTHONOPTIMIZE` 실행은 QA assert 제거를 막기 위해 실행 전 명시 거부한다.

`artifacts` 보고 필드는 실제 직렬화한 실행 notebook 및 HTML의 파일명을 키로 SHA-256과 바이트 수를 기록한다. 같은 bytes를 새 디렉터리에 쓴다. `input_sha256`은 읽었던 원본 bytes이며 실행 산출물 SHA와 다를 수 있다. validation.json 자체는 자기 참조 해시를 포함하지 않는다. 재현 실행기는 `--python /path/to/existing/python`으로 준비된 환경을 지정할 수 있고, 기본값은 이 작업에서 승인받은 기존 venv 실행 파일이다. 패키지 설치·수정은 하지 않는다.

동일 실행의 출력이 서로 다른 stream 메시지 조각으로 도착할 수 있어 인접한 같은 stdout/stderr stream만 합친다. 텍스트와 순서, display/그림 output은 보존한다. 최초 재현 비교의 바이트 차이는 `reproduction-diff.json`에 보존했다.

이 검증기의 교사 QA는 기존 A/B worked example과 별도 독립 연습의 유한 사례를 검사한다. 새 `known_train_4w` 및 4주 그룹 CV의 가능성은 이 검증기가 검사하지 않으며 작성자·독립 검토의 별도 결과가 필요하다. 보고서에도 이를 명시한다.

## 최종 후보 결과

- 검증기 SHA: `bcb7c3be3f0dcc4405ac8e1971ff932ba363d660949af8740a249acc3fa4fe5a`
- 검사한 본문 실행 후보 SHA: `7bfe0429035c3a5a96bf6be5ceac63eaa34e8f212567e96dcf3447b6d67fa997`
- 최종 후보 임시 사본 33/33 회귀 통과: `candidate-final-results.json`. 정상·학생칸 가드·실질적 QA 오류·경로 거부·코드/QA/렌더/출력 실패·입력/기존 출력 SHA·캐시 정리를 분리해 기록했다.
- 인접/분리/metadata/출력 순서의 합성 반례 9/9 통과: `stream-coalescing-results.json`.
- 최종 두 NEW 출력의 notebook 및 HTML은 바이트 SHA까지 일치했다. 모든 숫자 QA도 두 실행에서 통과했으며, report의 파일별 SHA/bytes는 실제 출력과 일치했다. report의 output_directory는 실행별로 다를 수 있다.
- 이전 후보의 stream 조각 차이 조사와 초기 결과는 삭제하지 않고 보존했다. `results.json`은 산출물 manifest/stream 정규화 전 baseline 32개 결과이며 최종 판정은 `candidate-final-results.json`/`final-summary.json`이다.
- 일반 소켓 커널은 baseline에서 한 번 시도했으나 환경의 `Operation not permitted`로 kernel_info 전 사망했다. 의미 검출 성공으로 세지 않으며 재시도/우회하지 않았다. traceback과 그 실패의 원본 보존 증거는 `baseline-first-results.json`에 있다.
- 이 작업은 커밋·푸시하지 않았다. 이후 원본 notebook SHA가 달라지면 그 bytes로 최소 정상/학생칸 가드/NEW 생성 경로를 다시 확인해야 한다.
