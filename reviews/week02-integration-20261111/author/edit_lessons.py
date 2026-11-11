from pathlib import Path
import ast
import json
import textwrap
import nbformat as nbf

ROOT=Path('lessons/week02')
main_path=ROOT/'week02_prediction_evaluation.ipynb'
temporal_path=ROOT/'week02_temporal_preprocessing.ipynb'
main=nbf.read(main_path,as_version=4)
temporal=nbf.read(temporal_path,as_version=4)
assert len(main.cells)==25 and len(temporal.cells)==19

def replace_once(s,old,new):
    count=s.count(old)
    if count!=1:
        raise ValueError(f'expected one occurrence, got {count}: {old[:100]!r}')
    return s.replace(old,new,1)

main.cells[1].source=main.cells[1].source.replace('NumPy, pandas, scikit-learn, Matplotlib이 필요합니다.', 'NumPy, pandas, scikit-learn 1.3 이상, Matplotlib이 필요합니다. 1.3 이상은 이 노트북에서 `zero_division=np.nan`을 사용하기 위해 필요합니다.')
main.cells[4].source=replace_once(main.cells[4].source,
 'A·B는 훈련, C·D는 검증, E·F는 별도 보관할 최종 테스트 개체입니다. E·F의 자료와 정답은 이 노트북에서 사용하지 않습니다. 훈련 A/B의 두 클래스 수가 우연히 같지만 그룹을 나눌 때마다 같은 비율이 보장되는 것은 아닙니다.',
 '이번 수업의 작은 예제에서는 A·B만 훈련, C·D는 검증에 사용합니다. E·F는 최종 테스트 개체의 자리 표시이며 자료와 정답은 아직 만들어지지 않았습니다. 훈련 A/B의 두 클래스 수가 우연히 같지만 그룹을 나눌 때마다 같은 비율이 보장되는 것은 아닙니다.')
