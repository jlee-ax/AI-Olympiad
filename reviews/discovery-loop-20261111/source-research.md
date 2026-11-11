# 외부 요구 발견 조사 · 2026-11-11

공식 범위, 실제 문제 세 종류, 배열·텐서 계약, 평가 실수 사례, 기초 이론의 **12개 primary 문서**를 읽었다. 이 조사는 제한된 표본이며 전체 인터넷·전체 출제범위·학습자 숙달의 완전성을 주장하지 않는다. 구체 chain과 실제 cell locator는 [source-research.json](source-research.json)에 있다.

## 적용 범위 판정

[KOAI 2027 안내](https://kitpa.org/koai/2027)의 현재 연결 [국내 실라버스](https://kitpa.org/koai/syllabus)는 본문 L74에 IOAI 2026 기준으로 표시한다. 별도 [IOAI 2027 공식 PDF](https://ioai-official.org/wp-content/uploads/2026/11/IOAI_Syllabus.pdf)는 p2 technical fundamentals, p4 §5 강화학습을 포함한다. 국제 최신 항목을 국내 2027 확정 범위 또는 1주차 필수로 자동 승격할 근거는 찾지 못했다. 국내 적용성은 research backlog다.

[2026 예시 게시물](https://kitpa.org/files/36)은 고등부 학습 참고, 정답 미공개, 난도 순 아님을 명시한다. 예시의 개별 요구를 교안 전체 또는 난도 순서로 취급하지 않았다. 공식 범위에 포함됨, 실제 과거 문제에 등장함, 후속 학습에 필요한 선수임, 지금 주차에 가르쳐야 함은 별개의 판단이다.

## 직접 읽은 문서

| ID | primary 문서 | 정확 읽은 위치 | 지위 |
|---|---|---|---|
| S01 | [KOAI/IOAI 출제 기준](https://kitpa.org/koai/syllabus) | L72–196; 특히 L74, L87–132, L133–160 | 2026 기준이라는 본문 표시; KOAI 2027 페이지가 연결 |
| S02 | [KOAI 2026 예시문제](https://kitpa.org/storage/c4016751-0e2c-4548-ab70-ecec994e8f8d.pdf) | PDF p1 Q1–2; p2 Q6; p6 Q19–22; p7 Q25; p9 Q32; p10 Q34; p17 서술2; p18 서술3 (페이지 1-based) | 2026 고등부 학습 참고 예시; 정답 미공개; 난도 순 아님 |
| S03 | [IOAI 2027 Syllabus](https://ioai-official.org/wp-content/uploads/2026/11/IOAI_Syllabus.pdf) | PDF pp1–4; L0–139 | IOAI 2027; 2026/11 경로 |
| S04 | [IOAI 2025 Individual Contest — Radar](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Radar/Radar.ipynb) | raw L19–167 statement; L211–255 loading; L309–340 model/loss shapes; L431–443 output | 2025 본대회 개인전; main 동적 원문/공식 baseline |
| S05 | [IOAI 2025 Individual Contest — Restroom Icon Matching](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Restroom/Restroom.ipynb) | raw L19–114 statement; L153–162 sorting; L210–277 embedding/matching | 2025 본대회 개인전; main 동적 원문/공식 baseline |
| S06 | [IOAI 2025 Individual Contest — Concepts](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Concepts/Concepts.ipynb) | raw L23–163 description/schema; L167–218 scoring/API; L268–275 runtime | 2025 본대회 개인전; main 동적 원문/공식 baseline |
| S07 | [NumPy — Broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html) | General broadcasting rules L73–106; 설명 L44–65 | stable 조회 시 NumPy v2.5 Manual |
| S08 | [PyTorch — Embedding](https://docs.pytorch.org/docs/2.15/generated/torch.nn.Embedding.html) | L560–591 parameters/shape; L611–636 examples | stable redirect → 2.15, 조회일 2026-11-11 |
| S09 | [PyTorch — scaled_dot_product_attention](https://docs.pytorch.org/docs/2.15/generated/torch.nn.functional.scaled_dot_product_attention.html) | L458–489 equivalent computation; L494–516 mask semantics; L552–583 shape | stable redirect → 2.15; beta API |
| S10 | [scikit-learn — Common pitfalls and recommended practices](https://scikit-learn.org/stable/common_pitfalls.html) | §12.1 L76–119; §12.2 L120–208 | 조회 시 1.9.1 documentation |
| S11 | [Stanford CS231n — Linear Classification](https://cs231n.github.io/linear-classify/) | Softmax classifier / Numeric stability L182–209 | 정적 course notes; 현재 optimizer 권고로 전용 안 함 |
| S12 | [Stanford CS231n — Learning](https://cs231n.github.io/neural-networks-3/) | Gradient Checks L25–47; Sanity checks L66–72; Train/Val accuracy L88–104 | 정적 course notes; 임계값을 보편 채점 기준으로 복사하지 않음 |

## 발견 결과와 배치

- **now:** 현재 1주차에 있는 축·원소 대응, feature/target 구분, 예측 시점, 순서와 식별자를 보존하는 토대를 확인한다. 단순 실행 성공이나 같은 shape로 숙달을 대체하지 않는다.
- **later:** KNN의 거리→이웃→투표, label encode/decode, 검색 행렬과 ID 복원, train-only preprocessing, embedding lookup 축, attention mask 의미, softmax/수치 안정화를 각각 선수와 연결한다.
- **defer:** mutable default/alias 심화, 수치 gradient-check의 정밀도와 상대오차. 존재를 기록하되 초보 1주차 필수로 확대하지 않는다.
- **research:** 국내/국제 syllabus 버전차 및 새 강화학습·remote tooling 적용 여부.

행렬곱·embedding·stack은 탐색 출발 후보였다. 읽은 자료는 행렬곱과 embedding의 후속 쓰임을 지지하지만 특정 주간 배치를 정하지 않는다. 실제 Restroom baseline은 cat을 사용하므로 stack 자체를 필수 기법으로 만들지 않았다. baseline의 두 번째 topk 선택은 공인 정답이나 최적 matching 규칙으로 일반화하지 않았다.

현재 교안은 91셀, notebook SHA-256 `733c0093b44f30d31354567331c2c39ee325ed074e7a6368bb1f2e96f0c174c0`으로 확인했다. baseline은 87셀, HEAD `204743d94a4176ace81c64f138567c2cc12041d1`이다. 두 교안은 읽기만 했다. actual id와 0-based index를 기록하여 prose 키워드 존재와 실제 학습·독립 평가를 구별했다.

## 봉인된 신규 요구 평가 후보

`H01` weighted metric의 분모와 순위 역전, `H02` 개발 API와 추론 환경 가용성을 JSON에 별도 heldout split으로 기록했다. 상세는 implementation agent에게 직접 전달하지 않았다. H01은 개발 요구와 Radar source를 공유하므로 **요구 단위 holdout**이며 source-family holdout은 아니다. H02는 다른 generation task에서 나왔다. 이 연구 기록만으로 loop가 검증됐다고 주장하지 않으며, root의 동결된 구현에 대한 evaluator 실행 기록이 추가로 필요하다.

## 한계

코드·자료·문제 전체를 실행하거나 학생 답안을 채점하지 않았다. 독립 assessment는 원문 복제가 아닌 새 입력 및 이유 설명으로 설계한 교육적 추론이다. 학습자 숙달은 미측정 상태다. 원격 main/stable 문서는 바뀔 수 있어 조회일·해결된 library 버전·읽은 위치를 기록했으며, 원격 commit hash는 확보하지 못했다. 기존 교안·데이터·시스템 파일 수정, commit, push는 하지 않았다.
