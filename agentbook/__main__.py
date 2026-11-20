"""Run a pattern's example from the terminal.

    python -m agentbook               list the patterns
    python -m agentbook tool_loop     run the example and the failure case
"""

from __future__ import annotations

import sys

from agentbook.patterns import ORDER, load


def show(label: str, run) -> None:
    outcome, counter = run()
    print(f"--- {label}")
    for message in outcome.trace:
        print(f"  {message['role']:>9}: {message['content'][:90]!s}")
    print(f"  answer: {outcome.answer!r}"[:200])
    print(f"  stop: {outcome.stop}   calls: {counter.calls}   est. tokens: {counter.tokens}")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    names = [name for name, _ in ORDER]
    if not args:
        for number, (name, title) in enumerate(ORDER, 1):
            print(f"{number:>2}. {name:<20} {title}")
        return 0
    if args[0] not in names:
        print(f"unknown pattern {args[0]!r}. Try one of: {', '.join(names)}")
        return 2
    module = load(args[0])
    show("example", module.example)
    show("failure case", module.failure_example)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