main.cells[4].source=replace_once(main.cells[4].source,'\n**예상**:', '''
같은 합성 원본에는 **추가 훈련 후보** G/H도 있습니다. 아래 네 행은 이번 A/B 손계산이나 `fit`에는 넣지 않습니다. 이 표와 위 표의 열은 같습니다.

| 행 | 개체 | reading(u) | label |
|---|---|---:|---:|
| g1 | G | 2 | -1 |
| g2 | G | 4 | +1 |
| h1 | H | 4 | -1 |
| h2 | H | 6 | +1 |

4주차에 A/B/G/H를 훈련 후보로 함께 사용한다면 정답이 알려진 행을 고른 뒤 전처리와 모델을 **다시 fit**하고, 기준 모델도 같은 조건에서 다시 계산합니다. C/D는 검증에 남기고 E/F는 생성 전 자리 표시로 둡니다. 전체 원본은 같아도 이번 수업과 4주차의 훈련 행과 `fit` 상태는 다릅니다. 교차검증은 각 훈련 fold에서 전처리를 새로 fit해야 하며, 이 작은 합성 자료는 안정적인 성능 추정용이 아닙니다.

**예상**:''')
insert='''# 같은 원본의 추가 훈련 후보. 이번 수업의 A/B fit에는 넣지 않습니다.
additional_train = pd.DataFrame([
    ("g1", "G", 2, -1), ("g2", "G", 4, 1),
    ("h1", "H", 4, -1), ("h2", "H", 6, 1),
], columns=records.columns)
course_records = pd.concat([records, additional_train], ignore_index=True)
train_4w = course_records[course_records["group"].isin(["A", "B", "G", "H"])].copy()
known_train_4w = train_4w[train_4w["label"].isin([-1, 1])].copy()
assert course_records["row_id"].is_unique
assert set(train_4w["group"]).isdisjoint({"C", "D"})

'''
main.cells[5].source=replace_once(main.cells[5].source,'train = records[records["group"].isin(["A", "B"])].copy()',insert+'train = records[records["group"].isin(["A", "B"])].copy()')
main.cells[5].source += '\nprint("4주 추가 훈련 후보 행:", additional_train["row_id"].tolist())'
main.cells[14].source=replace_once(main.cells[14].source,'\n### 미상은 음성이 아닙니다','''
### 무엇을 기준으로 선택할까요?

위 검증 네 행에서 고정 규칙의 정확도는 $1/4$, 재현율은 $1/2$입니다. 항상 `-1`인 기준 모델의 정확도는 $1/2$, 재현율은 0입니다. 정확도를 기준으로 정했다면 이 두 후보 중 기준 모델의 검증 점수가 높고, 재현율을 기준으로 정했다면 고정 규칙의 점수가 높습니다. 기준 모델의 정밀도는 정의되지 않으므로 0으로 정해진 실제 측정값처럼 비교하지 않습니다. 후보와 기준을 먼저 정하고 검증 근거로 선택합니다. 이 네 행의 결과는 실제 성능을 추정하기에 너무 작습니다.

### 미상은 음성이 아닙니다''')
main.cells[19].source='''## 6. 새로운 입력으로 혼자 확인하기

이 절은 앞의 예시와 코드·교사용 해설을 가리고 풉니다. 결과·이유와 사용한 도움(없음/힌트/예시/직접 설명)을 남기세요. 이 입력의 해답은 학생 자료에 넣지 않았습니다.

새 합성 자료도 측정 **직후** 제공되는 `reading` 하나로 판정합니다. `+1`은 이상, `-1`은 정상, `0`은 미상입니다. M·N은 훈련, O·P는 검증이며 Q는 최종 테스트의 자리 표시입니다. Q의 자료와 정답은 아직 없습니다. 이 파이프라인은 알려진 **훈련 행만** 대체·표준화를 학습합니다.

| 행 | 개체 | reading(u) | label |
|---|---|---:|---:|
| m1 | M | 3 | -1 |
| m2 | M | 6 | +1 |
| n1 | N | 9 | +1 |
| n2 | N | 결측 | -1 |
| n3 | N | 12 | 0(미상) |
| o1 | O | 99 | +1 |
| o2 | O | 결측 | +1 |
| p1 | P | 결측 | -1 |
| p2 | P | 결측 | -1 |

**선택형 1.** 이 예제의 `fit`에 사용할 행은 어느 묶음인가요? 미상과 결측 측정값을 서로 다르게 취급하는 이유도 말하세요.

- 가. m1, m2, n1, n2
- 나. m1, m2, n1, n2, n3
- 다. m1, m2, n1, n2, o1
- 라. m1, m2, n1

**선택형 2.** 검증의 모든 행을 `-1`로 예측하면 정밀도와 재현율은 각각 무엇인가요?

- 가. 정밀도는 정의 불가, 재현율은 0
- 나. 정밀도와 재현율은 모두 0
- 다. 정밀도는 0, 재현율은 정의 불가
- 라. 정밀도와 재현율은 모두 1

**짧은 서술.** M의 m1과 m2를 서로 다른 묶음으로 보내면 왜 처음 보는 개체를 평가하는 목적에 맞지 않나요? 예측 후에 기록된 수리 결과를 입력에 넣는 것과도 비교하세요.

**추가 필기:**

1. 훈련 관측 평균과 검증 관측값까지 섞은 잘못된 평균을 각각 구하세요.
2. 결측 대체 후 훈련 평균·모집단 표준편차를 구하세요. 이 값으로 검증을 변환해 $z\\ge1$이면 `+1`, 아니면 `-1`인 고정 규칙의 예측을 o1,o2,p1,p2 순서대로 적으세요. TP/FP/FN/TN, 정확도·정밀도·재현율을 분모와 함께 구하세요.
3. 선택형 2에서 정의 불가와 라이브러리의 `zero_division=0`을 구별하세요.
4. 별도의 불균형 평가에서 X는 3행 중 3행, Y는 5행 중 1행을 맞혔습니다. 전체 행 정확도와 개체별 평균을 각각 구하고 분모가 다른 이유를 쓰세요.
5. 미래를 예측할 때 시간 역전의 위험과 Q를 사용할 시점을 적으세요.

**코딩:** 새 자료를 직접 입력하고 학습 가능한 행을 고른 뒤 `SimpleImputer`와 `StandardScaler`를 훈련에서만 `fit`하여 검증에 `transform`하세요. 위 고정 규칙의 행 순서별 예측과 `confusion_matrix(..., labels=[-1, 1])`를 출력하고 손계산과 비교하세요. 테스트 Q는 읽거나 사용하지 않습니다.'''
main.cells[22].source='''## 7. 필수 연습의 이어지는 경로

앞에서 만든 분할 ID와 훈련 파이프라인을 보존하고, 모든 설정 선택 전에 최종 테스트를 열지 않습니다. 아래는 같은 필수 연습을 이어서 수행하는 경로입니다. 본문의 목록과 보충의 같은 활동을 각각 다시 제출할 필요는 없습니다. [보충 노트북](week02_temporal_preprocessing.ipynb) 또는 [보충 HTML](week02_temporal_preprocessing.html)을 엽니다.

1. **지표·ROC:** 아래의 0~1 점수표를 손으로 계산하고 코드와 대조한 뒤, 보충 4절과 6절의 지표·임계값·ROC 독립 과제를 풉니다. 양성 예측이 없는 경우처럼 분모가 0인 경우를 설명합니다.
2. **전처리:** 이 노트북 2절의 평균 대체·표준화를 사용하고, 보충 3절과 6절에서 중앙값 대체, 최소·최대 변환, one-hot과 미지 범주를 수행합니다. 각 통계와 범주 목록은 훈련에서만 배웁니다.
3. **과거 특성:** 보충 1–2절과 6절에서 개체별·시간순 forward-fill, 원본 관측의 최근 세 값과 평균·모집단 표준편차, 범주형 특성을 만듭니다. 목표 행과 허용된 과거 문맥을 구분합니다.
4. **분할·재실행:** 이 노트북 6절의 새 입력과 보충 6절의 분할 설계·코드를 수행합니다. 개체와 시간 조건, 입력·출력 순서, 통계량, 오류 반례와 받은 도움을 기록합니다. 모든 제약을 만족할 수 없을 때에는 그 이유를 설명합니다.

이 노트북은 **측정 직후**에 그 측정값을 사용할 수 있는 계약이고, 보충은 **측정 전**에 예측하므로 같은 시각의 측정값을 쓸 수 없습니다. 계약이 달라진 것이며 어느 규칙을 모든 과제에 적용할 수는 없습니다.

### ROC 연습용 별도 표

실제 라벨 `[1, -1, 1, -1]`과 양성 점수 `[0.9, 0.6, 0.4, 0.1]`입니다. 점수가 임계값 이상이면 `+1`로 예측합니다. 임계값 0.5와 0.3의 혼동행렬 및 TPR/FPR을 먼저 적으세요. 예제의 네 점수는 확률처럼 읽는 0~1 값이지만 실제 확률의 보정 여부는 이 표만으로 알 수 없습니다.'''

