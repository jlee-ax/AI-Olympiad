from pathlib import Path
import hashlib
import nbformat as nbf

root = Path.cwd()
author = root / 'reviews/week02-baseline-20261111/author'
lesson = root / 'lessons/week02'
for path in (lesson / 'week02_prediction_evaluation.ipynb', lesson / 'week02_temporal_preprocessing.ipynb', lesson / 'build_week02.py', lesson / 'teacher-notes.md', lesson / 'week02_temporal_preprocessing_teacher.md'):
    baseline = author / ('baseline-' + path.name)
    if path.read_bytes() != baseline.read_bytes():
        raise RuntimeError(f'Original changed concurrently: {path}')

main = nbf.read(lesson / 'week02_prediction_evaluation.ipynb', as_version=4)
cell = next(c for c in main.cells if c.id == '4e3b494b')
cell.source += '\n\n이 기준은 사람이 정한 고정 음성이며 훈련 최빈 라벨을 배운 결과는 아닙니다. A/B의 알려진 라벨은 -1과 +1이 각 2개로 동률이므로 최빈 기준을 쓰려면 먼저 동률 정책을 정해야 합니다. 보충 5절에서는 알려진 훈련 라벨을 세어 최빈 기준을 배우고 같은 검증 입력에 적용합니다.'

