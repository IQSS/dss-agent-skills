---
name: review-plan
description: "Review a proposed project or analysis before implementation, identifying consequential gaps, assumptions, and verification needs. Use for an existing plan or proposal; use a code or analysis review for work already executed."
compatibility: "Requires file access and an agent capable of launching a fresh reviewer with controlled context. Produces a Markdown brief without executing the planned work; optional PDF rendering uses the project’s chosen tools."
---

# /review-plan

Adversarial, *ex-ante* review of a project plan — the "Reviewer 2" pass you run **before** committing effort, written as a structured brief under `docs/briefs/`. Sibling to `/review-analysis`, which audits *executed* analysis (ex-post); this one critiques the *design*, across any project shape.

## Whose conventions?

This skill reviews against two things, and keeps them separate on purpose.

**Review criteria** are bundled at `references/default-standards.md`. Apply the core criteria to every plan and the scientific criteria only where relevant. A document-production plan does not need a statistical estimand or Bayesian convergence diagnostics.

**Project conventions** — layout, naming, where outputs live, which tier of `code/` a script belongs
to — are the project's, not this skill's. Pass `conventions=<path>` to name the file that records
them. With no argument, look for `CONVENTIONS.md`, `CLAUDE.md`, `AGENTS.md` or `CONTRIBUTING.md` at the project
root and reconcile the applicable guidance; if there is none, review against the bundled standards alone and
**say so in the brief**, so nobody reads silence as approval.

Never invent a house convention and then fault the work for breaching it.

## Source of truth

Project shapes, structure and naming come from the project's own conventions file — see § Whose conventions? below. The general standards each lens applies are bundled at `references/default-standards.md`. This skill encodes the *review heuristics* — what to interrogate in a plan and why — and cross-references those docs rather than duplicating them. When unsure of a convention, read the cited section and compare against the plan.

## Stance

You are Reviewer 2: constructive but unsparing. The author is competent and in the room; your job is to find what will sink the project **before** effort is spent — the unstated assumption, the missing step, the estimand nobody pinned down, the scrape with no ToS check. State uncertainty when a concern cannot be established from the plan. Avoid speculative findings that do not affect the project's outcome. `--harsh` raises the bar — include lower-confidence concerns and challenge choices that merely *feel* settled. It lowers the *confidence* bar, never the *relevance* bar.

## Execution — a fresh reviewer

Use a fresh reviewer with the target, requirements, and conventions but without the invoking agent's opinions. Use a supported subagent mechanism with conversation inheritance disabled where possible, or an authorized separate headless agent. State the isolation actually achieved. If the host cannot launch a fresh reviewer, report that limitation rather than claiming independence. The invoking agent relays the resulting brief; it does not supply findings in the reviewer's initial context.

## Workflow

The fresh reviewer carries out these steps under the isolation described above.

### 1. Parse scope from the argument

| Arg | Scope | Brief filename |
|---|---|---|
| (none) | auto-detect the most plan-like doc (`*plan*.md`, a `docs/briefs/*` design doc, README, or AGENTS.md if it carries the plan) | `<date>-plan-review-<doc-stem>.md` |
| `<path-to-doc>` | that document | `<date>-plan-review-<doc-stem>.md` |
| `--harsh` | (with or without a path) same scope, harsher stance | same |

Use the authorized project scope and supplied paths; ask about ambiguous boundaries. Reject nonexistent targets. If auto-detect finds several candidates, list them and ask which.

### 2. Detect project shape (→ pick the lens)

Establish the root from the supplied path, repository root, or project documentation. Select the lens from the plan's actual content, not its parent directory name or a required marker file. Hybrids may use several lenses; when none applies, use the generic core only.

State the detected shape + chosen lens(es) in the brief and the terminal report, so the author can correct a misdetection.

### 3. Gather context

Read in this order, and no further:

