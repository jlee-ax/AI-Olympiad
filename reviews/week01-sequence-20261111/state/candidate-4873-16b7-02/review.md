# 설명 보강 후보 freshness 재조회

통합본 `487379bf0c9c5fae5877d1eb5ec1414dedabbe2f2634a3827ae224f6e31bc568`와 bridge `16b797de3935af5e25d6e297cdd8b4c72d7dbb32667ab36b9fb9df36965cd84d`의 시작·종료 SHA가 전달값과 일치했다. 이 기록은 바이트 결합과 기존 상태의 조회이며 교육적 충족이나 기능 정확성 판정이 아니다.

| 조회 대상 | 실제 결과 |
|---|---|
| 직전 f3f7… 관측 | 통합본 바이트는 같고 bridge 바이트는 달라 직전 관측의 bridge 결합이 stale이다. 직전 관측·검증 및 기존 보고서는 그대로 보존했다. |
| 이전 retrieval 독립 검토 | b530…/de5… notebook·HTML·teacher에 대한 6개 SHA 중 현재 일치는 0개다. 기존 검토의 역사적 판단을 변경하지 않았으며 새 후보에 이전하지 않는다. |
| 원래 통합 discovery | bound 15ab… / current 4873…에서 `artifact_changed`, `needs_work`, `ready_for_review=false`. 기존 19요구·8질문·큐17이 그대로다. |
| 원래 bridge discovery | bound 09efa… / current 16b797…에서 `artifact_changed`, `needs_work`, `ready_for_review=false`. 기존 3요구·3질문·큐3이 그대로다. |
| 옛 ee827 workflow | `pause/criteria_agreement_required` 유지. 이 workflow는 새 후보의 승인 상태가 아니다. |

`freshness-observation.json`에 실행 명령·exit·원출력 SHA·기존 기록 전후 SHA를 보존했다. 실제 세 CLI stdout은 각 `*.stdout.json.gz`에서 원바이트로 복원할 수 있다. `previous-observation-recheck.json`은 직전 f3f7… 기록의 전후 SHA와 새 후보의 바이트 대조다. `saved-evidence-verification.json`은 저장 원출력·현재 바이트·이전 기록의 재검증이다. CLI exit 0은 조회 성공이며 교안 통과를 뜻하지 않는다.

이번 조회 동안 기존 기록 15개와 git index는 불변이었고, 직전 관측 폴더와 기존 collector·보고서 8개도 불변이었다. 새 쓰기는 이 별도 state run 아래에만 했다. 새 quality/graph 승인·discovery session을 만들지 않았고, 독립 내용 검토 결과를 판정하거나 이전 covered/승인을 계승하지 않았다. 원격 작업도 수행하지 않았다.

재현은 저장한 실제 CLI 명령으로 읽기 전용 실행할 수 있다.

```sh
python3 -B tools/discovery_loop.py report reviews/week01-integration-20261111/discovery/runs/integrated-candidate-01/session.json --root .
python3 -B tools/discovery_loop.py report reviews/week01-pipeline-20261111/discovery/runs/bridge-navigation-01/session.json --root .
python3 -B tools/workflow.py decide reviews/week01/independent-transfer-20261111/workflow.json --quality reviews/week01/independent-transfer-20261111/quality.json --root .
```

이 관측 이후 후보가 바뀌면 기존 기록을 보존하고 새 이름으로 재조회해야 한다.
