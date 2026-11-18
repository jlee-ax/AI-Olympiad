# 공개 반납 자료의 병합과 집계 재검산

1회차 학생 예제와 교사용 풀이에서는 양쪽의 반납함 이름이 비었을 때도 구역이 붙었다. 같은 입력으로 2회차를 실행하면 학생 예제가 집계 전에 멈추고, 교사용 함수는 구역을 연결하지 못한 기록 `T1`을 알린다. [1회차 판정](../rounds/0001/reviews/functional.json) · [2회차 판정](../rounds/0002/reviews/functional.json)

|보관 회차|학생 노트북 SHA-256 앞 12자|교사용 해설 SHA-256 앞 12자|공개 대조 결과|
|---|---|---|---|
|1|d4689c347113|b81abef89ebd|13개 중 11개 통과. 학생용 `R2`와 교사용 `T1`에 근거 없이 East가 붙었다.|
|2|1487703f78c5|3586f486052f|13개 모두 통과. 두 예제 모두 빈 키를 알려진 반납함으로 취급하지 않았다.|
|3|ef1586ee0eef|c1a0e2c14b05|13개 모두 다시 통과. 교사용 함수는 두 가지 다른 빈 키 표현에서도 문제 기록을 찾아냈다.|

검산 코드는 각 회차 노트북의 `real-merge` 셀과 해설에 실린 `attach_zones`, `summarize_returns` 함수를 직접 실행한다. 원본 CSV의 구역 대응, 구역표를 뒤집은 결과, 점심 기준 4권과 6권의 선택·집계, 특정 구역의 하교 관측이 모두 사라진 경우, 선택 결과가 빈 경우를 확인한다. 열 누락, 중복 키, 모르는 키, 한쪽과 양쪽의 빈 키를 만든 입력도 함께 실행한다. [재현 코드](check_public_tables.py)

세 회차에서 정상 입력의 West 하교 평균은 기준 4권에서 13/3권, 기준 6권에서 3권이다. East의 한 건은 하교에 관측한 0권으로 남는다. 반면 하교 관측이 모두 빠진 구역은 관측 수가 0이고 합과 평균을 구할 수 없다. 각 대조의 기대값·실제값, 실행 버전, 노트북과 자료의 전체 해시는 결과 파일에 있다. [1회차 결과](round-0001.json) · [2회차 결과](round-0002.json) · [3회차 결과](round-0003.json)

저장소 루트에서 Python 3.12와 pandas 2.2.3 환경으로 실행한다. 1회차 명령은 원래의 두 실패를 재현하여 종료 코드 1을 반환한다. 2회차와 3회차 명령의 종료 코드는 0이다.

```console
python3 -B reviews/week01-depth-20261118/functional/check_public_tables.py --root . --round 1
python3 -B reviews/week01-depth-20261118/functional/check_public_tables.py --root . --round 2
python3 -B reviews/week01-depth-20261118/functional/check_public_tables.py --root . --round 3
```

3회차의 추가 두 대조에서는 전체 키 열이 빈 실제 CSV와 표에 직접 쓴 빈 문자열을 확인했다. 2회차의 원래 판정과 뒤의 추가 판정을 모두 보관했다. [추가 비교](missing-key-forms.ko.md) · [뒤늦게 기록한 2회차 판정](../rounds/0002/reviews/late-integration.json) · [3회차 판정](../rounds/0003/reviews/functional.json)
