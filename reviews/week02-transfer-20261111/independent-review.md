# 2주 두 명세 전이 · 독립 최종 검토

검토 식별자: `/root/lesson_review`. 정확한 실행 모델 ID는 확인 가능한 정보가 없어 기재하지 않는다. 2026-11-11 검토. 이 파일만 새로 작성했으며 교안·교사자료·생성기·다른 agent 기록·1주/사용자 작업·index·remote는 수정하지 않았다. 작성자 임시 결과가 아니라 부모가 고정한 최종 원문과 지정 참조 검산기를 읽었다.

**판정:** 확인한 최종 표·수식·교사답안과 두 계약에서 실질적으로 차단할 새 결함은 재현하지 못했다. 실제 학생의 독립 해결·시간·이해가 통과했다는 뜻은 아니다. 계획의 분할 표현 충돌과 선택 범위의 한계는 아래에 열린 항목으로 남긴다.

## 실제 읽은 최종 SHA

- `lessons/week02/week02_prediction_evaluation.ipynb`: `8edc5014f9d80f8cc0813153471cd5878b73023e9e3b4903a23d8e44688f9577` (전달 SHA 일치)
- `lessons/week02/week02_prediction_evaluation.html`: `5e2f5a41b7f26ccf673529900ffa586f6a62af347296e13aeced41cbb5c86319` (전달 SHA 일치)
- `lessons/week02/week02_temporal_preprocessing.ipynb`: `4852a81b3cd19d40e3baba5447b68f6a5765402e17edf658f9c5b84e1a669ba0` (전달 SHA 일치)
- `lessons/week02/week02_temporal_preprocessing.html`: `30e27e99936beb934797148baf9646e5abb5ff8caa3da78eeb97cf550517f49f` (부모 전달값이 아닌 검토 시 관측값)
- `lessons/week02/build_week02.py`: `8d2e1754e07c4e0da8f8f80f489c047111a983bd52e77ee45ac94462747b6653` (전달 SHA 일치)
- `lessons/week02/teacher-notes.md`: `8c9f005ea78669f6b9c97face48c940a3a96a79e98e580e945386ed3f2747a9a` (전달 SHA 일치)
- `lessons/week02/week02_temporal_preprocessing_teacher.md`: `04fe73baac6f6a46874991ff5fa469834820a6fe28f1f1fcc95dd7b14e11213a` (전달 SHA 일치)
- `lessons/week02/teacher_validate_contracts.py`: `2fd86ccbdfa9cd65dc1e1f4efeb79141ef057c75b4d625bc0ebeeb559a9b46c6` (전달 SHA 일치)

이전 최초 본문813f…/교사e9f8… 등은 수정 전 정적 관찰 대상이었다. 최종 결론은 위8edc…/4852…/8c9f… 조합에만 결합한다. 이 회차는 읽기 전용으로 진행했으므로 후보 원바이트의 새 복제본은 만들지 않았다. 이전 baseline 독립 보고서와 dtype addendum, `curriculum/student-plan.html`의2~10주 선수 경로도 읽었다. 현재 두 notebook의 모든 제공 코드 source는 이전 baseline `candidate03-inputs` 판본과 ID별로 동일함을 비교했다. 이를 전체 notebook SHA가 같다고 표현하거나 옛 실행 대상을 새 SHA로 바꾸어 기록하지 않는다.

## 실제 실행과 산술 결과

준비된 venv Python의 새 subprocess에서 다음 **교사용 참조 코드**를 직접 실행했다. 출력은 `result: passed`, 종료코드는0이었다. 이 파일은 읽기와 계산·stdout만 사용함을 실행 전에 확인했다. 일반 Jupyter 커널·브라우저·원격은 사용하지 않았다.

```bash
OPENBLAS_NUM_THREADS=1 /workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python -B lessons/week02/teacher_validate_contracts.py
```

