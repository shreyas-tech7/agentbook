# Blockers

## B1. No GitHub repo or token
- Error: the session's GitHub token does not work and no repo is attached. API calls answer "GitHub access to this repository is not enabled for this session".
- Instead: pushed to a local bare remote and wrote a bundle. CI steps ran locally.
- Manual step: docs/HUMAN_STEPS.md step 1.

## B2. No free model provider
- Error: `curl: (56) CONNECT tunnel failed, response 403` for api.groq.com and openrouter.ai on 2026-11-20. No key variable is set.
- Instead: the FakeModel drives every example. `scripts/record_demo.py` is ready for record mode. The README says the live demo did not run.
- Manual step: docs/HUMAN_STEPS.md, the record mode step.

## B3. Skill install refused
- Error: the permission system denied `npx skills add` and `git clone` of the ponytail and humanizer repos.
- Instead: applied the Ponytail rules (small, plain, no extra layers) and the humanizer rules by hand. A reviewer agent that did not write the code stood in for `ponytail-review`.
- Manual step: none.

## B4. Hosts blocked
- huggingface.co, api.osv.dev and semgrep.dev did not answer. pip-audit (PyPI data), ruff S, gitleaks and actionlint ran instead. The project has no runtime dependencies.

## Bugs found and fixed
- Live bug, score 4 x 4 = 16: `call("delete_file", name=...)` raised TypeError. Fixed with a positional-only parameter. Test: `test_call_accepts_a_tool_argument_named_name`.
- Live bug, score 3 x 3 = 9: handoff allowed one handoff more than `max_handoffs`. Fixed. Test: `test_failure_case_ping_pong_stops_at_the_limit`.
- Live bug, score 2 x 4 = 8: a hung fan-out worker blocked the merge because the thread pool waited on exit. Fixed with `shutdown(wait=False)`. Test: `test_a_hung_worker_times_out`.