temporal.cells[0].source += '''\n\n앞 교안은 측정 **직후**에 그 측정값을 사용할 수 있었지만, 이 보충은 측정 **전** 예측입니다. 따라서 같은 시각의 측정은 사용할 수 없습니다. 각 자료의 계약에 따라 달라지는 것이며 서로 모순되는 규칙이 아닙니다. [앞 교안 노트북](week02_prediction_evaluation.ipynb) · [앞 교안 HTML](week02_prediction_evaluation.html).'''
old=temporal.cells[16].source
assert '예측 행 M4/M5/N4/N5' not in old
old=replace_once(old,'''예측 행 M4, M5, N4, N5는 훈련이고, P6, P7, Q6, Q7은 검증입니다. 훈련 정답은 시각 6 전에 모두 알려졌다고 가정합니다. P/Q의 허용된 과거는 예측 서비스에 이미 도착한 라벨 없는 같은 개체의 문맥입니다. 검증 정답은 순서대로 $[+1,-1,+1,-1]$입니다. 최종 테스트의 새 개체와 정답은 별도 보류합니다.''','''아래는 **예측 대상 행**과 사후에 확인할 정답입니다. 정답 열은 예측 특성으로 사용하지 않습니다. 각 정답은 해당 시각의 예측 후 그날 끝에 도착하고, 시각 5의 정답은 시각 6 전에 알려진다고 가정합니다.

| 대상 행 | M4 | M5 | N4 | N5 | P6 | P7 | Q6 | Q7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 사후 정답 | -1 | +1 | -1 | +1 | +1 | -1 | +1 | -1 |

**먼저 분할을 직접 설계하세요.** 시각 6 전에 학습을 끝내고, 그때까지 훈련에 없던 새 개체의 시각 6·7을 순차적으로 예측하는 것이 목표입니다. 위 여덟 대상 행을 빠짐없이 훈련과 검증에 배정하세요. 훈련·검증의 개체가 겹치지 않으며, 훈련 정답은 검증 예측 전에 도착해야 합니다. 선택한 행 ID와 이유를 쓰고, 코드로 그룹 교집합과 훈련·검증 대상 시각의 순서를 검사하세요. 각 개체의 허용된 과거는 라벨 없는 문맥으로 쓸 수 있지만 훈련 대상 행이나 전처리 `fit`에 자동으로 들어가지는 않습니다. 같은 개체를 양쪽에 두는 후보와 시간 순서를 거꾸로 한 후보가 왜 이 목표에 맞지 않는지도 설명하세요. 최종 테스트의 새 개체와 정답은 생성되지 않았습니다.''')
old=replace_once(old,'''3. 점수는 변환한 `recent` 자체이고 클수록 양성입니다. 이 자료는 훈련 범위가 8이어서 아래 값과 임계값을 이진 부동소수로 정확히 표현할 수 있습니다. 다른 자료의 경계는 부동소수 오차를 확인하고 비교 정책을 정해야 합니다. 점수가 임계값 이상이면 양성입니다. 임계값 $2$, $5/4$, $-1/8$에서 TP/FP/TN/FN, 정확도·정밀도·재현율·F1, FPR/TPR을 구하세요. ROC 좌표를 임계값이 높은 순으로 적어 가로축 FPR, 세로축 TPR에 그린 뒤 동점이 한 번에 바뀌는지 확인하세요. 실제 양성 또는 음성이 없는 표와 양성 예측이 없는 표에서 어떤 분모가 0인지 쓰세요.''','''3. 점수는 변환한 `recent` 자체이고 클수록 양성입니다. 이 자료는 훈련 범위가 8이어서 아래 값과 임계값을 이진 부동소수로 정확히 표현할 수 있습니다. 다른 자료의 경계는 부동소수 오차를 확인하고 비교 정책을 정해야 합니다. 점수가 임계값 이상이면 양성입니다. 임계값 $2$, $5/4$, $-1/8$에서 TP/FP/TN/FN, 정확도·정밀도·재현율·F1, FPR/TPR을 구하세요. ROC 좌표를 임계값이 높은 순으로 적어 가로축 FPR, 세로축 TPR에 그린 뒤 동점이 한 번에 바뀌는지 확인하세요. 실제 양성 또는 음성이 없는 표와 양성 예측이 없는 표에서 어떤 분모가 0인지 쓰세요.

   이제 후보 임계값은 $2$, $5/4$, $-1/8$, $-1$이며 **검증 F1이 가장 큰 값**을 고릅니다. F1이 같으면 **더 높은 임계값**을 고른다는 기준을 미리 정합니다. $-1$에서 달라지는 예측이 있는지 먼저 확인하고, 선택한 임계값과 이유를 적은 뒤 고정하세요. 같은 예측을 만드는 두 임계값은 ROC의 서로 다른 새 좌표를 만들지 않습니다. 이 선택은 검증용 정답으로만 하고 최종 테스트는 사용하지 않습니다.''')
