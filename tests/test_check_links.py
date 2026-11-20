"""The link checker finds every kind of broken link it claims to find."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_links import check  # noqa: E402


def make(tmp_path: Path, text: str) -> list[str]:
    (tmp_path / "other.md").write_text("# Other page\n\n## A real part\n")
    (tmp_path / "page.md").write_text(text)
    errors, _ = check(tmp_path)
    return errors


def test_the_real_repo_has_no_broken_links():
    errors, _ = check(ROOT)
    assert errors == []


def test_good_links_pass(tmp_path):
    assert make(tmp_path, "[ok](other.md) [part](other.md#a-real-part) [web](https://x.org)") == []


def test_missing_file_is_caught(tmp_path):
    assert make(tmp_path, "[gone](nope.md)") == ["page.md: missing file nope.md"]


def test_missing_anchor_is_caught(tmp_path):
    assert make(tmp_path, "[bad](other.md#no-such-part)") == [
        "page.md: missing anchor other.md#no-such-part"]


def test_bare_hash_is_caught(tmp_path):
    assert make(tmp_path, "[later](#)") == ["page.md: bare '#' link"]


def test_placeholders_are_caught(tmp_path):
    errors = make(tmp_path, "Clone github.com/<owner>/x. TODO. See example.com.")
    assert len(errors) == 3


def test_links_inside_code_are_ignored(tmp_path):
    assert make(tmp_path, "```\n[gone](nope.md) TODO\n```\n") == []


def test_external_links_are_listed_not_fetched(tmp_path):
    (tmp_path / "page.md").write_text("[web](https://x.org)")
    _, external = check(tmp_path)
    assert external == ["page.md: https://x.org"]


def test_linked_files_are_not_ignored_by_git():
    """A file that only exists in one working copy breaks every fresh clone."""
    import re
    import subprocess

    from check_links import MD_LINK, files, strip_code
    listed = subprocess.run(["git", "ls-files", "--others", "--ignored", "--exclude-standard"],
                            cwd=ROOT, capture_output=True, text=True, check=True).stdout
    ignored = {(ROOT / line).resolve() for line in listed.splitlines()}
    bad = []
    for path in files(ROOT):
        if path.suffix != ".md" or path.resolve() in ignored:
            continue
        for target in MD_LINK.findall(strip_code(path.read_text())):
            file_part = target.partition("#")[0]
            if file_part and not re.match(r"[a-z]+:", target):
                if (path.parent / file_part).resolve() in ignored:
                    bad.append(f"{path.relative_to(ROOT)} -> {target}")
    assert bad == []
