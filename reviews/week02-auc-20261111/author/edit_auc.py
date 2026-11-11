from pathlib import Path
import ast
import nbformat as nbf

ROOT=Path('lessons/week02'); mp=ROOT/'week02_prediction_evaluation.ipynb';tp=ROOT/'week02_temporal_preprocessing.ipynb'
main=nbf.read(mp,as_version=4);temporal=nbf.read(tp,as_version=4)
assert len(main.cells)==25 and len(temporal.cells)==24

def rep(s,a,b):
 if s.count(a)!=1:raise ValueError((s.count(a),a[:100]))
 return s.replace(a,b,1)

main.cells[6].source=rep(main.cells[6].source,'어떤 방식으로든 평가 자료가 모델 선택·학습에 끼어든 점이 문제입니다.','이 사례에서 검증 입력을 전처리의 `fit`에 섞어 평가 정보가 학습에 들어간 점이 문제입니다. 검증 결과로 후보를 선택하는 것은 검증 자료의 정해진 역할입니다.')
main.cells[18].source=rep(main.cells[18].source,'위 R1/R2 불균형 숫자는 이 차이를 설명하려고 새로 만든 교육용 자료이지 원문 자료가 아닙니다.', '원문에서는 훈련과 공개 test에 같은 여섯 로봇이 등장하고 행은 시간 순서의 에피소드가 아닌 독립 snapshot입니다. 이전 관측·행동은 평가 시 제공되지 않으며, 익숙한 표현·색·물체의 새로운 조합이 등장할 수 있습니다. 따라서 이 원문을 이 교안의 새 개체 분할이나 보충의 시계열 예측으로 해석하지 않습니다. 위 R1/R2 불균형 숫자는 이 차이를 설명하려고 새로 만든 교육용 자료이지 원문 자료가 아닙니다.')
main.cells[22].source=rep(main.cells[22].source,'예제의 네 점수는 확률처럼 읽는 0~1 값이지만 실제 확률의 보정 여부는 이 표만으로 알 수 없습니다.','''예제의 네 점수는 0~1 값이지만 실제 확률의 보정 여부는 이 표만으로 알 수 없습니다.

**ROC-AUC**는 가로축 FPR, 세로축 TPR인 ROC 선 아래의 면적입니다. 두 점 사이를 직선으로 잇고 사다리꼴 면적을 더할 수 있습니다. 같은 수치는 양성 행 하나와 음성 행 하나를 뽑는 모든 쌍 중, 양성 점수가 더 높은 쌍의 비율이기도 합니다. 동점인 쌍은 절반만 셉니다. 이 표에서 양성 점수와 음성 점수로 만들 수 있는 네 쌍을 세고 ROC 면적과 비교해 보세요. 점수가 높을수록 `+1` 쪽이라는 약속을 지킵니다.''')
main.cells[23].source='''from sklearn.metrics import auc, roc_auc_score
import matplotlib.pyplot as plt

roc_truth = np.array([1, -1, 1, -1])
roc_scores = np.array([0.9, 0.6, 0.4, 0.1])
roc_matrices = {}
for threshold in [0.5, 0.3]:
    pred = np.where(roc_scores >= threshold, 1, -1)
    cm = confusion_matrix(roc_truth, pred, labels=[-1, 1])
    tn, fp, fn, tp = cm.ravel()
    roc_matrices[threshold] = cm.tolist()
    f1_at_threshold = 2 * tp / (2 * tp + fp + fn)
    print("임계값", threshold, "혼동행렬", cm.tolist(),
          "TPR", tp / (tp + fn), "FPR", fp / (fp + tn),
          "정확도", (pred == roc_truth).mean(), "F1", f1_at_threshold)
fpr, tpr, thresholds = roc_curve(roc_truth, roc_scores, pos_label=1, drop_intermediate=False)
print("ROC 좌표 (FPR, TPR):", list(zip(fpr.round(2).tolist(), tpr.round(2).tolist())))
# roc_auc_score의 1을 양성으로 명시합니다. 양쪽 클래스가 모두 있을 때만 계산합니다.
binary_truth = (roc_truth == 1).astype(int)
roc_area = auc(fpr, tpr)
rank_area = roc_auc_score(binary_truth, roc_scores)
print("사다리꼴 면적:", roc_area, "양성 점수의 ROC-AUC:", rank_area)
assert np.isclose(roc_area, 0.75) and np.isclose(rank_area, roc_area)

# 점수와 임계값을 함께 1만큼 옮기면 판정은 같습니다. 점수만 옮기면 달라질 수 있습니다.
shifted_scores = roc_scores + 1
original_pred = np.where(roc_scores >= 0.5, 1, -1)
shifted_pred = np.where(shifted_scores >= 1.5, 1, -1)
fixed_threshold_pred = np.where(shifted_scores >= 0.5, 1, -1)
print("원래 판정:", original_pred.tolist(), "함께 이동:", shifted_pred.tolist(),
      "임계값을 그대로 둠:", fixed_threshold_pred.tolist())
assert np.array_equal(original_pred, shifted_pred)
assert not np.array_equal(original_pred, fixed_threshold_pred)
assert np.isclose(roc_auc_score(binary_truth, shifted_scores), rank_area)

fig, ax = plt.subplots()
ax.plot(fpr, tpr, marker="o", color="navy")
ax.fill_between(fpr, tpr, 0, color="skyblue", alpha=0.4)
ax.set(xlabel="FPR", ylabel="TPR", title="ROC and area", xlim=(-0.03, 1.03), ylim=(-0.03, 1.03))
ax.grid(True, alpha=0.3)
plt.show()'''
main.cells[24].source=rep(main.cells[24].source,'ROC는 임계값에 따른 FPR과 TPR을 함께 보여 줍니다. 이 네 행만으로 실제 모델의 성능을 주장할 수는 없습니다. 더 작은 임계값에서 재현율이 늘 때 FP도 늘 수 있는 이유를 두 표의 행 번호로 설명하세요.','''ROC는 임계값에 따른 FPR과 TPR을 함께 보여 줍니다. 위 표에서 양성 점수 0.9는 두 음성 점수보다 높고, 양성 점수 0.4는 두 음성 점수 중 0.1보다만 높습니다. 따라서 네 양성–음성 쌍 중 세 쌍을 올바르게 정렬해 AUC는 $3/4=0.75$입니다. 코드의 사다리꼴 면적과 같은 값입니다. 이 네 행만으로 실제 모델의 성능을 주장할 수는 없습니다.

AUC는 여러 임계값에 걸친 **점수 순서**, 정확도와 F1은 **정한 한 임계값의 판정**을 봅니다. 위 표에서 임계값만 0.5에서 0.3으로 바꾸면 F1은 바뀌지만 점수 순서는 그대로여서 AUC는 바뀌지 않습니다. 점수와 임계값을 함께 같은 만큼 올리면 판정이 같지만, 임계값을 그대로 두고 점수만 올리면 판정이 바뀔 수 있습니다. 순서가 그대로인 점수 변환은 AUC를 보존하지만, 이것만으로 점수가 잘 보정된 확률인지 알 수 없습니다.

이진 평가에서 AUC 0.5는 해당 자료의 쌍 순위 점수가 절반이라는 뜻입니다. ROC의 모든 점이 대각선 위에 있다거나 점수가 무작위로 만들어졌다는 증거는 아닙니다. AUC가 0.5보다 작을 수도 있습니다. 실제 양성 또는 음성 중 하나가 전혀 없으면 비교할 양성–음성 쌍과 ROC의 한 축이 없어 AUC는 정의되지 않습니다. 최종 테스트를 열기 전에 후보와 임계값을 정하고, 정해진 검증 결과로 선택하세요.''')
main.cells[24].source=rep(main.cells[24].source,'- [scikit-learn: 데이터 누수와 전처리]', '- [scikit-learn: ROC-AUC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html), [사다리꼴 면적](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.auc.html): 양성 점수와 면적 계산.\n- [scikit-learn: 데이터 누수와 전처리]')

