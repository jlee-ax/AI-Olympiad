# 새 후보의 시스템 문맥·독립 검토 연결

후보 `ca89cf21b31a82e51f083344f3d156e046ad1356d31c22ffd87607aeeddd4551`에 대한 별도 문맥 기록을 완료했다. `candidate-ca89-01/context.json`은 캡처 당시 독립 검토 pending을 그대로 보존한다. 이후 확정된 독립 내용·기능 판정은 `candidate-ca89-01/independent-review-addendum-01.json`에서 실제 보고서·결과·변이 판정의 SHA와 같은 notebook SHA로 연결했다.

독립 검토는 정상12개·의도 오류8개가 기대와 맞았으며, 오류 검출은 교안 자체 assert4개와 독립 oracle4개로 구분했다. 유한한 후보 범위에서 차단 결함을 재현하지 않았고, 여러 필드→표현→학습 전이의 평가 기회를 자료설계 수준에서 보완했다고 판정했다. 이 보고는 학생의 독립 성취·시간·10주 readiness나 K01–K16 통과가 아니다. 검토자의 참조 해답을 학생의 빈 답안으로 계산하지 않았다. 이후 이식성 검사는 별도 후속 증거다.

옛15ab discovery는 실제 새 바이트에서 artifact_changed를 표시했으며 session SHA는 `9c4ceb26…9145`로 그대로다. 원래19요구·8질문·큐17과 옛 criteria_agreement_required pause를 유지했다. 옛 ee827 품질·그래프 기록을 새 교안의 승인으로 옮기지 않았다. 새 quality bundle·graph 승인·discovery tool session은 만들지 않았다.

명령·exit·실제 stdout 원바이트는 query-results-summary.json 및 queries/*.stdout.json.gz, 직접 읽은 적용 범위는 scope-review.md에 있다. 보정된 validation SHA `54b8e0b9…33e1`과 검사기 SHA `c7c8d4f1…a1b10`도 실제 재확인했다. 기계적 바이트/결합 검증은 다음으로 재현할 수 있다.

```sh
python3 -B reviews/week01-deepening-20261111/system-context/verify_context.py --run candidate-ca89-01 --independent-addendum independent-review-addendum-01.json
```

결과는 `candidate-ca89-01/mechanical-verification-final.json`이다. 이 검증기는 파일/결과 결합과 기록된 상태만 검사하며 원문 진실성·교육적 충족이나 학습 효과를 도출하지 않는다. 기존 pending 원본과 이전 두 검증 결과는 덮어쓰지 않았다. 이번 검토자는 이 system-context 폴더에만 썼고 원 교안·옛 기록·git index·원격을 변경하지 않았다.
