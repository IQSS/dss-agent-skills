---
name: litsearch
description: "Conduct an auditable literature search with saved queries, screening decisions, an evidence table, and bibliography checks. Use for research discovery or a documented search supporting a review. Does not establish systematic-review compliance or perform a meta-analysis."
compatibility: "Requires Python 3.9+ (standard library only) and network access to api.openalex.org, api.crossref.org, api.datacite.org, eutils.ncbi.nlm.nih.gov and export.arxiv.org."
---

# /litsearch

Turn a research question into an auditable search record, evidence table, and bibliography. Verify bibliographic identity separately from whether a paper supports a claim; a resolved identifier does not establish full-text access or research quality.

## The rule

> **No record enters the evidence table without a resolved identifier.**

Every included row carries a DOI, PMID or arXiv ID that was fetched from a live API, and whose
title, first author and year were compared against what the evidence table claims. Anything that cannot be
resolved goes to `unverified.md`.

Two consequences that are easy to get wrong, and are the whole point:

- **An unresolved record is not verified.** Record it in `unverified.md` with the lookup result. Distinguish a missing record, malformed identifier, incomplete metadata, and an inaccessible service; do not infer fabrication from a network failure.
- **Do not screen from your own knowledge of a paper.** A screening decision cites the abstract
  text that was actually fetched. If no abstract was retrieved, the record is screened on title
  only, and the evidence table says so.

## Arguments

| Form | Meaning |
|---|---|
| (none) | Ask for the question. If a run directory exists with `protocol.md` but no `evidence.csv`, offer to resume it instead. |
| `<question>` | Start a new run. Free text, quoted if it contains shell metacharacters. |
| `verify <run-dir>` | Re-run the checks against an existing run and stop. Changes nothing. |

Options, appended as `key=value`:

| Option | Default |
|---|---|
| `out=<dir>` | `outputs/litsearch/<YYYY-MM-DD>-<slug>/` under the current project, else `./litsearch-<YYYY-MM-DD>-<slug>/` |
| `sources=<list>` | `openalex,crossref`. Add `pubmed` for health, `arxiv` for preprints, `ssrn`, `repec`, `nber` for economics and the social sciences. |
| `from=<year>` `to=<year>` | unbounded |
| `style=<apa/vancouver/chicago>` | `apa` |
| `mailto=<email>` | Optional contact address. An address supplied on its own goes to Crossref only. |
| `mailto-to=crossref\|datacite\|both\|neither` | Services allowed to receive the address for this run. Accept the same choices in plain language. |

Use `out=` when supplied; otherwise preserve the project's documented output convention or use the listed default.

## Workflow

### 1. Protocol, before any searching

For an interactive search or verification run, ask once during setup if the researcher has not already given an email preference:

> Crossref and DataCite allow more frequent citation checks when you include a contact email, which can speed up larger searches. Would you like to share an email address with Crossref, DataCite, both, or neither? If you choose a service, which email address should I use?

Use the answer for searches and citation checks, including a lookup that moves from Crossref to DataCite. If the researcher has already chosen a service but omitted the address, ask only for the address. If they choose neither or skip the question, continue without an address.

Skip the question for an offline check, when the caller says to run unattended, or when it is unclear whether anyone can answer. On unattended searches and checks, use any email options supplied at launch. Without an address, continue the run without sending one.

Write `protocol.md` from the user's approved scope:
question, inclusion and exclusion criteria, date range, languages, the sources to be queried, and
what "done" means. If the question is vague ("papers about social mobility"), say what is
ambiguous and ask, rather than guessing a scope and searching a large literature against it.

If the user already supplied these decisions, proceed within them. Ask only for missing choices that would materially change the search. Distinguish an exploratory search from one intended to support a systematic review.

### 2. Search

Query the APIs. **Never** answer from your own knowledge of the literature.

| Source | Endpoint | Notes |
|---|---|---|
| OpenAlex | `api.openalex.org/works` | Broad discovery; check current access limits and available authorized credentials. |
| Crossref | `api.crossref.org/works` | DOI metadata and discovery; DataCite covers additional DOI registrations. |
| PubMed | `eutils.ncbi.nlm.nih.gov/entrez/eutils` | `esearch` then `esummary`. Health. |
| arXiv | `export.arxiv.org/api/query` | Preprints. |
| SSRN / RePEc / NBER | site search | Coverage is uneven; record what was reachable. |

Save every raw response under `raw/` unmodified, and append the exact query string, source and
date to `queries.md`. Use one bullet per request/page with a Markdown link to its saved response, for example `- OpenAlex; 2026-11-19; query=...; [response](raw/openalex-001.json)`. Record failures as failures, not completed retrievals.

Paginate to the protocol's stopping rule. If a source returns more than the protocol expects, stop
and report the count rather than silently truncating.

For exploratory discovery, an explicitly agreed limited search is acceptable; disclose the cap and ranking. A systematic search needs its own justified coverage and stopping rules. Pause at resource checkpoints rather than silently truncating a search or expanding its budget.

### 3. Deduplicate

Group repeated records with the same identifier. When two sources give the same publication different identifiers, compare the title, authors, year, and publication details before combining their records. For a preprint or working paper, look for a link to the published article even if the title or year changed. Check the journal DOI on the repository page or a Crossref `is-preprint-of` or `has-preprint` link. Similar titles and overlapping authors can suggest a pair. If you cannot confirm the link, flag both records for the researcher and keep them separate.

