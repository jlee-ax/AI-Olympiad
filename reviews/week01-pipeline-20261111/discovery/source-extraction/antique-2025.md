# 공식 Antique 원문 재독 메모

독립 추출자: /root/discovery_resume/pipeline_source_extract
URL: https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb
직접 읽은 범위: raw web L19–72, L118–158, L176–210 (2026-11-11 UTC)
판본: IOAI2025 개인전 공식 저장소 main, upstream 고정 commit은 확인하지 않음.

표의 앞 다섯 열은 특성이고 여섯째 열은 +1/-1/0 라벨이다. 미상 포함 자료에서 모형을 학습하는 과제이며, 검증·테스트는 대회 중 직접 접근할 수 없다고 설명한다. 기준 코드는 SVC의 fit과 그 모델의 predict를 구별한다. 0을 랜덤 ±1로 대입하는 부분은 기준 휴리스틱으로, 관측 정답이나 정당화된 일반 반지도 방법을 뜻하지 않는다. 알려진 행만 쓰는 작은 지도학습은 전체 과제의 축소 경로다.

출력은 submission.ipynb가 만드는 submission.zip 안의 submissionA.csv와 submissionB.csv다. 각 파일은 입력에 대응하는 ±1 예측을 header 없이 저장하며, 기준 코드도 index를 저장하지 않는다. 지표는 전체 평가 표본 중 맞힌 비율이다. 기준 코드의 Solution 경로는 실제 대회에서 숨은 자료를 자유롭게 읽을 허가를 뜻하지 않는다.

실제 자료·숨은 평가·반지도 성능은 실행하지 않았다. 이 파일은 의역 메모이며 원본 notebook 바이트나 인증 사본이 아니다. 교안은 읽지 않았다.
