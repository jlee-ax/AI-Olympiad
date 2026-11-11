from pathlib import Path

def replace_once(s,a,b):
 if s.count(a)!=1:raise ValueError((a[:80],s.count(a)))
 return s.replace(a,b,1)

p=Path('lessons/week02/teacher-notes.md');s=p.read_text(encoding='utf-8')
s=replace_once(s,'학생 교안은 `week02_prediction_evaluation.ipynb`입니다.', '학생 교안은 `week02_prediction_evaluation.ipynb`, 이어지는 필수 연습은 `week02_temporal_preprocessing.ipynb`입니다.')
s=replace_once(s,'기존 2주차 계획에 맞춰 이론 30분, 비코딩 30분(이 중 필기 10분), 코딩 60분입니다. 자습 6~8시간은 별도입니다. 모든 세부 시간과 독립 문제에 배정한 10분+10분은 **제안이며 실측하지 않았습니다**. 학생의 실제 수행을 관찰해 조정하고 소요 시간과 도움을 기록합니다.', '기존 2주차 계획에 맞춰 이론 30분, 비코딩 30분(이 중 필기와 해설 10분), 코딩 60분입니다. 자습 6~8시간은 별도입니다. 본문 독립 과제의 선택형 2문항·짧은 서술 1문항과 피드백은 기존 필기 시간에 넣고, 추가 필기와 코딩은 기존 코딩·필수 자습에 연결합니다. 이는 편성 제안이며 **실측하지 않았습니다**. 학생의 실제 수행을 관찰해 조정하고 소요 시간과 도움을 기록합니다.')
s=replace_once(s,'\n## 수업 예제 해설','''
## 두 자료의 경로와 4주 준비

본문의 필수 연습 1~4는 본문 2·6·7절과 보충 1~4·6절을 가리킵니다. 목록과 해당 보충 문제를 별도로 두 번 제출하라는 뜻이 아닙니다. 다만 평균/표준화와 중앙값/MinMax, 미상 정답과 미지 범주, 행/개체 평균과 정답 가중 점수, 두 예측 시점은 서로 다른 목표입니다. 본문은 측정 직후라 그 측정이 제공되고 보충은 측정 전이라 같은 시각 측정이 허용되지 않습니다. 두 사례의 계약을 학생이 비교하게 합니다.

같은 합성 원본의 추가 훈련 후보는 G의 `(2,-1),(4,+1)`와 H의 `(4,-1),(6,+1)`입니다. 본문의 `records`·`known_train`은 A/B worked subset으로 그대로 두며, `additional_train`, `course_records`, `train_4w`, `known_train_4w`가 4주에 재사용할 후보를 제공합니다. C/D는 검증, E/F는 아직 자료와 정답이 없는 최종 테스트 자리 표시입니다. 4주에 A/B/G/H의 알려진 8행을 쓴다면 전처리와 모델을 다시 fit하고 Dummy 기준 모델도 그 훈련 조건으로 다시 계산해야 합니다. 2주 A/B의 fitted 객체를 재사용한 점수와 4주의 다른 훈련 조건을 같은 비교로 취급하지 않습니다.

2-fold 그룹 교차검증의 한 결정적 분할은 A/G 대 B/H입니다. 각 학습 fold는 4행이고 두 라벨을 포함합니다. A/G에서 훈련한 대체 평균은 3, B/H에서는 16/3입니다. 전처리는 **fold마다** 훈련 부분만 fit합니다. 예컨대 `k=3`은 두 학습 fold의 4행에 대해 유효하지만 4보다 큰 k는 유효하지 않습니다. 그룹 분리, 양 클래스, 각 fitted 통계 및 실제 fit/predict 결과는 새 검사기의 결과에서 확인합니다. 이 작은 구성은 방법의 작동 확인이며 4주 교안 완성이나 성능의 신뢰할 만한 추정이 아닙니다.

## 수업 예제 해설''')
s=replace_once(s,'## 독립 과제 답안·관찰 기준\n\n수업 예제를 가리고', '## 독립 과제 답안·관찰 기준\n\n선택형 1의 답은 가(알려진 훈련 m1,m2,n1,n2), 선택형 2의 답은 가(정밀도 정의 불가, 재현율 0)입니다. 짧은 서술에서는 개체가 겹쳐 새 개체 평가가 아닌 문제와 예측 후 수리 결과를 입력에 넣는 시간 누수를 각각 확인합니다.\n\n수업 예제를 가리고')
s=replace_once(s,'훈련 A/B와 검증 C/D에 속하지 않는 새 개체의 최종 테스트 자료와 정답을 별도로 구성하고', '훈련 후보 A/B/G/H와 검증 C/D에 속하지 않는 새 개체의 최종 테스트 자료와 정답을 별도로 구성하고')
start=s.index('`teacher_validate_week02.py`는 nbformat 형식 확인')
end=s.index('\n원문 조회 2026-11-11:',start)
s=s[:start]+'''`teacher_validate_week02.py`의 기본 실행은 원본을 쓰지 않고 검사 결과를 stdout에 출력합니다. 예를 들어 저장소 루트에서 `python -B lessons/week02/teacher_validate_week02.py --inprocess`를 실행합니다. 산출물이 필요하면 `--output-dir /existing-parent/NEW-name`을 더해 아직 없는 새 디렉터리를 지정합니다. 그 안에 실행한 `week02_prediction_evaluation.ipynb`, HTML, `validation.json`이 생성됩니다. `--notebook PATH`로 신뢰한 별도 사본을 지정할 수도 있습니다. 기존 경로나 심링크는 거부하며 원본 디렉터리 갱신은 지원하지 않습니다. 이 검사는 노트북 코드를 실행하므로 신뢰한 코드에만 사용합니다. 복사본과 출력 분리는 **OS 차원의 보안 격리**가 아닙니다.

기존 `lessons/week02/validation.json`은 산출물 SHA가 없는 과거 본문 실행 기록이고, `week02_temporal_preprocessing_validation.json`은 이전 보충 SHA에 결합된 기록입니다. 현재 후보 통과 근거로 간주하지 마세요. 두 원본 보고서는 `reviews/week02-integration-20261111/author/`의 `baseline-main-validation.json`, `baseline-temporal-validation.json`에 바이트 그대로 보존했습니다. 새 실행·독립 검토는 실제 대상 SHA와 결과 경로를 확인합니다. 학생 이해·성취나 수업 시간은 관찰되지 않았습니다. 브라우저 전체와 오프라인 MathJax 시각 검증은 제한될 수 있으며, 실행 결과나 HTML 구조 확인만으로 시각 검토 완료를 뜻하지 않습니다.

생성기 예시는 `python -B lessons/week02/build_week02.py --check-source lessons/week02/week02_prediction_evaluation.ipynb`(셀 ID·종류·source 비교, 무쓰기)와 `python -B lessons/week02/build_week02.py --output /existing-parent/NEW-file.ipynb`(새 파일만 생성)입니다. 기존 경로 및 심링크는 거부합니다. 생성본은 학생 셀 내용과 ID가 같아도 실행 출력·metadata가 달라 실행본과 원바이트 SHA가 같다는 뜻은 아닙니다.''' +s[end:]
p.write_text(s,encoding='utf-8')

