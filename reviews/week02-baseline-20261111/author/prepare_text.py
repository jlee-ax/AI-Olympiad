from pathlib import Path
import nbformat as nbf

root=Path.cwd(); lesson=root/'lessons/week02'; author=root/'reviews/week02-baseline-20261111/author'
for name in ['week02_prediction_evaluation.ipynb','week02_prediction_evaluation.html','week02_temporal_preprocessing.ipynb','week02_temporal_preprocessing.html','build_week02.py','teacher-notes.md','week02_temporal_preprocessing_teacher.md','validation.json','week02_temporal_preprocessing_validation.json']:
    if (lesson/name).read_bytes() != (author/('baseline-'+name)).read_bytes():
        raise RuntimeError('Original changed concurrently: '+name)
old=nbf.read(lesson/'week02_prediction_evaluation.ipynb',4)
new=nbf.read(author/'executed-main.ipynb',4)
oldcell=next(c.source for c in old.cells if c.id=='4e3b494b')
newcell=next(c.source for c in new.cells if c.id=='4e3b494b')
builder=(lesson/'build_week02.py').read_text()
assert builder.count(oldcell)==1
builder=builder.replace(oldcell,newcell)

main=(lesson/'teacher-notes.md').read_text()
old='3. 항상 -1 기준모델: [[2,0],[2,0]], 정확도 1/2, 재현율 0/2=0, 정밀도 0/0은 수학적으로 정의 불가.'
new='3. 항상 -1 기준모델: [[2,0],[2,0]], 정확도 1/2, 재현율 0/2=0, 정밀도 0/0은 수학적으로 정의 불가. 이 기준은 사람이 미리 정한 상수이지 최빈값으로 학습한 결과가 아닙니다. A/B의 알려진 훈련 라벨은 2:2 동률이므로 최빈 기준을 쓰려면 사전에 동률 정책을 정해야 합니다. 보충 5절은 별도 훈련 라벨의 최빈값을 학습해 같은 검증에 적용합니다.'
assert main.count(old)==1
main=main.replace(old,new)
main += '\n이번 최빈 기준 개정의 별도 실행·새 입력 기록은 [작성자 검증](../../reviews/week02-baseline-20261111/author/README.md)을 보세요. 기존 두 검사기는 새 최빈 기준 과제를 자동 채점하지 않습니다. 기존 본문 및 보충 검증 보고서는 이전 판본의 기록으로 보존합니다.\n'

