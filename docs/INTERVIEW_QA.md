# Interview questions

Fifteen questions a founder or interviewer might ask, with answers from this repo. Every number comes from `results/call_counts.json`, made by `scripts/run_examples.py` with the scripted `FakeModel` on 2026-11-20. No real model was used.

## 1. When does a plain prompt chain beat an agent loop?

When you know the steps before the run. `run_chain` in `agentbook/patterns/prompt_chain.py` runs fixed steps with a code gate between them. Its example costs 2 calls and about 108 tokens. The tool loop in `agentbook/patterns/tool_loop.py` lets the model pick the next step. That freedom costs more, and its failure case burns 5 calls and 535 tokens before `max_steps` stops it. Use a loop only when the steps depend on what the tools return.

## 2. What does each pattern cost in model calls?

The examples range from 2 calls (tool loop, router, prompt chain, handoff, budgets, retrieval) to 5 calls (memory). All twelve examples together cost 36 calls. The README pattern map lists every count. `CallCounter` in `agentbook/counter.py` measures them, so nobody types a number by hand.

## 3. Where does each pattern fail, and which guard stops it?

Every pattern has a `failure_example()` and a test for it. Three examples:

- The tool loop repeats the same call. `max_steps` stops it with stop reason `max_steps`.
- Two handoff agents pass the task back and forth. `max_handoffs` in `run_handoffs` stops it after 3 handoffs.
- The retrieval model cites `[d7]`, which no search returned. `answer_with_search` compares cited ids with returned ids and stops with `bad_citation`.

## 4. Why no framework?

A framework hides the loop, the prompts and the stop rules. This repo teaches exactly those parts. Each pattern fits in 200 lines with only the standard library. `tests/test_repo_rules.py` scans every import against an allowlist, so a framework cannot sneak in.

## 5. How do the tests run without a model or a network?

`FakeModel` in `agentbook/model.py` replays a script of replies. `tests/conftest.py` patches the socket module so any non-local connection raises `NetworkBlocked`. `tests/test_network_guard.py` proves the block works. The whole suite runs in under a second.

## 6. Why does a token budget matter more than a step budget?

Each call resends the whole history, so cost grows faster than the step count. In the budgets failure case, 5 calls cost about 1,655 tokens. The fifth call alone costs more than the first two together. `over_budget` in `agentbook/patterns/budgets.py` checks steps, tokens and seconds before every call.

## 7. How do you stop an agent from doing something it cannot undo?

`run_with_approval` in `agentbook/patterns/human_approval.py` checks each tool's `risky` flag. A risky call needs a true answer from an approver function. A missing approver counts as no. The failure test checks the files that are left, which proves the delete never ran.

## 8. When would you use a router instead of a handoff?

A router decides once, at the start, in one cheap call. Its example costs 2 calls. A handoff lets an agent change its mind mid-conversation. Use a router when the first message is enough to decide. `route` in `agentbook/patterns/router.py` also sends an unknown label to a fallback handler instead of guessing.

## 9. How do you know the evaluator loop ends?

`optimize` in `agentbook/patterns/evaluator_optimizer.py` stops on a score of 8 or more, or after `max_rounds`. The failure case never reaches the score. It stops after 6 calls with `max_rounds` and returns the best draft so far, not the last one.

## 10. How does fan-out handle a worker that hangs?

`fan_out` in `agentbook/patterns/fan_out.py` runs workers in a thread pool with a timeout. It shuts the pool down without waiting, so a hung worker cannot block the merge. In the failure case the tone worker crashes. The merge still runs, marks the gap as missing and stops with `partial`. That costs 3 calls.

## 11. How does memory stay inside its size cap?

`Memory` in `agentbook/patterns/memory.py` keeps pinned facts and a window of recent turns. When the window passes the cap, it drops the oldest turns. One message bigger than half the cap gets cut and marked `[cut]`. The failure case pastes a huge log and ends with stop reason `cut`.

## 12. How do the lessons stay in step with the code?

Each lesson quotes code with a marker like `<!-- quote: agentbook/patterns/tool_loop.py#L10-L32 -->`. `tests/test_repo_rules.py` reads the marker and compares the fence with the real lines. If someone edits the code and forgets the lesson, the test fails.

## 13. What did the build not do?

Record mode did not run. No free provider was reachable from the build machine on 2026-11-20 (`BLOCKERS.md`, B2). So the repo makes no claim about how a real model behaves. `scripts/record_demo.py` is ready for when a key exists.

## 14. Why one tool call per reply?

`Reply` in `agentbook/model.py` holds text or one tool call. Several calls per reply would need extra bookkeeping in every loop. One call keeps each loop short enough to read in one sitting. `DECISIONS.md` line 3 records the trade.

## 15. What would you add next?

A thirteenth lesson that joins three patterns into one agent: a tool loop inside a budget, with an approval gate on risky tools. Then a real record-mode run, with the date, the model and the call counts in the README.
