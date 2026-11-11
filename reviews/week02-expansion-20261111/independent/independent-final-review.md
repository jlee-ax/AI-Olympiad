# 학생용 문구 정리·2주차 확장 독립 검토 — 2026-11-11

수정 대상 학생용 notebook/HTML에서 시간 배정·실측·교사용 운영 배치 문구가 제거됐고, 코드와 예측 시점·평가 경계의 의미는 보존됐다. 기존 1주 보충과 2주 교안을 새 in-process 커널에서 재실행했다. 신규 2주 보충은 최종 SHA `a830a15e8d2bf2cb91e17cd2e8b14172390fc7cea3a07539add3fe52a05b5865`에서 19셀을 모두 읽고 9개 코드 셀을 순차 실행해 통과했다. 이 중 8개는 예제 코드이고 1개는 주석뿐인 학생 답안 칸이다. 정상 시나리오 10개와 오류 소스 변이 14개를 확인했으며, 현재 추가 본문 변경이 필요한 차단 결함은 발견하지 못했다.

| 자료 | 최종 독립 확인 |
|---|---|
| 기존 1주 보충 `1c3ccb5d79d5e6c0a1cb919fd9f8cfac723637b1dedac2d056fe45379ffd8847` | 29셀/13코드 새커널 실행, 48개 질문·후보 ID 공동순열 및 기존8개 변이 재확인. prechange와 코드셀 source·ID는 동일하다. |
| 기존 2주 `9bb1ea5110b74ea1cf32fbc9ee9e9a5aadbceba2f750c2dfc2d6587e18954bdf` | 25셀/8코드 새커널 실행, 기존6개 오류 변이와 답안 코드 주입 guard 재확인. prechange와 코드셀 source·ID는 동일하다. |
| 신규 2주 `a830a15e8d2bf2cb91e17cd2e8b14172390fc7cea3a07539add3fe52a05b5865` | 19셀/9코드(예제8+빈답안1) 새커널 실행, 별도 list/Fraction 구현·10개 정상 시나리오·14개 오류 변이 확인. source notebook/HTML/key/validator4파일은 실행 전후 불변이다. |

학생 문구 검토는 키워드 검색 뒤 의미를 읽는 방식으로 했다. 분·시수·시간 배정, 편성, 실측, 교사용 진도 조정 등의 잔여는 수정 대상 notebook과 HTML에서 없었다. Jupyter 실행·저장법, 문제 자체의 계산·설명 지시, 독립 응답과 도움 기록은 학습에 필요한 문구로 구별했다. 예측 시점, 관측 시각, 과거/미래, 시간순과 윈도 길이는 학습 개념이므로 보존됐다. HTML의 각 셀 표시 텍스트는 해당 최종 notebook의 새 export와 일치했다. 기존 1주 본교안의 ‘수업 밖 필수 연습’ heading은 여전히 있으나, 부모가 기존 원본 보존을 위해 이번 수정 범위에서 제외하라고 지시해 잔여 관찰로만 기록했다. 교육과정 계획표 자체의 시간 편성은 이번 학생 교안 정리의 수정 대상이 아니다.

신규 보충본의 핵심 결과는 다음과 같다.

