# Release check

Done on 2026-11-20, before the v0.1.0-rc1 commit.

| Step | Result |
| --- | --- |
| Code review | A fresh reviewer agent stood in for `ponytail-review`, which could not be installed (BLOCKERS B3). It found 3 must-fix items and 7 smaller ones. All 10 are fixed, see below. |
| Security audit | Skipped, as the brief allows. The project has no sign-in, personal data or payments. |
| `gitleaks git -v .` | No leaks found, on every commit. |
| `pip-audit` | No known vulnerabilities found. The package has no runtime dependencies. |
| `ruff check --select S` | All checks passed. Two `noqa` comments carry a reason: the URL scheme check in `agentbook/model.py` and a fixed git command in a test. |
| `actionlint` | No problems in `.github/workflows/ci.yml`. |
| `scripts/check_links.py` | 0 errors. 18 external links listed as not checked, because the build ran offline. |
| Humanizer pass | Done by hand, since the skill could not be installed. A script found no em dashes, en dashes, semicolons or banned filler words in the prose. |
| Outside check | A fresh agent cloned the repo and checked the nine Done-means items. 8 passed. Item 1 failed on a fresh clone, see below. Fixed, and a fresh clone now passes. |
| `git status` | Clean at the release commit. |

## What the review found and what changed

1. Must fix. The record adapter sent the API key over plain http and let it follow a redirect to any host. Now the key goes only over https or to this machine, and the adapter follows no redirects. Tests check both.
2. Must fix. Lesson 11 said a budget is the most you can pay. Limits are checked between calls, so a run can go one call past a limit. The lesson now says so.
3. Must fix. Fan-out waited one timeout per worker, one after another. Now all workers share one deadline. Lesson 5 now says a hung thread keeps running and a timed-out call is still billed.
4. `parse_json` missed a fence on one line. Fixed and tested.
5. Bad JSON in tool arguments crashed the adapter. Now `run_tool` reports it as text.
6. The network guard did not block DNS lookups. Now it does.
7. The adapter had only one retry test. Added tests for a server error, the key header and redirects.
8. Pinned memory could crowd out the whole chat. `pin` now refuses to use more than half the cap.
9. The router could not match handler names with capitals. Fixed and tested.
10. A README test passed on almost any text. It now checks the three human-check lines word for word.

## What the outside check found

1. Fixed. `.gitignore` had `build/`, which also hid `docs/build/BUILD_PROMPT.md`. A fresh clone failed the link check. A new test fails if a linked file is git-ignored.
2. Kept. CI skips pushes that change only docs, as the brief asks. Doc-only changes still run all checks on pull requests.
3. Logged. The import scan reads `import` lines only, so `importlib.import_module` would slip past it. No pattern uses it.