1. **The plan document** — the target.
2. **Project instructions and requirements** — `CLAUDE.md`, `AGENTS.md`, `SPECIFICATION.md`, or equivalent documents that are present. Consult `METHODOLOGY.md` for decisions behind research requirements.
3. **`TASKS.md`** if present — what's already done vs proposed (don't critique done work as if it were proposed).
4. **The convention doc section(s)** for the chosen lens(es) only.

A plan review reasons about the *design*, not the implementation — do **not** read the whole codebase. Skim the repo only enough to check feasibility claims (does the referenced dataset / file / API / tool actually exist?).

### 4. Run the review — universal core + shape lens

Apply the **universal core to every plan**, then layer the matching **shape lens(es)**. Tag every finding with a category bracket; assign severity in § 5.

#### Universal core (always)

- `[goal]` **Goal & done-ness** — is the objective and "what done looks like" precise? Success criteria stated and checkable?
- `[approach]` **Approach soundness** — is the method fit for the goal? Is there a simpler path to the same result?
- `[scope]` **Scope & feasibility** — doable in the stated time/resources? What's explicitly out of scope? Where will scope creep?
- `[seq]` **Sequencing & dependencies** — right order; critical path; what blocks what; are long-poles started first?
- `[risk]` **Risks & failure modes** — what breaks, how likely, mitigations, fallbacks?
- `[assume]` **Assumptions & unknowns** — what's assumed without justification? What should be de-risked with a spike / dry-run *before* committing?
- `[gap]` **Missing pieces** — what isn't addressed that should be (the Reviewer-2 specialty).
- `[verify]` **Verification & reversibility** — how will the author know it worked? Anything hard-to-undo, outward-facing, or destructive that needs a checkpoint first?

#### Shape lenses (apply the matching one[s])

**analysis** — the *ex-ante* counterpart of `/review-analysis`:
- `[estimand]` Is the target estimand precise (population, contrast, scale; causal vs descriptive)?
- `[ident]` For causal claims, is the identification strategy stated and credible *before* analysis (confounding, selection, measurement)? Assumptions explicit and checkable?
- `[power]` Sample size / precision / power considered? Missing-data plan?
- `[methods]` Methods suited to the question, the data structure (clustering, repeated measures), and the estimand? Primary vs exploratory delineated?
- `[prespec]` Primary vs secondary analyses, multiplicity, sensitivity analyses, stopping rules pre-specified?
- `[calib]` Calibration and diagnostics planned — is the model checked against data it should reproduce, and is the decision rule it feeds calibrated too?

**data / web-scraping** — prefer the least fragile acquisition route available: a published API or bulk download over a scraper, and a scraper over manual collection. Record which was used and why:
- `[source]` Does the plan reach for the right tier — **API / structured first**, scrape only when there's no API? Are ToS / `robots.txt` honored, with rate-limiting, a real User-Agent, and a `mailto` where the API asks?
- `[robust]` Is collection idempotent + resumable (checkpointing), with retry/backoff, and does it persist raw *then* parse as a separate pass?
- `[quality]` Data validation, schema, dedup, coverage/completeness, provenance?
- `[ops]` Volume / storage / cost; the sandbox egress allowlist for the target hosts; politeness/throttle; long jobs routed to an appropriate approved scheduler?

**document production** — one source of truth per document, a scripted build, and generated artefacts that are never hand-edited:
- `[audience]` Is the audience and purpose explicit — who reads it, what they do with it? Right length/depth for them?
- `[structure]` Outline coherence and logical flow; does the structure serve the purpose?
- `[grounding]` Are claims grounded in real sources (not model-confabulated)? A citation / fact-verification plan?
- `[build]` Does the chosen document workflow preserve editable source, produce the required format, and check the final artifact? Do not require a particular renderer or font stack.
- `[voice]` Voice matches the project's own writing conventions, where it has them; no AI tells.

