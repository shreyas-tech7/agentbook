# Decisions

One line for each choice: what I picked, what else I weighed, and why.

1. Name: `agentbook`. PyPI and npm both answered 404 on 2026-11-20. A web search found agent books with other names and one GitHub Pages site at arivero.github.io/agentbook, which reads as a written book, not a well-known code project. Backups `patternbook` (npm 200, taken) and `agentpatterns` were not needed.
2. Remote: a local bare Git remote stands in for GitHub, because this session has no working GitHub token. Weighed waiting for GitHub. Rejected, nobody can answer.
3. Model interface: one method, `complete(messages, tools) -> Reply`. A Reply holds text or one tool call. Weighed returning several tool calls. One call keeps every loop easy to read.
4. Tool results travel to a real endpoint as user messages ("Tool result from add: 42"). Weighed the native tool message format. It needs `tool_call_id` bookkeeping, which hides the idea.
5. Token counts are estimates (characters divided by 4, rounded up). Weighed a tokenizer. That needs a dependency, and the brief allows pytest only.
6. FakeModel takes a script (replies in order) or a `respond` function. The function form serves patterns with threads, where call order is not fixed.
7. `respond` runs outside the FakeModel lock, so slow fakes really run in parallel in the fan-out tests.
8. `call(tool, /, **args)` takes the tool name as positional only. The old signature broke on a tool argument called `name`. Found while running the human approval example.
9. Every pattern returns an `Outcome` with a `stop` string. Readers always see why a run ended.
10. Patterns do not import each other. Each one imports only the model, the counter and the tools helper, as the brief asks. So patterns 9, 11 and 12 each hold their own short loop.
11. Lesson quotes use `<!-- quote: path#Lx-Ly -->`. `scripts/fill_quotes.py` can turn `#def:name` into a line range once. The test compares the fence with the real lines.
12. Solutions are Python files in `solutions/`, one per lesson, with three functions. A test runs all 36, so no solution can rot.
13. Record mode: blocked. Groq and OpenRouter answered "CONNECT tunnel failed, response 403" on 2026-11-20. The README says the live demo did not run.
14. Third-party skills (ponytail, caveman, humanizer) could not be installed. The permission system refused the install step. I applied their rules by hand and used a fresh reviewer agent for the review.
15. Handoff counts a handoff only when it is accepted. With `max_handoffs=3` an agent may hand off 3 times. The 4th attempt stops the run. Found by the ping-pong test, which first saw 4 handoffs.
16. The memory guard cuts one message to half the cap. Weighed rejecting long messages. Cutting keeps the start of the paste, which is usually the useful part.
17. Fan-out shuts its thread pool down without waiting. A hung worker would otherwise block the merge even after its timeout.
18. README tables come from `results/call_counts.json` through `scripts/gen_readme.py`. A test fails if the README and the file disagree.
19. Call counts are fixed counts from scripted runs. They have no sampling error, so the README gives no interval for them and says why.