- 명세 가의 훈련 입력0,2,2,6: 대체값·중심2.5, 모집단 표준편차√19/2. 명세 나의 훈련0,2,4,6: 대체값·중심3, 표준편차√5.
- 두 검증의 R 예측은 모두[+1,+1,+1,+1], K는 모두−1. K 정확도3/4·재현율0, R 정확도1/4·재현율1이다. 따라서 가의 정확도 목표는K, 나의 재현율 목표는R을 선택한다.
- 고정 후 무라벨 출력은 가의(w8,v8)=[−1,−1], 나의(rZ,sZ)=[+1,−1]. 코드가 임의로 새 자료를 다시 fit하거나 여기서 후보를 바꾸는 절차는 아니다.
- 참조의 sklearn Pipeline과 별도 수식 통계·예측이 일치했다. 실제 이상이 없는 재현율은정의 불가로 처리한다. 참조 안의 다른 라벨/도착시각 사례는 교사용 유한 control이며 학생이 풀었다는 증거가 아니다.

다른 새 subprocess에서는 고정 SHA의 참조 파일에서 함수 AST만 읽어 메모리에 올리고, **검토자가 만든 새 입력**에 `fit_statistics/rule/counts/metrics/evaluate`를 적용했다. 파일은 수정하지 않았다. 훈련 입력[1,3,결측,5], 검증 입력[−1,3,8,결측], 검증 정답[−1,−1,+1,−1]에서 다음이 통과했다.

| 항목 | 기대·실제 |
|---|---|
| 대체값·중심·표준편차 |3,3,√2 |
| R 예측 |[−1,+1,+1,+1] |
| K 정확도·재현율 |3/4,0 |
| R 정확도·재현율 |1/2,1 |
| 검증 ID 순열(q7,p6,q6,p7) | R=[+1,−1,+1,+1] |
| sklearn fit 비교·transform 불변 | 수식과 일치,10000을 transform해도 fitted 통계 유지 |
| 잘못된 train+validation fit | 대체 평균19/6으로 달라짐; 검토자 기대 통계 비교로 누수 반례 확인 |
| 실제 이상 없음 | 재현율None(정의 불가) |

아래는 새 입력의 핵심 검산을 같은 SHA의 실제 참조 함수로 재현하는 코드다. 본문 학생 코드가 아니라 **교사용 함수+검토자 입력**이라는 경계를 유지한다.

```python
import ast, hashlib, math
from pathlib import Path
p = Path('lessons/week02/teacher_validate_contracts.py')
raw = p.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '2fd86ccbdfa9cd65dc1e1f4efeb79141ef057c75b4d625bc0ebeeb559a9b46c6'
g = {'math': math}
functions = [n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef)]
exec(compile(ast.Module(body=functions, type_ignores=[]), str(p), 'exec'), g)
g['rows'] = {
 'n1':('N',1,1,-1), 'n2':('N',2,3,1),
 'm1':('M',1,None,-1), 'm2':('M',2,5,1),
 'p6':('P',6,-1,-1), 'p7':('P',7,3,-1),
 'q6':('Q',6,8,1), 'q7':('Q',7,None,-1)}
tr = ['n1','n2','m1','m2']; va = ['p6','p7','q6','q7']
stats, pred, scores = g['evaluate'](tr, va)
assert stats[:2] == (3,3) and math.isclose(stats[2], math.sqrt(2))
assert pred == {'K':[-1]*4, 'R':[-1,1,1,1]}
assert scores == {'K':(3/4,0), 'R':(1/2,1)}
assert g['metrics']([-1,-1],[-1,1])[1] is None
assert g['evaluate'](tr, ['q7','p6','q6','p7'])[1]['R'] == [1,-1,1,1]
assert math.isclose(g['fit_statistics']([g['rows'][i] for i in tr+va])[0], 19/6)
```

검토자만의 의미 검사도 따로 수행했다. 같은 목표 행의 양쪽 중복과 미래 목적의 시간 역전은 각각 예상ValueError로 거부했고, 다른 명세라면 동일ID 사용 자체가 금지가 아님을 확인했다. 관측/도착이(1,1.2,값4),(3,7,값900)이고 예측시각5인 별도 입력에서는 도착까지 검사하면[4], 관측시각만 보면[4,900]으로 다르다는 계산도 했다. **이 의미 검사와 도착시각 계산은 검토자 참조이며 교안 내 범용 검증 함수가 아니다.** 교사 `evaluate`는 받은 ID의 숫자를 계산할 뿐 분할의 목적·자료 출처를 자동으로 판정하지 않는다. 임의의 틀린 학생 답안을 실제 검출했다는 주장도 하지 않는다.

## 내용·학생의 선택 여지

