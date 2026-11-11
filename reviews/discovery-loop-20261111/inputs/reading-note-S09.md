# Direct-read research note S09

This is the research agent's paraphrased reading record, not an original-source snapshot.

{
  "source_id": "S09",
  "family": "tensor_contract",
  "title": "PyTorch — scaled_dot_product_attention",
  "url": "https://docs.pytorch.org/docs/2.15/generated/torch.nn.functional.scaled_dot_product_attention.html",
  "version": "stable redirect → 2.15; beta API",
  "location": "L458–489 equivalent computation; L494–516 mask semantics; L552–583 shape",
  "read_extent": "동등 계산, bool/float mask 의미, broadcast 조건, Q/K/V/output 축 읽음; fused kernel 상세 제외",
  "status": "direct_primary_read",
  "evidence_paraphrase": "attention score의 마지막 축은 source 위치다. mask는 score shape로 broadcast되어야 한다. 이 API의 bool True는 참여이며 MHA key_padding_mask와 극성이 반대다."
}
