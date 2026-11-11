# Direct-read research note S11

This is the research agent's paraphrased reading record, not an original-source snapshot.

{
  "source_id": "S11",
  "family": "foundational_theory",
  "title": "Stanford CS231n — Linear Classification",
  "url": "https://cs231n.github.io/linear-classify/",
  "version": "정적 course notes; 현재 optimizer 권고로 전용 안 함",
  "location": "Softmax classifier / Numeric stability L182–209",
  "read_extent": "softmax·cross entropy·상수 이동·overflow 코드 읽음; subagent가 mapping/loss 앞부분도 교차 확인",
  "status": "direct_primary_read",
  "evidence_paraphrase": "분류 점수의 정규화와 정답 index 선택은 서로 다른 연산이다. 공통 최댓값을 빼면 확률을 유지하면서 지수 계산의 큰 값을 줄일 수 있다."
}