supp=(lesson/'week02_temporal_preprocessing_teacher.md').read_text()
old='실제 완수율, 학습 성취, 도움, 소요시간은 관찰하지 못했습니다.'
new='기존 6번을 확장하여 최빈 기준의 학습·혼동행렬·여러 지표와 빈도 반전까지 묻고 worked 코드 셀 하나를 추가했습니다. 새 번호의 대형 문제는 없지만 필수 수행 단계와 글은 늘었습니다. 실제 완수율, 학습 성취, 도움, 소요시간은 관찰하지 못했습니다.'
assert supp.count(old)==1; supp=supp.replace(old,new)
anchor='- 가중 예제는 실제 B 5개·T 1개에 가중치 1·5: 가는 행 정확도 5/6, 가중 5/10, 나는 4/6과 8/10. 분모는 모든 실제 행의 최대점수 10입니다. 정답 의존 가중치는 사후 채점에 사용하며 예측용 입력이 아닙니다.'
addition='''\n- 별도 훈련 라벨 B 3, T 1, 미상 0 다섯 개 중 알려진 라벨만 세면 B가 유일한 최빈입니다. 상수 c의 훈련 정확도는 n_c/N이므로 argmax는 최빈 상수를 고릅니다. `DummyClassifier(strategy="most_frequent")`는 X와 y의 관계를 배우지 않으며 알려진 행만 fit합니다. 검증 B 5, T 1에서 이 기준의 예측은 가와 같습니다. T 양성일 때 가는 TP=0, FP=0, TN=5, FN=1, 재현율 0, 정밀도 0/0 정의 불가, F1 0입니다. `zero_division=0`은 보고 정책입니다. 나는 TP=1, FP=2, TN=3, FN=0, 정밀도 1/3, 재현율 1, F1 1/2입니다. 이 수치와 기존 가중 점수를 서로 다른 목표에서 비교합니다.\n- 알려진 훈련이 동률이면 이 코드의 정책은 오류로 중단하고 사람이 정책을 정하는 것입니다. 알려진 정답이 없으면 중단합니다. 한 클래스만 알려지면 Dummy는 fit할 수 있으나 없는 클래스를 학습했다고 말하지 않습니다. `classes_`와 `predict_proba` 열 수를 확인합니다. 미상 0 제외는 이 합성 지도학습 예제의 계약이지 IOAI Antique의 반지도 입력 활용을 일괄 금지하는 말이 아닙니다. 검증 정답의 빈도만 B 1, T 5로 바꿔도 같은 fitted 기준의 예측은 B 여섯 개이며 정확도는 1/6로 달라집니다.'''
assert supp.count(anchor)==1; supp=supp.replace(anchor,anchor+addition)
old='익숙한 표현·색·물체의 새 조합이라는 문제 조건을 따르므로, 새 개체의 미래를 목표로 하는 이 합성 과제와 분할 및 과거 문맥의 의미가 다릅니다. 개체 분리를 모든 과제에 일괄 강제하지 않습니다.'
new='익숙한 표현·색·물체의 새 조합이 나올 수 있습니다. (가)가 맞고 (나)는 틀립니다. 로봇 ID 중복만으로 누수를 단정할 수 없고 제공되지 않은 이전 관측을 입력에 넣을 수도 없습니다. 새 개체의 미래를 목표로 하는 이 합성 과제와 분할 및 과거 문맥의 의미가 다르며 개체 분리를 모든 과제에 일괄 강제하지 않습니다.'
assert supp.count(old)==1; supp=supp.replace(old,new)
old='**6. 가중 기준.** 분모는 실제 B 6개와 T 2개 모두의 가능한 점수 6×1+2×4=14. U는 정확도 6/8=3/4, 가중점수 6/14=3/7. V는 정확도 5/8, 가중점수 (3+8)/14=11/14. U의 예측을 B 8개, V의 예측을 B 3개 뒤 T 5개로 두면 학생 함수로도 재현됩니다. 정확도는 U, 가중점수는 V가 높습니다. 맞힌 행만으로 분모를 세거나 예측한 종류로 가중치를 정하는 오류를 짚습니다.'
new='''**6. 훈련 최빈 기준과 가중 비교.** 훈련 라벨 `[B,T,T,T,0,0,0,0]`에서 미상 0을 제외하면 B 1, T 3이므로 유일한 최빈은 T입니다. 이 알려진 훈련 행에만 fit하여 검증 순서 B 여섯 행, T 두 행 모두에 T를 예측합니다. T 양성 기준 TP=2, FP=6, TN=0, FN=0; 정확도 1/4, 정밀도 1/4, 재현율 1, F1 2/5입니다. 분모는 실제 B 6개와 T 2개 모두의 가능한 점수 6×1+2×4=14이고 가중점수는 8/14=4/7입니다.\n\nU의 예측 B 여덟 개는 TP=0, FP=0, TN=6, FN=2; 정확도 3/4, 정밀도 정의 불가(0/0; 보고 정책값은 별도), 재현율 0, F1 0, 가중점수 6/14=3/7입니다. V의 예측 B 세 개 뒤 T 다섯 개는 TP=2, FP=3, TN=3, FN=0; 정확도 5/8, 정밀도 2/5, 재현율 1, F1 4/7, 가중점수 11/14입니다. 세 후보 중 정확도는 U, 재현율은 T 기준과 V가 공동, 가중점수는 V가 높습니다. 목표·공식 채점에 따라 선택하고 맞힌 행만으로 분모를 세거나 예측 종류로 가중치를 정하지 않습니다.\n\n훈련 빈도를 B 3, T 1로 반전해 새로 fit하면 예측은 B가 됩니다. 처음 fit된 T 기준을 그대로 두고 검증 정답만 바꾸면 모델 상태와 예측은 그대로입니다. 미상 0 네 개는 이 자료의 알려진 클래스가 아니며, 수가 많다는 이유로 학습 대상이 되지 않습니다. 검증 정답을 최빈값 선택에 끼워 넣는 오류를 확인합니다.'''
assert supp.count(old)==1; supp=supp.replace(old,new)
supp+='\n이번 판본의 추가 fit/predict, 반전·미상·동률·빈 훈련·한 클래스와 기존 AUC·4주 fold 재실행은 [별도 작성자 기록](../../reviews/week02-baseline-20261111/author/README.md)을 참조합니다. 기존 검사기는 이 새로운 독립 답안을 자동 채점하지 않습니다. [scikit-learn DummyClassifier 공식 문서](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyClassifier.html)를 참고하세요.\n'
for name,contents in [('candidate-build_week02.py',builder),('candidate-teacher-notes.md',main),('candidate-week02_temporal_preprocessing_teacher.md',supp)]:
    with (author/name).open('x',encoding='utf-8') as f:f.write(contents)
    print('Prepared',name)
