# 시퀀스 lookup·유효 위치 평균 · 후보 전 기준

현재 b530 통합본/de5 bridge 및 연결 필수·2주/10주 계획을 읽고 새 후보 편집 전에 고정한다. 해시/코드 실행·자료 설계 판단·학생 성취는 구분한다. 이번 기록은 기존 승인·미해결 큐를 자동 변경하지 않는다.

1. **선택 범위:** 기존 lookup을 토큰 ID→벡터(B,T,d)→유효 위치 합/개수→query(B,d)로 확장하고 기존 필수 B의 raw/cosine/ID 문제에 잇는다. 새 검색/표 단원이나 별도 전체 모델 파이프라인을 쌓지 않는다. 기존 원본 A–E·교량 A/B·통합 fit/검증/CSV·다른 합리적 모델 허용을 보존한다.
2. **이미 있는 기초 인정:** 현 bridge21–23은 lookup 축·실제 값·자리 교환을 올바르게 설명한다. 부족한 부분은 V=T=3의 우연 일치를 깨는 새 독립 전이와 padding을 제외한 벡터 평균이다. 현 평균/axis/코사인이 잘못됐다는 판정으로 확장하지 않는다.
3. **축·의미:** V(어휘행), T(문장 자리), d(벡터좌표), B(문장 묶음)를 구별한다. 고정 입력은 V7,T4,d3,B2로 모두 다르다. ID는 lookup이지 matmul 가중치가 아니다. 각 위치의 실제 조회값과 pooled 결과를 확인한다.
4. **수식·손계산·코드:** m=유효 토큰 여부, count=sum_t m, sum_j=sum_t m*E[...,j], mean_j=sum_j/count를 구체 값/축/분모와 연결한다. 분모는 T나 V나 d가 아니다. mask(B,T,1) broadcast와 합산 후 남는 B,d를 설명한다. 직접 루프/NumPy 등 타당한 구현을 허용한다.
5. **PAD·영벡터·반복:** PAD는 ID 계약으로 제외한다. 비영 PAD 벡터와 영벡터 정상 단어를 반례로 둔다. 반복 토큰은 위치마다 센다. deduplicate나 벡터0 여부로 유효성을 결정하면 틀릴 수 있다. PAD를 늘리거나 PAD 벡터만 바꿔도 올바른 mean은 유지돼야 한다.
6. **ID 경계:** 토큰 ID의 0<=ID<V 정수 계약을 지킨다. 음수는 NumPy에서 끝행을 고를 수 있어 의미상 잘못된 토큰을 조용히 허용하지 않는다. 범위밖을 clip/modulo하거나 ID를 무근거 실수로 평균내지 않는다. 광범위 타입 검증은 실제 선언 범위로 판단한다.
7. **빈 문장·단계 경계:** all-PAD는 count0으로 수학적 평균이 없다. 명확한 오류 또는 count/invalid와 함께 설명한 placeholder를 허용하되 진짜 평균0이라고 하지 않는다. 정상 영벡터 단어는 count1/mean0일 수 있으며 이 평균은 유효하다. 이후 cosine의 zero-direction 오류는 별도 단계다. 이 구별을 숨긴 채 전체 경로 성공으로 꾸미지 않는다.
8. **순서 손실:** 토큰 위치를 바꾸면 lookup 자리는 바뀌지만 mean은 불변일 수 있다. 위치 정보를 잃는 설계의 한계이며, 문장 의미/FindOrder 시간순위를 모두 해결했다는 뜻이 아니다. padding mask는 여기서 평균 참여를 뜻하며 attention/causal mask와 같은 알고리즘·극성이라고 가르치지 않는다.
9. **실제 모델 경계:** 제공한 고정 벡터는 학습된 embedding이나 BERT·TF-IDF·오디오 인코더를 실제 실행한 것이 아니다. embedding 학습·신경망 loop는6주, 실제 텍스트 토큰화/padding/mask/모델은8주, 실제 오디오/멀티모달은9주의 별도 실물·평가로 남긴다. 10주 새 명세 평가를 이 예제로 완료하지 않는다.
10. **독립 평가/실행:** 최종 SHA를 받은 뒤 실제 교안 함수를 frozen 새 입력에 호출한다. 후보 실제 코드와 검토자 새 참조 해답을 분리한다. 각 사례는 새 subprocess/새 in-process 커널. 정상 control 후 한 오류씩 넣고 기대·실제·실패/검출 못함을 보존한다. 학생 빈 답안은 실행 성공이나 검토자 풀이로 대체하지 않는다.
11. **부담·보존:** lookup이 기존 B의 query를 만드는 한 경로로 통합돼야 한다. 기존 필수 결과물/단위를 지우거나 ‘선택’이라는 이유로 후속8주 필수까지 면제하지 않는다. 첫주 필수 승격/선수 범위를 명시하되 기존120분/5–7시간 적합성·학생 실패/난도를 관찰 없이 단정하지 않는다. 학생용에는 내부 운영·시간 배정/검증 상태를 넣지 않는다.
12. **비교 대안 유지:** inverse rank는 위치→ID와 다른 역대응으로 여전히 유효한 후속 공백이다. Pixel의 공간경계/면적 예산도 별도7주 적용 과제로 남는다. 이번 선택으로 이들 전체 요구가 닫혔다고 기록하지 않는다.

## 원문 대조와 이번 선택

현 lookup에는 토큰(B,T)과 표(V,d)의 의미 설명이 있으나 독립 lookup 빈칸과 유효 평균 평가가 없다. 이번에는 그 선택 예를 기존 B의 입력 생성으로 연결해 별도 신규 과제 누적을 줄이는 설계를 검토한다.

- [PyTorch Embedding](https://docs.pytorch.org/docs/2.15/generated/torch.nn.Embedding.html): 입력(*)→출력(*,H), 어휘행/좌표 및 padding_idx의 동작을 확인했다. padding_idx가 downstream mean 분모를 자동으로 고치는 기능은 아니다. 새 PAD 벡터는0이 기본이지만 바꿀 수 있다.
- [DAN 원논문](https://aclanthology.org/P15-1162.pdf), §2.1 평균식과 §3.1 선택된 토큰 평균: 벡터를 유효 원소 수로 나누는 원리와 순서 없는 표현의 범위를 대조했다. 논문의 신경망 학습·성능을 이 고정 표로 재현했다고 주장하지 않는다.
- [NumPy indexing](https://numpy.org/doc/stable/user/basics.indexing.html): 음수 index와 정수 array lookup의 실제 의미를 확인했다.
- [Find the Order 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/1_Find_the_Order/statement.md) 및 [argsort](https://numpy.org/doc/stable/reference/generated/numpy.argsort.html): 순서 리스트와 원래 항목별 순위는 별도 계약이다. 초기 대안1순위였으나, 실제 다축/유효분모 공백을 기존 B 안에서 연결하는 제한된 lookup 안과 비교해 후속으로 유지한다.
- [Pixel 원문](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Pixel/Pixel.ipynb): 실제 이미지 모델과 픽셀 예산/출력의 별도 적용 과제다. 조건부 공간 개수의 이전 합성 예만으로 완료되지 않으며 첫주에 전체 과제를 당기지 않는다.

실제 학생 시간·도움·독립 성취·전체10주 숙달은 미관찰이다. frozen 값의 오류가 나중 확인되면 기존 파일을 보존하고 이유/시점/영향을 새 addendum에 기록한다.
