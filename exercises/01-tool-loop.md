# Exercises: Tool loop

Lesson: [Tool loop](../docs/lessons/01-tool-loop.md). Solutions: `solutions/s01_tool_loop.py`.

## Exercise 1

Add a `multiply` tool next to `add`. Script a FakeModel that asks for `multiply` with 6 and 7, then answers. Check that the tool result in the trace is "42".

## Exercise 2

Run `tool_loop` with `max_steps=1` and a model that asks for a tool first. Predict the stop reason and the number of calls before you run it.

## Exercise 3

Write a `respond` function for the FakeModel. It asks for `add` once. When it sees a tool result in the messages, it answers with that result. It must not need a script.
