# Example: a data project

For collecting, documenting, transforming, and distributing data. Adapt this example to the user's workflow; shared context-file and environment guidance is in `example-shared.md`.

```text
data-project/
├── CLAUDE.md
├── STATUS.md
├── TASKS.md
├── README.md
├── scripts/
├── data/
│   ├── sources/
│   ├── processed/
│   ├── checkpoints/
│   └── validation/
├── outputs/
│   ├── eda/
│   ├── figures/
│   ├── reports/
│   └── tables/
└── docs/
    ├── briefs/
    ├── findings/
    └── notes/
```

Separate collection from parsing so a parsing correction need not recollect the source. Preserve raw responses, queries, dates, and source identifiers. Choose permitted APIs or structured downloads before browser-based collection. Honor service limits, use retry/backoff for transient failures, and distinguish an empty result from a failed request.

For long collection runs, save completed batches and a checkpoint that identifies what remains. Test restart behavior for missing or duplicated records. Log progress and failures without exposing credentials or confidential data.

Numbered scripts can express execution order; a dependency runner is useful for more complex relationships. Keep Python module filenames compatible with imports. Validate schemas, keys, ranges, and coverage against the source documentation rather than assuming every dataset follows one schema.

Use the chosen language's pinned environment. For Python, uv is one option; a conda-based manager may suit compiled dependencies. Install only packages the project actually uses. If a dashboard is needed, keep its templates separate from generated `site/` output and provide a documented build command.

Add service credentials only when the requested sources need them, using the user's approved mechanism. A public API may work without a token; do not create a GitHub token solely because this is a data project. Record data access and redistribution conditions in the README.