supp = nbf.read(lesson / 'week02_temporal_preprocessing.ipynb', as_version=4)
cell = next(c for c in supp.cells if c.id == '98d2cf0f')
cell.source += r'''\n\n### 훈련에서 최빈 기준 배우기\n\n이번에는 별도 훈련 라벨을 B 3개, T 1개, 미상 0 5개로 둡니다. 미상 0은 **이 합성 계약에서만** 모르는 정답 표시이므로 B/T 빈도에서 뺍니다. 알려진 훈련 라벨에서 각 클래스 c의 개수를 $n_c$라 할 때 최빈 클래스는 $\operatorname{argmax}_c n_c$입니다. 모든 정답이 알려진 훈련 행에 같은 c를 예측하면 맞힌 수가 $n_c$이므로 이 알려진 행에 대한 상수 예측의 훈련 정확도가 최대인 c를 고릅니다. 이 예에서는 B입니다. B/T가 동률이면 이 예제는 학습을 중단하고, 미리 정한 동률 정책이 필요하다고 알립니다.\n\n`DummyClassifier(strategy="most_frequent")`를 알려진 훈련 행에 `fit`한 뒤 **같은 검증 여섯 행**에 그대로 `predict`합니다. 이 기준은 훈련 X값과 정답 사이의 관계를 배우지 않습니다. 훈련과 검증의 클래스 빈도는 달라질 수 있지만 검증 정답으로 기준을 다시 정하지 않습니다. 아래 코드는 검증 정답만 바꿔도 예측이 유지되는지 보여 줍니다. 알려진 훈련 라벨이 한 종류뿐이어도 fit할 수 있지만, 보지 못한 클래스를 배운 것은 아닙니다. `predict_proba`의 열은 `classes_`를 확인하세요.\n\n검증에서 대상 T를 양성으로 볼 때 가(모두 B)의 TP=0, FP=0, TN=5, FN=1이므로 정확도 5/6에 비해 재현율은 0, 정밀도는 0/0으로 **정의되지 않습니다**. `zero_division=0`은 이 경우의 보고값 0을 정하는 정책이고 F1은 0입니다. 나의 TP=1, FP=2, TN=3, FN=0이므로 재현율 1, 정밀도 1/3, F1 1/2이고, 가중 정확도는 표에서 8/10입니다. 어느 지표도 언제나 우월하지 않습니다. 먼저 과제의 목적과 공식 평가 기준을 확인한 뒤 비교합니다.'''.replace('\\n','\n')
new_source = '''from sklearn.dummy import DummyClassifier
from sklearn.metrics import precision_recall_fscore_support


def fit_known_mode(raw_labels):
    # 이 합성 자료에서 0은 미상이고 Boolean은 받지 않습니다. 동률이면 중단합니다.
    raw = np.asarray(raw_labels, dtype=object)
    if (raw.ndim != 1 or any(isinstance(v, (bool, np.bool_)) for v in raw.flat)
            or not np.isin(raw, np.array(["B", "T", 0], dtype=object)).all()):
        raise ValueError("이 예제의 훈련 라벨은 B/T/0이어야 합니다.")
    known_mask = np.isin(raw, ["B", "T"])
    known = raw[known_mask].astype(str)
    if len(known) == 0:
        raise ValueError("알려진 훈련 라벨이 없습니다.")
    classes, counts = np.unique(known, return_counts=True)
    if np.count_nonzero(counts == counts.max()) != 1:
        raise ValueError("최빈 동률: 먼저 동률 정책을 정하세요.")
    chosen = classes[np.argmax(counts)]
    # Dummy는 X의 값과 정답 사이의 관계를 학습하지 않습니다.
    training_x = np.arange(len(raw)).reshape(-1, 1)
    model = DummyClassifier(strategy="most_frequent")
    model.fit(training_x[known_mask], known)
    return model, chosen, known_mask


raw_training_labels = np.array(["B", "B", "B", "T", 0, 0, 0, 0, 0], dtype=object)
mode_model, mode_label, mode_known = fit_known_mode(raw_training_labels)
validation_x = np.arange(len(actual)).reshape(-1, 1)  # 기존 B5/T1 표의 여섯 행 순서
mode_predictions = mode_model.predict(validation_x)
assert mode_label == "B" and np.array_equal(mode_predictions, guess_a)
print("알려진 훈련 라벨 수:", mode_known.sum(), "선택한 최빈 클래스:", mode_label)
for name, guess in [("최빈 기준=가", mode_predictions), ("나", guess_b)]:
    precision, recall, f1, _ = precision_recall_fscore_support(
        actual, guess, average="binary", pos_label="T", zero_division=np.nan)
    print(name, "정밀도·재현율·F1:", precision, recall, f1,
          "가중 정확도:", weighted_accuracy(actual, guess))
reported_precision = precision_recall_fscore_support(
    actual, mode_predictions, average="binary", pos_label="T", zero_division=0)[0]
print("정의되지 않은 정밀도의 0 보고 정책:", reported_precision)
changed_validation_truth = np.array(["B", "T", "T", "T", "T", "T"])
assert np.array_equal(mode_predictions, mode_model.predict(validation_x))
print("검증 정답만 바꾼 뒤 같은 예측:", mode_predictions.tolist(),
      "바뀐 정확도:", (mode_predictions == changed_validation_truth).mean())
only_t_model, _, _ = fit_known_mode(["T", 0, 0])
print("한 종류만 알려진 훈련의 classes_:", only_t_model.classes_.tolist(),
      "predict_proba 열 수:", only_t_model.predict_proba(validation_x[:1]).shape[1])'''
