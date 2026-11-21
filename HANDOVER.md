# Handover

State on 2026-11-20: v0.1.0-rc1 is built on branch `claude/build-agentbook`. Every Done-means item is true except the live record-mode demo, which is blocked and says so in the README.

Read first:

1. `docs/HUMAN_STEPS.md`: what only Shreyas can do, in order.
2. `docs/RELEASE_CHECK.md`: what was checked and fixed.
3. `BLOCKERS.md`: what could not be done here.

To resume in a new Claude Code session, paste this:

> Read docs/build/BUILD_PROMPT.md and follow it. Resume from PROGRESS.md on branch claude/build-agentbook. Do not ask questions. Do not stop until every Done-means item is true or blocked with a fallback.

Check first before you trust the repo:

1. Run `./init.sh` on a fresh clone. It must end with "init.sh: all checks passed".
2. Read lesson 1 and lesson 11 as a beginner. They set the tone for the rest.
3. Read `agentbook/model.py`. It is the only code that can reach the network or a key.