| 시나리오 | 결과·실행 증거 |
|---|---|
| 예측·도착 시점과 분할 | 통과. t 측정 전 예측·측정은 해당 예측 뒤 도착·정답은 날 끝에 도착한다는 계약을 따른다. A/B 목표 t4,5의 라벨이 t6 전에 알려진다는 가정 아래 C/D t6,7을 평가한다. 새 개체 미래라는 목적에서 그룹·목표 시각을 함께 나누되, 모든 과제에 두 조건을 일괄 강제하지 않는다. |
| strict `< t`·그룹·전체 관측 범위 | 통과. 각 목표마다 현재/미래 값과 다른 개체 값을 크게 바꾸어도 특성이 불변이었다. 전체 원본으로 계산한 결과와 그 개체의 허용된 prefix만 준 결과가 같았다. 20개 원본 행 순서에서도 결과가 같다. 첫 관측 전/과거 전부 결측/원본 관측3개 미만은 결측을 유지하며, 중복 개체·시각은 ValueError다. |
| 온라인·일괄 예측 차이 | 통과. 온라인 검증 recent는 [8,12,1,7], t6 이전에 한꺼번에 예측하는 cutoff에서는 [8,8,1,1]이다. t6 측정이 t7 전에 도착한다는 명시 계약에 의해서만 전자를 허용한다. 이 문맥은 전처리 fit에 들어가지 않는다. 늦은 도착을 다루는 실제 서비스 전반을 검증한 것은 아니다. |
| ffill·최근 원본 관측 윈도 | 통과. 별도 list/sum/Fraction 구현으로 원본 ID·시각과 모든 recent/mean3/std3를 재계산했다. A4 [2,4,6]은 평균4·분산8/3, A5 [4,6,4]는 평균14/3·분산8/9. C6은 [3,5,8], C7은 [5,8,12]를 쓴다. ffill 복제값을 원본 관측 횟수에 넣지 않는다. 이 단원의 윈도는 ‘최근 비결측 원본 관측3개’이며 고정된 달력3칸과 같다는 주장은 없다. |
| 훈련 통계·중앙값·MinMax | 통과. train recent [6,4,결측,2]의 중앙값4·min2·max6; mean3 중앙값13/3, std3 중앙값(√(8/3)+√(8/9))/2도 별도 계산과 같다. 검증 극단값·미지 범주를 transform해도 통계·범주 목록이 바뀌지 않는다. 검증 recent8→1.5, 1→−0.25이므로 기본 MinMax가 검증을 반드시[0,1]로 제한한다는 오해를 반증한다. |
| 미지 범주·같은 shape의 잘못된 fit | 통과. train blue/red의 열 의미가 고정되고 green은 두 열0이다. 기본 unknown 오류와 ignore, drop='first'의 알려진 생략 범주/미지 범주 영벡터 모호성을 확인했다. 별도 train red/blue와 val green/blue의 개별 fit은 열 수2가 같아도 열 이름과 의미가 달라진다. |
| 독립 새 표·중앙값 구별 | 통과. M/N train recent [9,9,결측,1]은 median9·range[1,9]이고 결측 훈련 행의 scaled recent는1이다. 평균19/3을 대신 쓰면 이 값은2/3이 되어 구별된다. M4 평균7·분산8/3, P6 평균9·분산8/3; 검증 점수는 [5/4,2,−1/8,5/4]로 실제 float에서도 정확히 같다. bronze는[0,0], gold는[1,0]이다. 손계산과 코드·해설이 일치한다. |
| CM·F1·0분모·ROC 동점 | 통과. 독립 Fraction 계산과 실제 함수가 일치한다. 본 예제 threshold1.5의 TP/FP/TN/FN=(2,1,1,0), accuracy3/4·precision2/3·recall1·F1 4/5. 새 표의 threshold2는(0,1,1,2), 5/4는(1,2,0,1), −1/8은(2,2,0,0)이다. 동점은 함께 움직이며 새 표 ROC는 (0,0), (1/2,0), (1,1/2), (1,1), AUC1/8이다. 실제 양성/음성 또는 양성 예측이 없을 때의 None 보고와 분모0을 구별했다. |
| 실제 ROC 그림 | 통과. 코드의 선 좌표가 계산된 FPR/TPR와 같고 축 이름도 맞는다. 최종 학생 notebook에 ROC PNG가 저장돼 있다. 그 PNG를 실제 이미지로 열어 네 점·임계값·축의 가독성을 확인했다. HTML 전체의 브라우저 CSS·MathJax 렌더링을 확인한 것은 아니다. |
| 정답 기준 가중점수 | 통과. 실제 truth/pred 배열을 별도 Fraction 구현으로 계산했다. 새 U는 행정확도3/4·가중3/7, V는5/8·11/14이며 분모14는 모든 실제 B6·T2에서 나온다. 예측 기준 가중치와 맞힌 행만의 분모는 다른 결과를 내며 변이 검사에 걸렸다. 0·음수·NaN·inf 등은 거부하고, 1e308/1e-308의 유한 양수에서도 전부 정답1·전부 오답0을 확인했다. 공통스케일 합산에는 약1e-16의 순서 반올림이 있을 수 있어 평가값은 허용오차로 비교한다. 예측 임계값 `>=`를 허용오차 판정으로 바꾼 것은 아니다. |

14개 오류 변이는 현재 시각 포함, 개체 경계 제거, 시간 역정렬, 정렬 제거, ffill 복제값을 관측으로 계수, 표본표준편차 사용, 중앙값 대신 평균, backward-fill, 훈련+검증에 fit(행 수 유지), 검증에서 재fit, 범위 밖 clip, `>=`를 `>`로 변경, 예측 기준 가중치, 맞힌 행만 분모로 사용한 경우다. notebook 내장 assert가12개를 탐지했고, 원본 관측/복제값 윈도와 평균/중앙값2개는 주 예제 assert만으로 통과했으나 별도 새 자료 oracle가 탐지했다. 모든 의미 오류를 notebook 스스로 감지하는 범용 검증기로 평가하지 않는다.

