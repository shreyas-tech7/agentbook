# Demo

A real terminal session on the build machine, on 2026-11-20. Nothing here needs a sign-in, a key or a network. Every model reply comes from the scripted `FakeModel`.

## Set up and check everything

```console
$ ./init.sh   # took 2.2 seconds of wall time
........................................................................ [ 27%]
........................................................................ [ 55%]
........................................................................ [ 83%]
...........................................                              [100%]
259 passed in 0.55s
README.md and docs/index.html match the results
18 external links not checked (offline).
0 errors.
init.sh: all checks passed
```

## List the patterns

```console
$ .venv/bin/python -m agentbook
 1. tool_loop            Tool loop
 2. plan_execute         Plan and execute
 3. router               Router
 4. prompt_chain         Prompt chain with gates
 5. fan_out              Fan-out and fan-in
 6. orchestrator         Orchestrator and workers
 7. evaluator_optimizer  Evaluator and optimizer
 8. memory               Memory
 9. human_approval       Human approval
10. handoff              Handoff
11. budgets              Budgets and stop rules
12. retrieval            Retrieval as a tool
```

## Run the tool loop and its failure case

The example answers in 2 calls. In the failure case the model repeats the same call, and `max_steps` stops it after 5.

```console
$ .venv/bin/python -m agentbook tool_loop
--- example
     system: You can call tools. When you know the answer, reply with plain text.
       user: What is 19 + 23?
  assistant: CALL add {"a": "19", "b": "23"}
       tool: 42
  assistant: 19 + 23 = 42
  answer: '19 + 23 = 42'
  stop: done   calls: 2   est. tokens: 185
--- failure case
     system: You can call tools. When you know the answer, reply with plain text.
       user: What is 1 + 1?
  assistant: CALL add {"a": "1", "b": "1"}
       tool: 2
  assistant: CALL add {"a": "1", "b": "1"}
       tool: 2
  assistant: CALL add {"a": "1", "b": "1"}
       tool: 2
  assistant: CALL add {"a": "1", "b": "1"}
       tool: 2
  assistant: CALL add {"a": "1", "b": "1"}
       tool: 2
  answer: None
  stop: max_steps   calls: 5   est. tokens: 535
```

## Run retrieval and catch a made-up source

In the failure case the model cites `[d7]`. No search returned it, so the run stops with `bad_citation`.

```console
$ .venv/bin/python -m agentbook retrieval
--- example
     system: Search before you answer. Cite each document you use like [d1].
       user: Can I keep unused leave?
  assistant: CALL search {"query": "unused leave next year"}
       tool: [d2] Unused leave carries over for up to 5 days into the next year.
[d1] Staff get 25 days
  assistant: Up to 5 unused days carry over to next year [d2].
  answer: 'Up to 5 unused days carry over to next year [d2].'
  stop: done   calls: 2   est. tokens: 207
--- failure case
     system: Search before you answer. Cite each document you use like [d1].
       user: Can I keep unused leave?
  assistant: CALL search {"query": "unused leave"}
       tool: [d2] Unused leave carries over for up to 5 days into the next year.
[d1] Staff get 25 days
  assistant: You can carry over all of it [d2][d7].
  answer: 'You can carry over all of it [d2][d7].'
  stop: bad_citation   calls: 2   est. tokens: 199
```

## The results page

Open [docs/index.html](index.html) from disk in any browser. It shows the same call counts as the README.
