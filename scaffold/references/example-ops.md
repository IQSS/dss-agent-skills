# Example: ongoing operations

For coordinating a program, service, or group of projects. Use the team's existing task system rather than installing a particular tracker. Shared context-file guidance is in `example-shared.md`.

```text
program-operations/
├── CLAUDE.md
├── STATUS.md
├── TASKS.md
├── README.md
├── projects/
│   └── registry.yml
├── data/
└── outputs/
    └── dashboard/
```

For oversight of several projects, a registry can record names, owners, approved paths, and access scope. It is a roster, not a second task database. Keep each commitment in one authoritative tracker and derive summaries or dashboards from it.

Limit cross-project reading to the authorized sources. A symlink is a navigation convenience, not an access-control boundary. Use actual filesystem/tool permissions where enforcement is needed; do not automatically change those permissions during scaffolding.

Only add collection scripts, environment variables, or dashboard build commands if the workflow needs them. Save external feed snapshots with provenance and relevant access restrictions. Do not create credentials or connect external services as an incidental setup step.
