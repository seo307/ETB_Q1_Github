# ETB Q1 GitHub-hosted Native Preflight v0.8.0 — AWS 불필요

**현재 단계:** Q0 `PASS_SOURCE_PIN_ONLY` · v0.6.5 Docker `DEVELOPMENT PASS`(사용자 제공 기록) · v0.7.2 local release `PASS`(사용자 제공 기록) · GitHub external run **NOT EXECUTED** · native agent runs **0** · Q1 **BLOCKED** · Q2 **NOT STARTED**.

## 무엇을 제공하나

수동 실행 전용 `.github/workflows/etb-q1-native-preflight.yml`은 최소 권한 `contents:read`, GitHub-hosted `ubuntu-24.04`, SHA 고정된 checkout/upload-artifact action을 사용한다. 원본 τ²-bench 소스 commit `c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4`를 **실행 시점에 clone하고 정확히 checkout**하고, Python 3.12 및 고정된 `uv==0.13.9`로 원본 `uv.lock`을 `uv sync --frozen` 적용한 후 기존 native Airline Task 8 preflight를 실행한다. 실행 결과와 설치 패키지를 GitHub workflow artifact로 게시한다. Actions나 GitHub 계정을 이 채팅에서 연결/변경하지 않았다.

이것은 **소스스코프 원본 상태 전이 사전검증**이지, 실제 LLM 에이전트 실험이 아니고 process assurance의 독립 외부 오라클이 아니다. 원본 tau2-bench를 번들하지 않는다. `_PRIVATE_PROVENANCE.zip`는 별도 보존본이며 공개 실행용 ZIP에는 원본 Q0나 v0.7.2 ZIP을 넣지 않았다.

## 1. Mac에서 릴리스만 검증 (GitHub 불필요)

```bash
cd ETB_Q1_GitHubNative_v0.8.0
python3 -m unittest discover -s tests -q
python3 scripts/verify_release.py
```

## 2. GitHub Actions에서 수동 실행 (별도 서버/AWS 불필요)

1. 패키지의 **공개 실행용 파일만** GitHub 저장소 루트에 push한다. **`_PRIVATE_PROVENANCE.zip`은 절대로 업로드하지 않는다.** 공개본 Q0는 개인 Mac 경로 한 필드만 비식별화했고 원본 SHA는 `protocol/q0_redaction_v080.json`에 기록돼 있다. 보안상 비공개 저장소도 가능하다. workflow는 `.github/workflows/` 경로를 유지한다.
2. GitHub 웹의 **Actions → ETB Q1 Native Preflight (source-scoped) → Run workflow**를 클릭한다. 이 워크플로는 `workflow_dispatch`만 허용하고 모델 API 자격증명을 요구하지 않는다. GitHub 실행 비용·정책은 사용자 계정 조건에 따름.
3. 완료 후 Actions 화면에서 `etb-q1-native-preflight-<RUN_ID>-<ATTEMPT>` artifact를 내려받아 Mac에서 `native_dir/`로 압축 해제한다. 실패 시 아티팩트가 없을 수 있고 그것 자체가 실패 증거다. `GITHUB_RUN_ID`, `GITHUB_RUN_ATTEMPT`는 Actions UI에서 확인한다.
4. Mac에서 GitHub API의 **실제** run/jobs 기록을 별도 조회한다. 공개 저장소는 인증 없이도 읽힐 수 있지만 호출 제한이 있고, 비공개 저장소는 터미널의 `GH_TOKEN`이 필요할 수 있다. 토큰을 채팅이나 아티팩트에 첨부하지 않는다.

```bash
python3 scripts/fetch_github_run.py --repo OWNER/REPO --run-id RUN_ID --out-dir results/gh_run_RUN_ID
python3 scripts/evaluate_github_run.py \
  --run-json results/gh_run_RUN_ID/run.json \
  --jobs-json results/gh_run_RUN_ID/jobs.json \
  --native-dir /path/to/downloaded/native_dir \
  --out results/gh_run_RUN_ID/evaluation.json
```

결과가 `GITHUB_HOSTED_NATIVE_PREFLIGHT_CORROBORATED`여도 **`q1_status=Q1_BLOCKED`**가 정상이다. 작업 전 스크립트에 이미 동결된 freeze 및 prior Q0를 사용자 결과에 맞춰 다시 쓰지 않는다. 원격 실패는 기록하고 무단 재실행/모델 변경을 피한다.

## 중요 제약

- **관리 독립성:** 같은 GitHub 저장소 관리자라면 워크플로·아티팩트에 영향 가능. GitHub REST는 실행 메타데이터 확인 도구일 뿐 별도 관리 trust root가 아님.
- **오라클:** Task 8 reference actions는 원본 DB의 상태 변화 확인에만 사용하며 정책 승인·정당성의 gold가 아님. 원본 τ²-bench native reward를 재구현하거나 교체하지 않음.
- **환경:** 원본 commit·Q0·원본 `uv.lock`을 고정하고 `uv sync --frozen`을 사용한다. 결과에 `upstream_uv.lock`, `python_packages.txt` 및 환경을 보존한다. 다만 Python 패치·OS·네트워크 미러 환경의 동등성까지 자동 보장하지 않음.
- **소스 정보:** v0.7.2 이전 결과를 Q1 PASS로 변경하지 않음. 외부 독립 effect oracle 확보 전에는 Q2를 실행하지 않음.
- **안전:** 제3자 저장소 코드를 CI에서 설치/실행하므로 읽기 전용 토큰과 비밀키 부재를 유지. `pull_request_target`, PR 트리거, write scope를 추가하지 말 것.

연구 프로토콜: `docs/01_qualification_protocol_KO.md` · 품질·한계: `docs/02_quality_and_claims_KO.md`.