p=Path('lessons/week02/week02_temporal_preprocessing_teacher.md');s=p.read_text(encoding='utf-8')
s=replace_once(s,'## 독립 과제 답과 피드백\n\n**1. 시점·과거.**','''## 독립 과제 답과 피드백

**0. 분할 설계.** 시각 6 전에 끝난 학습과 이후 시각 6·7의 새 개체라는 조건에서 훈련 대상은 M4/M5/N4/N5, 검증 대상은 P6/P7/Q6/Q7입니다. 훈련 그룹 {M,N}과 검증 그룹 {P,Q}의 교집합은 없고, 훈련 대상 최대 시각 5는 검증 대상 최소 시각 6보다 작습니다. P/Q의 이전 관측은 그들의 검증 시점에서만 허용된 과거 문맥이고 훈련 대상 행이나 학습형 `fit`에 섞지 않습니다. 학생이 스스로 행을 배정하고 두 조건을 검사하는지 확인합니다.

**1. 시점·과거.**''')
s=replace_once(s,'동점 5/4의 P6과 Q7은 함께 바뀝니다.', '''검증 F1 기준의 후보 $2,5/4,-1/8,-1$의 F1은 각각 $0,2/5,2/3,2/3$입니다. $-1/8$과 $-1$은 모두 양성을 예측하므로 같은 ROC 좌표 $(1,1)$입니다. 미리 정한 'F1 동률이면 높은 임계값'으로 $-1/8$을 선택해 고정합니다. 동점 5/4의 P6과 Q7은 함께 바뀝니다.''')
s=replace_once(s,'**4. 경계·코드.**', '''**고정 후 라벨 없는 연습 입력.** R8/S8/U8의 최근값은 9,0,-1이고 학습된 최소 1·범위 8로 변환하면 1,−1/8,−1/4입니다. 고정한 임계값 −1/8에 `>=`를 적용하면 행 순서별 예측은 `[+1,+1,-1]`입니다. R의 `bronze`는 훈련에 없으므로 ignore 설정에서 범주 열이 모두 0, S의 gold와 U의 silver는 훈련된 열을 사용합니다. 이 데이터에는 정답 열이 없어도 변환과 예측을 할 수 있으며, 최종 테스트가 아닌 연습입니다. 이 입력으로 재학습하거나 설정을 바꿨다면 고정된 예측 절차가 아닙니다.

**4. 경계·코드.**''')
s=replace_once(s,'`--write`를 지정한 실행 결과는 `week02_temporal_preprocessing_validation.json`에 기록합니다.', '원본의 `week02_temporal_preprocessing_validation.json`은 이전 보충 SHA에 결합된 과거 기록입니다. 새 후보 검증에는 신뢰한 노트북과 검사기를 별도 사본에서 실행하고 새 경로에 `--write`를 지정해 SHA가 일치하는지 확인합니다.')
p.write_text(s,encoding='utf-8')
print('updated teacher notes')
