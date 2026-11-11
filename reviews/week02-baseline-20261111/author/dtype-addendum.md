# dtype 설명 추가 — 최종 보충 판본 기록 (교사용)

기존 [README](README.md)의 보충 SHA와 [artifact-audit.json](artifact-audit.json)은 dtype 문장 추가 **이전** 후보의 기록입니다. 이전 결과를 고쳐 쓰거나 새 판본의 검사로 제시하지 않습니다. 이 추가 기록은 아래 두 최종 산출물에 결합됩니다.

| 파일 (`lessons/week02/`) | 최종 SHA-256 | 이전 후보 SHA-256 |
|---|---|---|
| `week02_temporal_preprocessing.ipynb` | `c35d1977f79e102b933e86ee8dc547924e4054001ab04ad8609b7ffdf14ce5d1` | `549cd18bfad99a720587b65b80a4de0b2402435cbdc95a0a5619e779f80f94e0` |
| `week02_temporal_preprocessing.html` | `f1ad6f978d04844c9e9849c9a8b7cc64a9eeb24b46bf6ad96371075d6bb81475` | `5695b6c2adfd12dce7cf349a1ff9f0d448178b7b8c3c0ffb1507c9e94932c520` |

## 변경과 새 실행

보충의 worked 설명 셀 `98d2cf0f`에 문자 B/T와 숫자 0을 NumPy 배열에 섞을 때의 변환 및 `dtype=object`/원래 목록 사용을 설명하는 문장 하나를 추가했습니다. 이전 [실행본](executed-temporal-v4.ipynb)과 비교하여 그 문장 외 모든 셀의 ID·종류·소스가 같고 모든 셀의 저장 출력·실행 횟수가 같음을 확인했습니다. 실행 코드는 변경하지 않았습니다.

NumPy 2.5.4에서 `np.array(['B','T',0])`의 dtype은 `<U21`이었고 0은 문자열 `'0'`으로 바뀌었습니다. 같은 데이터에 `dtype=object`를 지정하거나 원래 목록을 유지하면 0은 정수로 남았습니다. 실제 학생의 `fit_known_mode`에 B/B/T/0을 전달한 추가 검사에서 기본 혼합 배열은 문자열 `'0'`으로 인해 `ValueError`로 중단했고, object 배열과 목록은 각각 B를 선택하고 known 마스크 `[True, True, True, False]`를 반환했습니다. 문자열을 숫자로 임의 변환하지 않는다는 설명과 일치합니다.

문장 추가 후보를 별도 fresh in-process kernel에서 실행하여 예제 코드 셀 9개가 오류 없이 끝났고, 각 셀의 stdout이 저장된 출력과 일치했습니다. 독립 답안 셀은 비어 있고 출력 없이 미실행입니다. 결과 노트북을 HTMLExporter로 내보낸 내용은 최종 HTML과 정확히 일치했습니다. 이 실행 결과는 도구 실행 출력으로 확인했으며 별도 raw 로그 파일을 생성하지 않았습니다.

로컬 네트워크 인터페이스 탐색에서 `Operation not permitted` 경고가 발생했으나 in-process 실행은 끝났습니다. 일반 소켓·브라우저 권한을 우회하지 않았고 HTML 또는 MathJax의 시각 렌더링은 확인하지 않았습니다. 이전 검사들이 이 새 SHA 자체를 자동 재검사했다고 주장하지 않으며, 실제 학생의 성취와 소요시간도 관찰하지 못했습니다. 이 문서와 README 판본 표시 외 교안·교사용 해설·1주 파일은 변경하지 않았습니다.
