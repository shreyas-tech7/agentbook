"""Lesson quotes. A marker names a file and a line range. The code fence after it must match.

    <!-- quote: agentbook/patterns/tool_loop.py#L28-L37 -->
    ```python
    ...those exact lines...
    ```
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = re.compile(r"<!-- quote: (?P<path>[\w/.]+)#(?P<ref>L\d+-L\d+|def:\w+) -->\n"
                    r"```python\n(?P<body>(?:.*\n)*?)```(?=\n|$)")


def lines_of(path: str, start: int, end: int, root: Path = ROOT) -> str | None:
    file = root / path
    if not file.is_file():
        return None
    lines = file.read_text().splitlines()
    if start < 1 or end > len(lines) or start > end:
        return None
    return "\n".join(lines[start - 1:end]) + "\n"


def def_range(path: str, name: str, root: Path = ROOT) -> tuple[int, int]:
    tree = ast.parse((root / path).read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
            return node.lineno, node.end_lineno
    raise KeyError(f"{name} not found in {path}")


def check_text(text: str, root: Path = ROOT) -> list[str]:
    """Return one problem string for each quote that does not match the code."""
    problems = []
    for match in MARKER.finditer(text):
        ref = match["ref"]
        if ref.startswith("def:"):
            problems.append(f"{match['path']}#{ref}: unresolved marker, run fill_quotes.py")
            continue
        start, end = (int(x) for x in ref[1:].split("-L"))
        expected = lines_of(match["path"], start, end, root)
        if expected is None:
            problems.append(f"{match['path']}#{ref}: lines do not exist")
        elif expected != match["body"]:
            problems.append(f"{match['path']}#{ref}: quote does not match the code")
    return problems


def count_quotes(text: str) -> int:
    return len(MARKER.findall(text))


def fill_text(text: str, root: Path = ROOT) -> str:
    """Resolve def: markers to line ranges and copy the current lines into each fence."""
    def replace(match: re.Match) -> str:
        path, ref = match["path"], match["ref"]
        if ref.startswith("def:"):
            start, end = def_range(path, ref[4:], root)
        else:
            start, end = (int(x) for x in ref[1:].split("-L"))
        body = lines_of(path, start, end, root) or match["body"]
        return f"<!-- quote: {path}#L{start}-L{end} -->\n```python\n{body}```"
    return MARKER.sub(replace, text)
