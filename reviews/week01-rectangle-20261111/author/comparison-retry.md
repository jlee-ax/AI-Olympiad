# 저장 전 비교기 오류와 재시도

387b… 가독성 후보의 HTML 목록 뒤 빈 줄을 보정하며, 빌더는 44셀·21코드 전체 실행을 마쳤다. 그러나 첫 저장 전 비교 스크립트는 노트북 문장 비교에 쓰던 변수 `a`, `b`를 뒤이어 validator 문장 비교에 재사용했다. 따라서 서로 다른 비교 문자열을 사용해 `AssertionError`가 났다. 이는 교안 코드의 실행 오류가 아니라 **작성자 비교기 오류**다.

원본 candidate notebook `387b80845473172d35f9b7a979ca9f3098024b4b5c0c1b3a5df018144e16cba4`, HTML `8879c7d0b668a2f215406808cb1b54404c0590e47d4fadb47a7b55094d17143d`, teacher `de3ac1b2b84a81f9a52abce0e351d29a4cbb92c52db2ad9794eeeec021df65c3`은 비교가 끝나기 전에 교체하지 않았고 재시도 직전에 SHA를 다시 확인했다. 당시 author의 빌더와 validator는 빈 줄 보정을 위해 이미 갱신되어 있었다. 그 직전 도구는 `build_readability.py`, `validate_readability.py`에 보존했다.

재시도에서는 `old_fragment`, `new_fragment`를 별도로 정의해 위부터 다시 실행하고 비교했다. Markdown 한 셀의 빈 줄만 바뀌고 모든 코드·저장 출력이 같은 것을 확인한 뒤 중간 notebook `4a78610d39b6aa334566aabba689a61a7ecb9404ac2a1728044033ee68d13d2a`, HTML `af6082fc6262822d07c9c92a42f2b43696cb0f76a795d41ad9915a29c6a6a511`을 저장했다. 이후 부모 요청에 따라 공식 비율 환산 설명을 더하고 다시 실행해 최종 201e… 후보를 만들었다. 이 비교기 실패는 교안 실패나 독립 검토 결과로 세지 않는다.
