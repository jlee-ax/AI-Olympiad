# ca89 후보의 문맥·적용 범위 조회

이 기록은 새 후보의 실제 바이트와 읽기 전용 도구 출력에 대한 **별도 문맥 관측**이다. K01–K16 quality bundle, graph 승인, workflow 승인이나 새 discovery_loop session을 생성하지 않았다. JSON을 작성했다는 이유로 도구가 새 교육적 판정을 검증했다고 표현하지 않는다. 독립 내용 검토는 완료 후 별도 파일로 연결한다.

후보 notebook SHA는 `ca89cf21b31a82e51f083344f3d156e046ad1356d31c22ffd87607aeeddd4551`, HTML은 `f2d7d0fb5326e901335aa47350caba489bf64309e27f1befc866442f30883b28`, teacher는 `d93a33f70a4db3e028f0f00a68c83c50270f73351c68987a2a71f721b69015d7`다. 읽은 후보의 원바이트는 artifact-exact.ipynb, source 투영은 lesson-source.md에 있다. context.json은 읽은 자료·기준·도구 버전을 각각 결합한다.

## 직접 읽은 변화와 아직 하지 않은 판단

15ab…의 기존34셀 ID가 모두 유지되고 4개 셀이 추가되어38셀/18코드가 되었다. source가 같은 셀도 앞에서 만든 상태가 바뀌면 실행 의미가 달라질 수 있으므로 자동 유지 판정으로 사용하지 않는다.

직접 source를 읽어 다음 변화를 확인했다.

- 같은 합성 화분의 (2,2,2) 행·열·범주 채널을 읽고, 잎 AND 노랑 조건을 공간 축에 걸쳐 합산한다. 배경 색 변경 불변성과 같은 shape의 위치 차이를 비교한다.
- 물/10ml와 직접 만든 잎 개수를 함께 사용한다. 훈련 전용 물 평균, 두 특성의 class 중심, 제곱거리, 훈련 변경에 따른 새 중심/예측을 연결한다. 평균의 제곱편차 합 성질 및 중심이 잃는 분산·위치 정보도 설명한다.
- 독립 기기 문제는 채널 순서/코드 의미를 바꾸고, 학습자가 panel 특성을 만들고 모델을 선택하도록 요구한다. 원래 후속 필수 본문·bridge 경로는 남는다.

이는 이 검토자의 **source 내용 관측**이다. 새로운 모든 입력에 대한 정확성, 공식 Robot 해결, 과거19개 요구의 새 covered 판정, 학생 독립 수행이나 부담 개선을 입증하지 않는다. 기존 N01/P01의 자료설계 판정은 15ab… 당시 범위의 역사 기록이다. 새38셀에 그 승인을 자동 이전하지 않았다.

`../sources-and-scope.md`는 후보를 읽기 전에 수행한 별도 교사 연구의 원문 비교·교육 추론·한계를 기록한다. 이 capture 프로그램은 그 로컬 메모와 실제 파일을 해시로 결합할 뿐 원출처 진위나 상위 웹사이트 최신성을 인증하지 않는다. 작성자의 validation.json은 별도 실행 주장/영수증이며 독립 내용 검토와 구분한다. 이 상태 조회에서 변형 notebook 코드나 학생 답안을 실행하지 않았다.

## 실제 옛 상태 조회

실제 실행 명령·종료값·stdout 원바이트 SHA는 query-results-summary.json에 있다. 각 queries/*.stdout.json.gz는 **실제 CLI stdout 전체**를 그대로 압축 보존했다. gzip 해제 후 JSON으로 읽을 수 있다. 도구 exit0은 내용 승인이나 완료 신호가 아니다.

| 조회 | 관측한 결과와 해석 |
|---|---|
| 옛15ab discovery report | bound=15ab…, actual=ca89…로 artifact_changed. 요구19·질문8·큐17·needs_work·ready=false를 유지 |
| 옛 context verifier | exit2. 새 artifact 바이트와 도구3개 SHA/저장 CLI 결과의 변경을 감지. 예전 판단을 고치지 않음 |
| 옛 ee827 quality/workflow | 다른 원본 교안 전용. quality uncertain/ready=false, workflow criteria_agreement_required pause |
| 옛 graph/depth/paths에 옛 통합 discovery를 함께 입력 | artifact mismatch, discovery 미해결 및 N01/P01 path 누락 등으로 blocked. 새 교안의 quality/graph 승인으로 사용할 수 없음 |
| 옛 quality의 artifact path/SHA만 바꾼 메모리 내 대조 | K05/W1-table의 옛 cell:1ab9cd79가 없어 거부. 원 record는 쓰지 않음 |

옛 session 파일 SHA는 실행 전후 모두 `9c4ceb26c18bb2a2c9e0b912036bff2fb9aff8dfaf3adf0fdc3e08e9bafe9145`다. context.json은 session/report/manifest·옛 quality/graph/workflow와 보존된 원본3교안의 전후 SHA를 기록한다. 새 user-directed 작업의 실행 승인은 과거 기준 합의가 아니다. 옛 pause를 해제하거나 옛 큐17을 덮어쓰지 않았다.

## 후속 전이의 조건

현재는 문맥 기록만 있다. 새 최종 후보와 독립 검토가 확정되면 그 실제 artifact/result/report SHA를 새 증거 파일에 추가한다. 후보 바이트가 달라지면 이 기록을 남기고 새 run으로 캡처한다.

도구가 지원하고 요구별 실제 근거가 준비된 경우에만 새 discovery session을 만들 수 있다. 그때도 원래19개 요구 payload와8개 질문을 보존하고, 영향 차원은 직접 대조하며, 나머지 유지에는 명시적 근거를 남겨야 한다. 이번 기록은 그런 전이를 실행했다고 주장하지 않는다. 새 source 요구는 별도 frontier/read/trace로 추가해야 하며 기존 요구를 축소하지 않는다.

좁은 새 quality/graph를 만들 경우에도 현재 명세의 unit·선수·oracle·T체크와 실제 셀/외부 필수 자료를 직접 매핑해야 한다. scope fingerprint와 context_bindings 캡처는 승인과 다르다. graph의 실제 평가·피드백 내용은 독립 의미 검토가 필요하며, 빈 역할 이름·일치하는 해시로 충족을 추론할 수 없다. 기존 전체 artifact/실행/집계 게이트와 criteria 합의 대기는 그대로 남는다.
