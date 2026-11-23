# Q1B v0.8.1 — 과학적 품질·주장 제한

## Novelty (미입증)
원본 native DB oracle 자체는 새로운 보증 방법이 아니다. ETB의 잠재적 기여는 **결과 상태 일치와 실행 과정 증거 신뢰도**를 분리해 인증 여부를 판단하는 메커니즘에 있다. 여기에서는 원본의 native evaluator가 어디까지 주장할 수 있는지 경계만 시험한다. lineage-aware ETB가 오류율을 줄였다는 성능 주장은 아직 시험하지 않았다.

## Relevance (높음, 실증 영향은 미확인)
도구 사용 에이전트의 최종 상태 해시가 정책/실행 경로의 보증을 의미하지 않는다는 운영상 혼동을 구분하는 데 유용하다. 개선된 안전성·보증 효과는 향후 동일 환경에서 비교해야 한다.

## Soundness (Q1 기준 Critical)
Task 8 한 사례, 저자 작성 통제, 원본 환경의 DB로 만든 구조적 체크, 사용자/모델/정책 보증 부재, `strict=False`의 의도된 사용 경계가 핵심 제한이다. 위조 ToolMessage를 재생하더라도 환경에서 적용하는 실제 함수는 native 함수이므로 이는 외부 공격이 아니라 **원본 평가 메커니즘의 관측 변수 차이를 설명하는 반례**다. native DB 일치와 response fidelity를 혼동해서는 안 된다.

## Presentation
문제 → 원본 oracle 정의 → 동일 task 정상·부정 통제 → DB component 결과 → 인증 가능/불가능한 주장 → 독립 root 미충족 순으로 보고한다. `DB reward`와 `full-task reward`를 혼합하지 않는다.

## Verifiability
반복 가능한 소스 pin, task ID, 요구 Python/uv.lock, 공개 run artifact의 내부 해시, GH workflow run/job API 대조, 구조적 체크와 negative 케이스, 파일 manifest를 포함한다. 원본 증거 바이트는 변경하지 않는다. 다만 개발 시나리오가 원본 오라클과 같은 구현에 의존하므로 독립 의미 판정은 입증하지 못한다.

## 연구 게이트
Q0 (source pin): PASS; v0.8.0 external reference preflight: PASS; v0.8.1 code release: separate; Q1B external semantic replay: **not yet executed** at packaging; independent administrative/semantic root Q1A: BLOCKED; Q2: NOT STARTED.
