# Example: a confidential review project

For reviewing an unpublished manuscript or proposal. Confirm that the material may be processed by the selected agent and stored in the intended locations before opening confidential inputs. Institutional approval alone may not satisfy a venue's review policy. Shared file guidance is in `example-shared.md`.

```text
review-project/
├── CLAUDE.md
├── STATUS.md
├── TASKS.md
├── README.md
├── manuscript/
│   └── round-1/
├── review/
│   └── round-1.md
├── notes/
├── reproduction/
│   ├── code/
│   ├── authors-materials/
│   └── README.md
└── output/
```

Ignore confidential source material before staging anything. Git ignore rules prevent accidental commits; they do not prevent an agent from transmitting text to its provider or a synchronization service from storing it. Apply the venue's actual conditions to manuscripts, notes, and reports. Do not assume that derived material may be pushed to a private remote.

Keep each review round and author response identifiable. An example report structure is: summary, assessment against the criteria, major points, minor points, recommendation, and confidential comments to the editor. Follow the venue's recommendation scale.

Use `reproduction/` when an authorized computational check is needed. Record whether it reruns supplied code or independently implements the specification, and pin its software environment. Creating a scaffold does not authorize executing untrusted supplied scripts.

The report can use the publishing example's build tools, but only if needed. Preserve submitted review versions and archive them to an approved destination. No remote or credentials are assumed.
