#!/usr/bin/env bash
# One command: make .venv, install agentbook with pytest, run every check offline.
set -euo pipefail
cd "$(dirname "$0")"
if command -v uv >/dev/null 2>&1; then
  [ -d .venv ] || uv venv -q .venv
  uv pip install -q --python .venv/bin/python -e ".[dev]"
else
  [ -d .venv ] || python3 -m venv .venv
  .venv/bin/python -m pip install -q -e ".[dev]"
fi
PY=.venv/bin/python
"$PY" -m pytest
"$PY" scripts/gen_readme.py --check
"$PY" scripts/check_links.py
echo "init.sh: all checks passed"
