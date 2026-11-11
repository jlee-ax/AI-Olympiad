# Week 1 source brief — 2026-11-11

- [KOAI 2027 안내, 2단계 문제 구성](https://kitpa.org/koai/2027): 고등부와 중등부 모두 1~4과목 전 범위에서 선택형·서술형과 코드작성형 시험을 본다고 설명한다. 특정 주차의 개별 과제나 1주차 완성 난도를 지정하지는 않는다.
- [연결된 KOAI/IOAI 출제 기준](https://kitpa.org/koai/syllabus): 확인 당시 제목이 **IOAI 2026 기준**이다. 1-1은 Python, NumPy/Pandas, 시각화, 텐서 조작을 실전 범위로 나열하고, 1-4는 통계적 모멘트와 전처리를 나열한다. 1주차 과제는 이 범위의 기초에 한정되며 학습자의 숙달을 뜻하지 않는다.
- [2026 예시문항 공지](https://kitpa.org/files/36)와 [원본 PDF](https://kitpa.org/storage/c4016751-0e2c-4548-ab70-ecec994e8f8d.pdf): 학습 참고용 고등부 기준 예시이고 정답 전체를 공개하지 않았다. 예시 선택형 2는 배열 shape·축 연산·reshape의 메모리 주장, 6은 PyTorch 다차원 축 교환, 서술형 2는 NumPy KNN 예측의 입력·출력·다수결 계약을 제시한다. 이들은 관찰 가능한 요구의 예이며 2027 중등부 기출·난도 분포나 1주차 완료 기준이 아니다.
- 같은 예시 PDF의 선택형 1은 Python 함수 호출과 상태에 따른 출력을, 선택형 3은 두 연속 변수의 분포와 관계를 함께 보는 시각화 선택을 묻는다. 새 traceback·좌표 구성은 각각 관련 기초이며 해당 문제의 동일한 요구나 완전한 대체가 아니다.
- [Python 내장 예외](https://docs.python.org/3/library/exceptions.html#IndexError): 범위 밖 인덱스의 오류 구분. 교안의 비어 있지 않은 목록 계약에서 수정 후 결과는 별도 실행했다.
- [NumPy broadcasting 규칙](https://numpy.org/doc/stable/user/basics.broadcasting.html): 뒤쪽 차원부터 크기가 같거나 한쪽이 1인지 비교한다. 실제 (2,3), (3,), (2,1), (2,) 반례는 별도 실행했다.
- [NumPy variance](https://numpy.org/doc/stable/reference/generated/numpy.var.html): 분산의 분모·ddof가 계산 정의에 영향을 준다. 이 과제는 명시적으로 분모 n인 분산을 쓴다.
- [pandas DataFrame.merge](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html): left join과 `validate="many_to_one"`의 범위를 대조했다. 없는 키·중복 키의 실제 행 수와 오류는 새 CSV의 복사본으로 실행해 확인했다.

## 공식 요구와 1주차 목표의 구분

| 경로 | 공식 예시에서 직접 확인한 요구 | 1주차 목표와의 관계 |
|---|---|---|
| traceback | 2026 선택형 1: Python 함수 호출에서 상태와 출력을 판별 | 범위 밖 인덱스 traceback 수정은 코드 상태를 읽는 **별도 기초 목표**다. 해당 예시가 traceback을 요구하지는 않는다. |
| chart | 2026 선택형 3: 두 연속 변수의 관계와 분포를 함께 보여 줄 시각화 선택 | 표의 좌표 구성과 이동은 표현 해석의 **기초**다. 시각화 도구 선택이나 낯선 그래프 판독과 같지 않다. |
| broadcast | 2026 선택형 2: 배열 shape·축별 합과 reshape의 메모리 주장. 서술형 2: KNN 거리 계산에서 broadcasting 활용을 권장 | shape에 맞는 보정과 오류는 **관련 기초**다. 메모리 공유 판단, PyTorch 축 교환이나 KNN 전체 구현을 대체하지 않는다. |
| variance | 2026 선택형 24: 제시된 항목 중 피처 엔지니어링 기법을 판별 | 분산·단위·배율은 통계적 모멘트의 **관련 기초**다. 기법 분류 문제와 동일하지 않다. |
| merge | 2026 서술형 2: NumPy KNN의 입력·출력과 다수결 계약 | 결측/키 검사는 자료 준비의 **별도 기초**라는 교육적 추론이다. 해당 예시는 join을 요구하지 않는다. |

추가된 문자열 단위·결측 높이 과제는 syllabus 1-1의 Pandas 활용과 1-4의 결측·불규칙 자료 전처리를 위한 기초다. 내적 순서 과제는 1-1의 NumPy 활용을 위한 기초다. 세 과제의 구체적 입력이나 문항 형태를 공식 기준이 직접 요구한다고 해석하지 않는다. 결측 높이에는 집계 예시가 제공되며 세 과제는 위 다섯 개의 문제별 그래프 비교 목표 범위 밖에서 별도로 검토했다. 결측 높이 문항은 merge 경로의 문항과 같은 셀을 공유한다.

모든 웹 자료는 2026-11-11에 원문을 다시 확인했다. URL은 살아 있는 자료이므로 향후 바뀔 수 있다. 교안의 새 문제는 자체 작성했으며 예시문제를 복제하지 않았다. 학습자 응답, 교육자 보정과 실제 수업 시간은 아직 없다.
