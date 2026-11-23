# DSS agent skills

Reusable skills for researchers working with AI coding agents. Each skill supplies instructions and, where useful, a helper script or template. The agent applies them to your project; you supply the research decisions and permitted access.

Browse the [skill library](https://iqss.github.io/dss-agent-skills/) by task, preview each procedure, and download individual skills or the full collection. Each skill page provides examples and requirements.

## Skills

| Skill | Purpose | Main requirements |
|---|---|---|
| [dag](dag/) | Draw a causal diagram and check possible adjustment sets. | R with dagitty; XeLaTeX/TikZ; a PDF image viewer or rasterizer. |
| [eda](eda/) | Create an exploratory report for a dataset. | R, Quarto, and the packages listed in the supplied template; XeLaTeX for PDF. |
| [litsearch](litsearch/) | Save a literature search, screening decisions, evidence table, and checked bibliography. | Python 3.9+ and access to the selected literature services. |
| [pueue](pueue/) | Queue long commands and verify their progress and results. | Pueue client and daemon; jq for the illustrated status queries. |
| [review-analysis](review-analysis/) | Review an existing analysis against its scientific requirements. | Access to the analysis and specification; a separate reviewer session for an independent review. |
| [review-plan](review-plan/) | Identify gaps and risks in a proposed project or analysis. | Access to the plan; a separate reviewer session for an independent review. |
| [review-prose](review-prose/) | Find unclear phrasing and propose revisions in context. | Python 3.9+ for the bundled detector. |
| [scaffold](scaffold/) | Create or adapt a project layout and its context files. | Tools appropriate to the selected project; Git only when version control is requested. |
| [targets](targets/) | Build, run, and diagnose a reproducible R pipeline. | R with targets; crew for parallel workers; just or Pueue only when appropriate. |

Each `SKILL.md` explains its requirements. The skills use the project's supplied conventions and authorized resources. Bundled layouts are examples to adapt; no private accounts, aliases, global instruction files, or credential stores are required.

## Install in Claude Code

Add the marketplace and open the plugin's installation panel:

```text
/plugin marketplace add IQSS/dss-agent-skills
/plugin install dss-agent-skills@dss-agent-skills
```

Invoke a skill with its plugin namespace, for example:

```text
/dss-agent-skills:litsearch <research question>
```

Adding a marketplace alone does not install its plugin. See the [Claude Code marketplace documentation](https://code.claude.com/docs/en/plugin-marketplaces).

Choose an installation scope in the panel and follow any reload instructions shown by your app.

## Use with other agents

The directories follow the [Agent Skills format](https://agentskills.io/specification). Copy a selected skill directory, including its supporting files, to a location your agent supports. Directory discovery, invocation names, and separate-session capabilities depend on the host. A valid `SKILL.md` does not guarantee that every host supplies every capability.

Review a skill before installing it. It does not grant access or install its dependencies automatically.

## Contribute and check

Skills are maintained through pull requests. Start revisions from the latest repository version so they preserve other contributors' work. See [CONTRIBUTING.md](CONTRIBUTING.md).

Run `just check` with Python, uv, and just installed to validate the skills and run the helper tests. Python dependencies are pinned in `uv.lock`. With Quarto installed, `just site` builds and checks the catalogue; `just preview` serves a local preview.

These checks do not establish scientific validity or prove that a skill works with every research dataset, software installation, or agent host. Rendering, queue execution, and statistical workflows also need task-specific checks in the environment where they will run.
