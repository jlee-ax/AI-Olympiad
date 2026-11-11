# 2주차 교안 독립 검토 — 2026-11-11

최종 학생 노트북의 25셀을 전부 읽고, 원본을 바꾸지 않은 검토 복사본에서 새 in-process IPython 커널로 8개 코드 셀을 위에서 아래까지 실행했다. 정상본은 오류 0으로 통과했고, 의도적 오류 6건과 학생 답안 코드 주입 1건은 모두 수정된 검증기가 탐지했다. 이는 유한한 합성 예제·배포 템플릿의 확인이며 학생의 독립 수행이나 2주차 전 범위 숙달을 입증하지 않는다.

검토 원본 SHA-256:
- 학생 notebook: `52b5c170ab2c83fc29327c302e9c77e34c58bce81061c7a167228d0cc67c36e3`
- 최종 teacher validator: `f31d8057913167b87a1489034ab9b98f7a7e3e1ace801a5919762040e7260a28`
- 최종 교사용 notes: `2d9667b059f1556613117ce6648fe16b3c6c67c4c0a7cdf2b2be06fd0f6b6977`

코드 실행 당시 세 파일 해시는 검토 시작·종료 사이 같았다. 실행 당시 notes SHA는 `ac9907e60ece1f135f81bb2603f0d958a7244e61810b1316e2c6cf0bb267a7dd`이며, 이후 최종 테스트 평문 제거만 반영한 notes를 위 최종 SHA로 다시 확인했다. 학생 notebook은 빈칸 검증기 수정 전후에도 같은 SHA였다. 따라서 notebook 원본에 묶인 발견 큐의 SHA는 영향을 받지 않는다. validator나 notes를 함께 묶은 증거는 위 최종 SHA로 다시 연결해야 한다. 원본 교안·Git index를 수정하거나 commit/push하지 않았다. 실행·변이·기록은 이 새 검토 폴더 안에만 썼다.

| 핵심 시나리오 | 결과와 확인 범위 |
|---|---|
| 예측 시점 | 통과. 초안의 ‘예측 직후 reading’과 ‘알림 직후’ 모순을 보고했고 최종본은 측정 직후 예측 시점 제공 입력으로 통일됐다. row_id/group/label을 모델 입력에서 구별한다. |
| 그룹 분할 | 통과. 훈련 A/B와 검증 C/D의 그룹이 겹치지 않고 row_id가 유일하다. 실제 최초 모델 입력은 reading 한 열이다. E/F 최종 테스트 자료는 학생 notebook에 없다. |
| 시간 분할 | 설명·서술 과제는 적절하다. 실제 timestamp 기반 분할·시간 역전 자동 검사는 이 notebook에 없으므로 실행 검증은 미완료다. Robot Chasing 원문의 독립 snapshot을 에피소드로 오해하는 주장은 없다. |
| 훈련 전용 fit | 통과. 별도 Fraction 계산의 훈련 평균 4, 대체 후 분산 2, 표준편차 √2와 실제 imputer/scaler가 일치한다. 검증을 포함한 잘못된 평균은 9다. 검증 입력을 ±1e12·결측으로 바꿔 transform/predict해도 실제 두 파이프라인의 fitted statistics가 변하지 않았다. Dummy 점수만으로 판정하지 않았다. |
| 미상 0 | 통과. b3은 지도학습 fit에서 제외되고 0을 정상 −1로 바꾸지 않는다. 알려진 행만의 혼동행렬 [[0,1],[1,1]]과 잘못 0→−1 처리한 [[1,1],[1,1]]을 확인했다. 이 규칙을 Antique에서 허용하는 반지도 특성 사용 전체에 대한 금지로 일반화하지 않는다. |
| 혼동행렬·지표 | 통과. 행=실제·열=예측, 순서 [−1,+1]에서 [[0,2],[1,1]], 정확도 1/4·정밀도 1/3·재현율 1/2. 비대칭 결과라 축·분모 교환을 구별한다. |
| 0 분모 | 통과. 상수 음성 예측의 정밀도는 미정의이고 recall은 0이다. zero_division=0/NaN 정책을 구별했다. 별도 전부 음성 truth/pred에서는 precision·recall·F1 모두 NaN, 실제 양성 없이 양성 오예측 시 precision=0·recall=NaN도 재검산했다. |
| 집단별 점수 | 통과. R1=8/10, R2=0/2에서 행 평균 2/3과 개체 평균 0.4를 구별한다. 공식 Robot 공개 자료의 각600행 균형에서는 두 평균이 같다는 설명도 정확하다. 집단 미관측 정책을 공식 규칙으로 지어내지 않는다. |
| 행 순서·ID | 통과. 검증 행을 뒤집어 다시 변환·예측해도 row_id에 연결한 예측 사전은 같다. |
| 독립 새 입력·교사용 키 | 통과(설계·계산). 교사용 키를 읽기 전에 별도 Fraction 코드로 m1,m2,n1,n2의 평균6·분산9/2·표준편차√4.5, 검증누수 평균117/4, 예측[1,−1,−1,−1], CM[[2,0],[1,1]], accuracy3/4·precision1·recall1/2를 계산했다. X/Y 행평균1/2·집단평균3/5도 키와 일치했다. 앞 예제와 같은 구조의 근거리 전이 과제이며 새 문제 전략 수립 전반을 평가하지 않는다. |
| 학생 답안 노출·성취 | 원본 코드칸은 주석뿐이고 출력이 없다. 원본 8개 코드셀 실행에는 이 빈 칸 1개가 포함된다. 학생이 새 과제 코드를 작성·실행했다는 뜻이 아니다. 별도 QA가 교사용 정답을 실행했다. 학생 산출물·도움·첫 반응·수행시간은 미관찰이다. 교사용 파일은 저장소 접근이 가능하므로 분리는 접근 통제가 아니다. 교사용 notes에 있던 E/F 최종 테스트 4개 행과 정답도 제거됐다. 실제 숨은 최종 테스트는 미생성·미검증이며 교사가 학생과 모델 선택 담당자의 접근이 차단된 별도 장소에서 새로 구성·보존해야 한다. 이미 공개된 수치·정답은 최종 독립 평가에 재사용하지 않는다. |
| 수업·자습·최종 경계 | 편성 합계 통과. 이론30+비코딩30+코딩60=120분, 독립 필기10·코딩10은 그 안에 포함. 자습 120~150+120~150+60~90+60~90=360~480분이다. 실제 중학생 완수시간은 미관찰. 4주차 필수 자습의 설정 선택 후 최종 테스트를 한 번 쓰라는 경계는 학생/교사용 자료에 일치한다. 실제 4주차 운영은 미검증이다. |

