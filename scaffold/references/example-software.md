# Example: a software operations project

Use this example for product operations when application code has its own repository. For the application itself, follow the framework's scaffold rather than this layout. Shared context-file guidance is in `example-shared.md`.

```text
product-operations/
├── CLAUDE.md
├── STATUS.md
├── TASKS.md
├── README.md
├── docs/
│   ├── notes/
│   ├── briefs/
│   └── plans/
├── assets/
├── outputs/
├── data/
└── scripts/
```

Keep runbooks and decisions in `docs/`, reusable source material in `assets/`, and delivered artifacts in named `outputs/` subdirectories. System exports may contain personal or confidential data; ignore them and establish approved storage before collection.

Track code bugs and features in the application repository's issue system; operational work belongs in this project's tracker. Link related items rather than maintaining contradictory copies. Document the authorized application repositories and environments. A scaffold grants no authority to change a live service.

Use the team's actual credential and deployment tools when an operation requires them. Do not assume a password manager or a standing environment. Remote creation, production access, and deployment remain separate explicit operations.
