# Direct-read research note S08

This is the research agent's paraphrased reading record, not an original-source snapshot.

{
  "source_id": "S08",
  "family": "tensor_contract",
  "title": "PyTorch — Embedding",
  "url": "https://docs.pytorch.org/docs/2.15/generated/torch.nn.Embedding.html",
  "version": "stable redirect → 2.15, 조회일 2026-11-11",
  "location": "L560–591 parameters/shape; L611–636 examples",
  "read_extent": "lookup 정의, weight/input/output shape, padding_idx 예 읽음; sparse/max_norm 세부는 범위 제외",
  "status": "direct_primary_read",
  "evidence_paraphrase": "정수 index 입력의 shape (*)에 embedding_dim 축이 추가되어 (*, H)가 된다. weight의 어휘 크기와 출력의 시퀀스 길이를 구별해야 한다."
}