초안에서 preprocess 누수·미상 훈련 포함·CM 순서 반전·precision/recall 교환은 notebook assert가 탐지했지만, 검증자료로 baseline을 fit한 변이와 ROC의 ≥를 <로 바꾼 변이는 통과했다. 저자가 실제 Dummy 파이프라인 통계와 임계값별 실제 ROC 혼동행렬 검사를 추가한 뒤 같은 6건을 최종 복사본에 재적용했다. 최종판에서는 전부 AssertionError로 실패했으며 정상본만 성공했다.

추가로 검증기가 output 없는 `x_student=1` 답안 코드를 허용하면서 answer_cell_filled=False를 고정 기록하는 결함을 발견했다. 최종판은 실행 전에 AST body 유무로 실제 코드를 판정한다. 주석만 있는 정상본은 성공하고 `x_student=1` 변이는 커널 실행 전 실패했다. 이전 결함과 최종 수정의 증거를 모두 남겼다. 임의의 의미 오류를 자동 탐지하는 일반 검증기로 평가하지 않는다.

학생 출력은 전체 텍스트 약1,017자로 짧고 각 코드셀 출력은 200자 이하이며 NumPy scalar wrapper를 제거했다. 셀의 표·수식·설명을 읽었으나 브라우저/인쇄 시각 렌더링은 독립 확인하지 않았다. HTML은 외부 MathJax CDN에 의존하므로 완전 오프라인 수식 표시는 미검증이다. 일반 소켓 Jupyter 커널·Colab도 이번 독립 실행의 대상이 아니다.

중앙값·one-hot·최소최대 정규화·forward-fill·sliding window는 자습 지시로만 있고 해당 실제 구현·학생 수행은 검증하지 않았다. 따라서 이번 확인은 계약→그룹분할→평균대체·표준화→기준예측→검증지표라는 국소 교안의 작동 확인이다.

재현: 준비된 Python으로 `python -B reviews/week02-independent-20261111/run_review.py`를 실행한다. 원본을 읽고 이 검토 폴더의 복사본·실행환경 파일만 기록한다. 실행 로그와 각 변이 복사본은 `cases/`, 전체 수치·해시·명령·결과는 `week02-review-results.json`, 실제 학생 셀 출력은 `executed-cell-evidence.json`에 있다. 이전 빈칸 결함의 검증기는 `before-answer-guard-fix-validator.py`에 보존했다.

직접 확인한 근거: [Antique 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb), [Robot Chasing 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md), [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html), [혼동행렬 계약](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html), [정밀도·재현율·0분모 정책](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html), [그룹·시간 분할](https://scikit-learn.org/stable/modules/cross_validation.html), [ROC 계약](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html). 문서는 조회 시1.9.1, 실제 실행은 scikit-learn1.8.0이었다.
