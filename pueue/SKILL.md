---
name: pueue
description: "Submit and monitor long-running commands with the local pueue job queue. Use when a task should outlive the agent session or when independent jobs need bounded concurrency. Verify actual task outcomes and preserve the IDs needed to inspect or resume work."
compatibility: "Requires pueue, a reachable pueued daemon, and jq for the illustrated status checks. Commands must use the project's own runtime/environment. Examples use pueue 4.x; inspect installed command help when options differ."
---

# Queue and monitor work

Use pueue for commands that need a durable queue; short checks can run in the foreground. For a dependency-aware R pipeline, pueue can host the outer command while `targets` manages its stages. Use the project's existing scheduler on a cluster rather than installing a competing local queue.

## Check access and execution first

1. Check `pueue --version` and `pueue status`. Do not assume a daemon is already running or that its socket has a particular path.
2. If connection fails, distinguish missing software, a stopped daemon, configuration mismatch, and denied access. Consult the installed help and platform setup. Request only the access or setup needed, through the host agent's normal permission mechanism. Do not disable sandboxing or rewrite global permissions as a default.
3. Identify the project's working directory, command, environment, expected outputs, and resource limits. Prefer an existing recipe such as `just analysis` or the project's language-native runner. Check that the queue's execution environment can find it; the daemon may not inherit the interactive shell's aliases or credentials.
4. Smoke-test a new workflow with a small input in the foreground before queueing expensive work. Use any project-required runtime wrapper, including a pseudo-terminal wrapper if the installed R environment requires one.

Pueue launches commands through a daemon with its own access. Permission to contact it does not authorize arbitrary jobs. Keep credentials out of saved command strings and logs; use the project's approved runtime credential mechanism.

## Submit the project command

From the project root, for a project with an `analysis` recipe:

```sh
pueue add --print-task-id -- just analysis
```

Record the returned task ID, working directory, command, and expected output in the project's task record. Use the numeric ID in later commands. If the project uses another runner, submit that command instead; do not assume `just` or a particular recipe already exists.

For a command with complicated shell quoting, use an existing script or recipe rather than embedding layers of quoted code. When necessary, add a small project-local wrapper with an explicit working directory and failure exit status. Do not depend on interactive aliases.

## Verify progress and completion

After submission, inspect the specific task's status and initial log. Report `queued`, `running`, `failed`, or `completed` from evidence. A returned ID proves submission, not progress. For expensive runs, confirm fresh log output or the expected early artifact before describing the calculation as healthy.

```sh
pueue status --json
pueue log <task-id> --lines 40
pueue wait <task-id>
```

Replace placeholders with the actual ID. `pueue wait` blocks: use it through the host's supported background/wait facility when a foreground wait would prevent conversation. If that facility is unavailable, retain the ID and explicitly recheck; do not promise a completion notification the host cannot provide.

In pueue 4.0.4, the wait command's exit status does not distinguish successful from failed jobs. Check the task record instead:

```sh
pueue status --json | jq -e --arg id '<task-id>' '.tasks[$id].status.Done.result == "Success"'
```

In this schema, queued/running statuses differ from `Done`; a completed result is `"Success"`, `{"Failed": <code>}`, or `"DependencyFailed"`. A missing task record is unresolved, not success. Check the expected artifact too: the program might exit successfully without producing the required result.

## Dependencies and concurrency

Use `pueue add --after <task-id> -- <command>` when one queued command depends on another. For bounded concurrency, create a project-specific group if needed and set its limit before adding work:

```sh
pueue group add project-fits
pueue parallel --group project-fits 2
pueue add --group project-fits -- just fit-a
pueue add --group project-fits -- just fit-b
```

Adapt group and recipe names to the project. Groups set concurrency; they do not by themselves impose dependencies between groups. Account for each job's own threads and memory, including any workers launched by `targets` or model-fitting software.

## Recovery and task records

Pueue preserves queue state and logs across agent sessions while the daemon remains available. It does not checkpoint a calculation or keep a sleeping computer computing. Restarting a failed command may repeat side effects. Inspect logs and saved outputs before restarting, and use supported checkpoints or completed pipeline stages where available.

Keep completed records until their result and diagnostic information have been recorded. If cleanup is requested, remove only the relevant task IDs with `pueue remove <task-id>`. Do not run a global `pueue clean` as routine project cleanup; it may remove other projects' records. Stop or restart only the jobs within the authorized scope.

See the [pueue documentation](https://github.com/Nukesor/pueue) for platform-specific setup and current command options. If pueue is unavailable, report that and use an already-approved scheduler or agree on setup; do not silently replace durable queueing with an unmonitored detached process.
