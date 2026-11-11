# 시퀀스 후보의 이전 검토 freshness

관측 후보는 통합본 `487379bf0c9c5fae5877d1eb5ec1414dedabbe2f2634a3827ae224f6e31bc568`, bridge `f3f739cf8fdd90a68550e3b1b093bedaeb3fc7ce1a310bcf4303b6feb29de544`다. 조회 시작·종료 시 실제 SHA가 전달값과 일치했다.

`candidate-4873-f3f7-01/freshness-observation.json`에 명령·exit·실제 stdout SHA·전후 기록 SHA와 결과를 보존했다. CLI stdout 전체는 각 *.stdout.json.gz로 저장했고 원바이트 일치를 확인했다. `prior-retrieval-live-binding.json`은 이전 독립 검토의 final_artifact_sha256 선언을 현재 파일과 직접 대조한 결과다. 이 바이트 대조는 독립 의미 검토를 다시 실행한 것이 아니다.

| 대상 | 실제 관측 |
|---|---|
| 이전 retrieval 독립 검토 | b530… 통합본·de5… bridge와 각 HTML/teacher6개에 결합되어 있다. 현재는 **0/6 SHA 일치**로 새 후보에 대한 live 결합이 stale이다. 원래 검토 summary 자체는 변하지 않았다. |
| 이전 retrieval 상태 기록 | 당시 b530…/de5…의 관측은 보존됐으며 현재 두 notebook과 일치하지 않는다. 저장 당시 true를 새 후보의 통과로 사용할 수 없다. |
| 원래 통합 discovery | bound15ab… / actual4873…로 artifact_changed. 기존19요구·8질문·큐17, needs_work/ready=false 유지 |
| 원래 bridge discovery | bound09efa… / actualf3f7…로 artifact_changed. 기존3요구·큐3, needs_work/ready=false 유지 |
| 역사적 ee827 workflow | pause/criteria_agreement_required 유지. 새 후보의 승인 대기를 해제하지 않았다. |

이전 session/report/manifest·retrieval 독립 검토 및 상태·옛 quality/workflow 파일의 전후 SHA는 모두 같고, git index SHA도 같았다. 원격 작업은 수행하지 않았다. 원래 통합 session SHA `9c4ceb26…9145`와 bridge session SHA `75ac4108…51bf`도 그대로다.

이 wrapper의 확인 항목 true는 **요청된 바이트에서 기대된 stale 감지와 이력 보존을 확인했다는 뜻**이다. 새 교안의 의미 충족·기능 정확성·학생 성취나 전체 readiness 판정이 아니다. 이전 covered/승인을 자동 이전하지 않았고, 새 quality/graph 승인·discovery session도 만들지 않았다. 독립 내용 검토 결과는 이 관측에서 판단하지 않는다.

원래 도구의 읽기 전용 재조회 명령은 다음과 같다.

```sh
python3 -B tools/discovery_loop.py report reviews/week01-integration-20261111/discovery/runs/integrated-candidate-01/session.json --root .
python3 -B tools/discovery_loop.py report reviews/week01-pipeline-20261111/discovery/runs/bridge-navigation-01/session.json --root .
python3 -B tools/workflow.py decide reviews/week01/independent-transfer-20261111/workflow.json --quality reviews/week01/independent-transfer-20261111/quality.json --root .
```

이번 쓰기는 `reviews/week01-sequence-20261111/state/`에만 한정했다. 기존 교안·검토 기록·세션·index·원격은 수정하지 않았다. 후보가 바뀌면 이 관측을 보존하고 새 이름의 기록으로 재조회해야 한다.
