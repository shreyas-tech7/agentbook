"""The quality files, the study kit and the hand-off files exist and say what they must."""

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(name: str) -> str:
    return (ROOT / name).read_text()


def test_quality_files_exist():
    for name in ["LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", ".github/workflows/ci.yml",
                 ".github/ISSUE_TEMPLATE/bug_report.md",
                 ".github/ISSUE_TEMPLATE/lesson_feedback.md",
                 "docs/TOPICS.md", "docs/index.html", "docs/DEMO.md"]:
        assert (ROOT / name).is_file(), name
    assert "MIT License" in read("LICENSE")


def test_social_preview_is_1280_by_640_and_made_by_a_script():
    data = (ROOT / "docs" / "social-preview.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", data[16:24]) == (1280, 640)
    assert (ROOT / "scripts" / "social_preview.py").is_file()


def test_ci_matches_the_rules():
    ci = read(".github/workflows/ci.yml")
    for word in ["workflow_dispatch", "pull_request", "cancel-in-progress", "paths-ignore",
                 "3.11", "./init.sh", "timeout-minutes"]:
        assert word in ci, word


def test_demo_has_a_real_transcript():
    demo = read("docs/DEMO.md")
    assert "python -m agentbook tool_loop" in demo
    assert "stop: max_steps" in demo and "$ ./init.sh" in demo


def test_topics_list_has_topics():
    topics = [line for line in read("docs/TOPICS.md").splitlines() if line.startswith("- ")]
    assert 5 <= len(topics) <= 20


def test_study_kit_is_complete():
    walk = read("docs/WALKTHROUGH.md")
    for path in ["agentbook/model.py", "agentbook/counter.py", "agentbook/tools.py",
                 "conftest.py", "gen_readme.py", "tool_loop.py", "retrieval.py"]:
        assert path in walk, path
    qa = read("docs/INTERVIEW_QA.md")
    assert 13 <= qa.count("\n## ") <= 18
    for point in ["prompt chain beat an agent loop", "cost in model calls", "which guard",
                  "Why no framework"]:
        assert point in qa, point
    assert read("DECISIONS.md").count("\n1") >= 1


def test_handoff_files_are_complete():
    steps = read("docs/HUMAN_STEPS.md")
    for word in ["agentbook.bundle", "git push origin --all", "v0.1.0-rc1", "gitleaks",
                 "public", "BUILD_PROMPT.md"]:
        assert word in steps, word
    assert "v0.1.0-rc1" in read("CHANGELOG.md")


def test_feature_flags_are_booleans():
    features = json.loads(read("feature_list.json"))
    assert all(isinstance(f["passes"], bool) for f in features)
    assert [f["id"] for f in features] == [f"F{n:02d}" for n in range(1, len(features) + 1)]