**software** — `[arch]` architecture & interfaces/contracts · `[test]` testing strategy & error handling · `[deploy]` deployment / rollback / observability · `[sec]` security & secrets handling.

**consulting** — `[fit]` client-question ↔ deliverable fit and data adequacy for the ask · `[confid]` confidentiality / de-identification before anything is shown or shared · `[comms]` scope boundaries + communication cadence with the client.

**generic** — universal core only (process / ops / other plans with no domain lens).

### 5. Severity classification

Tag every finding with a severity and the category bracket(s) from § 4:

- **`blocker`** — a design flaw that means the plan, as written, won't achieve its goal or will fail in execution (no identification strategy for a causal claim; a scrape that ignores ToS / has no resume; unbounded scope against a fixed deadline; a missing critical-path dependency).
- **`should-revise`** — sound but suboptimal; fix before committing (a simpler approach exists; a long-pole sequenced last; a sensitivity analysis or fallback omitted).
- **`consider`** — a worthwhile alternative or addition the author may not have weighed.
- **`question`** — something the reviewer can't resolve from the plan alone (why this scope boundary; what's the fallback if the API rate-limits).

### 6. Write the brief

Use a supplied output path or the project's review-output convention. Otherwise compute `<date> = date +%Y-%m-%d` and use:

```
docs/briefs/<date>-plan-review-<scope>.md
```

`<scope>` = the plan doc's stem (e.g. `demo-plan`), or `project` for a whole-project auto-detect. If the brief exists, ask: overwrite, `-v2`, or abort. **Never silently overwrite.** (If the project has no `docs/briefs/`, write to `docs/` and note it; minimal-shape projects may have neither — fall back to the project root.)

Brief template:

```markdown
# Plan review: <human-readable scope>

Project: <project-slug>
Shape / lens: <detected shape> → <lens(es) applied>
Scope: <plan doc path>
Date: <YYYY-MM-DD>

## Summary

<2-4 sentences: overall assessment, count of findings by severity, the single most important takeaway. Is the plan ready to execute, ready-with-revisions, or back-to-the-drawing-board?>

## Blockers

### [scope] <one-line title>
**Where:** `<doc>:<section or line>`
**Issue:** <description, 1-3 sentences>
**Revise:** <suggested change, 1-2 sentences>

<repeat>

## Should revise

<same structure>

## Consider

<same structure>

## Questions

### [assume] <one-line title>
**Where:** `<doc>:<section>`
**Question:** <what you need from the author to resolve>

<repeat>

## What held up (checked, no finding)

<Brief: the load-bearing things you actively verified and found sound — so "few findings" reads as a result, not a skipped review. Skip only if there were many findings.>
```

If a section has no items, omit the entire section (don't leave empty headers).

### 7. Report to terminal

After writing, print one paragraph:

- Path to the brief.
- Detected shape + lens(es).
- Counts by severity: `<N blocker · M should-revise · K consider · L questions>`.
- The single most pressing finding (one line, with doc:section).
- "Read the brief for details."

## Things to NOT do

- **Do not duplicate the conventions file or the bundled standards** into the brief — cite the section, so the author can check the citation.
- **Do not review executed work.** This skill stops at the design. If the "plan" is actually finished work, say so and redirect to `/review-analysis` (analysis) or `/review` / `/code-review` (code).
- **Do not modify the project.** Write the brief in `docs/briefs/` and stop. No `Edit` calls on the plan or anywhere else — the author decides what to act on.
- **Do not pad.** Reserve `blocker` for genuinely design-fatal flaws; not every omission is a blocker, and trivial preferences don't belong in the brief at all.
- **Do not silently overwrite** an existing brief — ask first (§ 6).
- **Do not rubber-stamp.** A plan with zero findings is rare; if you found nothing, fill in "What held up" so a clean review is a *result*, not a skipped one.
- **State the review method honestly.** A fresh reviewer reduces inherited framing but does not guarantee correctness. Follow the supported isolation route described above.
