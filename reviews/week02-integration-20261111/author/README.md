# 2주차 작성자 기록

이 기록은 작성자의 설계·유한 사례 검증이다. 독립 검토나 실제 학생의 수행·소요시간을 대신하지 않는다. 1주와 공유 계획 파일은 수정하지 않았다. 두 노트북 및 HTML, 두 교사용 문서, 생성기만 작성자 범위에서 변경했다. 두 validator의 현재 구현과 그 별도 검토는 다른 작성자가 소유한다.

## 현재 후보

| 파일 | SHA-256 |
|---|---|
| `lessons/week02/week02_prediction_evaluation.ipynb` | `7bfe0429035c3a5a96bf6be5ceac63eaa34e8f212567e96dcf3447b6d67fa997` |
| `lessons/week02/week02_prediction_evaluation.html` | `786fdc0319070d3c4953a5ccf888e1205146055d0e1d4a58fcd67e229820a42c` |
| `lessons/week02/week02_temporal_preprocessing.ipynb` | `b5f555d8d089b5856f952f74f683fc44bd8404c6449c355f1e48b4a25f98477c` |
| `lessons/week02/week02_temporal_preprocessing.html` | `0b45f63af46cbfe25b06ae95a4d8688ac3d9f720246eadcd9200f37f3caff90d` |
| `lessons/week02/teacher-notes.md` | `9f25ba75e0956042be5862850f0a00cbfa94cb4846fa85d8694ff77c0dbc294a` |
| `lessons/week02/week02_temporal_preprocessing_teacher.md` | `56c185091604d90799e3b8cf62ed12be29013e87029834d7b8c3489b0a6f23d3` |
| `lessons/week02/build_week02.py` | `45763bd5f44e06e7c3684169f9ca9ba0bb1d103acbbb53ec571b93a018164cb9` |

A/B 수업용 4개 알려진 행, 기존 평균·표준편차·누수 반례 9 및 C/D 검증은 유지했다. G/H 추가 후보를 같은 원본의 재사용 가능한 행으로 제공하고, 4주에는 A/B/G/H로 전처리·모델·기준 모델을 다시 fit하도록 명시했다. E/F 최종 테스트는 데이터와 정답을 생성하지 않았다. 보충 과제에서 그룹·시각 분할을 직접 정하고 검증 F1과 사전 동률 정책으로 임계값을 선택·고정한 다음 라벨 없는 연습 입력을 처리한다. 본문과 보충의 서로 다른 예측 시점과 필수 연습 경로를 연결했고, 본문의 기존 독립 과제에 선택형 둘과 짧은 서술을 포함했다.

## 작성자 확인과 범위

- [별도 유한 검산 결과](independent-checks.json)는 후보 notebook의 SHA에 결합됐다. A/G와 B/H의 2-fold에서 각 학습 4행의 ID·그룹 비중복·양 클래스·`scaler.n_samples_seen_=4`, 대체 평균 3과 16/3, 로지스틱과 kNN `k=3`의 fit/predict를 확인했다. 전체 후보의 Dummy 재fit은 알려진 8행 ID와 `n_samples_seen_=8`을 확인했다. 작은 예제의 안정적 성능이나 4주 교안 완성을 뜻하지 않는다.
- 동일 기록에서 검증 F1 동률의 사전 정책과 라벨 없는 R/S/U 예측, 새로운 W/Z/V 입력의 예측·ID 순서·훈련 통계 불변을 확인했다. [CLI 점검](candidate-cli-checks.json)은 `check_candidate.py`의 기본 stdout, 명시한 `--output NEW` 및 기존 결과 재지정 거부를 확인한다. 기존 기록은 덮어쓰지 않았다. 이는 `teacher_validate_week02.py`와 별도 검산이다.
- [생성기 검사](builder-checks.json)는 두 새 경로에서 같은 생성 바이트, 25개 기존 셀 ID·종류·source 일치, import 무부작용, 기존 파일·디렉터리·심링크 및 일치하지 않는 source 거부를 확인한다. 생성 중 일부 바이트를 쓰고 발생시킨 오류가 부분 파일을 정리하는지도 확인했다. 생성본은 실행 출력이 없는 notebook이므로 실행본과 raw SHA가 같다는 뜻이 아니다.
- `execute_candidate.py`로 두 후보를 각각 새 in-process 커널에서 위에서 아래로 실행했다. 본문 25셀 중 8코드를 실행했고 학생 코드칸은 주석과 빈 출력이었다. 보충 24셀 중 예제 코드 8셀을 실행했으며 독립 답안 코드칸은 실행하지 않고 비워 두었다. 각 notebook에서 다시 HTML을 내보낸 결과는 저장된 해당 HTML과 바이트가 같았다. [보충 PNG](temporal-roc.png)의 축과 표시를 직접 확인했다. 이는 HTML 전체의 브라우저·인쇄 시각 확인이나 오프라인 MathJax 확인이 아니다. 실행 시 로컬 인터페이스 탐색에서 `Operation not permitted` 경고가 있었지만 in-process 실행과 이미지 저장은 끝났다.
- [보충 후보 복제본 검사](temporal-check-02.json)는 당시 별도 사본의 이전 검사기 SHA `fd7071e8…`로 후보 `b5f555d8…`의 저장 출력과 유한 사례를 확인했다. 이 검사기의 고정 `saved_output_capture` 문자열은 빈 답안을 실행했다고 쓰지만, 실제 저장한 독립 답안의 실행 번호는 `null`이며 출력도 없다. 이 검사 당시 보충 해설은 `ac2be76a…`였고 이후 검사기 사용 안내를 고친 현재 해설은 `56c18509…`다. 따라서 이 기록은 현재 해설의 최신 전체 결합 검증도 아니다. 이후 별도 담당자가 보충 검사기를 수정했으므로 위 기록을 그 새 검사기의 검증으로 승격하지 않는다.
- 본문 검사기는 `--notebook candidate-main.ipynb`에서 기본 stdout과 새 출력 디렉터리 모드가 각각 exit 0이었다. 실제 새 출력은 `candidate-main.ipynb`, `candidate-main.html`, `validation.json`이며 입력 SHA는 `7bfe0429…`다. [stdout 기록](main-validator-stdout.stdout)과 [새 출력 기록](main-validator-new_output.stdout)을 보존했다. 작성자 보조 wrapper `check_main_validator.py`는 출력명을 기본 notebook 이름으로 잘못 가정해 두 성공적인 subprocess 뒤에 자체 assertion으로 실패했으므로 wrapper의 exit 1을 검사기 실패나 통과로 바꾸어 기록하지 않는다. 본문 검사기 자체는 4주 CV를 검사하지 않는다고 명시한다.

기존 `validation.json`과 `week02_temporal_preprocessing_validation.json`은 각각 [기존 본문 보고서](baseline-main-validation.json), [기존 보충 보고서](baseline-temporal-validation.json)에 원바이트 보존했다. 전자는 산출물 SHA가 없고 후자는 이전 notebook SHA를 사용하므로 현재 후보 pass로 해석하지 않는다. 초기 notebook과 생성기도 이 폴더의 `baseline-*`로 보존했다. 작성 중 만든 `runtime-main`, `runtime-temporal` 캐시는 검증 후 삭제했다.

현재 학생 응답·도움·완수 시간과 숨은 최종 테스트의 독립성은 미관찰이다. 일반 소켓 Jupyter/Colab과 HTML 전체 브라우저 시각 검증도 이번 실행 범위가 아니다. 작은 합성 사례·단위 검사·정적 HTML 비교는 이 한계를 해소하지 않는다.
