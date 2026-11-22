# ETB v0.8.0 — AWS 비의존형 Q1 / τ²-bench source-scoped native 검증

## 관측 단위와 주장

대상 원본은 `sierra-research/tau2-bench`의 정확한 커밋 `c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4`이며 Q0 공개 비식별화본 SHA-256은 `6706cfaef1665e685ebadc1f328528c5f2eca618e2d5eaa38cba5c82da476ee4`이다. **비공개 원본 Q0 SHA-256은 `345f4f6673bf31fcec0d50bde87ff970b00d0171da504c383ea02b050a6c10cc`로 따로 고정**되며, 변환 규칙은 `protocol/q0_redaction_v080.json`에 보존되어 있다. 이 연구 패키지는 이미 선택된 Airline Task 8 한 개의 native 환경 초기화 재현성과 reference tool-call replay의 DB 해시 변화를 재검사한다. `get_environment`, `get_tasks`, `set_state`, `make_tool_call`, `get_db_hash`, `get_user_db_hash`는 기존 v0.5.2 소스 네이티브 프로브를 그대로 재사용한다. 이는 새로 구현한 가짜 `SET_EFFECT` API가 아니다.

**Native reference action은 독립된 허가/보안 오라클이 아니다.** native DB 해시 비교는 원본 환경 구현과 같은 코드에 의존한다. 따라서 native benchmark task reward의 재현·과정 인증·실제 외부 시스템의 부수효과 인증과 구분한다. 사용자 LLM 에이전트를 호출하지 않으며 신규 SUT 시도는 0회다.

## 사전 동결

`protocol/freeze_v080.json`: 목표, source commit, Q0 hash, Task 8, 두 정상 대조, 수행 환경, 중단 조건 및 Q1/Q2 차단 판정을 패키지 발행 전에 고정한다. Task 8 선택은 이미 수행된 개발 preflight를 따르므로 새로운 confirmatory sample selection이 아니다. 대안 과제를 실행 결과에 따라 추가하거나 실패를 제외하지 않는다.

## 2계층 검증

**계층 A — source-scoped native:** GitHub runner가 benchmark commit을 확인하고 원본 Python 라이브러리로 Task 8를 실행한다. 결과 바이트, 패키지 설치 현황, Q0/freeze 해시, GitHub 실행 환경 자기보고 및 파일 단위 SHA-256을 업로드한다. 원본 결과에 오류가 있으면 차단하며 경고 없이 자동 재시도하지 않는다.

**계층 B — 외부 GitHub control-plane 조회:** Mac에서 GitHub REST API의 workflow-run과 jobs 문서를 읽기 전용으로 수집한다. 결과에 기록된 repository/run-id/run-attempt/commit/event/workflow path를 외부 조회 값과 대조하며 `ubuntu-24.04` GitHub runner label을 검사한다. `GITHUB_ACTIONS=true` 같은 환경 변수 자체는 증거로 보지 않는다. 보고서의 실행 자체를 GitHub가 독립 관측한 정도로만 인정한다. GitHub API 또한 같은 GitHub 관리·신뢰 영역이며 허위 워크플로·허위 소스와 싸울 수 있는 별도 관리자 신뢰 원천이 아니다.

## 실패조건과 경쟁 설명

- 잘못된 commit/Q0/task 또는 tracked source 변경: 불합격.
- API JSON 필드 누락·변조, run-attempt 차이, public API 미접속, 러너 레이블 불일치, 아티팩트 해시 불일치: 불합격.
- 정상 reference replay에서 native DB가 변했다는 것은 **권한 있는 agent action을 실제로 수행했다는 증거가 아니다.**
- GitHub runner에서 성공하더라도 GitHub 프로젝트의 write/admin 제어 권한을 가진 주체가 워크플로 자체를 수정할 수 있다. `Q1_BLOCKED` 유지.
- 고정 commit에 포함된 `uv.lock`을 `uv sync --frozen`으로 사용하고 원본 lockfile과 `python_packages.txt`를 보존한다. Python 패치/OS/공급망 차이의 전체 동등성은 별도 검증이 필요하다.
- Task 8 한 건만 재현되면 selection/subject heterogeneity가 평가되지 않는다. 확대 연구 전 전체 qualified-task census와 negative controls, 방법론 baseline을 별도 동결한다.

## 외부 검증 단계

source/version=고정 τ²-bench commit, license/사용 조건=upstream 저장소에서 확인 후 기록, provenance=외부 GitHub API + raw artifact, native oracle validity=DB hash 변화만, contamination=기존 Task 8 개발 사용 이력 노출, environment=Mac vs GitHub Ubuntu/Python 3.12, selection attrition=사전 선택 1/1 이외 과제 없음. 결과는 개발 사전검증으로만 보고한다.

## Q1A, Q1B, Q2

- **Q1A:** 원격 별도 관리 주체, 권한 차단, 독립 최신 체크포인트, 외부 상태 효과 오라클. *이 패키지로는 미충족*.
- **Q1B:** 원본 τ²-bench 소스·환경 의미 확인. GitHub에서 원본 Task 8 replay가 확인될 경우 개발 수준의 일부 충족.
- **Q2:** Q1A+Q1B 적격성 및 새로운 분석 freeze 완료 후에만 확증 시도 가능. 이 패키지는 Q2 호출 기능을 제공하지 않는다.
