"""The README has the ten parts in order, a CI badge, and numbers that match the results file."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_readme  # noqa: E402

README = (ROOT / "README.md").read_text()
COUNTS = json.loads((ROOT / "results" / "call_counts.json").read_text())

PARTS = ["**Status:**", "## The problem", "```mermaid", "## Results", "## Cost per task",
         "## Run it in 10 minutes", "## Limits", "## Glossary", "## Related work",
         "## How this was built"]


def parts_in_order(text: str) -> bool:
    places = [text.find(part) for part in PARTS]
    return -1 not in places and places == sorted(places)


def test_readme_has_the_ten_parts_in_order():
    assert parts_in_order(README)


def test_order_check_catches_swapped_parts():
    """Broken case: Limits moved above Results must fail the check."""
    swapped = README.replace("## Limits", "## Lim1ts")
    swapped = swapped.replace("## Results", "## Limits\n## Results")
    assert not parts_in_order(swapped)


def test_readme_has_a_ci_badge():
    assert re.search(r"\[!\[CI\]\([^)]*badge\.svg\)\]", README)


def test_build_section_links_the_prompt_and_lists_human_checks():
    section = README.split("## How this was built", 1)[1]
    assert "docs/build/BUILD_PROMPT.md" in section
    assert "AI agents wrote most of this code under Shreyas's direction" in section
    assert section.count("not") >= 3


def test_pattern_map_covers_all_twelve_patterns():
    block = README.split("<!-- map:start -->")[1].split("<!-- map:end -->")[0]
    rows = [line for line in block.splitlines() if re.match(r"\| \d+ \|", line)]
    assert len(rows) == 12
    for row, pattern in zip(rows, COUNTS["patterns"], strict=True):
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert cells[-2:] == [str(pattern["example"]["calls"]), str(pattern["failure"]["calls"])]


def test_results_table_numbers_match_the_results_file():
    block = README.split("<!-- results:start -->")[1].split("<!-- results:end -->")[0]
    total_calls = sum(p["example"]["calls"] for p in COUNTS["patterns"])
    total_tokens = sum(p["example"]["tokens"] for p in COUNTS["patterns"])
    assert f"{total_calls} calls and about {total_tokens} estimated tokens" in block
    for pattern in COUNTS["patterns"]:
        assert f"| {pattern['title']} | `{pattern['example']['stop']}` |" in block


def test_readme_and_page_are_up_to_date():
    readme, page = gen_readme.build()
    assert readme == README
    assert page == (ROOT / "docs" / "index.html").read_text()


def test_record_mode_line_says_what_happened():
    block = README.split("<!-- live:start -->")[1].split("<!-- live:end -->")[0]
    live = list((ROOT / "results" / "live").glob("*.json"))
    if live:
        assert "model" in block.lower() and re.search(r"\d{4}-\d{2}-\d{2}", block)
    else:
        assert "Record mode did not run" in block


def test_readme_prose_has_no_em_dashes_or_semicolons():
    prose = re.sub(r"```.*?```", "", README, flags=re.S)
    assert "—" not in prose and "–" not in prose
    assert ";" not in prose
