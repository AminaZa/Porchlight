---
tags: [hackathon, porchlight, builder-post]
status: draft
created: 2026-08-21
target: builder.aws.com
---

# Post 3 — the guarantee as a hook, not a prompt

> Draft. Bonus scoring: 0.2 of a possible 0.6, and it only counts if it is
> **published** on builder.aws.com before 14 Sep 2026, 5pm PT.
> Title must contain the phrase *Agents for Humans*.

**Title:** A Prompt Is Not a Control: Enforcing a Safety Guarantee With a Strands Hook in an Agents for Humans Build

**Tags:** `agents-for-humans` `strands-agents` `amazon-bedrock` `ai-safety` `guardrails`

---

My neighbourhood safety agent makes one promise that actually matters: **no stored record and no alert ever describes a person.** Places, times, behaviour — never a height, a jacket, an ethnicity, a plate, a name.

That promise is not decoration. This is a system where residents report on neighbours, and where correlation *amplifies* what they report. "Suspicious person" reports are the ones most prone to bias, and a correlation engine can launder that bias into something that looks official. If the promise fails, the product is worse than not existing.

For most of the build I had that promise implemented twice, and neither one was a control.

## What I actually had

**The prompt asked for it.** The triage prompt says: strip names, physical descriptions, vehicles, house numbers.

**A test checked it.** `tests/test_redaction.py` runs reports containing person detail through a live model and asserts none of it survives.

Both are necessary. Neither is a control, and the distinction took me longer to see than it should have:

- **A prompt is an instruction a model may choose not to follow.** It does the actual work — nothing else in the system is capable of rewriting "tall guy in a red jacket" into "a person was reported near the lockers" — but compliance is a probability, not a guarantee, and the failure is *silent*.
- **A test tells you about the cases you thought of, after the fact, on your machine.** Twelve of them, in my case. It says nothing about report thirteen at 2am in production.

Between "usually complies" and "guaranteed", there was nothing.

## The hook

Strands fires `AfterModelCallEvent` after the model responds and before the agent loop continues. A `HookProvider` can subscribe to it — and crucially, the event carries a **`retry` flag**.

```python
class RedactionGuard(HookProvider):
    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(AfterModelCallEvent, self.inspect)

    def inspect(self, event: AfterModelCallEvent) -> None:
        if event.exception is not None or event.stop_response is None:
            return

        findings = []
        for text in _texts(event.stop_response.message.get("content", [])):
            findings.extend(scan(text))

        if not findings:
            return

        if self.attempts >= self.max_retries:
            raise RedactionViolation(findings, self.attempts + 1)

        # Discard this response and make the model produce another one.
        self.attempts += 1
        event.retry = True
```

That's the whole mechanism. It inspects what the model *actually produced*, and if person detail survived, it throws the response away and asks again.

## Why the retry flag is the entire point

This is the part I want to make the case for, because it is the difference between a hook and a check you could have written anywhere.

I could have put this scan in the pipeline, right after the triage call. It would catch the same leaks. But a pipeline check can only ever **reject a finished result** — the model has already spoken, so my options are to drop the report or crash the run. A safety control that turns every leak into a lost report is one that gets an exception carved into it the first time it costs somebody real data.

Inside the hook, before the response is returned to the agent loop, `event.retry = True` discards it and re-invokes the model. The leaked version never reaches the pipeline, never reaches storage, never reaches the vector index. And the cost of enforcement is **one extra Haiku call**.

Cheap enforcement is enforcement that survives contact with a deadline. That is not a small property.

Two retries, then it raises. Failing the report is the correct end state for a model that keeps leaking — and it fails *loudly*, which is the opposite of how the prompt fails.

## The bug that made it real

My first version scanned `text` blocks and passed every test I threw at it. It was also inspecting nothing.

Structured output on Bedrock doesn't come back as text. With `structured_output_model`, the generated fields arrive inside a **`toolUse` block's `input`** — so the redacted summary and the alert message, the only two fields the guarantee is actually about, were in the one place I wasn't looking. The guard was a no-op that reported success.

```python
for block in content or []:
    if "text" in block:
        walk(block["text"])
    if "toolUse" in block:               # <- where structured output lives
        walk(block["toolUse"].get("input"))
```

Worth stating plainly: **a guard that inspects the wrong field is worse than no guard**, because it converts an open question into false confidence. If you build one of these, write a test that feeds it a known-bad structured output and asserts the guard *fires*. Testing that clean input passes proves nothing at all.

## Tuned for precision, on purpose

The patterns match constructions that are unambiguously person-identifying — `black man`, `named Dave`, `silver van`, `number 42` — and deliberately let borderline phrasing through to the prompt.

That asymmetry is a product decision, not laziness. A false positive costs a retry, real money, and can abort a demo run; more importantly, **a guard that fires on ordinary reports is a guard somebody switches off.** So the guard is a net *under* the prompt, not a replacement for it. Recall is the prompt's job and the live tests measure it; precision is the guard's job, and `tests/test_guards.py` asserts it against the offline fixtures and the untouched holdout set — 32 tests, none of which need an AWS account, because `scan()` is a pure function.

## The shape worth stealing

Three layers, doing three different jobs, failing three different ways:

| | does what | fails how |
|---|---|---|
| The prompt | asks for redaction, and does the actual work | **silently**, if the model doesn't comply |
| The hook | refuses non-compliant output inside the agent loop | **loudly**, and only after a retry |
| The tests | prove both hold against a live model | after the fact, on cases you thought of |

None is redundant and none can be dropped. If your agent has a property that must hold rather than usually hold, the prompt is where you ask for it and the hook is where you *require* it.

The build is open source under MIT: **https://github.com/AminaZa/Porchlight** — the guard is `src/guards.py`, in about 240 lines including the reasoning.