index = next(i for i,c in enumerate(supp.cells) if c.id == 'e12109a7')
supp.cells.insert(index+1, nbf.v4.new_code_cell(new_source, id='w02-known-mode'))
cell = next(c for c in supp.cells if c.id == 'ae6c7104')
old = '**계약 비교:** IOAI 2026 Robot Chasing에서는 훈련과 공개 평가에 같은 여섯 로봇이 나오고, 각 행은 독립 snapshot이며 이전 관측은 제공되지 않습니다. 익숙한 구성 요소의 새 조합이 나올 수 있습니다. 위 새 개체의 미래 예측과 어떤 점에서 평가 목적과 사용할 정보가 다른지, 개체 분리나 시간 윈도를 모든 문제에 적용해도 되는지 설명하세요.'
new = '**계약 비교:** IOAI 2026 Robot Chasing에서는 훈련과 공개 평가에 같은 여섯 로봇이 나오고, 각 행은 독립 snapshot이며 이전 관측은 제공되지 않습니다. 익숙한 구성 요소의 새 조합이 나올 수 있습니다. 다음은 원문의 실제 분할이 아닌 별도 합성 설계이며, 목표는 **알려진 두 로봇의 새로운 색×물체 조합 예측**입니다. (가) 두 로봇 각각의 일부 조합은 훈련, 다른 조합은 검증에 두어 같은 ID가 양쪽에 있습니다. (나) 로봇 ID를 나누어 훈련에 없던 로봇을 검증합니다(조합은 겹칠 수 있습니다). 각각 무엇을 평가하고 이 합성 목표에 어느 쪽이 더 직접 맞나요? 각각 원문처럼 이전 관측이 제공되지 않을 때 시간 윈도를 쓸 수 있는지도 설명하세요. 위 새 개체의 미래 예측과도 비교하세요.'
if old not in cell.source: raise RuntimeError('Robot comparison changed')
cell.source = cell.source.replace(old,new)
cell = next(c for c in supp.cells if c.id == 'w02-exercise-4')
old = '6. 별도 합성 평가에서 실제 B 6개·T 2개, 가중치는 실제 B에 1, 실제 T에 4입니다. 후보 U는 B 6개와 T 0개, 후보 V는 B 3개와 T 2개를 맞혔습니다. 두 후보의 전체 행 정확도와 가중 정확도를 손으로 계산하고, 실제 정답·예측 배열을 만들어 `weighted_accuracy`로 확인한 뒤 순위가 같은지 비교하세요. 가중 분모에 어떤 행이 포함되는지 설명하세요.'
new = '''6. **새 훈련과 같은 검증에서 기준 비교.** 별도 합성 훈련의 정답을 순서대로 `["B", "T", "T", "T", 0, 0, 0, 0]`으로 둡니다. 0은 이 자료의 미상입니다. 알려진 훈련 정답만 세어 최빈 클래스를 고르고, 같은 행의 훈련 입력에 `DummyClassifier(strategy="most_frequent")`를 fit하세요. 검증의 실제 정답은 순서대로 B 6개와 T 2개입니다. 검증 입력 순서를 보존해 고정한 기준을 예측하세요. 후보 U는 B 6개와 T 0개, 후보 V는 B 3개와 T 2개를 맞혔습니다.\n\n   양성 T에 대해 기준·U·V의 TP/FP/TN/FN, 전체 행 정확도·정밀도·재현율·F1을 계산하세요. 정밀도 분모가 0이면 정의와 보고 정책을 구분하세요. 실제 B에 1, 실제 T에 4를 주는 가중 정확도도 손으로 구하고 정답·예측 배열과 `weighted_accuracy`로 확인하세요. 정확도, 재현율, 가중 정확도를 각각 목표로 미리 정했을 때 어떤 후보가 좋은지, 동점과 가중 분모를 설명하세요. 공식 평가 목표가 다른 문제에서 무엇이 달라질지도 말하세요.\n\n   훈련 빈도를 B 3개·T 1개로 바꿔 **새로 fit**하면 기준이 어떻게 달라지나요? 처음 fit한 모델은 그대로 두고 검증 정답만 바꾸었을 때 예측이 바뀌는지도 확인하세요. 미상 0이 가장 많이 등장해도 왜 클래스 빈도에 세지 않는지 설명하세요.'''
if old not in cell.source: raise RuntimeError('Exercise changed')
cell.source=cell.source.replace(old,new)
for name,nb in [('source-main.ipynb',main),('source-temporal.ipynb',supp)]:
    nbf.validate(nb)
    with (author/name).open('x',encoding='utf-8') as f: nbf.write(nb,f)
    print(name,hashlib.sha256((author/name).read_bytes()).hexdigest())
