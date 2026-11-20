# Prompt for Claude Cowork

Paste everything below the line into Claude Cowork after you finish steps 1 to 4 of `docs/HUMAN_STEPS.md`.

---

You are helping Shreyas finish the GitHub setup for his repo `shreyas-tech7/agentbook`. Do only free steps that can be undone.

Do these steps in the browser:

1. Open https://github.com/shreyas-tech7/agentbook/actions. Report whether the latest CI run on `main` passed. If it failed, copy the failing step name.
2. Open the repo's About box (the gear icon on the main page). Fill in the description and topics from `docs/TOPICS.md` in the repo.
3. Open Settings, then General, then Social preview. Upload `docs/social-preview.png` from the repo.
4. Check that the release `v0.1.0-rc1` or its tag exists on the Releases page. Report what you see.

Rules:

- Do not make the repo public. Shreyas does that himself.
- Do not publish a package, turn on paid features or pay for anything.
- Do not enter keys, tokens or passwords. Do not sign in for Shreyas.
- Do not merge pull requests or delete anything.

When you finish, give Shreyas this prompt for his next Claude Code session, with your findings filled in:

> Context: agentbook is a small book of twelve agent patterns in Python. Branch `claude/build-agentbook` is merged into `main`. Complete: patterns, lessons, exercises, solutions, README, CI, study kit. Open: record mode did not run (no provider key), and these Cowork findings: (fill in). Read docs/build/BUILD_PROMPT.md and follow it. Resume from PROGRESS.md on branch claude/build-agentbook. Do not ask questions. Do not stop until every Done-means item is true or blocked with a fallback.
