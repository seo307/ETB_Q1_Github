# 학술적 판정 — ETB v0.8.0

1. **Novelty — 아직 미입증:** GitHub CI, 원본 benchmark replay, 해시 바인딩은 자체 방법론적 기여가 아니다. 유망한 메커니즘 가설은 ancestry-aware certificate의 필요한 독립 witness 집합을 판정하는 규칙이 동일 인프라에서 강한 기준선 대비 잘못된 인증을 제거할 수 있는가이다. 현재 데이터에는 그 인과 비교가 없다.
2. **Relevance — 높음(연구 문제):** tool-using agent의 상태 변화 주장과 실제 부수효과를 분리하는 문제는 중요하다. 운영 효과·보안 개선은 아직 추정.
3. **Soundness — Critical 미해결:** 별도 관리 root / 독립적인 effect oracle / 네이티브 SUT 결과가 없다. Task 8 골드 실행은 같은 oracle을 재실행하는 자기 일치 시험이다. GitHub Actions 변경 권한은 이 원천을 지배할 수 있다.
4. **Presentation — 개발/외부실행/Q1/Q2 상태 구분:** GitHub-hosted 실행 corroboration은 실제 root independence를 뜻하지 않으며, 파일별 hash는 의미적 진실성 증명이 아니다.
5. **Verifiability — 제한적 양호:** 원본 Q0, prior v0.7.2, freeze, 복원 가능한 코드를 제공하며 실행 결과의 SHA 및 외부 API 기록을 분리했다. 완전 환경잠금과 실험적 외부 복제는 아직 없다.

**반증 가설:** 같은 관리 권한이 모든 증거와 GitHub 워크플로를 통제하면 서명/해시가 유효한 거짓 증거를 만들 수 있다. native DB final hash가 같아도 무단 도달 경로를 배제할 수 없다. ETB 메커니즘은 이 반례에서 독립 process certification을 내면 안 된다. 런타임 제한, 버전별 이질성, agent/harness/tool 변경에 따른 결과 변화는 Q2의 별도 평가 대상이다.

본 패키지에서 `GITHUB_HOSTED_NATIVE_PREFLIGHT_CORROBORATED`는 실행 출처의 일관성 판정이지 `Q1_PASS` 또는 완성된 외부 validation 판정이 아니다.
