# ETB Q1B Native Semantic Qualification v0.8.1

**AWS 없는 GitHub Actions 기반, 고정된 τ²-bench Airline Task 8의 native DB component 자격 검증.**

This package is a new **development-only Q1B** stage. It does not run an LLM agent, does not compute full task success, and cannot certify an independently administered observer. `Q1_BLOCKED` is by design.

## Source and evidence

- Original benchmark: Sierra `sierra-research/tau2-bench` at `c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4`.
- Prior GitHub workflow run: `45085918830` (success), source commit `eaecb26bddd8a70df5668d2646160e00d7315b44`.
- Prior workflow artifact ZIP SHA256: `a48f2ac62d2c5ac286fe77f533b33f840d1206be1afea2ef0b483f99b0006081`.
- The prior artifact's **five raw files** are included unmodified in `evidence/v080_run45085918830/`.
- The original v0.8.0 source layout and workflow are retained; a second workflow and new Q1B scripts are added. No private v0.7.x or non-redacted Mac Q0 evidence is bundled. Original source ZIP is preserved outside this public package.

## Local release validation (no tau2 install required)

```bash
python3 -m unittest discover -s tests -q
python3 scripts/verify_q1b_release.py
```

## GitHub Actions execution

Upload the **contents** of this package to the existing public `seo307/ETB_Q1_Github` repository, preserving hidden `.github/` and `.gitignore`. Commit as a **new version**. Existing workflow `.github/workflows/etb-q1-native-preflight.yml` is not replaced. A new workflow will appear:

**Actions → ETB Q1B Native Semantic Qualification (source-scoped) → Run workflow**.

This manually triggered workflow validates the package, fetches exactly pinned tau2, installs the original locked dependencies, then calls the actual native `EnvironmentEvaluator.calculate_reward` on five deterministic controlled trajectories and evaluates target-state semantics. It writes only bounded, non-PII booleans and hashes, plus environment/dependency provenance. Any mismatch halts with evidence instead of auto-correcting results.

After the GitHub run completes, download the workflow artifact `etb-q1b-semantic-<RUN_ID>-<ATTEMPT>` separately from the repository ZIP. It contains `native_semantic.json`, `context.json`, `upstream_uv.lock`, `python_packages.txt`, and `SHA256_MANIFEST.json` if successful.

```bash
python3 scripts/validate_q1b_artifact.py --artifact-dir /path/to/unpacked/q1b_artifact

python3 scripts/fetch_github_run.py \
 --repo seo307/ETB_Q1_Github --run-id YOUR_RUN_ID \
 --out-dir results/gh_q1b_run_YOUR_RUN_ID

python3 scripts/evaluate_q1b_github_run.py \
 --run-json results/gh_q1b_run_YOUR_RUN_ID/run.json \
 --jobs-json results/gh_q1b_run_YOUR_RUN_ID/jobs.json \
 --artifact-dir /path/to/unpacked/q1b_artifact \
 --out results/gh_q1b_run_YOUR_RUN_ID/q1b_external_audit.json
```

**Do not change the frozen thresholds, task, tool definitions or source after seeing GitHub outputs.** If the native integration finds compatibility gaps, keep the failed run and record a scoped development repair as a separate version. Never re-label a repair as a preregistered confirmatory success.

## Native result semantics

Native task 8 uses DB and communication; this stage runs **only the DB evaluator**, not user communication or full task reward. Positive gold replay and negative omitted/rejected tool controls are expected to match/negate native DB target. A deliberately corrupted final ToolMessage should be rejected under strict replay yet can preserve DB equality under `strict=False` (a designed upstream regrade mode). **This does not establish independent process trust or a vulnerability in tau2.**

Research docs: `docs/03_Q1B_native_semantic_protocol_KO.md`, `docs/04_research_quality_claim_guard_KO.md`.

## Status at packaging

Local 73 automated tests, 40/40 release-manifest files verified. **No v0.8.1 GitHub-hosted native run performed at packaging.** Native effect-oracle independence not established; administrative trust-root Q1A remains `BLOCKED`; confirmatory Q2 not started.
