# AI 올림피아드: 연구 및 설계 기초

상태: **논의용 초안**. KOAI 2027 준비를 위한 중학생 대상 수업(기초 코딩 경험, 10주 × 2시간)을 추후 설계하기 위한 근거와 작업 구조다. 1–2주차 수업 자료 제작, 반복 작업 실행 및 자동 일정 등록은 아직 승인된 단계가 아니다. 대회 범위와 대상 수준은 공식 공지와 사용자와의 논의를 통해 확인한다.

## 시작하기

1. [논의 및 결정 항목](docs/decisions.md)을 읽는다.
2. [설계와 반복 절차](docs/design.md), [근거 목록](docs/evidence.md)을 살펴본다.
3. [스킬 계약](skills/README.md), [작업 기록 양식](templates/run.json), [검증 양식](templates/review.json)을 활용한다.
4. 예시 데이터는 가상의 예시이며 실제 학습자 정보, 요청이나 완료된 업무를 나타내지 않는다.

```sh
python3 -m unittest discover -s tests -v
python3 tools/validate.py examples/graph.json
```

기계 검증은 참조와 구조의 일부만 확인하며 학술적 타당성, 정확성, 교육 효과 또는 안전성을 보장하지 않는다. 논의된 기준을 확정하기 전에는 자동 실행하지 않는다.
