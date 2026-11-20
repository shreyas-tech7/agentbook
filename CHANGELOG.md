# Changelog

## v0.1.0-rc1 (2026-11-20)

Release commit: RELEASE_SHA

The first release candidate. The tag is not created yet. Shreyas creates it, see `docs/HUMAN_STEPS.md`.

### Added

- A tiny `Model` interface, a scripted `FakeModel`, an OpenAI-compatible adapter and a call counter.
- Twelve agent patterns, each in one file of at most 200 lines, each with a failure case and its guard.
- Twelve lessons in plain English that quote the real code.
- 36 exercises with separate, tested solutions.
- A README pattern map and results table made from `results/call_counts.json`.
- A static results page in `docs/index.html` and a scripted social preview.
- Rule tests for line counts, imports, lesson quotes, lesson sections and sentence length.
- A network guard that blocks every non-local connection during tests.
- CI on Python 3.11, a link checker and issue templates.
- A study kit: walkthrough, interview questions and decisions.

### Not done

- Record mode did not run. No free provider was reachable from the build machine (`BLOCKERS.md`, B2).
