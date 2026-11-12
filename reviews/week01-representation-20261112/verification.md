# 1주차 자료 표현·경로 보완 검증

## 범위와 우선순위

기준은 승인됐으나 원격 lesson 브랜치에 아직 연결되지 않은 이전 후보의 재구성 커밋 `eb154346cfbc2f182f51a17e8b84a319f972dafb`이다. 이전 작업 공간은 없었고 GitHub에 남아 있던 파일 객체 12개를 개별 Git blob 해시로 확인해 새 체크아웃에 구성했다. 그 결과 트리 `c9efac48c38fbf7bd19470afb785366accc47dd9`는 이전 기록과 같지만 과거 작업 공간 전체를 복원한 것은 아니다. 사용자의 1주 본문·교사용, 2주차, 10주 계획 및 삭제된 README는 바꾸지 않았다.

[KOAI 2027 공지](https://kitpa.org/koai/2027)는 중등부도 필기와 코딩을 안내하고, 연결된 [출제 기준](https://kitpa.org/koai/syllabus)은 확인 당시 IOAI 2026 기준이다. [IOAI 2025 Antique](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb)의 특성·미상 라벨·제출과 [IOAI 2026 Robot Chasing](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/2_Robot_Chasing/statement.md)의 범주·축·ID를 선수 능력 비교에 사용했다. 두 국제 개인전 과제는 국내 중등 기출이 아니다.

기존 독립 기기 문제의 panel 열은 실제로 `(5,)` object Series이며 각 칸은 `(2,2,2)` 배열이다. 열 전체를 3차원 배열처럼 `[:, :, 0]`으로 접근하면 오류가 난다. 앞 완성 예제는 사전에서 배열을 찾으므로 명시되지 않은 자료 표현 전환이 있다. 기존 화분 예에서 ID와 관찰을 표에 연결해 열·한 칸의 shape와 각 복사 경계를 보여 주되 기기 특성·모델과 학생 답안은 제공하지 않았다. 예제의 기존 고정 순서 단언도 ID별 비교로 고쳐 재정렬된 표를 사용할 수 있게 했다. 이는 특정 학생이 실패했다는 뜻은 아니다. [pandas Series](https://pandas.pydata.org/docs/reference/api/pandas.Series.html), [loc](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.loc.html), [iloc](https://pandas.pydata.org/docs/reference/api/pandas.Series.iloc.html) 원문과 대조했다.

과거 89셀 기준 교사용 경로표는 현재 96셀 본문의 과제 C/D/E를 잘못 가리켰다. 통합 교사용 표를 현행 제목·셀 ID와 기대 산출물 중심으로 바꿨다. 통합 8절에는 기존 필수 활동의 완료/미완료, 답안 위치, 도움과 다음 할 일을 기록하는 표를 추가했다. 별도 메모도 허용하며 기록만으로 숙달을 판정하지 않고 고정 시간이나 새 문제를 추가하지 않았다.

## 실제 검증

- 최종 통합 노트북 SHA-256 `527848e74da7b6c004c845d4dbe240ac54e2be46087d8e4cf3e597042b5ff181`, 통합 교사용 `f69e6a74f7a4f1dd56400dbfdb92d0b34753238908b0c46c319ea944e8d89084`, 로컬 HTML `4ab46a7834892af8b295cc627cf03be4779fdb5cbe91afc408d657a84d4f4f42`다.
- 기존 후보의 기기 검사와 기록 결과를 재실행해 일치시켰다. 최종 후보에서는 [독립 재현 코드](audit.py)를 두 차례 실행해 정상·재정렬·비연속/중복 인덱스의 ID 대응, P02 누락·중복 오류, 표와 사본의 배열 변이 격리를 확인했다. 기존 학생 답안과 기기 입력, 사용자 본문·2주차는 보존됐다. [검사 결과](audit-final.json), [독립 검토](review.md).
- 최종 통합 노트북과 기존 본문·교량을 별도 in-process 커널에서 전체 실행해 코드 셀 22·31·16개가 오류 없이 통과했다. 통합→본문 준비→통합→교량→통합의 별도 커널 경로도 실행했다. 학생의 빈 답안이나 학습 성과를 검증한 것은 아니다. 코드 output이 원본 노트북의 바뀐 셀에 정확히 저장됐고 HTML의 기록 표 12행, 네 상대 링크, 한글 그래프 PNG를 확인했다. HTML 전체 브라우저 시각 검사는 수행하지 않았다.
- 기존 시스템 회귀 271개는 동일한 이전 후보 트리에서 앞선 환경에 통과한 기록이다. 이번 새 교안 변경에 대해 그 271개를 다시 실행한 것으로 주장하지 않는다. 일반 소켓 Jupyter는 앞선 기동 시 환경 권한 오류가 있었고, 이번에는 in-process 방식으로 실행했다. 실제 학생의 시간·도움·성취는 미관찰이다.

## 뒤에 남긴 반례

[검토자 재현 코드](open_gaps.py)와 [결과](open-gaps.json)는 학생용 정답이나 자동 채점기가 아니다. 검증 V7의 signal만 사본에서 결측으로 바꾸면 훈련 대체 평균 4와 검증에서 잘못 다시 구한 5.5가 다르다. 최근접 중심 예측은 달라지지만 결정트리는 같아, 예측만 같다는 사실이 전처리 계약 준수를 뜻하지 않는다. 2주 본문은 훈련 전용 대체와 검증 결측을 이미 다루므로 이번 1주에 중복 필수 문제로 더하지 않았다.

훈련 표를 T5부터 재정렬하면 앞 네 행만 쓰는 잘못된 선택은 미상 라벨을 포함하고 평균 34⅓을 얻지만 알려진 라벨만 선택하면 평균은 4다. 또 장소의 결측이 미상이라는 합성 계약에서는 양쪽 결측 키가 `many_to_one`과 행 수 검사를 통과하면서 pandas에서 서로 매칭된다. 결측 키의 취급은 과제 계약에 따라 판단해야 하며 무조건 모든 데이터에서 금지된다는 뜻은 아니다. [pandas merge 문서](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html). 이 둘은 기존 학생 과제를 완수했다는 증거가 아니며 후속 평가 설계 후보로 남긴다.

두 변수의 관계와 각 분포를 한 그림에서 함께 읽는 내용도 [고등부 공개 예시](https://kitpa.org/files/36) 및 [Seaborn jointplot](https://seaborn.pydata.org/generated/seaborn.jointplot.html)과 대조했다. 현재 1주 필수 분량을 고려해 이번에 새 문항을 추가하지 않았다. 기존 본문 교사용의 검증 파일 동봉 여부 불일치와 실제 전체 분량 검증도 남는다.
