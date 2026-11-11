# 2주차 ROC-AUC 작성자 기록

이 기록은 작성자의 구현과 유한 사례 검증이다. 학생의 이해·독립 성취·수업 및 자습 소요시간을 관찰하지 않았고, 별도 독립 검토의 결과를 대신하지 않는다. 기존 2주 ROC 예제와 독립 문제를 확장했으며 새로운 대형 필수 문제는 추가하지 않았다. 실제 과제량 증가와 중학생의 완수 가능성은 미측정이다.

## 현재 산출물과 SHA-256

| 파일 | SHA-256 |
|---|---|
| `lessons/week02/week02_prediction_evaluation.ipynb` | `dd360d9b78c8273253a688769bc14a4948dc4d8f89369da6c1f291e47a7e27a9` |
| `lessons/week02/week02_prediction_evaluation.html` | `40d1c41d88ffcdde6fa6726dab6e6f6811d9544cfcd6817b22878051c5ed0f6e` |
| `lessons/week02/week02_temporal_preprocessing.ipynb` | `8b7ded5749a9f5f8c16a00112ead4e13ed4c3f1749c121ef056631c52ba0e55c` |
| `lessons/week02/week02_temporal_preprocessing.html` | `fe8a10b1d50980fc6585fb6996efd1bbefbfe85d9f3c907ec7bdd5b5b5f5aadc` |
| `lessons/week02/teacher-notes.md` | `f91a29f97e4a94fdff7665d0cde8820efd7cff8f7cb74de15fb7a5d405771412` |
| `lessons/week02/week02_temporal_preprocessing_teacher.md` | `8f628190234ef0791e8d5249be9eea74e5a1ddd545713531a8db82345149a902` |
| `lessons/week02/build_week02.py` | `d4c16c27bfc158b7a495ff48b19a2b9f441cecb1383e4d1363cc78029e0bddc5` |

시작 HEAD는 `c56607716dcf198eb53cd3beb28ebcdf4b6aed3b`이고, 변경 직전 2주 경로에 기존 dirty 파일이 없음을 확인했다. 변경 전 노트북·HTML·해설·생성기와 기존 두 validation 보고서는 이 디렉터리의 `baseline-*` 파일로 원바이트 보존했다. 1주 교안, 공유 `curriculum/student-plan.html`, 기존 검토 이력은 수정하지 않았다.

본문의 기존 네 행에서 ROC-AUC의 양성–음성 쌍 비율, 사다리꼴 면적과 실제 두 API를 연결하고 F1·정확도·보정과 구분했다. 면적 공식과 두 폭의 손계산은 먼저 계산을 요청한 뒤 나오는 기존 해설에 넣었다. 보충의 기존 독립 과제는 이종 라벨 동점·미상 라벨 제외·단일 클래스 조건을 포함하되, AUC 정답은 학생 과제 전에 공개하지 않았다. 기존 새 개체/시계열 계약과 같은 로봇의 독립 snapshot인 Robot Chasing 계약의 비교를 기존 독립 분할 질문에 통합했다. 본문의 누수 문구는 검증 입력을 전처리 `fit`에 섞는 이 사례로 한정했다.

## 작성자 검증

