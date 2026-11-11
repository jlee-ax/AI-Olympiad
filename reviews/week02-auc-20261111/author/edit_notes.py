from pathlib import Path

def rep(s,a,b):
 if s.count(a)!=1:raise ValueError((s.count(a),a[:100]))
 return s.replace(a,b,1)
p=Path('lessons/week02/teacher-notes.md');s=p.read_text(encoding='utf-8')
s=rep(s,'입력 필드는 예측 시점 명세에 따라 결정하며 모든 test 라벨이 항상 없다고 말하지 않습니다.', '원문은 훈련과 공개 test에 같은 여섯 로봇이 있고, 각 행은 독립 snapshot이며 이전 관측·행동을 제공하지 않습니다. 익숙한 구성 요소의 새 조합이 나올 수 있습니다. 이 수업의 새 개체 분할이나 보충의 미래 시계열 계약과 목적이 다릅니다. 입력 필드는 명세에 따라 결정하며 모든 test 라벨이 항상 없다고 말하지 않습니다.')
s=rep(s,'\n## 독립 과제 답안·관찰 기준','''
## ROC-AUC 예제와 경계

본문의 실제 라벨 `[1,-1,1,-1]`, 점수 `[0.9,0.6,0.4,0.1]`에서 양성 0.9는 두 음성보다, 양성 0.4는 음성 0.1보다만 높습니다. 네 양성–음성 쌍 중 세 쌍이므로 순위 AUC는 3/4입니다. ROC 사다리꼴 면적과 `roc_auc_score((roc_truth == 1).astype(int), roc_scores)`도 0.75입니다. 임계값 0.5에서는 정확도·F1이 각각 1/2, 1/2이고, 0.3에서는 3/4, 4/5입니다. 점수는 고정했으므로 AUC는 둘 다 같습니다.

점수를 모두 1 올리고 임계값도 0.5에서 1.5로 올리면 예측이 같습니다. 점수만 올리고 임계값을 0.5로 그대로 두면 모두 양성으로 바뀌고 F1은 2/3입니다. 어느 경우에도 양성·음성 점수 순서는 같아 AUC는 0.75입니다. 순위가 같다는 것은 확률 보정이 같다는 뜻이 아닙니다.

보충의 기존 그림은 AUC 0.5이지만 ROC 전체가 대각선은 아닙니다. AUC 0.5는 해당 표에서 동점에 반 점을 준 양성–음성 쌍의 평균이 0.5라는 뜻이지, 데이터 생성이 무작위라는 증거가 아닙니다. 모든 양성 점수가 음성보다 낮으면 AUC 0, 반대로 정렬하면 1, 전부 동점이면 0.5입니다. 실제 양성 또는 음성이 전혀 없으면 양성–음성 쌍이 없어 AUC는 정의되지 않습니다. 실제 scikit-learn 1.8.0에서는 경고와 NaN을 보았으며 버전에 따라 오류가 날 수 있으므로 두 클래스 존재를 먼저 확인합니다.

국내 [출제 기준](https://kitpa.org/koai/syllabus)은 ROC 곡선을 명시하나 AUC를 별도 이름으로 열거하지 않습니다. [KOAI 2026 예시 공지](https://kitpa.org/files/36)의 23번은 AUC 관련 고등부 수준의 학습 참고 예시이며 중등 기출이나 KOAI 2027 출제 예측이 아닙니다. 예시 문제는 재배포하지 않았습니다.

## 독립 과제 답안·관찰 기준''')
s=rep(s,'- [scikit-learn precision_recall_fscore_support]', '- [scikit-learn ROC-AUC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html), [사다리꼴 면적](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.auc.html): 양성 방향과 ROC 면적.\n- [scikit-learn precision_recall_fscore_support]')
s += '\n이 단원의 기존 본문 검사기는 ROC-AUC의 이론·새 수치 경계를 자동 검증하지 않습니다. 새로운 유한 사례 결과는 `reviews/week02-auc-20261111/author/`의 별도 기록을 확인하세요.\n'
p.write_text(s,encoding='utf-8')

p=Path('lessons/week02/week02_temporal_preprocessing_teacher.md');s=p.read_text(encoding='utf-8')
s=rep(s,'결정 점수이므로 확률 보정이나 실제 모델 효과를 뜻하지 않습니다.', '양성 점수 1.5 두 개가 각각 음성 0은 이기고 음성 2.5에는 지므로 AUC는 2/4=0.5입니다. ROC 전체는 대각선이 아니며 0.5만으로 무작위 생성 여부를 판단할 수 없습니다. 결정 점수이므로 확률 보정이나 실제 모델 효과를 뜻하지 않습니다.')
s=rep(s,'학생이 스스로 행을 배정하고 두 조건을 검사하는지 확인합니다.', '학생이 스스로 행을 배정하고 두 조건을 검사하는지 확인합니다. Robot Chasing 원문은 훈련과 공개 평가에 같은 여섯 로봇이 있고 행은 독립 snapshot이며 이전 관측은 제공되지 않습니다. 익숙한 표현·색·물체의 새 조합이라는 문제 조건을 따르므로, 새 개체의 미래를 목표로 하는 이 합성 과제와 분할 및 과거 문맥의 의미가 다릅니다. 개체 분리를 모든 과제에 일괄 강제하지 않습니다.')
s=rep(s,"검증 F1 기준의 후보 $2,5/4,-1/8,-1$의 F1은 각각 $0,2/5,2/3,2/3$입니다.", '''독립 과제의 양성 점수는 P6=5/4, Q6=−1/8이고 음성은 P7=2, Q7=5/4입니다. P6과 Q7만 이종 라벨 동점이어서 반 점, 다른 세 쌍은 양성이 더 낮아 0점입니다. 따라서 AUC는 $(1/2)/4=1/8$입니다. ROC의 폭 1/2인 대각 구간 아래 사다리꼴 넓이도 $(1/2)(0+1/2)/2=1/8$입니다. 실제 양성 또는 음성이 없으면 AUC는 정의되지 않습니다. 이 답은 학생의 독립 문제 앞에 제공하지 않습니다.

검증 F1 기준의 후보 $2,5/4,-1/8,-1$의 F1은 각각 $0,2/5,2/3,2/3$입니다.''')
s=rep(s,'- [scikit-learn common pitfalls]', '- [scikit-learn ROC-AUC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html), [면적](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.auc.html): 양성 점수 방향과 사다리꼴 면적.\n- [KOAI 2026 예시 공지](https://kitpa.org/files/36): 23번은 고등부 수준의 참고 예시이며 문항 원문을 재배포하지 않았습니다. 현재 국내 기준에는 ROC가 명시되고 AUC는 별도 이름으로 열거되지 않습니다.\n- [scikit-learn common pitfalls]')
s += '\n기존 보충 검사기는 ROC-AUC의 새 독립 과제 정답이나 학습자 응답을 자동 채점하지 않습니다. 순위·면적·동점·단일 클래스 경계의 새 유한 검산은 `reviews/week02-auc-20261111/author/`의 별도 기록을 확인하세요.\n'
p.write_text(s,encoding='utf-8')
print('updated teachers: ROC-AUC, distinct validation contracts, original-source limits')
