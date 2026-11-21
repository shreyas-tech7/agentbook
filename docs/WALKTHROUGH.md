# Walkthrough

This is a tour of every file. Read it top to bottom once. Then open the files in the same order.

## The big picture

A pattern is a small loop around a model. The loop sends messages. The model replies with text or one tool call. Our code decides what happens next. Every run ends with an `Outcome`. The outcome says why the run stopped.

Tests never call a real model. They use `FakeModel`, which replays a script. So every test runs offline and gives the same answer every time.

## The package: `agentbook/`

### `agentbook/model.py`

This file defines what a model is.

- `Message` is a dict with a role and some content.
- `ToolCall` holds a tool name and its arguments.
- `Reply` holds either text or one tool call. Never both.
- `say(text)` makes a text reply. `call(tool, **args)` makes a tool call reply. Tests use both to write scripts.
- `Model` is the interface. It has one method: `complete(messages, tools)`.
- `FakeModel` replays a list of replies in order. It can also run a `respond` function instead. It raises `ScriptExhausted` when the script runs out.
- `OpenAICompatModel` talks to any OpenAI-compatible endpoint with `urllib`. It reads the key from an environment variable. It retries a rate limit up to five times. It refuses any URL that is not http or https.

### `agentbook/counter.py`

`CallCounter` wraps any model. It counts calls and estimates tokens. One token is about four characters. `summary()` returns the totals as a dict.

### `agentbook/tools.py`

Small helpers that every pattern shares.

- `system`, `user`, `assistant` and `tool_result` build messages.
- `Tool` holds a name, a description, a Python function and its parameters. A `risky` flag marks tools that need approval.
- `toolbox` turns a list of tools into a dict. `specs` turns them into the shape a model reads.
- `run_tool` runs one tool call. An error becomes text, so the model can see it.
- `parse_json` reads JSON from a reply, even inside a code fence.
- `Outcome` holds the answer, the stop reason, the step count, the trace and extra facts.

### `agentbook/__main__.py`

`python -m agentbook` lists the patterns. `python -m agentbook tool_loop` prints the example and the failure case as transcripts.

### `agentbook/patterns/`

Twelve files, one per pattern. Each one is at most 200 lines. Each one has the pattern itself, an `example()` and a `failure_example()`. Both return an outcome and a counter.

1. `tool_loop.py`: the model asks for tools until it answers. `max_steps` stops a loop that never ends.
2. `plan_execute.py`: the model writes a plan as JSON. Code checks the plan, then runs each step with a check after it.
3. `router.py`: one cheap call picks a handler. An unknown label goes to a fallback.
4. `prompt_chain.py`: fixed steps in order. A gate checks each output before the next step.
5. `fan_out.py`: independent reviews run in threads, then one call merges them. A timeout keeps a hung worker from blocking.
6. `orchestrator.py`: a lead call splits the task, workers do the parts, and a last call joins them. A cap limits the workers.
7. `evaluator_optimizer.py`: one call writes, another scores it. The loop stops on a good score or after `max_rounds`.
8. `memory.py`: a chat keeps pinned facts and a window of recent turns. A size cap drops old turns and cuts huge pastes.
9. `human_approval.py`: a risky tool waits for a yes from an approver. No approver means no.
10. `handoff.py`: an agent passes the task, with a note, to another agent. `max_handoffs` stops ping-pong.
11. `budgets.py`: one budget limits steps, tokens and seconds. The stop reason names the limit that ran out.
12. `retrieval.py`: search is a tool. Code checks that every citation came from a real search result.

`patterns/__init__.py` holds the order and the titles, and `load(name)` imports one pattern.

## Tests: `tests/`

- `conftest.py` blocks every network connection that is not local. A test that tries to reach the internet fails.
- `test_network_guard.py` proves the block works.
- `test_core.py` tests the model, the counter and the tools.
- `test_p01_tool_loop.py` to `test_p12_retrieval.py` test each pattern. Each file has a failure-case test. Its docstring names the broken case and the guard.
- `test_repo_rules.py` checks the house rules: the line limit, the import allowlist, the lesson quotes, the lesson sections and the sentence length. Each checker also has a test that feeds it a broken case.
- `test_solutions.py` runs all 36 solutions.
- `test_readme.py` checks the README parts and its numbers.
- `test_check_links.py` proves the link checker catches broken links.
- `test_repo_quality.py` checks that the quality files, the study kit and the hand-off exist.

## Scripts: `scripts/`

- `run_examples.py` runs every example and failure case. It writes `results/call_counts.json`.
- `gen_readme.py` writes the pattern map, the results table and the live section into the README. It also writes `docs/index.html`. With `--check` it only compares.
- `quotes.py` and `fill_quotes.py` read and fill the code quotes in the lessons.
- `check_links.py` checks every relative link and anchor in the Markdown and HTML files.
- `record_demo.py` runs three patterns against a real endpoint. It needs a key, so it has not run yet.
- `social_preview.py` draws `docs/social-preview.png` with the standard library.

## Lessons, exercises and solutions

- `docs/lessons/` has one lesson per pattern. Each one starts with the problem, quotes the code, explains the failure case and ends with when to use it.
- `exercises/` has three exercises per lesson.
- `solutions/` has the answers as Python files. Try the exercises first.

## Other files

- `README.md`: the front page.
- `DECISIONS.md`: each choice and its reason.
- `BLOCKERS.md`: what could not be done in the build and what was done instead.
- `docs/HUMAN_STEPS.md`: what Shreyas must do by hand.
- `docs/build/BUILD_PROMPT.md`: the brief the agents followed.
- `init.sh`: one command that sets up and checks everything.
- `.github/workflows/ci.yml`: CI runs the same steps as `init.sh`.