temporal.cells[16].source += "\n\n**계약 비교:** IOAI 2026 Robot Chasing에서는 훈련과 공개 평가에 같은 여섯 로봇이 나오고, 각 행은 독립 snapshot이며 이전 관측은 제공되지 않습니다. 익숙한 구성 요소의 새 조합이 나올 수 있습니다. 위 새 개체의 미래 예측과 어떤 점에서 평가 목적과 사용할 정보가 다른지, 개체 분리나 시간 윈도를 모든 문제에 적용해도 되는지 설명하세요."

temporal.cells[13].source=rep(temporal.cells[13].source,'`roc_curve`는 양성 점수에 확률뿐 아니라 임계값 적용 전의 결정 점수도 받습니다.', '`roc_curve`는 양성 점수에 확률뿐 아니라 임계값 적용 전의 결정 점수도 받습니다. 앞 교안에서 본 ROC-AUC는 곡선 아래 면적이자 양성–음성 쌍의 순위 점수이며, 이종 라벨의 동점은 반 쌍으로 셉니다. 한 임계값의 F1이나 정확도 및 확률 보정과는 다릅니다.')
temporal.cells[19].source=rep(temporal.cells[19].source,'실제 양성 또는 음성이 없는 표와 양성 예측이 없는 표에서 어떤 분모가 0인지 쓰세요.','''실제 양성 또는 음성이 없는 표와 양성 예측이 없는 표에서 어떤 분모가 0인지 쓰세요. 그린 ROC의 사다리꼴 면적과 양성–음성 점수 네 쌍의 순위 점수를 각각 구하세요. 양성 점수가 높으면 1, 같으면 1/2, 낮으면 0으로 세고 두 방법의 결과를 비교하세요. `roc_auc_score((y == 1).astype(int), scores)`와 `auc(fpr, tpr)`로도 확인하세요. 실제 양성이나 음성이 없을 때 왜 AUC가 정의되지 않는지 설명하세요.''')
temporal.cells[19].source=rep(temporal.cells[19].source,'같은 예측을 만드는 두 임계값은 ROC의 서로 다른 새 좌표를 만들지 않습니다.', '같은 예측을 만드는 두 임계값은 ROC의 서로 다른 새 좌표를 만들지 않습니다. 점수를 고정하고 임계값만 바꿀 때 AUC와 F1 중 무엇이 달라질 수 있는지도 설명하세요.')
nbf.validate(main);nbf.validate(temporal)

builderp=ROOT/'build_week02.py';builder=builderp.read_text(encoding='utf-8');tree=ast.parse(builder)
calls=[node for node in tree.body if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id in ('md','code')]
assert len(calls)==len(main.cells)
lines=builder.splitlines(keepends=True)
for node,cell in reversed(list(zip(calls,main.cells))):
 fn=node.value.func.id;source=cell.source;assert "'''" not in source
 lines[node.lineno-1:node.end_lineno]=[f"{fn}(r'''\n{source}\n''')\n"]
builder=''.join(lines);compile(builder,str(builderp),'exec')
# Reject concurrent changes after the saved baselines.
for path,name in [(mp,'baseline-week02_prediction_evaluation.ipynb'),(tp,'baseline-week02_temporal_preprocessing.ipynb'),(builderp,'baseline-build_week02.py')]:
 assert path.read_bytes()==(Path('reviews/week02-auc-20261111/author')/name).read_bytes(),str(path)
nbf.write(main,mp);nbf.write(temporal,tp);builderp.write_text(builder,encoding='utf-8')
print('updated notebook sources and builder; original cell IDs and independent code blanks retained')