old=replace_once(old,'''직접 새 DataFrame을 만들고 분할, 특성 생성, `fit`/`transform`, 임계값별 계산을 작성하세요. 결과를 적을 때 행 ID·점수 순서와 사용한 도움을 함께 남기세요.''','''**고정 후 라벨 없는 새 연습 입력.** P/Q의 시각 7 검증 정답까지 도착한 뒤, 아래 새 개체들의 시각 8을 예측합니다. 다음 원본 측정은 모두 해당 예측 전에 도착했고 정답 열은 제공되지 않습니다. 이 행들은 독립 최종 테스트가 아닌 합성 연습 입력입니다.

| 개체 | 시각 1 | 시각 2 | 시각 7 | 종류 |
|---|---:|---:|---:|---|
| R | 3 | 5 | 9 | bronze |
| S | 2 | 1 | 0 | gold |
| U | 3 | 1 | -1 | silver |

R8, S8, U8 순서로 `recent`, `mean3`, `std3`를 만들고, 선택한 훈련 행에서 이미 배운 변환과 **고정된 임계값**을 그대로 적용하세요. 정답 열 없이 행 ID에 대응한 예측을 출력하고, 행 수와 순서 및 미지 종류의 처리도 확인하세요. 이 입력으로 다시 `fit`하거나 임계값을 바꾸지 않습니다.

직접 새 DataFrame을 만들고 분할, 특성 생성, `fit`/`transform`, 임계값별 계산과 라벨 없는 예측을 작성하세요. 결과를 적을 때 행 ID·점수 순서와 사용한 도움을 함께 남기세요.''')
# Split the long exercise into focused markdown cells; retain the original exercise ID.
parts=old.split('\n\n1. 각 행의 `recent`를 구하고,',1)
assert len(parts)==2
setup=parts[0]
rest='1. 각 행의 `recent`를 구하고,'+parts[1]
chunks=[]
for marker in ['\n2. 훈련 `recent`','\n3. 점수는 변환한','\n4. 아래 코드는 왜','\n**고정 후 라벨 없는 새 연습 입력.**']:
 a,sep,b=rest.partition(marker)
 assert sep, marker
 chunks.append(a)
 rest=marker.lstrip('\n')+b
