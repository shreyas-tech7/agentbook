"""Write the README tables and docs/index.html from the results files.

    python scripts/gen_readme.py          rewrite README.md and docs/index.html
    python scripts/gen_readme.py --check  fail if either is out of date

Nobody types the numbers. They come from results/call_counts.json and results/live/.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
PAGE = ROOT / "docs" / "index.html"

USE = {
    "tool_loop": ("The steps depend on what the tools return", "You already know the steps"),
    "plan_execute": ("You want to see and check a plan before you pay for it",
                     "Each step depends on the last result"),
    "router": ("Requests fall into a few clear groups", "Every request needs the same handling"),
    "prompt_chain": ("The steps are fixed and each output can be checked in code",
                     "The steps depend on what the model finds"),
    "fan_out": ("Independent parts are known before the run", "Parts depend on each other"),
    "orchestrator": ("The parts depend on the task and cannot be listed in advance",
                     "You can list the parts yourself"),
    "evaluator_optimizer": ("Quality matters and a critic can name real problems",
                            "Code can check the result exactly"),
    "memory": ("A chat runs for many turns", "Each request stands alone"),
    "human_approval": ("A tool deletes, sends or pays", "Every tool is read-only"),
    "handoff": ("The right agent becomes clear mid-conversation",
                "One decision at the start is enough"),
    "budgets": ("Always, in any loop where the model decides when to stop",
                "Never skip it in a loop"),
    "retrieval": ("Answers depend on documents the model has not seen",
                  "The same documents fit in the prompt every time"),
}


def load() -> tuple[dict, list[dict]]:
    counts = json.loads((ROOT / "results" / "call_counts.json").read_text())
    live = [json.loads(p.read_text()) for p in sorted((ROOT / "results" / "live").glob("*.json"))]
    return counts, live


def slug(row: dict) -> str:
    return f"{row['number']:02d}-{row['name'].replace('_', '-')}"


def pattern_map(counts: dict) -> str:
    lines = ["| # | Pattern | Use it when | Avoid it when | Typical calls "
             "| Calls in failure case |", "| --- | --- | --- | --- | --- | --- |"]
    for row in counts["patterns"]:
        use, avoid = USE[row["name"]]
        link = f"[{row['title']}](docs/lessons/{slug(row)}.md)"
        lines.append(f"| {row['number']} | {link} | {use} | {avoid} | "
                     f"{row['example']['calls']} | {row['failure']['calls']} |")
    return "\n".join(lines)


def results_table(counts: dict) -> str:
    lines = [f"Source: {counts['source']}, recorded on {counts['generated_on']}. "
             f"Seed: {counts['seed']}. Tokens: {counts['token_estimate']}.", "",
             "| Pattern | Example stop | Calls | Est. tokens | Failure stop | Calls "
             "| Est. tokens |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for row in counts["patterns"]:
        e, f = row["example"], row["failure"]
        lines.append(f"| {row['title']} | `{e['stop']}` | {e['calls']} | {e['tokens']} | "
                     f"`{f['stop']}` | {f['calls']} | {f['tokens']} |")
    total_calls = sum(r["example"]["calls"] for r in counts["patterns"])
    total_tokens = sum(r["example"]["tokens"] for r in counts["patterns"])
    lines += ["", f"All twelve examples together: {total_calls} calls and about "
              f"{total_tokens} estimated tokens."]
    return "\n".join(lines)


def live_section(live: list[dict]) -> str:
    if not live:
        return ("Record mode did not run. No free provider could be reached from the build "
                "machine on 2026-11-20 (see BLOCKERS.md, B2). Every number above comes from the "
                "scripted FakeModel. `scripts/record_demo.py` runs the live demo once a key "
                "exists.")
    lines = ["| Pattern | Date | Model | Stop | Calls | Est. tokens |",
             "| --- | --- | --- | --- | --- | --- |"]
    for run in live:
        lines.append(f"| {run['title']} | {run['date']} | `{run['model']}` | `{run['stop']}` | "
                     f"{run['calls']} | {run['tokens']} |")
    return "\n".join(lines)


def splice(text: str, name: str, body: str) -> str:
    start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    return f"{head}{start}\n{body}\n{end}{tail}"


def page(counts: dict, live: list[dict]) -> str:
    rows = "\n".join(
        f"<tr><td>{r['number']}</td><td><a href=\"lessons/{slug(r)}.md\">{html.escape(r['title'])}"
        f"</a></td><td>{html.escape(USE[r['name']][0])}</td><td>{r['example']['calls']}</td>"
        f"<td>{r['example']['tokens']}</td><td><code>{r['failure']['stop']}</code></td>"
        f"<td>{r['failure']['calls']}</td></tr>" for r in counts["patterns"])
    live_note = (f"{len(live)} live runs recorded." if live else
                 "Record mode did not run. All numbers come from the scripted FakeModel.")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentbook results</title>
<style>
:root {{ --bg: #fbfaf7; --fg: #1f2328; --muted: #59636e; --line: #d8dee4; --accent: #0b6e4f; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg: #16181c; --fg: #e6e6e6; --muted: #a0a7b0; --line: #30363d; --accent: #4cc9a0; }}
}}
body {{ background: var(--bg); color: var(--fg); font: 16px/1.5 system-ui, sans-serif;
       margin: 0 auto; max-width: 960px; padding: 24px 16px; }}
h1 {{ margin-bottom: 4px; }} p {{ color: var(--muted); }}
a {{ color: var(--accent); }}
.wrap {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; min-width: 640px; }}
th, td {{ border-bottom: 1px solid var(--line); padding: 8px; text-align: left; }}
th {{ font-weight: 600; }}
</style>
</head>
<body>
<h1>agentbook</h1>
<p>Twelve agent patterns as small, tested Python files. Numbers below come from
results/call_counts.json, recorded on {counts['generated_on']}. {html.escape(live_note)}</p>
<div class="wrap">
<table>
<thead><tr><th>#</th><th>Pattern</th><th>Use it when</th><th>Calls</th><th>Est. tokens</th>
<th>Failure stop</th><th>Failure calls</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</div>
<p>Call counts come from scripted runs, so they are fixed numbers with no sampling error.
Tokens are estimates: characters divided by 4.</p>
</body>
</html>
"""


def build() -> tuple[str, str]:
    counts, live = load()
    text = README.read_text()
    text = splice(text, "map", pattern_map(counts))
    text = splice(text, "results", results_table(counts))
    text = splice(text, "live", live_section(live))
    return text, page(counts, live)


def main(argv: list[str]) -> int:
    readme, html_page = build()
    if "--check" in argv:
        stale = [p.name for p, new in ((README, readme), (PAGE, html_page))
                 if not p.exists() or p.read_text() != new]
        if stale:
            print(f"out of date: {', '.join(stale)}. Run scripts/gen_readme.py")
            return 1
        print("README.md and docs/index.html match the results")
        return 0
    README.write_text(readme)
    PAGE.write_text(html_page)
    print("wrote README.md and docs/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
