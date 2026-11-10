# 근거 검토 (2026-11, 논의용)

각 논문이 실제로 다룬 범위와 이 프로젝트에 제안하는 적용을 구별한다. 논문은 특정 에이전트 구조나 30분 주기의 효능을 입증하지 않는다. 공식 KOAI 2027 공지는 별도로 확인해야 한다.

## 외부 검증과 반복

**Huang et al., “Large Language Models Cannot Self-Correct Reasoning Yet,” ICLR 2024.** [논문](https://arxiv.org/html/2310.01798v2)

- 관찰: 외부 피드백 없는 자기 수정이 추론 성능을 떨어뜨릴 수 있다. 같은 응답 수를 쓴 실험에서 토론이 self-consistency를 넘어서지 못했다.
- 설계 제안: 반복 수 자체를 품질로 취급하지 않는다. 외부 검사, 반례, 동등한 자원 예산의 비교 기준과 중단 근거를 기록한다.
- 한계: 특정 모델·과제·시점의 결과다. 모든 피드백 기반 반복이나 이 프로젝트에 효과가 없다는 뜻은 아니다.

## 반복에 관한 상반된 결과와 외부 도구

**Madaan et al., “Self-Refine: Iterative Refinement with Self-Feedback,” NeurIPS 2023.** [논문](https://arxiv.org/abs/2303.17651) 7개 과제에서 반복 피드백·수정의 평균 향상을 보고했다. 이는 앞선 Huang 등과 함께 보아야 하며, 어떤 과제에서도 반복이 정확성을 보장한다는 뜻은 아니다.

**Gou et al., “CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing,” ICLR 2024.** [논문](https://arxiv.org/html/2305.11738v3) 검색·실행 같은 도구 피드백을 활용한 수정이 일부 실험에서 향상되었으나 모든 조건에서 우세하지 않았다. 이 논문의 반복 상한과 중단 조건은 실험 설계이지 30분이라는 시간의 최적성을 뜻하지 않는다.

**Zheng et al., “Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena,” NeurIPS 2023.** [논문](https://arxiv.org/html/2306.05685v4) 모델 판정의 유용성과 위치·길이·자기선호 등의 편향을 함께 보여준다. 판정 결과를 정답 증명으로 취급하지 않고, 기준 풀이·순서 교환·사람의 표본 검토를 함께 고려한다.

## 변경 영향과 출처 추적의 형식적 유추

**Mokhov et al., “Build Systems à la Carte,” Journal of Functional Programming, 2020.** [DOI](https://doi.org/10.1017/S0956796820000088) 소프트웨어 빌드의 의존성과 변경 감지·재실행을 설명한다. 입력, 프롬프트·스킬 버전, 산출물과 검증 결과의 버전을 남기고 관련 검사를 선택하는 데 참고할 수 있다. 교육용 에이전트의 효과를 실험한 논문은 아니다.

**Buneman, Khanna and Tan, “Why and Where: A Characterization of Data Provenance,” ICDT 2001.** [DOI](https://doi.org/10.1007/3-540-44503-X_20) 결과가 왜 나타났는지와 원천의 어디에서 왔는지를 구별한다. 링크뿐 아니라 주장과 원문 위치, 변환 경로를 연결하는 설계의 참고다. 교육 성과나 에이전트 성능을 직접 입증하지 않는다.

## 그래프 검색

**Edge et al., “From Local to Global: A Graph RAG Approach to Query-Focused Summarization,” 2024, 수정판 2025.** [논문](https://arxiv.org/html/2404.16130v2)

- 관찰: 두 문서군(약 100만/170만 토큰)에서 각각 125개의 전체적 질문을 실험했다. 전체 정보를 다루는 방법들이 일반 벡터 검색보다 포괄성·다양성 평가에서 우세했다. 그래프와 일반 map-reduce의 차이는 작았고 주장 기반 실험에서는 전체 방법 간 유의한 차이가 없었다. 평가에는 LLM 쌍대 비교가 쓰였다.
- 설계 제안: 관계 및 변경 영향을 표현하는 그래프는 선택적으로 사용하고, 단순 기록·검색 대비 비용과 유용성을 검증한다.
- 한계: 특정 데이터와 질의의 결과이며, 그래프가 언제나 우월하거나 환각을 없앤다는 증거가 아니다. 논문 내 한 인덱싱 작업은 281분이 걸렸다.

## 장기 기록과 갱신

**Wu et al., “LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory,” ICLR 2025.** [논문](https://arxiv.org/html/2410.10813v2)

- 관찰: 500개 질문으로 정보 추출, 여러 세션, 시간, 정보 갱신 및 답변 보류 등을 평가했다. 한 설정에서 원문과 사실 키를 함께 인덱싱하면 원문만 사용할 때보다 Recall@10이 .692에서 .784로, GPT-4o 질의응답 점수가 .670에서 .720으로 개선됐다. 원문을 요약이나 사실로 대체하면 정보 손실이 발생해 질의응답 성능이 저하됐다.
- 설계 제안: 원기록을 보존하고 검색용 요약·키·시간·대체 관계를 추가하며, 갱신과 답변 보류도 평가한다.
- 한계: 결과는 데이터, 검색·판독 모델과 자원 예산에 의존한다. 모든 기억 저장 방식에 일반화할 수 없다.

## 학습 문제의 혼합 배치

**Rohrer et al., “A Randomized Controlled Trial of Interleaved Mathematics Practice,” Journal of Educational Psychology, 2020.** [논문 DOI](https://doi.org/10.1037/edu0000367)

- 관찰: 중학교 7학년 54개 학급에서 약 4개월의 혼합/집중 연습을 비교했고, 한 달 뒤 예고 없는 시험에서 각각 61%/38%를 보고했다.
- 설계 제안: 향후 수업에서 이전 유형을 섞어 회상하는 연습과 지연 평가를 검토한다.
- 한계: 수학 학습 연구이며 KOAI 수업이나 에이전트의 30분 작업 주기에 직접 적용된 결과는 아니다. 수업 설계 시 학생 수준과 문제 유형을 함께 검토한다.

## 아직 결정되지 않은 것

검토 간격은 사용자가 요청한 30분이다. 위 논문은 이 간격의 효능이나 최적성을 입증하지 않는다. 재검토 범위, 통과 점수, 정체 판정 횟수, 보존 기간과 중단 조건은 사용자와 협의하고 검증한다.
