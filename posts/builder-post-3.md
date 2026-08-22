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
>
> **builder.aws.com caps a post at 3000 characters.** Everything below the rule
> is the post; keep it under the cap. Run `python scripts/postlen.py` to check.
> The longer draft this was cut from is in git history at commit `ba17e4f`.

**Title:** A Prompt Is Not a Control: Enforcing a Safety Guarantee With a Strands Hook in an Agents for Humans Build

**Tags:** `agents-for-humans` `strands-agents` `amazon-bedrock` `ai-safety` `guardrails`

---

My neighbourhood safety agent makes one promise that matters: **no stored record and no alert ever describes a person.** Places, times, behaviour — never a height, a jacket, an ethnicity, a plate, a name.

This is a system where residents report on neighbours and correlation *amplifies* what they report. A correlation engine can launder bias into something that looks official. If the promise fails, the product is worse than not existing.

For most of the build I had that promise implemented twice, and neither was a control.

**The prompt asked for it.** Triage strips names, descriptions, vehicles, house numbers. It does the real work — nothing else can rewrite "tall guy in a red jacket" into "a person was reported near the lockers" — but compliance is a probability, and the failure is *silent*.

**A test checked it.** Twelve reports with person detail, through a live model, asserting none survives. That tells me about cases I thought of, on my machine. It says nothing about report thirteen at 2am.

Between "usually complies" and "guaranteed" there was nothing.

**The hook.** Strands fires `AfterModelCallEvent` after the model responds and before the agent loop continues, and the event carries a `retry` flag:

```python
def inspect(self, event: AfterModelCallEvent) -> None:
    findings = [f for t in _texts(event.stop_response) for f in scan(t)]
    if not findings:
        return
    if self.attempts >= self.max_retries:
        raise RedactionViolation(findings)
    self.attempts += 1
    event.retry = True      # discard it, make the model answer again
```

**The retry flag is the entire point.** I could have put this scan in the pipeline after the triage call — same leaks caught. But a pipeline check can only reject a *finished* result: the model has already spoken, so my options are drop the report or crash the run. A control that turns every leak into lost data is one that gets an exception carved into it the first time it costs somebody something.

Inside the hook, the leaked version never reaches the pipeline, storage, or the vector index. Enforcement costs one extra Haiku call. Cheap enforcement is enforcement that survives contact with a deadline.

**The bug that made it real.** My first version scanned `text` blocks and passed every test. It was inspecting nothing. With `structured_output_model`, generated fields arrive inside a **`toolUse` block's `input`** — so the redacted summary and the alert message, the only two fields the guarantee is about, were the one place I wasn't looking.

A guard that inspects the wrong field is worse than no guard: it converts an open question into false confidence. If you build one, feed it a known-bad *structured* output and assert the guard fires. Testing that clean input passes proves nothing.

Open source, MIT: **https://github.com/AminaZa/Porchlight** — the guard is `src/guards.py`.
