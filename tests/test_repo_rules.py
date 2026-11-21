"""Rules the brief sets for the whole book. Each rule has a test that proves the checker works."""

import ast
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from quotes import check_text, count_quotes  # noqa: E402

from agentbook.patterns import ORDER  # noqa: E402

PATTERNS = [name for name, _ in ORDER]
SLUGS = {name: f"{n:02d}-{name.replace('_', '-')}" for n, name in enumerate(PATTERNS, 1)}
MAX_LINES = 200


# Rule 1: every pattern file has at most 200 lines.

def count_lines(path: Path) -> int:
    return len(path.read_text().splitlines())


@pytest.mark.parametrize("name", PATTERNS)
def test_pattern_file_is_at_most_200_lines(name):
    assert count_lines(ROOT / "agentbook" / "patterns" / f"{name}.py") <= MAX_LINES


def test_line_counter_catches_a_long_file(tmp_path):
    """Broken case: a 201-line pattern file must fail the rule."""
    long_file = tmp_path / "long.py"
    long_file.write_text("x = 1\n" * 201)
    assert count_lines(long_file) > MAX_LINES


# Rule 2: imports come from an allowlist. No agent framework.

def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def allowed_for(path: Path) -> set[str]:
    allowed = set(sys.stdlib_module_names) | {"agentbook"}
    parts = path.relative_to(ROOT).parts
    if parts[0] == "tests":
        allowed |= {"pytest", "conftest", "quotes", "check_links", "gen_readme"}
    if parts[0] == "scripts":
        allowed |= {"quotes", "gen_readme", "run_examples", "check_links"}
    if parts[0] == "solutions":
        allowed |= {"_run"}
    return allowed


def python_files() -> list[Path]:
    folders = ["agentbook", "tests", "scripts", "solutions"]
    return sorted(p for folder in folders for p in (ROOT / folder).rglob("*.py"))


@pytest.mark.parametrize("path", python_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_imports_are_on_the_allowlist(path):
    bad = imported_roots(path) - allowed_for(path)
    assert not bad, f"{path.name} imports {sorted(bad)}"


def test_import_scan_catches_a_framework(tmp_path):
    """Broken case: a pattern that imports langchain must fail the allowlist."""
    sneaky = tmp_path / "sneaky.py"
    sneaky.write_text("import json\nfrom langchain.agents import AgentExecutor\n")
    assert imported_roots(sneaky) - set(sys.stdlib_module_names) == {"langchain"}


def test_patterns_import_only_the_model_counter_and_tools():
    for name in PATTERNS:
        tree = ast.parse((ROOT / "agentbook" / "patterns" / f"{name}.py").read_text())
        inner = {n.module for n in ast.walk(tree)
                 if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("agentbook")}
        assert inner <= {"agentbook.model", "agentbook.counter", "agentbook.tools"}, name


# Rule 3: every lesson quotes code that exists, line for line.

def lesson(name: str) -> Path:
    return ROOT / "docs" / "lessons" / f"{SLUGS[name]}.md"


@pytest.mark.parametrize("name", PATTERNS)
def test_lesson_quotes_match_the_code(name):
    text = lesson(name).read_text()
    assert count_quotes(text) >= 2
    assert check_text(text) == []
    assert f"agentbook/patterns/{name}.py#" in text


def test_quote_check_catches_drift(tmp_path):
    """Broken case: the code changed after the lesson quoted it."""
    (tmp_path / "code.py").write_text("a = 1\nb = 2\n")
    good = "<!-- quote: code.py#L1-L2 -->\n```python\na = 1\nb = 2\n```\n"
    assert check_text(good, root=tmp_path) == []
    (tmp_path / "code.py").write_text("a = 1\nb = 3\n")
    assert check_text(good, root=tmp_path) == ["code.py#L1-L2: quote does not match the code"]
    gone = "<!-- quote: code.py#L5-L9 -->\n```python\nx\n```\n"
    assert check_text(gone, root=tmp_path) == ["code.py#L5-L9: lines do not exist"]


# Rule 4: lesson shape and writing style.

SECTIONS = ["## The problem", "## The idea", "## The code", "## The failure case and its guard",
            "## When to use it", "## When not to use it", "## Typical call count", "## Exercises"]


def prose_sentences(text: str) -> list[str]:
    text = re.sub(r"^```.*?^```$", "", text, flags=re.S | re.M)
    text = re.sub(r"<!--.*?-->", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith(("#", "|"))]
    joined = " ".join(re.sub(r"^\s*(\d+\.|-)\s+", "", ln) for ln in lines)
    return [s for s in re.split(r"(?<=[.!?])\s+", joined) if s]


@pytest.mark.parametrize("name", PATTERNS)
def test_lesson_has_every_section_in_order(name):
    text = lesson(name).read_text()
    positions = [text.find(section) for section in SECTIONS]
    assert -1 not in positions and positions == sorted(positions)
    assert "https://www.anthropic.com/research/building-effective-agents" in text


@pytest.mark.parametrize("name", PATTERNS)
def test_lesson_sentences_are_short_and_plain(name):
    text = lesson(name).read_text()
    long = [s for s in prose_sentences(text) if len(s.split()) >= 20]
    assert not long, long
    assert "—" not in text and "–" not in text  # no em or en dashes
    assert ";" not in "".join(prose_sentences(text))


def test_sentence_check_catches_a_long_sentence():
    """Broken case: a 25-word sentence must be flagged."""
    long = " ".join(["word"] * 25) + "."
    assert [s for s in prose_sentences(long) if len(s.split()) >= 20] == [long]


# Rule 5: three exercises per lesson. Solutions sit apart.

@pytest.mark.parametrize("name", PATTERNS)
def test_three_exercises_and_separate_solutions(name):
    exercises = (ROOT / "exercises" / f"{SLUGS[name]}.md").read_text()
    assert re.findall(r"^## Exercise (\d)$", exercises, re.M) == ["1", "2", "3"]
    assert "def solution" not in exercises and "assert" not in exercises
    number = SLUGS[name][:2]
    solution = (ROOT / "solutions" / f"s{number}_{name}.py").read_text()
    for n in (1, 2, 3):
        assert f"def solution_{n}():" in solution
    assert f"exercises/{SLUGS[name]}.md" in lesson(name).read_text()
