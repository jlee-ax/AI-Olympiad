# 2주차 학생 계획 연결과 평가 원칙 개정

학생 계획 HTML의 변경 영역은 기존 공통 평가 원칙과 2·4·8주 행이다. 1주 행, 교안, 사용자 작업과 기존 1주 검토 이력은 수정하지 않는다. 계약·미설정 템플릿의 pin, README의 계획 안내, 2주 교사용 해설을 함께 정정했다. 합성 시연은 기존 품질·워크플로 검토를 보존하고 현재 맥락의 합성 기록을 추가했다. 이전 계획·계약·템플릿·예시와 교사용 해설 바이트는 `plan-revision/`에 보존했다.

- 이전 계획 SHA-256: `cbe69f862ae76a87cd69233889c7fd6698e38ac34eb4d385f2b825722daeabb5`. 현재 계획 SHA-256: `c60063bf1c55b957f4b6271a0796d5301d9f209de28a91d468c0c20e72fa0133`. 계약의 supersedes는 직전 판본을 가리키며 그 이전 체인도 스냅샷에 남는다. 새 pin은 바이트와 구조를 잇는 것으로, 과거 검토의 재승인이 아니다.
- 평가 상황에 따른 새 개체와 알려진 개체의 별도 기록을 구분한다. 평가 사례의 복제·증강 누수는 금지하고, 예측 때 허용된 과거 문맥과 훈련 fit을 구분한다. 2·4주 공통 자료의 새 개체 분리와 4주 최종 선택까지 테스트 보류를 유지한다.
- 2주 본문·필수 보충 노트북의 GitHub 링크를 추가했다. 공개 GitHub 브라우저에서 이전 브랜치 HEAD `190eecaa4154a4ba7a641c9603b44ef5ddf9d148`의 본문 → 보충 → 본문 이동과 렌더링을 확인했다. GitHub 미리보기는 읽기 화면이다. 이 확인은 HTML 실행 화면이나 Colab 편집·실행을 뜻하지 않는다.
- 2주 6~8시간은 기존 편성 추정이며 현재 두 노트북에 대한 학생의 실제 소요 시간·도움·성취는 미관찰이다. 독립 최종 테스트 자료와 정답은 아직 없다. 공개 교사용 해설은 접근 통제가 아니므로 독립 평가의 보호는 별도로 마련해야 한다.
- 이전 공개 1주 품질 묶음의 최신 evaluator 조회에서 활성 20건은 `binding_required` 16건, `review_required` 1건, `current` 3건이었다. 이들은 이번 변경 전에 관찰된 상태다. 기존 3개 current는 1주 notebook의 table·array·visualise 주장 셀과 관련 원문에 결합된 K06 검토로 계획 영역을 의존성에 선언하지 않았다. 계획의 `#plan-context`에 실제 결합된 다른 검토는 변경 영향의 후속 확인이 필요하다. 기존 기록을 수정하거나 일괄 현행 승인으로 바꾸지 않는다.
- 진행 중인 별도 1주 worktree는 더 오래된 HEAD의 별도 파일을 사용하고 그 파일은 이 변경으로 자동 변경되지 않는다. 기존 미커밋 파일과 이전 HEAD에서 이 작업 이전 공개 트리까지의 변경 경로 사이에는 확인 시 교집합이 없었다. 이후 동시 편집 또는 통합 결과를 보증하지 않는다.


기존부터 `skills/references/quality-specification.md`는 현재 계획을 가리키며 과거 SHA `96deb5e5e781bf39cc6bb5effe34d6d04a01ac65e13a3811c37f5a825714f7a9`를 적고 있다. 해당 바이트는 `lessons/week01/provenance/student-plan.html`에 보존된 과거 판본이다. 이 파일은 1주 역사 자료에 결합돼 있어 이번에는 변경하지 않았고 현행 설명 정정은 열린 항목으로 남긴다.


독립 검토에서 첫 후보는 같은 원본의 복제·파생본이 훈련에 들어가는 경우만 막아 검증과 최종 테스트 사이의 중복을 남긴다는 결함을 발견했다. 첫 후보는 `plan-revision/student-plan-candidate-01.html`(SHA-256 `b631e5a13e51e5db2e54f6da069c3a3af89a47dd530f0bf227904da91fae0d57`)로 보존했다. 현재 문구는 같은 예측 대상 사례의 복제·증강·파생본이 훈련·검증·테스트의 어느 서로 다른 분할도 넘지 않도록 고쳤고, 허용된 과거 문맥은 해당 예측 대상의 복제나 정답과 구별한다.