For a confirmed pair, keep both identifiers in `screening.csv` and cite the source that links them. If the study is included, count it once. Choose the version that supplies the evidence under the protocol, mark that record as included, and use its identifier in `evidence.csv` and both bibliographies. Record the other version as a duplicate and name its counterpart. Report the counts before and after deduplication in `README.md`, along with any pairs awaiting review.

### 4. Screen

Title, then abstract, then full text. Write every record to `screening.csv` with the stage it left
at and the reason. Exclusion reasons come from the protocol's criteria, not invented per record.

Bring the borderline set to the user rather than deciding it. State how many were unambiguous and
how many need a judgement call; the researcher decides those.

Before including a paper, check for a retraction. Crossref links notices in the paper’s `updated-by` list. PubMed uses a “Retraction in” link or a “Retracted Publication” label. Follow up an OpenAlex `is_retracted` flag at the publisher. For an arXiv preprint with a journal DOI, check which version the notice covers.

Record the source, date, and result in `screening.csv`. If the source lacks retraction metadata, check the publisher or repository record. Distinguish “no notice found in this source” from “could not check.”

Show the researcher any notice you find. Keep the paper in `screening.csv` with the notice link and the researcher’s decision and reason. If the decision is pending, leave the paper out of the evidence table. If the researcher includes it, put their reason in `retraction_inclusion_reason` in `evidence.csv` so the flag stays visible.

### 5. Resolve identifiers and extract evidence

Resolve identifiers while screening and check metadata against the retrieved records. Record inaccessible or ambiguous entries separately. The complete run checker is executed after the files below have been created.

One row per included paper in `evidence.csv`, keyed by identifier. Columns come from the protocol —
typically design, population, N, exposure, outcome, effect, limitation. These columns are required:

- `id` — a bare DOI, PMID, or modern arXiv ID (optionally with its version). Never empty.
- `title`, `author`, `year` — retrieved title, first author (or group author), and four-digit publication year. If these cannot be established, keep the entry unresolved.
- `evidence` — `title`, `abstract` or `fulltext`: the deepest level actually read for this row.
- `source` — which API the record came from.

Leave a cell empty rather than inferring it. An empty cell is a reading task; a guessed one is a
fabrication with extra steps.

### 6. Create bibliographies and verify the complete run

Emit **both** `references.bib` and `references.ris`, carrying the identifier for every row, so
references enter the writing tool by a route that preserves it.

Use `doi={...}`, `pmid={...}`, or `eprint={...}` identifier fields in BibTeX. In RIS, use `DO  - <doi>` for DOIs and `AN  - <pmid-or-arxiv-id>` for the other supported identifiers. Preserve identifiers even if a reference manager ignores a display field. Keep the same included records in both formats.

Write the counts and limitations to `README.md`, then run the bundled checker. Resolve `<skill-directory>` to the installed folder containing this SKILL.md and `verify.py`, not the project's current directory:

```sh
python3 "<skill-directory>/verify.py" "<run-dir>"
```

When the researcher supplies an address and selects recipients, append `--mailto "<email>"` and `--mailto-to` with their choice. An address alone retains the Crossref-only default. For neither, or without an address, use the command as shown.

The checker compares citation metadata, checks again for retraction notices, checks bibliography identifiers and saved-response links, and reconciles screening counts. Exit 1 means a detected problem, including a retraction with no recorded reason for inclusion. Exit 2 means a source could not be fully checked. Report any retraction checks that required manual review. `--offline` performs structural checks only. Study quality and support for each claim require separate review.

The live checker also flags two included versions when Crossref links their DOIs or arXiv supplies the included article’s DOI. Similar titles and a matching first author can trigger a review even when the publication years differ.

## Output

```
<run-dir>/
  protocol.md        the question, the criteria, and what "done" means
  queries.md         every query string, source, and date run
  raw/               API responses, unmodified
  screening.csv      every record, the stage it left at, and why
  evidence.csv         the included set, one row per paper
  unverified.md      the quarantine: what could not be resolved, and where it came from
  references.bib     for Zotero, Mendeley, JabRef, Paperpile, Citavi, RefWorks
  references.ris     alternative reference-manager import format
  README.md          counts at each stage
```

Dated and self-contained, so a search can be re-run later and the two compared.

## Report

One paragraph to the user:

- Run directory, absolute path.
- Counts: retrieved, deduplicated, screened, included.
- **How many records went to `unverified.md`, and whether any came from the model rather than an
  API.** Say this even when the count is zero; it is the number the researcher is being taught to
  look at.
- What the verifier found, including any retraction notices, researcher decisions, and outstanding checks.
- What needs a human: the borderline screening set, and any row whose `evidence` is `title`.

The default deliverable is the search record and evidence table. Provide a synthesis only if requested, grounded in the material actually read.

## Constraints

- The bundled helper and these instructions are self-contained; research inputs and project conventions come from the authorized task.
- Use sources and subscriptions the user is permitted to access. Do not assume institutional access or credentials exist. State gaps in coverage.
- No paywall circumvention. Record what could not be reached as unreachable.
- Put the optional address in the User-Agent header only on requests to the selected services. Keep it out of query URLs and saved search records. Back off on 429 responses.
- Saved screening counts alone do not establish PRISMA compliance or a systematic review. Describe the actual scope and limitations.

## Things to NOT do

- Do not write a citation you did not fetch.
- Do not fill an evidence-table cell from an abstract when the protocol says full text.
- Do not report a count you did not compute from the files in the run directory.
- Do not describe a paper you did not open. `evidence` distinguishes the levels; keep it honest.
- Do not pool effect sizes, compute a summary estimate, or produce a forest plot. Different job,
  different skill, different expertise.
- Do not delete `unverified.md` when it is empty. An empty quarantine is a result.
