"""Check every relative link and anchor in the Markdown and HTML files.

It fails on missing files, missing anchors, bare "#" links and placeholders
such as <owner>, TODO and example.com outside code blocks.
External links are listed as "not checked", because tests run offline.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".venv", ".git", "node_modules", "build"}
PLACEHOLDERS = ["<owner>", "TODO", "example.com"]
MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
IMG_LINK = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
HTML_LINK = re.compile(r"(?:href|src)=\"([^\"]+)\"")


def files(root: Path) -> list[Path]:
    found = []
    for path in sorted(root.rglob("*")):
        if path.suffix in {".md", ".html"} and not SKIP & set(path.relative_to(root).parts):
            found.append(path)
    return found


def strip_code(text: str) -> str:
    text = re.sub(r"^```.*?^```$", "", text, flags=re.S | re.M)
    return re.sub(r"`[^`\n]*`", "", text)


def slugify(heading: str) -> str:
    text = re.sub(r"[`*_\[\]()]", "", heading.strip().lower())
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    text = path.read_text()
    if path.suffix == ".html":
        return set(re.findall(r"id=\"([^\"]+)\"", text))
    return {slugify(m) for m in re.findall(r"^#{1,6}\s+(.+)$", strip_code(text), re.M)}


def check(root: Path = ROOT) -> tuple[list[str], list[str]]:
    errors, external = [], []
    for path in files(root):
        rel = path.relative_to(root)
        if rel.parts[:2] == ("docs", "build"):
            continue  # the build prompt is kept word for word
        text = strip_code(path.read_text())
        for word in PLACEHOLDERS:
            if word in text:
                errors.append(f"{rel}: placeholder {word!r}")
        pattern_list = [HTML_LINK] if path.suffix == ".html" else [MD_LINK, IMG_LINK]
        for pattern in pattern_list:
            for target in pattern.findall(text):
                if target == "#":
                    errors.append(f"{rel}: bare '#' link")
                elif re.match(r"[a-z]+:", target):
                    external.append(f"{rel}: {target}")
                else:
                    file_part, _, anchor = target.partition("#")
                    dest = (path.parent / file_part).resolve() if file_part else path
                    if not dest.exists():
                        errors.append(f"{rel}: missing file {target}")
                    elif anchor and dest.suffix in {".md", ".html"} and anchor not in anchors(dest):
                        errors.append(f"{rel}: missing anchor {target}")
    return errors, external


def main() -> int:
    errors, external = check()
    for line in errors:
        print(f"ERROR {line}")
    print(f"{len(external)} external links not checked (offline).")
    print(f"{len(errors)} errors.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
