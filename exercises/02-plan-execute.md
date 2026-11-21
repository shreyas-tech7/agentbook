# Exercises: Plan and execute

Lesson: [Plan and execute](../docs/lessons/02-plan-execute.md). Solutions: `solutions/s02_plan_execute.py`.

## Exercise 1

Write a check that fails when a step's output contains the word "FIXME". Run a plan where step 1 returns "FIXME later". Which stop reason do you get?

## Exercise 2

A model returns a plan with seven numbered steps. `max_plan` is 6. How many model calls happen? Prove it with a counter.

## Exercise 3

Some models write "Step 1: ..." instead of "1. ...". Write your own `parse_steps` function that accepts both forms.
