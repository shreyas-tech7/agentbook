"""Pattern 3. Router.

One cheap call picks a label. The label picks the handler.
Each handler can have its own prompt, its own model or no model at all.

Failure: the model replies with something that is not a label.
Guard: an unknown label goes to the default handler, and the stop reason says "fallback".
"""

from __future__ import annotations

from collections.abc import Callable

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, Model
from agentbook.tools import Outcome, system, user

Handler = Callable[[str], str]


def route(model: Model, request: str, handlers: dict[str, Handler],
          default: str = "general") -> Outcome:
    if default not in handlers:
        raise ValueError(f"default handler {default!r} is missing")
    labels = ", ".join(handlers)
    prompt = f"Pick the best label for the request. Reply with one word from: {labels}."
    label = model.complete([system(prompt), user(request)]).text.strip().lower().rstrip(".")
    names = {name.lower(): name for name in handlers}
    if label in names:
        chosen, stop = names[label], "done"
    else:
        chosen, stop = default, "fallback"
    return Outcome(handlers[chosen](request), stop, steps=1,
                   extra={"label": label, "route": chosen})


def answer_with(model: Model, instructions: str) -> Handler:
    """Make a handler that answers with the model under its own instructions."""
    return lambda request: model.complete([system(instructions), user(request)]).text


def support_desk(model: Model) -> dict[str, Handler]:
    return {
        "billing": answer_with(model, "You answer billing questions in two sentences."),
        "technical": answer_with(model, "You fix technical problems step by step."),
        "general": lambda request: "Thanks. A person will read your message today.",
    }


def example() -> tuple[Outcome, CallCounter]:
    """A billing question goes to the billing handler. Two calls in total."""
    fake = FakeModel(["billing", "You paid twice. We refunded the second charge today."])
    counter = CallCounter(fake)
    result = route(counter, "Why was I charged twice this month?", support_desk(counter))
    return result, counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """The model rambles instead of giving a label. The default handler takes over."""
    fake = FakeModel(["Hmm, this could be billing or maybe technical, hard to say!"])
    counter = CallCounter(fake)
    result = route(counter, "Something is wrong with my account.", support_desk(counter))
    return result, counter
