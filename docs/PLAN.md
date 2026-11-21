# Plan: agentbook

Goal: twelve agent patterns as small tested files, with lessons, exercises and a pattern map.
The brief in docs/build/BUILD_PROMPT.md is the spec. There were no question rounds.

## Assumptions
- Tool results go to real endpoints as user text (DECISIONS 4).
- Token counts are estimates, four characters per token (DECISIONS 5).
- Record mode cannot run in this session (BLOCKERS B2). The offline examples carry the book.

## Tasks
1. Core: `model.py`, `counter.py`, `tools.py`. Tests in `tests/test_core.py`.
2. Network guard in `tests/conftest.py`, proven by `tests/test_network_guard.py`.
3. Rule tests in `tests/test_repo_rules.py`: line count, import allowlist, lesson quotes, exercises.
4. Patterns 1 to 12. For each: code with `example()` and `failure_example()`, a test file,
   a failure test whose docstring names the broken case, a lesson, three exercises and solutions.
5. `scripts/run_examples.py` writes `results/call_counts.json`. `scripts/gen_readme.py` writes the
   pattern map and the results tables into README.md and `docs/index.html`.
6. `scripts/record_demo.py` for record mode, with a `--status` flag.
7. README, CI, quality files, study kit, release check and hand-off.

## Verify
`./init.sh` passes in under 60 seconds. Each `passes` flag in feature_list.json is set only after its steps pass.
