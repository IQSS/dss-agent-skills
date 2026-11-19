---
name: review-prose
description: "Review finished prose for sentences a reader has to decode: a clause ending on an abstract noun the reader was never given, a noun handed across clauses so the pattern carries the argument, or a bare abstract noun as the object. Also reports banned tech-marketing phrasing, over-long sentences, and em-dash density broken down by kind. Use when the user runs \"/review-prose\", asks for a house-style or copy-edit pass, or asks whether a draft reads clearly. Reports for a human to rule on and never rewrites. Do NOT use to draft or rewrite prose, to check facts, or to review code."
compatibility: "Requires Python 3.9+ (standard library only). Reads markdown, or any plain text; code fences and HTML comments are skipped."
---

# /review-prose

Find the sentences a reader has to decode, in prose that is already written.

The defect is one thing: **a sentence that carries its argument in a pattern rather than in words.**
The writer knows the referent, so it reads as compression. The reader has none, so it reads as a
puzzle to solve or a slogan to skim past.

## Why this is a script and not a habit

These sentences feel like the best ones in the draft. They are short, they have rhythm, they sound
quotable, and that feeling is what protects them from a re-read.

Use the detector to identify passages for a closer read of the finished text. Its pattern matches
are prompts for editorial judgment, not evidence that a sentence is wrong.

## The three shapes

1. **A definite article with no antecedent.** "The refusal is the policy." "Its counterpart is the
   brief." Catchable by looking for a sentence that ends on `the <noun>`.
2. **A noun handed from one clause to the next**, so the pattern carries the argument. "The browser is
   for finding the interface; the interface is for the collection."

   The handoff alone is ordinary English. It becomes the defect when two other things are true, and
   both are about what the reader has to supply. **No connective**: a comma or semicolon juxtaposes
   the clauses and leaves the relation to be inferred, where "and", "so" or "because" would state it.
   And **an identity claim**: the second clause asserts `is the <noun>` rather than describing an
   effect with an ordinary verb. Compare:

   > ...is decoration, **and** decoration in this kind of writing **reads as** sales copy. *(fine)*
   >
   > ...is decoration**;** decoration in this register **is the** ad copy. *(the defect)*

   Same repeated noun, same length. The first states the relation and describes an effect; the second
   makes the reader infer the relation and then resolve a definite article with no antecedent.
3. **A bare abstract noun as the object.** "It does nothing about placement." "The trade is depth for
   breadth." No article to flag it, so it escapes a search for `the <noun>` — and escapes the writer,
   who knows what is being placed and traded.

`references/worked-examples.md` has eight before-and-after examples and explains why some similar
sentences remain clear. Read it before assessing the detector's results.

## Workflow

### 1. Run the detector

Resolve `<skill-directory>` to the installed directory containing this SKILL.md and `detect.py`; it is not the project's current directory. Quote the resolved path. In Claude Code, the supplied skill-directory variable can identify it. Use the host's equivalent location on other clients.

```sh
python3 "<skill-directory>/detect.py" "<file>" --conventions "<the-author-style-file>"
```

`--conventions` is optional and additive: banned phrases quoted in that file are added to the scan. It
is never required, and nothing about this skill depends on the author having such a file.

### 2. Read every hit

**Treat each hit as a candidate, not a verdict.** False positives vary with the document and
writing context. Read the surrounding passage before deciding whether a revision would help.

**Read the whole paragraph.** An unclear expression such as `remove the temptation` or a
`There ... Here ...` pair may appear beside the flagged sentence without matching a pattern.
Treat each hit as a cue to inspect the surrounding explanation too.

For each one, ask the two questions in order:

- **Does the reader get the meaning at once, or reconstruct it?** `Claude Code reads CLAUDE.md; Codex
  reads AGENTS.md` passes: both halves literal. `The browser is for finding the interface; the
  interface is for the collection` does not.
- **Does the sentence before it already say this?** The detector prints the previous sentence for
  this. A trailing short sentence that restates the preceding point is decoration, and decoration in this kind of writing reads as sales copy.

### 3. Report

One list, in file order: the sentence, why it fails, and a proposed rewrite that says the thing
plainly. Group the false positives at the end under a single line — do not make the reader scroll past
them to reach the real ones.

### 4. Check your own report

Run the detector over the report before returning it, then read the proposed rewrites in context.
For example, "the second session read the first implementation, and the check is void" leaves
*the check* undefined unless the surrounding passage identifies it. The detector looks for
`the <noun>` at the end of a sentence and can miss the same problem in subject position.

## What it does not catch

Worth saying plainly, so a clean report is not read as a clean document:

- **A definite article with no antecedent in subject position.** See above.
- **Constructions, as opposed to phrases.** `--conventions` harvests quoted strings from a style
  file, so it matches what is literally quoted there. A file banning "earns its place" and "earns
  its cost" does not catch `what earns the looser mode`, which is the same move.
- **Deictic pointers** — *here*, *there*, *this*, *that* standing in for something the reader must
  reconstruct. These words are also common in clear prose, so assess their referents in context.
- **A concrete noun standing in for the real subject** — "without seeing a real row", where the
  question is what a row is and who it would be sent to.

## Constraints

- **Report; never rewrite the file.** Propose the rewrite in the report and let the author apply it.
- **Explain specific strengths or problems.** Passing a pattern check does not establish that a
  sentence communicates its meaning clearly.
- Length and em-dash counts are **reported, not judged**. Compare them against the document's own
  register: a reference manual and an essay have different medians, and an absolute threshold is
  meaningless across both.
- Em-dashes come in three kinds and only one is the named pattern. `term — definition` entries in
  lists are conventional. Single dashes in prose are usually appositives. Matched pairs in running
  prose are the parenthetical-subclause habit worth counting.
- This skill reads nothing outside its own folder except the file under review and any `--conventions`
  file passed to it.

## Things to NOT do

- Do not rewrite the file.
- Do not report a count you did not get from the detector.
- Do not widen the detector to catch more. Ordinary English uses semicolons and repeats words
  constantly; a report nobody reads is the same as no report.
- Do not treat a long sentence as a defect on its own. Many long sentences are enumerations that parse
  fine. The question is whether it obstructs, and that needs reading.
- Do not check facts, spelling, or grammar here. Different job.
