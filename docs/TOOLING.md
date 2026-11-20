# Tooling

| Tool | Source | Version | Why | Check |
| --- | --- | --- | --- | --- |
| gitleaks | github.com/zricethezav/gitleaks | v8.30.1 (go install) | secret scan before commits and on history | installed, runs |
| actionlint | github.com/rhysd/actionlint | latest on 2026-11-20 (go install) | check the CI workflow | installed, runs |
| pip-audit | PyPI via uv tool | latest on 2026-11-20 | dependency check | installed, runs |
| ruff | preinstalled | VM version | lint and `--select S` security rules | runs |
| superpowers skills | already in the session | session copy | plans, TDD, debugging, verification | used |
| ponytail, caveman, humanizer | GitHub | none | style rules | install refused by the permission system. Rules applied by hand |
| graphify, skill-scanner | PyPI | none | not needed: first run, under 30 source files, no new skills installed | skipped |
