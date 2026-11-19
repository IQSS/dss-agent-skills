# Shared conventions for the bundled examples

These examples offer a coherent starting layout. The user's supplied conventions take precedence. Read the selected shape file alongside this one; no files outside this skill are required.

## Project context files

The instruction filename is app-dependent. The trees show `CLAUDE.md`; use `AGENTS.md` or a maintained link/import when the installed tools require it. Keep instructions concise and specific to this project.

| File | Purpose |
|---|---|
| `CLAUDE.md` or `AGENTS.md` | How the agent should work in this project; which scientific requirements and records to read. |
| `STATUS.md` | Current state, rewritten in place. |
| `TASKS.md` | Outstanding work and completed tasks, with completion dates. |
| `README.md` | What the project does, required software, and how to run it. |

An example status file:

```markdown
# Status

Stage: scaffold created. Last updated: YYYY-MM-DD

## Headline

## Now

## Blocked / waiting on

## Standing facts

## Watch items
```

Fill the headings with known facts; do not invent activity. A task file can start with `To Do`, `In Progress`, and `Done` sections. Paper projects add the specification and methodological decision log described in `example-paper.md`.

Decide which context files are local maintainer notes and which are shared project documentation. Follow that project's publication policy. For a public project using local-only maintainer notes, ignore those files before staging anything. Instruction templates inside a distributed skill are distinct from the repository maintainer's own notes.

## Files, environments, and commands

- Use consistent names and project-relative paths. Conventional tool filenames retain their required spelling. Use a committed root marker such as `.here` for R if the chosen root-resolution method needs one; do not depend on an ignored instruction file to locate a public project.
- Keep original data unchanged; save derived data separately with the command that produced it.
- Commit runtime dependency manifests and lockfiles. Ignore environments, caches, logs, and local secret files. Decide whether exact delivered outputs need versioning separately from rebuildable intermediate output.
- Use a command runner the team can maintain. `just` is an example for research scripts; framework-native commands are appropriate where a framework already provides them.
- Configure cloud-sync exclusions before populating new environments or caches. Follow the actual platform's mechanism and the host agent's permission controls.
- Confirm small jobs before scaling up. Save outcomes, logs, and expected artifacts for long jobs, and document restart behavior.

## Credentials

Do not create `.envrc` or credential configuration by default. A project may need environment activation without secrets, or credentials for a specific service. Use the user's existing method and only the variables the project's code consumes. Examples must use placeholders; do not assume 1Password, gopass, GitHub CLI, or a private vault is installed or authenticated.

Never print a token to prove authentication. Check connection status or a permitted operation with output redacted. Keep credential values and private store paths out of commits and generated reports. Review a direnv file before allowing it to execute.

The interactive agent's account and the project's programmatic API access are separate. Do not configure one as a side effect of setting up the other.
