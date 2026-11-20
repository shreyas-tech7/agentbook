# Contributing

Thanks for helping. agentbook is a teaching repo, so small and clear beats clever.

## Set up

```bash
./init.sh
```

This makes `.venv`, installs the package with pytest and runs every check. It needs no network after the install and takes a few seconds.

## Rules every change keeps

- A pattern file stays at or under 200 lines. `tests/test_repo_rules.py` counts them.
- Code imports only the standard library, the package itself and pytest in tests. No agent framework.
- Every pattern keeps a failure-case test. Its docstring names the broken case and the guard.
- A lesson quotes real lines. After you change a pattern, run `python scripts/fill_quotes.py` and check the lesson text still fits.
- The README tables come from a script. Run `python scripts/run_examples.py` and then `python scripts/gen_readme.py`.
- Tests never touch the network. `tests/conftest.py` blocks every non-local connection.
- Lesson sentences stay under 20 words. Use active voice. Use no em dashes and no semicolons.
- Run `gitleaks git -v .` before you commit. Never commit a key.

## Good first changes

- Fix a lesson sentence that confused you. Open a "Lesson feedback" issue first if you are unsure.
- Add a fourth exercise to a lesson, with its solution in `solutions/`.
- Report a bug with the "Bug report" template. Include the command you ran and the output.

## Pull requests

Keep each pull request to one idea. Say what a reader sees before and after. CI runs the same steps as `./init.sh`.