두 번째 독립 검토는 8주 자습의 기존 생성 틀별 분리 요구가 첫 교정에서 조건부로 완화된 점을 발견했다. 둘째 후보는 `plan-revision/student-plan-candidate-02.html`(SHA-256 `c0815a1de9d81556ca8135c6e6126bb4fefd28338098e72a650419d653875103`)로 보존했다. 현재 8주 자습은 새 생성 틀 평가를 목적으로 기존 문장·생성 틀별 분리 활동을 유지하며, 다른 과제에는 그 명세를 따른다.

## 검증과 제한

- `python3 -B tools/quality.py baseline`은 새 계획 SHA와 10개 120분 수업·60개 예정 항목에 대해 통과했다. 새 계획에 옛 계약 pin을 메모리로 적용하면 바이트 불일치로 실패하고, 새 pin은 통과했다. 미설정 템플릿의 K01은 통과하되 전체 평가는 `uncertain`이며 합의를 만들어 내지 않는다.
- 원본 HEAD와 보존한 계획·계약·템플릿·2주 해설·두 합성 예시를 원바이트 비교했다. 실제 계획에서 바뀐 영역은 `#plan-context`, `#week-2`, `#week-4`, `#week-8`이며 `#week-1` 행은 원바이트 동일하다. 주차 시간, 60개 항목, 이론·실전 플래그는 바뀌지 않았다.
- 공통 맥락 변경 후 옛 합성 예시의 6개 활성 검토 중 5개는 `review_required`, 1개는 `current`였다. 최초 `test_quality.py`는 43건 중 해당 시연 검사 1건이 실패했다. 독립적으로 확인한 범위의 새 합성 기록 5건을 추가한 뒤 옛 12건은 보존됐고 6개 활성 합성 검토가 현재가 됐다. 별도의 [합성 범위 확인](synthetic-context-review.md)은 실제 학생·교사·1주 교안 승인이 아니다.
- 옛 합성 workflow와 새 품질 묶음은 `quality_context_not_bound`, 묶음 pin만 갱신하고 옛 workflow 검토를 유지한 상태는 `stale_verification`으로 차단됐다. 기존 workflow 검토 3건을 보존하고 새 합성 검토를 추가한 뒤 `continue`가 됐다. 현재 공통 맥락을 다시 바꾸는 가상 반례에서 합성 검토 5개가 `review_required`, 무관한 3주 행의 가상 변경에서는 6개가 `current`였다.
- 최종 계획과 합성 예시에 대해 관련 묶음 164건과 전체 `python3 -B -m unittest discover -s tests -q` 271건을 실행해 통과했다(전체 89.430초). 전체 검사는 README의 HTML 다운로드 안내 문장과 이 결과 기록을 추가하기 직전에 실행했다. 이 검사는 코드·구조·합성 자료의 회귀 결과이며 실제 학생 소요 시간이나 성취의 근거가 아니다.
- [KOAI 2027 안내](https://kitpa.org/koai/2027)와 [국내 출제 기준](https://kitpa.org/koai/syllabus)은 중등 목표와 IOAI 2026 표기를 확인하는 근거다. [IOAI 2026 Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/2_Robot_Chasing/statement.md), [IOAI 2025 Antique](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb), [IOAI 2026 Ghost of the Machine](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/main/Individual-Contest/5_Ghost_of_Machine/statement.md)은 별도의 국제 과제다. [scikit-learn의 그룹·시계열 교차검증](https://scikit-learn.org/stable/modules/cross_validation.html)은 일반화 목표에 맞는 분할의 근거다.
- 계획의 GitHub HTML 파일 페이지는 소스 보기다. README에 HTML 파일을 내려받아 브라우저에서 열라는 사용 안내를 추가했으나, 실제 다운로드·로컬 브라우저 렌더링은 이번에 확인하지 않았다. 기존 공개 브랜치의 두 노트북 페이지와 양방향 이동은 브라우저로 확인했고, 새 계획 링크가 가리키는 저장소 파일도 로컬에서 존재를 확인했다. 이후 공개된 새 계획에서의 전체 경로 검증은 별도로 필요하다.
- README의 안내 문장 추가 후 `test_graph_paths.py` 42건과 변경된 추적 파일의 `git diff --check`를 다시 실행해 통과했다.

[별도 독립 검토](independent-review.md)는 최종 대상 SHA와 확인 범위·미검증 항목을 기록한다.
