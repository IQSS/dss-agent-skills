# Example: a research paper project

Adapt this layout to the study, language, and research group's conventions. It does not prescribe a statistical method. Shared file purposes and environment rules are in `example-shared.md`.

```text
paper-project/
├── CLAUDE.md
├── STATUS.md
├── TASKS.md
├── README.md
├── SPECIFICATION.md
├── METHODOLOGY.md
├── code/
│   ├── _startup/          # Shared setup/helpers, if needed
│   ├── _experiments/      # Investigations separate from the main analysis
│   ├── _data-acquisition/
│   ├── _final/            # Assemble figures and tables from saved results
│   └── _report/           # Working report
├── data/
│   ├── raw/
│   └── processed/
├── outputs/
│   ├── eda/
│   ├── figures/
│   │   ├── working/
│   │   └── final/
│   ├── models/
│   ├── results/
│   └── tables/
├── manuscript/
├── archive/               # Prepared reproduction bundles
├── dags/                  # Only if causal graphs are used
└── docs/
    ├── briefs/
    ├── responses/
    ├── findings/
    ├── notes/
    └── references/
```

Create only the subdirectories the selected scaffold needs. Add the chosen command runner and dependency manifests. For R, a `.here` marker and `renv.lock` serve different purposes: root resolution and package versions. An RStudio `.Rproj` file is useful only if that editor is used. For targets, `_targets.R` is the default pipeline entry point; keep its cache outside Git and configure sync exclusions before it is populated.

## Scientific specification and decision log

`SPECIFICATION.md` gives current approved scientific requirements. Populate it from the researcher's decisions, with unresolved choices clearly marked:

```markdown
# Research specification

Last updated: YYYY-MM-DD
Status: Draft — unresolved choices are listed below.

## Research question and objectives

## Population, sample, and inputs

## Quantities to estimate or evidence to assess

## Methods, assumptions, and uncertainty

## Required checks and tolerances

## Outputs to produce

## Unresolved decisions
```

Adapt the headings for qualitative or theoretical work. Rewrite this file when approved requirements change; preserve earlier versions in version control. Link to frozen preregistrations or protocols rather than overwriting them.

`METHODOLOGY.md` records decisions and reasons, with newest entries first:

```markdown
# Methodological decisions

Current requirements are in SPECIFICATION.md.

## YYYY-MM-DD — Decision title

Decision: What was approved.
Reason: Why, including relevant evidence and alternatives.
Specification update: Which requirement changed.
```

Start with “No decisions recorded yet” if none were supplied. Tell the agent to read the specification before implementing/checking an analysis, consult the log for rationale, and update both when an approved scientific change occurs. Execution tasks belong in `TASKS.md`.

## Runnable analysis and saved outputs

Keep analysis stages independently runnable with explicit inputs. Shared setup can live in `_startup/`, but do not create empty source files that claim to implement a workflow. A real `init.R` should source only existing files, in dependency order. Avoid loading datasets into every session when only some stages need them.

Save fitted objects separately from the smaller tables, contrasts, and figure inputs used by reporting code. Reporting should read those outputs rather than silently refit. Use consistent output names and document the input/output relationships. Record seeds and software versions where reproducibility depends on them.

For long fits, record failures clearly and write success markers only after required outputs exist. Set worker counts and sampling effort from the method, diagnostics, and available resources, not fixed counts copied from another paper. Test recovery: completed targets can be reused, whereas restarting an unfinished fit requires support from its fitting software.

If using DAGs, retain editable graph sources and a description of their variables, focal causal questions, and chosen adjustment sets. Measurement proxies and alternative structural assumptions need explicit explanation. A directory name does not establish causal validity.

## Manuscripts and archives

Keep working drafts separate from submission snapshots. Build each reproduction bundle from the code, permitted inputs, specification, software records, and expected outputs used for that result. An `archive/` folder may contain work in preparation; a version actually deposited or otherwise frozen should receive a new version for a correction.

Decide which outputs are canonical deliverables and which can be rebuilt. Large models and caches are usually ignored; exact submitted tables and figures may be versioned. Data sharing follows the study's access conditions, independently of Git ignore rules.
