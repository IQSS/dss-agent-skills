# Example: a consulting project

For receiving client data, analyzing it, and delivering advice or artifacts. Use `example-shared.md` for context files and environment setup.

```text
client-project/
├── CLAUDE.md
├── STATUS.md
├── TASKS.md
├── README.md
├── data/
├── code/
├── outputs/
│   ├── eda/
│   ├── figures/
│   ├── models/
│   ├── results/
│   └── tables/
├── deliverables/
└── docs/
    ├── briefs/
    ├── responses/
    └── notes/
```

Document the client question, authorized data access, and scope. Use a scientific specification and decision log when the analysis needs them, adapting the paper example. Keep working analysis outputs separate from delivered copies.

Each delivered bundle can live in `deliverables/<date>-<topic>/`, paired with the relevant correspondence. Preserve it after delivery; revisions get another dated copy. Label cleanup or format conversion for the client should be reproducible from the working source. Do not send files merely because a deliverable directory exists.

Use the analysis language's pinned environment and a documented command surface. Confidential inputs and reports need approved storage and sharing; a private GitHub repository is not automatically permitted. Add credentials only for services the engagement actually uses. Archive to the team's chosen destination when the engagement closes.