검토 과정에서 발견되거나 부모 검토로 전달된 결함은 수정 후 재확인했다. 초기 독립 문제의 min1/max7에서13을 변환하면1.9999999999999998이 되어 threshold2의 손계산과 판정이 달랐다. 최종판은 범위8·이진수로 정확히 표현되는 임계값을 사용하고 일반 데이터의 부동소수 경계 정책 필요성을 설명한다. 처음에는 저장 표 출력·ROC PNG와 실제 배열 기반 가중 계산이 없었으나 최종판에 추가됐다. 가중치 NaN/inf 허용과 부동소수 결과의 exact assert도 수정돼, 유한 양수 guard와 원/역순 근사 비교를 재확인했다. 이전774f의 반올림 증거는 별도 JSON에 보존했다.

기존 계획·공식 원문과의 정합성도 확인했다. 현재 국내 [KOAI/IOAI 기준](https://kitpa.org/koai/syllabus)은 IOAI2026 기준 표기이며, 지표·ROC·one-hot·sliding window·평균/표준편차·평균/중앙값/forward-fill·정규화/표준화·분할을 요구한다. 기존2주와 새 보충을 함께 보면, 이전에 자습 지시만 있던 중앙값·미지 범주·MinMax·시계열/윈도·F1/ROC 그리기에 실제 코드와 독립 문제가 생겼다. 앞 교안의 평균대체·표준화·Dummy·미상 라벨·집단 평균을 다시 완료했다는 것으로 대체하지 않는다. [Radar 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Radar/Radar.ipynb)의 실제 배경1·비배경50 및 전체 가능한 점수 분모를 확인했다. 교안의1·5와1·4는 별도 합성 예제이며 실제 레이더 분할이나 H01 모든 맥락을 해결한 것으로 취급하지 않는다.

[scikit-learn 누수 지침](https://scikit-learn.org/stable/common_pitfalls.html), [MinMaxScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html), [OneHotEncoder](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html), [ROC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html), [NumPy std](https://numpy.org/doc/stable/reference/generated/numpy.std.html), [pandas ffill](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ffill.html)의 계약과 비교했다. 새 학생본의 sklearn1.3+ 조건은 sparse_output과 첫+∞ ROC 임계값에 맞는다. 실제 실행은 Python3.12.14·sklearn1.8.0·NumPy2.5.4·pandas3.1.1이다.

남은 검증 한계는 다음과 같다. 학생 답안은 AST와 출력이 비어 있어 코드 실행 성공을 학생 독립 성취로 보지 않는다. 문제는 새 수치·범주·관측 패턴의 근거리 전이이며 임의의 실제 문제 해결력은 미관찰이다. 교사용 답과 검토자료는 공개 저장소의 파일 분리만으로 숨겨지지 않는다. 실제 숨은 최종 테스트는 아직 생성·확보·독립 보관되지 않았다. 기존 계획의120분·자습6~8시간과 연결하는 보충이라는 운영 설명은 교사용 자료에 유지되지만, 새 총부담·중학생 실제 소요시간·완수 가능성은 측정하지 않았다. 이 실행으로 기존 시간 안의 완료를 보장하지 않는다. 일반 소켓 Jupyter·Colab·HTML 전체의 브라우저 시각·오프라인 MathJax는 미검증이며 정책 제한을 우회하지 않았다.

재현 코드와 결과는 이 폴더 안에 있다. `review_student_cleanup.py`는 문구·코드 보존·HTML 동기화, `run_existing_week01_bridge_review.py`와 `run_existing_week02_review.py`는 기존 정리본 실행, `run_temporal_review.py`는 신규 전체 커널·별도 계산·14변이·PNG·HTML을 확인한다. 지정 venv Python으로 실행하며 원본은 읽기만 하고 새 독립 검토 폴더의 복사본·결과만 쓴다. `student-cleanup-results.json`, `week01-bridge-results.json`, `week02-review-results.json`, `temporal-review-results.json` 및 `temporal-roc.png`가 주요 증거다. 실행 캐시·history.sqlite·복제 HTML은 정리했고 실제 교안·Git index 수정, commit/push는 하지 않았다.
