---
name: scaffold
description: "Create or adapt a project scaffold from a supplied template or bundled examples for paper, data, publishing, consulting, review, software, ops, and minimal projects. Use when setting up a project folder and its context files, environment, and runnable commands. Preserve existing files and project conventions."
compatibility: "Uses filesystem tools; Git only when repository setup is requested. Runtime setup depends on the chosen project: for example uv for Python, renv for R, or the framework's own tools. Credentials, cloud-sync settings, and remotes are configured only when needed and authorized."
---

# Scaffold a project

Build a useful starting structure without assuming the researcher's computer, accounts, or folder conventions. Accept a target directory, project purpose, and optional `shape=<name>`, `templates=<dir>`, or `conventions=<path>`. Default to the current directory only when that is clearly the intended project.

## Choose the template

Use an explicitly supplied template first. Otherwise inspect the project's documented conventions and any template directory the user identified. Do not search unrelated parent directories or global configuration for private templates. If no template is supplied, select a bundled example from the purpose of the project and state that choice. The parent folder name alone does not determine a project's purpose.

The bundled `references/example-<shape>.md` files are examples to adapt, not required layouts:

- `example-paper.md`: research leading to a paper, including the scientific specification and decision log.
- `example-data.md`: collection, transformation, and documented data outputs.
- `example-publishing.md`: documents, guides, reports, and slide decks.
- `example-consulting.md`: client work with distinct working files and delivered copies.
- `example-review.md`: confidential review material and review reports.
- `example-software.md`: software-product operations when application code lives elsewhere.
- `example-ops.md`: ongoing coordination or oversight of a program.
- `example-minimal.md`: a small project or a framework with its own layout.

Read only the chosen shape and `references/example-shared.md`. Resolve these paths relative to this skill. If a supplied template directory lacks the selected shape, ask for a suitable template rather than silently replacing the user's choice.

## Inspect before creating

Identify the intended root, existing files, project instructions, version-control state, and any framework scaffold. Describe the intended additions briefly. Preserve useful organization; an existing Git repository is not a reason to reject the task. Ask about genuinely ambiguous destinations or conflicts before moving, renaming, or overwriting existing files. An empty-folder scaffold already requested by the user does not need another blanket confirmation.

Do not read or print credential values to determine the project layout. If the purpose or language is unknown, create only the agreed minimal structure and leave the unresolved choice explicit.

## Create the selected structure

Create the selected folders and starting files. Use the user's names and conventions; the bundled examples use lowercase kebab-case for flexible names and conventional names for tool-parsed files. Keep empty tracked folders with `.gitkeep` only when they are useful; ignored caches need no placeholder.

Create the app-appropriate project instruction file. For Claude Code that can be `CLAUDE.md`; other tools may read `AGENTS.md`. If several tools will be used, maintain one source and configure the other to read it, using a supported import or symlink where appropriate. Do not create two independently edited instruction copies or assume symlinks work on every platform.

Use the selected template for status, tasks, and documentation. For paper projects, preserve the distinction:

- `SPECIFICATION.md` states current approved scientific requirements and is rewritten when those requirements change.
- `METHODOLOGY.md` is a dated decision log, newest entries first, explaining what changed and why.

Populate scientific content from the researcher's decisions. Do not choose an estimator or invent prior decisions just to fill a template. The project instructions should tell the agent which files to consult and maintain.

## Set up only the required environment

Use the project's chosen runtime manager. For a new Python project using uv, create its manifest and lockfile and add only known dependencies. For an R project using renv, initialize and record the project environment when R setup is within scope; a `.here` root marker does not replace a package lockfile. Adapt the commands to the host and honor any required runtime wrapper.

Before populating caches or environments in a cloud-synced location, establish the supported exclusion mechanism or place those directories outside the synced tree. For Dropbox on macOS, an empty directory can be marked with `xattr -w com.dropbox.ignored 1 <directory>` and the attribute verified before population. The command is platform-specific; do not assume it works for another sync client. Do not retrofit exclusions onto a populated directory without a recovery plan. Use normal agent permission requests for any necessary system operation; no permission rules are implied by this skill.

Create a command surface suited to the selected project, such as a `justfile` for a small analysis or the existing framework's commands. Do not create recipes that claim to run analyses that have not been implemented.

## Credentials and external services

Most scaffolds need no credentials. R/renv alone does not require a GitHub token; private packages or service requests may. Git and GitHub CLI authentication should use the user's existing configuration.

When project code needs a credential, identify the variable and approved retrieval method without fetching its value into conversation. Do not assume a secrets manager, vault, item name, account, or shell alias exists. An example configuration should contain placeholders, not secret values or private store paths. Ignore local secret files. If using direnv, inspect the actual `.envrc` before authorizing its execution; follow the user's existing authorization rather than treating `direnv allow` as an unconditional scaffold step.

Project API calls and the interactive agent's authentication are different concerns. Add provider credentials only for the project's actual runtime needs. Avoid changing how the user's agent authenticates merely by entering this project.

## Check and hand off

Check that generated references resolve, declared commands have the required inputs, and ignored/private files will not be staged. Run an appropriate small setup check using synthetic or permitted data. State which checks could not run because a dependency or research decision is outstanding.

Create an initial commit or remote only when requested or included in the user's authorized setup. Stage explicit reviewed paths and inspect the staged diff. Do not push or publish as an incidental consequence of scaffolding.

Report the target folder, template used, meaningful deviations, checks performed, and next research decisions. Leave no dependencies on the skill's installed path in generated project files; copy necessary template content or link to public documentation instead.
