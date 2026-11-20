# Project context: agentbook

## What it is
A small book made of working code. Twelve agent patterns, one short Python file each.
Every pattern has tests with a scripted FakeModel, one failure-case test with its guard,
a plain English lesson and three exercises with separate solutions. No framework.

## Status
v0.1.0-rc1 candidate. See PROGRESS.md for what is done and BLOCKERS.md for what is not.

## Stack
Python 3.11+, standard library only. pytest is the only dev dependency.
Record mode calls any OpenAI-compatible endpoint with `urllib`.

## Commands
- `./init.sh`: make `.venv`, install, run every test and check offline.
- `python -m agentbook`: list the patterns.
- `python -m agentbook tool_loop`: run one pattern's example and failure case.
- `python scripts/run_examples.py`: rewrite `results/call_counts.json`.
- `python scripts/gen_readme.py`: rewrite the README tables and `docs/index.html` from results.
- `python scripts/fill_quotes.py`: refresh quoted code in lessons (`--check` only checks).
- `python scripts/check_links.py`: check links and anchors in Markdown and HTML.
- `python scripts/record_demo.py`: record mode. Needs AGENTBOOK_BASE_URL, AGENTBOOK_MODEL, AGENTBOOK_API_KEY.

## Layout
- `agentbook/model.py`: Model interface, Reply, ToolCall, FakeModel, OpenAICompatModel.
- `agentbook/counter.py`: CallCounter and the token estimate.
- `agentbook/tools.py`: message helpers, Tool, run_tool, Outcome.
- `agentbook/patterns/*.py`: the twelve patterns, each with `example()` and `failure_example()`.
- `docs/lessons/NN-name.md`: one lesson per pattern.
- `exercises/NN-name.md` and `solutions/sNN_name.py`: three exercises per lesson.
- `tests/`: one test file per pattern, plus rule tests.
- `results/`: call counts written by scripts. Never edit by hand.

## Rules
- A pattern file has at most 200 lines.
- Imports: standard library, `agentbook`, and pytest in tests. A test enforces it.
- Lessons quote code by line range. A test checks every quote.
- README numbers come from `results/`. A test checks them.
- Tests run offline. `tests/conftest.py` blocks the network.
- Prose: active voice, plain words, no em dashes, no semicolons.

## Skills that fit
superpowers test-driven-development, systematic-debugging, verification-before-completion.

## Do not read
`.venv/`, `logs/`, `docs/build/BUILD_PROMPT.md` unless you need the full brief.
