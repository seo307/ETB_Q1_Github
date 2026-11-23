# ETB Q1B — Native Semantic Qualification (개발용, v0.8.1)

## 1. 무엇을 확인하는가

- **원본 기준**: Sierra τ²-bench, `c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4`, Airline Task 8. 직전 외부 preflight Run `45085918830`, Artifact ZIP SHA256 `a48f2ac62d2c5ac286fe77f533b33f840d1206be1afea2ef0b483f99b0006081`.
- **원본 평가 의미**: `tau2.evaluator.evaluator_env.EnvironmentEvaluator`는 gold actions를 새 환경에 재생하여 얻은 최종 DB를, 관측된 trajectory를 새 환경에 재생한 최종 DB와 비교한다. 해당 과제는 `reward_basis=[DB, COMMUNICATE]`로 사전 동결했다. 이 단계는 **DB 구성요소만** 검사하므로 전체 task reward를 보고하지 않는다.
- **기존 preflight보다 발전한 것**: 단순한 DB hash 변화 여부가 아니라, native 목표 상태와 실제 재생 DB hash가 같은지, 예약 생성·user linkage·항공편 재고 차감이라는 제한된 구조적 관계가 맞는지, 실패·변조에 대한 원본 evaluator의 경계를 시험한다.

## 2. 동결한 검증 사례

| 개발 사례 | 입력 경로 | Native DB 목표상태 일치 예상 | 주장의 범위 |
|---|---|---|---|
| `no_write` | 아무 신규 도구 호출 없음 | 거짓 | negative control |
| `gold_path` | native gold 4회 호출의 진짜 ToolMessage를 재생 | 참 | 기준선 상태 일치 |
| `omitted_write` | 마지막 `book_reservation` 누락 | 거짓 | 필요한 전이 부재 |
| `rejected_write` | 마지막 도구 메시지를 `execution_status=rejected` | 거짓 | harness에서 거부한 경로 |
| `tampered_tool_output_lenient` | 마지막 응답 내용을 위조하고 strict=False 재생 | 참 (일부 상태) | native DB oracle의 프로세스 한계 |
| strict tamper control | 동일 위조 응답에 strict=True | 예외로 거부 | response consistency 검사 |

이것은 저자가 만든 진단용 negative cases이며 실제 에이전트 공격 결과가 아니다. Native evaluator가 판단하는 DB target-state agreement를 승인된 실행 경로, 독립적 실세계 효과, 독립 관측으로 과장하지 않는다. `strict=False`는 upstream에서 역사적 도구 출력 형식 차이의 재등급화를 위해 의도적으로 제공되는 옵션이다. 따라서 lenient acceptance 자체를 upstream 결함이라고 주장하지 않는다.

## 3. 무조건 차단해야 하는 상황

- native 태스크나 reward_basis 변경, 원본 commit/uv.lock 불일치, 이전 외부 증거 ZIP 해시·맥락 불일치.
- gold action replay 예외, DB baseline/target hash drift, 구조적 상태 관계가 단 하나라도 틀림.
- negative control가 target DB와 같거나 gold positive control가 다름.
- strict replay에서 위조된 도구 출력이 거부되지 않음.
- 출력 ZIP 누락·변조, GitHub run/job 출처 불일치, API에 없는 최신 head를 임의 주장.
- 실험 범위 밖의 native LLM agent 실행·Q1 PASS·Q2 진입 주장.

## 4. 잔여 신뢰 가정 및 실증 조건

1. **독립 의미 오라클 없음**: 동일 tau2 native `FlightDB`, `AirlineTools`, `EnvironmentEvaluator`에 의존한다. 구조적 예약·좌석 검사도 동일 DB 객체를 사용하므로 구현 결함/공통 제어권은 여전히 공유한다.
2. **제한된 대표성**: Task 8 한 건의 저자선정 개발 케이스. Airline 전체와 Retail에 일반화 불가.
3. **실제 AI 없음**: LLM 모델, 사용자 시뮬레이터, 전체 reward, policy/authorization, 재시도, 그 이후 실세계 결과 미실행.
4. **외부 GitHub runner**는 호스트 재현성 자료이지 독립적인 운영 관리자나 상태 원천의 증거가 아니다.
5. **Q1A 자격 보유 여부**: NO. `Q1_BLOCKED`, `confirmatory_eligible=false` 유지. 정식 Q2는 외부 독립 root와 construct-matched native target의 적격성을 별도로 통과한 뒤 시작.

## 5. 결과를 논문에 옮길 때

이 단계의 결과가 실제 GitHub에 성공적으로 실행되면 `native DB component development controls independently rerun on GitHub-hosted infrastructure` 정도로만 기술한다. 연구의 신규성을 native 성능이나 새로운 benchmark로 주장하지 않는다. 원본 DB oracle의 결과와 ETB가 새로 판단할 과정 증거의 차이만 식별하고, 반증 사례 및 불확정 결과를 그대로 기록한다.

## 6. 원본 소스 앵커

- https://github.com/sierra-research/tau2-bench/blob/c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4/src/tau2/evaluator/evaluator_env.py
- https://github.com/sierra-research/tau2-bench/blob/c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4/src/tau2/environment/environment.py
- https://github.com/sierra-research/tau2-bench/blob/c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4/src/tau2/domains/airline/tools.py
- https://github.com/sierra-research/tau2-bench/blob/c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4/src/tau2/data_model/tasks.py
