# Direct-read research note S10

This is the research agent's paraphrased reading record, not an original-source snapshot.

{
  "source_id": "S10",
  "family": "ml_validation_contract",
  "title": "scikit-learn — Common pitfalls and recommended practices",
  "url": "https://scikit-learn.org/stable/common_pitfalls.html",
  "version": "조회 시 1.9.1 documentation",
  "location": "§12.1 L76–119; §12.2 L120–208",
  "read_extent": "전처리 일관성·누수 정의·split-before-fit·랜덤 label 반례 읽음; random-state 심화 미포함",
  "status": "direct_primary_read",
  "evidence_paraphrase": "전처리의 통계와 선택은 training 자료에서만 학습하고 validation/test에는 같은 변환을 적용한다. 테스트 자료가 feature 선택에 들어가면 평가가 부풀 수 있다."
}