- [AUC 별도 검산](auc-validation.json)은 현재 7개 파일 SHA를 기록한다. 독립 `Fraction` 쌍 계산과 사다리꼴 계산을 `roc_auc_score` 및 `auc(fpr,tpr)` 실행 결과에 대조했다. 본문 3/4, 보충 예제 1/2, 보충 독립 과제 1/8, 역순 0, 올바른 순서 1, 전체 동점 1/2, 별도의 이종 동점 사례 4/9가 일치했다. AUC 0.5인 보충 예제의 ROC는 대각선 전체와 다르다. 이 기록에는 학생 독립 과제의 답이 있으므로 학생에게 제공하지 않는다.
- 점수를 고정해 임계값만 0.5→0.3으로 바꾸면 본문 F1은 1/2→4/5이나 AUC는 3/4로 유지된다. 점수와 임계값을 함께 +1 하면 판정이 같고, 점수만 +1 하고 임계값 0.5를 유지하면 F1은 2/3으로 달라진다. 0을 미상으로 가정한 별도 사례는 미상을 제외하면 AUC 1, 잘못 음성으로 바꾸면 1/2이다. 양성이나 음성 하나만 있는 경우의 AUC는 수학적으로 미정의이며 실제 scikit-learn 1.8.0은 `UndefinedMetricWarning`과 NaN을 반환했다. 다른 버전의 오류·경고 처리와는 구분한다.
- [기존 4주 교차검증 및 새 입력 회귀](week04-regression-v3.json)는 현 notebook 두 개의 SHA에 결합됐다. A/G와 B/H의 학습 fold는 각각 4행·양 클래스이며 전처리 fit 평균은 3과 16/3이다. 로지스틱과 kNN `k=3`의 fit/predict, 확대 Dummy의 실제 8행 fit 및 표준화 샘플 수, 라벨 없는 입력·ID 순서·학습 통계 불변을 재확인했다. 이는 4주 교안 완성이나 성능 추정이 아니다.
- [기존 본문 검사 결과](main-validation-v3/validation.json)의 `input_sha256`은 현재 본문 SHA다. [보충 검사 결과](temporal-validation.json)는 현재 보충 notebook·HTML·교사용 해설과 검사기 SHA에 결합돼 있다. 두 검사는 기존 유한 예제와 빈 답안 템플릿을 확인하며, 새 AUC의 전체 이론·독립 과제나 학생 답안을 자동 평가하지 않는다. 새 AUC 검산은 위 별도 기록이다.
- [기존 정상·오류 주입 회귀](prior-safety-v3.json)는 현 본문 SHA에 대해 정상 사례, 답안 코드·주석·출력 주입, 미상 학습 포함, 전처리 누수, 그룹 겹침, 지표 축 반전, 별도 새 입력을 포함해 9/9 통과했다. 소켓 커널은 환경의 이전 거부에 따라 재시도하지 않았다.
- [생성기 회귀](builder-checks.json)는 현재 본문 cell ID·종류·source 일치, 두 번의 동일 생성, 기존 파일·디렉터리·심링크 거부, import 무부작용 및 출력 실패 시 부분 파일 정리를 확인했다. 생성본은 실행 출력이 없으므로 실행된 notebook과 raw SHA는 다르다.
- 저장소 단위 회귀 `python -B -m unittest discover -s tests -q`는 271개를 실행해 통과했다([stderr](unit-tests.stderr)). 실행은 본문이 최종 markdown 설명으로 바뀌는 동안 진행됐으며, 이 도구·단위 회귀 자체는 특정 notebook SHA에 결합된 판정이 아니다.
- 각 notebook을 별도 새 in-process 커널에서 전체 순서로 실행했다. 본문 25셀/코드 8셀과 보충 24셀/코드 9셀 중 예제 8셀을 실행했고, 학생 답안 칸은 코드 AST와 출력이 비어 있다. 보충 답안은 미실행이다. [HTML·빈칸 확인](html-sync.json)에서 두 HTML이 현재 notebook의 새 nbconvert 결과와 바이트 일치한다. 로컬 인터페이스 탐색에서 `Operation not permitted` 경고가 있었지만 in-process 실행과 그림 저장은 성공했다.
- 본문 [ROC PNG](main-roc-auc.png)는 notebook의 유일한 PNG 원바이트와 같고 SHA는 `7cf15e7ec7bfbcc4ff3ae938188d7aceae47809998b736cf0c5b1a15f9e017f1`이다. 부모 검토자가 축과 음영을 직접 확인했다. 이는 전체 HTML의 브라우저·인쇄 렌더링이나 오프라인 MathJax 검증이 아니다.

기존 `lessons/week02/validation.json`은 산출물 SHA가 없는 과거 기록이고, `week02_temporal_preprocessing_validation.json`은 변경 전 보충 SHA를 가리킨다. 두 원본은 그대로 두었고 현재 교안의 검증 기록으로 사용하지 않는다. 새 검증 결과는 이 작성자 폴더의 별도 파일에 있다. 교사용 정답이 저장소에 있다는 사실만으로 학생 접근이 차단되지는 않으며, 실제 최종 테스트 자료와 정답은 아직 생성·검증되지 않았다.

## 직접 읽은 공식 원문과 남은 경계

- [KOAI/IOAI 출제 기준](https://kitpa.org/koai/syllabus) 데이터 사이언스 기초 L119–132는 지표와 ROC 곡선을 명시하며 AUC를 별도 이름으로 열거하지 않는다. 페이지는 IOAI 2026 기준이라고 표시한다.
- [KOAI 2026 예시 공지](https://kitpa.org/files/36)와 연결된 PDF 7쪽의 23번은 AUC에 관한 고등부 수준의 학습 참고 예시다. 중등 기출이나 2027 출제 예측이 아니며 문항 원문은 재배포하지 않았다.
- [IOAI 2026 Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md) 원문의 Task·Dataset·Scoring에서 같은 여섯 로봇, 독립 snapshot, 이전 관측 부재, 익숙한 요소의 새 조합과 로봇별 점수를 확인했다. 합성 새 개체/미래 시계열 평가와 같다고 주장하지 않는다.
- [scikit-learn ROC-AUC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html), [사다리꼴 면적](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.auc.html) 및 실제 설치된 scikit-learn 1.8.0에서 양성 점수 방향과 API 실행을 확인했다. 공식 페이지의 `stable`과 저장소의 `main`은 변할 수 있다.

공유 `curriculum/student-plan.html`의 일괄적인 원본 개체 분리 표현은 예측 목적에 따라 Robot Chasing의 같은 로봇 평가와 충돌할 수 있다. 이번 2주 승인 범위 밖이므로 수정하지 않았으며 이후 과정 차원의 검토가 필요하다. 브라우저 전체, MathJax 외부 접근, 일반 소켓 Jupyter/Colab과 실제 학생 수행은 미확인이다. 이 작업의 임시 runtime/cache만 정리했고, 새 최종 테스트를 만들거나 커밋·푸시하지 않았다.