chunks.append(rest)
temporal.cells[16].source=setup
new_cells=[nbf.v4.new_markdown_cell(chunk.strip(),id=f'w02-exercise-{i}') for i,chunk in enumerate(chunks,1)]
temporal.cells[17:17]=new_cells

nbf.validate(main); nbf.validate(temporal)
# Rewrite only the existing declarative cell calls in the main source builder.
builder_path=ROOT/'build_week02.py'
builder=builder_path.read_text(encoding='utf-8')
tree=ast.parse(builder)
calls=[node for node in tree.body if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id in ('md','code')]
assert len(calls)==len(main.cells)
lines=builder.splitlines(keepends=True)
for node,cell in reversed(list(zip(calls,main.cells))):
 fn=node.value.func.id
 source=cell.source
 assert "'''" not in source
 replacement=f"{fn}(r'''\n{source}\n''')\n"
 lines[node.lineno-1:node.end_lineno]=[replacement]
builder=''.join(lines)
old_header='''from pathlib import Path
from textwrap import dedent
import nbformat as nbf

ROOT = Path(__file__).resolve().parent
cells = []
def md(s):
    cells.append(nbf.v4.new_markdown_cell(dedent(s).strip()))
def code(s):
    cells.append(nbf.v4.new_code_cell(dedent(s).strip()))
'''
ids=[c.id for c in main.cells]
new_header='''from pathlib import Path
from textwrap import dedent
import argparse
import os
import nbformat as nbf

# IDs are bound to the existing lesson, rather than freshly randomized on each build.
CELL_IDS = %s
cells = []
def md(s):
    cells.append(nbf.v4.new_markdown_cell(dedent(s).strip(), id=CELL_IDS[len(cells)]))
def code(s):
    cells.append(nbf.v4.new_code_cell(dedent(s).strip(), id=CELL_IDS[len(cells)]))
''' % repr(ids)
builder=replace_once(builder,old_header,new_header)
old_tail='''nbf.validate(nb)
nbf.write(nb, ROOT / "week02_prediction_evaluation.ipynb")
print(f"Created {len(cells)} cells")'''
new_tail='''nbf.validate(nb)

parser = argparse.ArgumentParser(description="Build the lesson only at an explicitly new notebook path.")
parser.add_argument("--output", type=Path, help="new .ipynb file under an existing non-symlink directory")
parser.add_argument("--check-source", type=Path, help="compare cell IDs, types, and sources without writing")
args = parser.parse_args()
if args.output is None and args.check_source is None:
    parser.error("provide --output or --check-source")
if args.check_source is not None:
    existing = nbf.read(args.check_source, as_version=4)
    nbf.validate(existing)
    projection = lambda book: [(c.id, c.cell_type, c.source) for c in book.cells]
    if projection(existing) != projection(nb):
        parser.error("builder and notebook cell IDs/types/sources differ")
    print(f"Source and IDs match: {args.check_source} ({len(cells)} cells)")
if args.output is not None:
    target = Path(os.path.abspath(args.output))
    if target.suffix.lower() != ".ipynb":
        parser.error("--output must name a new .ipynb file")
    if target.exists() or target.is_symlink():
        parser.error("--output already exists or is a symlink")
    if not target.parent.is_dir():
        parser.error("--output parent must already exist")
    if any(part.is_symlink() for part in (target.parent, *target.parent.parents)):
        parser.error("--output parent path must not contain symlinks")
    # Exclusive creation refuses an existing file, directory or symlink even if it appears later.
    with target.open("x", encoding="utf-8") as handle:
        nbf.write(nb, handle)
    print(f"Created {len(cells)} cells at {target}")'''
builder=replace_once(builder,old_tail,new_tail)
compile(builder,str(builder_path),'exec')
nbf.write(main,main_path)
nbf.write(temporal,temporal_path)
builder_path.write_text(builder,encoding='utf-8')
print('updated', main_path, temporal_path, builder_path, 'cells',len(main.cells),len(temporal.cells))
