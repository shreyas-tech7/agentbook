# Lesson 12. Retrieval as a tool

Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) describes an augmented model that can search, use tools and remember. This lesson treats search as one more tool. The model decides when to search and what to search for.

## The problem

A model does not know your documents. It may guess an answer that sounds right. It may even name a source that does not exist. We want the model to look things up, and we want proof that it used what it found.

## The idea

We build a tiny search index over a few documents. The model gets one tool, `search`. Our code remembers every document id that a search returned. The final answer must cite documents like `[d2]`. Our code then compares the citations with the ids that search really returned.

## The code

The index ranks documents by the number of words they share with the query.

<!-- quote: agentbook/patterns/retrieval.py#L37-L46 -->
```python
class Index:
    def __init__(self, docs: dict[str, str]):
        self.docs = docs

    def search(self, query: str, k: int = 2) -> list[str]:
        """Rank documents by how many query words they share. Ties go to the lower id."""
        wanted = words(query)
        scored = [(len(wanted & words(text)), doc_id) for doc_id, text in self.docs.items()]
        hits = sorted((s for s in scored if s[0] > 0), key=lambda s: (-s[0], s[1]))
        return [doc_id for _, doc_id in hits[:k]]
```

A real system might use a better search. The shape of the pattern stays the same.

The loop searches, answers and checks the citations.

<!-- quote: agentbook/patterns/retrieval.py#L49-L73 -->
```python
def answer_with_search(model: Model, question: str, index: Index, max_steps: int = 4) -> Outcome:
    returned: set[str] = set()

    def search(query: str) -> str:
        ids = index.search(query)
        returned.update(ids)
        return "\n".join(f"[{i}] {index.docs[i]}" for i in ids) or "no results"

    tools = toolbox(Tool("search", "Search the documents.", search, {"query": "search words"}))
    messages = [system(SYSTEM), user(question)]
    for step in range(1, max_steps + 1):
        reply = model.complete(messages, specs(tools))
        messages.append(assistant(reply))
        if reply.tool_call is not None:
            messages.append(tool_result("search", run_tool(tools, reply.tool_call)))
            continue
        cited = set(re.findall(r"\[(d\d+)\]", reply.text))
        extra = {"cited": sorted(cited), "returned": sorted(returned)}
        if not cited:
            return Outcome(reply.text, "no_citation", steps=step, trace=messages, extra=extra)
        if not cited <= returned:
            extra["unknown"] = sorted(cited - returned)
            return Outcome(reply.text, "bad_citation", steps=step, trace=messages, extra=extra)
        return Outcome(reply.text, "done", steps=step, trace=messages, extra=extra)
    return Outcome(None, "max_steps", steps=max_steps, trace=messages)
```

Read it line by line:

1. `returned` collects every document id that any search returned.
2. The `search` tool is a small function inside the loop, so it can update `returned`.
3. A tool call runs the search and adds the results to the conversation.
4. A plain answer ends the loop. We read the citations with a regular expression.
5. No citation stops with `no_citation`.
6. A citation that no search returned stops with `bad_citation`.
7. Good citations stop with `done`.

## The example

The question is "Can I keep unused leave?". The model searches for "unused leave next year". The search returns `d2` and `d1`. The model answers with a citation of `[d2]`. That is two calls.

```bash
python -m agentbook retrieval
```

## The failure case and its guard

In the failure case, the model searches, then cites `[d2]` and `[d7]`. No search returned `d7`. The model made up a source.

<!-- quote: agentbook/patterns/retrieval.py#L91-L96 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """The model cites [d7]. No search returned d7, so the guard flags the answer."""
    fake = FakeModel([call("search", query="unused leave"),
                      say("You can carry over all of it [d2][d7].")])
    counter = CallCounter(fake)
    return answer_with_search(counter, "Can I keep unused leave?", HANDBOOK), counter
```

The guard compares the two sets of ids. `d7` is not in `returned`, so the run stops with `bad_citation`. The outcome lists `d7` as unknown. Another test skips the search and cites `[d1]` from thin air. The guard flags that too, because nothing was returned.

The guard does not prove the answer is right. It proves the answer points at real search results. A person or a second check can then read those documents.

## When to use it

- The answer depends on documents the model has not seen.
- The model should choose what to search for.
- You need to show where an answer came from.

## When not to use it

- You always need the same documents. Put them in the prompt.
- The question never needs outside facts.
- You cannot store or search the documents safely.

## Typical call count

Typical call count: example 2, failure case 2.

The rule is one call for each search, plus one call for the answer.

## Exercises

Try the [exercises for this lesson](../../exercises/12-retrieval.md) before you read the solutions.
