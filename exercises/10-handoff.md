# Exercises: Handoff

Lesson: [Handoff](../docs/lessons/10-handoff.md). Solutions: `solutions/s10_handoff.py`.

## Exercise 1

Add a `billing` agent that triage may hand off to. Route a question about a double charge to it.

## Exercise 2

Run the ping-pong failure with `max_handoffs=1`. What is the path, and how many calls happen?

## Exercise 3

After one handoff, what is the last message the new agent sees? Read it from the FakeModel's `seen` list.