본문19는 실제로 목표가 다른 두 명세를 읽고 분할 ID·통계·같은 검증 ID 예측·평가 분모·K/R 선택·선택 고정 후 출력을 연결하게 한다. 가는 새 기기의 미래, 나는 알려진 기기의 새 설정이다. X/Y가 같은 원본의 복사·증강이 아니며 별개 원본이고, 같은 기기의 관측이 통계적으로 독립이라는 주장이 아님을 최종 본문과 교사자료에 명시했다. 이전 관측이 없으므로 시간창을 만들어 쓰는 것도 허용하지 않는다. Robot의 실제 분할을 복원한 과제가 아니다.

학생에게 답안 코드나 정답 후보를 직접 적어주지는 않았다. 양쪽의 서로 다른 점수 정의에서 정확도와 재현율을 식별하고 후보를 고르는 여지가 있다. 반면 전처리는 평균 대체/표준화, 후보는K/R, 임계값은z≥0으로 **제한되어 있다**. 이는2주의 비교 과제로 타당하지만 자유로운 표현/전처리/알고리즘 계열 설계나 비상수 학습모델 선택을 충분히 평가했다고 확대할 수 없다. R은 훈련 전처리에 의존하는 규칙이며 새로운 분류기의 관계 학습을 했다는 뜻도 아니다. 명세 가/나의 현재 표는 사실상 지정 조건으로 분할이 정해지므로 다른 입력의 복수 타당 분할까지 실제 학생이 해결했다는 증거는 없다.

보충17에서 반복 분할 설계·Robot 비교를 본문으로 통합하고 훈련/검증을 제공해 특성/변환에 집중시켰다. 보충22는 동률 결과를 미리 말하던 힌트를 ‘최고점이 여럿이라면’으로 바꿨다. 기존 AUC·최빈 기준을 더 늘리지 않았고 제공 코드 source도 유지됐다. 학생 본문20/보충23은 계속 주석만 있는 빈 답안이다. 교사용 답안과 참조값 일치는 학습자 성취가 아니다.

## 부담과 열린 문제

교사자료는 기존 단일 사례를 두 명세로 교체하고 보충 반복 분할을 통합한 점을 명시한다. 본문 독립 문장1529→2541자, 보충 도입1558→1026자로 두 부분 합계가3087→3567자라고 보고하며, 실제 고정 문서도 본문이 길어지고 두 표/두 fit·선택을 요구한다. 문제 수나 코드칸이 같아도 작업량이 줄었다고 단정할 수 없다. 수업120분·자습6~8시간은 기존 편성 추정이며 실제 학생 시간·도움·이해는 미관찰이다. 3~10주의 학습·CV·텍스트/음원/영상 분할로 이어지는 경로는 계획상의 선수 연결이지 후속 교안 완성이나 성취 확인이 아니다.

**남은 계획 충돌:** `curriculum/student-plan.html`29행의 무조건적인 같은 개체/파생 입력 분리 표현,40행2주 및52행4주 그룹 분리 표현은 알려진 동일 기기의 새 설정 평가와 여전히 표현상 충돌할 수 있다. 최종 교사자료는 이를 후속 재검토 항목으로 정확히 기록했지만 학생 시작점인 계획 자체는 수정하지 않았다. 같은 원본의 중복·증강 분리는 동일 ID의 다른 관측을 목적에 맞게 평가하는 것과 구별해야 한다. 따라서 전체 진입 경로가 완전히 일관됐다고 승인하지 않는다.

새 notebook 전체의 fresh커널 실행, 브라우저/MathJax 시각 렌더, 새 주차 전체 회귀, 학생 코드·독립 성취·실측시간·비공개 최종 평가 생성은 이번 독립 검토에서 수행하지 않았다. 제공 코드가 이전 판본과 동일하다는 비교는 그 한계를 없애지 않는다. 실행한 것은 읽기 전용 교사용 참조와 그 함수의 새 입력 계산 및 별도 검토자 의미 control이다. 소켓/브라우저 정책을 우회하지 않았고 runtime·캐시·실행 산출물을 만들지 않았다. 이 기록 파일 외의 새 파일도 작성하지 않았다.

근거 원문: [Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md), [Antique](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb), [Radar](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Radar/Radar.ipynb), [전처리와 누수](https://scikit-learn.org/stable/common_pitfalls.html), [분할과 검증 선택](https://scikit-learn.org/stable/modules/cross_validation.html). 국제 원문·축소 교육 예·학생 성취를 서로 구별했다.
