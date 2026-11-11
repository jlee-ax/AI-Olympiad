# 후보의 기존 검토 freshness 조회

조회한 실제 후보는 통합본 `b530a36ae4f0b4fe9237fb29d604dc288198df7027c85c2e99d1a2e6f2a41611`, bridge `de5ba77f7cd1325769ca4af29a8fd9c851d14c8c83d5acb88a127bc277579ef0`다. 조회 전후 두 SHA가 같았다. 앞의 b080… 초안에서는 최종 freshness 실행·기록을 보류했고, 안내 수정 후 전달된 위 바이트로 실제 실행했다.

`candidate-b530-de5-01/freshness-observation.json`에 명령·exit·stdout SHA·전후 파일 SHA·실제 상태·해석을 남겼다. 각 *.stdout.json.gz는 실제 CLI stdout 전체를 gzip으로 보존했으며 해제한 bytes가 원출력과 일치하는지 확인했다. 이 기록은 기존 도구의 조회 결과를 보존한 것이며 새 quality/graph 승인이나 discovery session이 아니다.

| 실제 조회 | 결과 |
|---|---|
| ca89 문맥 verifier + 기존 독립 검토 addendum | exit2. current_artifacts_match_capture, old_records_still_unchanged, independent_result_and_mutation_bind_current_artifact가 false |
| 통합본 원래 discovery | bound15ab… / actual b530…로 artifact_changed. 기존19요구·8질문·미해결 큐17 그대로, needs_work/ready=false |
| bridge 기존 discovery | bound09efa… / actual de5…로 artifact_changed. 기존3요구·미해결 큐3 그대로, needs_work/ready=false |
| 역사적 ee827 workflow | pause/criteria_agreement_required 유지. 해당 옛 교안 전용이며 새 후보로 적용 범위를 옮기지 않음 |

ca89 verifier의 `old_records_still_unchanged` 보호 목록에는 session뿐 아니라 **bridge notebook artifact 자체**도 있다. 해당 notebook이 09efa…에서 de5…로 바뀌어 이 항목이 false다. 이번 실행에서 비교한 기존 session/report/manifest·ca89 context/addendum·옛 quality/graph/workflow 등17개 **검토 기록 파일**의 전후 SHA는 전부 같았다. 따라서 이 false를 기존 검토 기록이 변조됐다는 의미로 읽으면 안 된다.

옛 ca89 snapshot·projection·저장 stdout과 독립 evidence 파일의 자체 보존 검사는 별도다. 그것들이 보존돼도 실제 현재 notebook과의 결합은 stale이다. 원래 통합 session SHA는 `9c4ceb26c18bb2a2c9e0b912036bff2fb9aff8dfaf3adf0fdc3e08e9bafe9145`, bridge session SHA는 `75ac4108f14505e5cd147e9c0754f9ed979e969372c8d2860c2295c1b84251bf`로 전후 동일하다. 옛 N01/P01 covered 및 ca89 독립 검토 결과를 새 후보에 자동 이전하지 않았다.

wrapper의 모든 확인 항목이 true라는 뜻은 **기대된 stale 감지·기록 보존·명령 출력 보존을 확인했다는 뜻**이다. 새 교안의 교육적 충족·기능 정확성·학생 성취나 전체 readiness를 승인한 결과가 아니다. 독립 검토 전 내용 판정은 pending이며, 이번 작업에서 notebook 코드는 실행하지 않았다.

root에서 기존 도구를 읽기 전용으로 재조회할 수 있다.

```sh
python3 -B reviews/week01-deepening-20261111/system-context/verify_context.py --run candidate-ca89-01 --independent-addendum independent-review-addendum-01.json
python3 -B tools/discovery_loop.py report reviews/week01-integration-20261111/discovery/runs/integrated-candidate-01/session.json --root .
python3 -B tools/discovery_loop.py report reviews/week01-pipeline-20261111/discovery/runs/bridge-navigation-01/session.json --root .
python3 -B tools/workflow.py decide reviews/week01/independent-transfer-20261111/workflow.json --quality reviews/week01/independent-transfer-20261111/quality.json --root .
```

verifier의 exit2는 위 변경을 드러내는 실제 결과이며 이를 숨기거나 옛 expected SHA를 고치지 않았다. 이번 쓰기는 이 state 폴더뿐이다. git index는 캡처 전후 SHA가 같고 원격 작업은 수행하지 않았다.
