---
name: review-analysis
description: "Review research analysis code against its scientific specification, checking statistical correctness, relevant identification assumptions, diagnostics, and reproducibility. Use for a script, analysis directory, or whole project. Produces findings without changing the analysis; not a substitute for running or independently reimplementing it."
compatibility: "Requires file access and an agent capable of launching a fresh reviewer with controlled context. Reviews R/brms and frequentist analyses; other languages require equivalent subject expertise. No analysis execution or package installation is required for the static review."
---

# Review an analysis

Find consequential errors in an implemented analysis and explain how each affects the research question. Review the analysis the researcher prescribed; flag methodological concerns separately from implementation mismatches.

## Establish the review context

Accept a script, directory, or project path, plus optional `conventions=<path>` and `out=<path>`. With no target, use the current project. Confirm the project root from the supplied path, repository root, or project documentation; do not require a particular directory tree or filename. If several projects or targets are plausible, ask which to review.

Read the applicable project instructions (`CLAUDE.md`, `AGENTS.md`, or the app's equivalent), the scientific specification (`SPECIFICATION.md` if present), relevant decisions (`METHODOLOGY.md` if present), and the supplied conventions. Equivalent files are fine. If the requirements are missing, record that limitation and identify what can still be checked; do not invent a specification.

Use `references/default-standards.md` for the checks relevant to this analysis. Project conventions govern names, folders, formatting, and defaults. Do not fault work for differing from the reviewer's personal setup.

## Use a fresh reviewer

Have a fresh reviewer carry out the assessment, with the target, requirements, and conventions but without the invoking agent's opinions. Use the host's supported subagent mechanism with conversation inheritance disabled where possible. A separately launched headless agent is an alternative when authorized and available. State the actual isolation achieved; a different agent name alone does not establish independence. If fresh-review capability is unavailable, report that limitation rather than claiming an independent review.

The invoking agent relays the review. The reviewer reads the necessary code and saved evidence and writes one integrated brief. This skill authorizes a static review, not execution of the analysis or edits to its scientific requirements.

## Inspect the implementation

Trace the selected analysis through the inputs and helper functions it actually uses. Inspect saved diagnostic summaries and reported results when available. For a whole-project review, map the analysis stages and their dependencies before examining individual scripts. Avoid loading unrelated confidential material.

### Statistical correctness

- Check the outcome support, distribution, link, parameter scales, transformations, and missing-data handling against the scientific objective.
- Verify that contrasts, standardization, averaging samples, weights, and uncertainty calculations estimate the requested quantity. A coefficient need not equal the reported marginal effect.
- Check factor reference levels, units, predictor scaling, and grouping identifiers. Nested groups can be represented with nested syntax or globally unique group identifiers; inspect the data design rather than judging syntax alone.
- For Bayesian analyses, assess priors on the scales used by the model and examine saved prior-predictive evidence. Do not impose a fixed prior or sampling schedule across projects.

For a concrete scale check, in `brms::lognormal(link="identity")`, mu is the location of **log(y)** and the linear predictor equals mu. The conditional median is `exp(mu)` and the conditional mean is `exp(mu + sigma^2 / 2)`. `expm1(mu_hi - mu_lo)` gives the relative change in conditional medians; it also gives the relative change in conditional means when sigma is unchanged. Marginalizing over observations or random effects requires the corresponding predictions and averaging. Distinguish these quantities before recommending a correction. See the [brms parameterization reference](https://paulbuerkner.com/brms/articles/brms_families.html).

### Identification, when the analysis makes causal claims

- Examine the identification strategy whether or not a DAG file exists. Check whether the implementation and data support the stated assumptions.
- If a DAG supplies an adjustment set, compare the implemented set with the justified set and any saved derivation. Several sufficient sets may exist; an extra covariate is not automatically biasing. Inspect mediators, colliders, measurement proxies, and selection mechanisms in context.
- Effect modification is a scientific/modeling commitment; graph topology alone does not prescribe interaction terms.
- Distinguish planned sensitivity analyses from unexplained departures after results were seen. Treat unresolved identifying assumptions as questions, not established facts.

This is a read-only assessment. If a graph calculation or numerical check is needed to settle a finding, name that check as outstanding rather than claiming it was run.

### Diagnostics and precision

- For MCMC, inspect convergence, effective sample sizes, Monte Carlo error, and sampler warnings for quantities supporting the conclusions. Low R-hat alone does not establish adequate exploration. Investigate divergent transitions and insufficient precision; longer chains cannot fix every geometry problem.
- Examine whether predictive/residual checks were interpreted, rather than merely generated. Match diagnostics to the family and dependence structure.
- For frequentist analyses, check the relevant fit, uncertainty, and model-assumption diagnostics. Do not demand Bayesian diagnostics from a frequentist fit.
- Where simulated scenarios were used, check that the saved truth, performance criteria, and summaries support the reported conclusions. Separate code agreement from methodological adequacy.

### Code and reproducibility

- Trace inputs, transformations, models, and reported values through saved files. Flag hidden session state, unintended overwrites, missing dependencies, and inconsistent units or samples.
- Check recorded software versions, random-number settings, parallel RNG handling, and the documented commands. Use each library's supported seed mechanism; a saved seed does not guarantee identical results across software changes.
- Apply documented naming and output conventions only where they matter. Do not require a particular bootstrap filename, script header, model-object name, or folder layout.
- Distinguish a working archive directory from a version actually deposited or frozen. Published snapshots need versioned corrections; an unfrozen folder is not immutable solely because its name contains `archive`.

## Write and report the findings

Use `out=` if supplied; otherwise use the project's review-output convention, falling back to `docs/briefs/<date>-review-<scope>.md` or a clearly named file in the project root. Preserve existing reviews with a new filename unless overwriting was authorized.

Include the scope, requirements consulted, review isolation, and limitations. For each finding, give a file/line or section, the evidence, its consequence, and a proposed correction or question. Classify as:

- `must-fix`: a demonstrated error or contradiction that materially affects the result.
- `should-fix`: a consequential gap or reproducibility problem.
- `consider`: a justified alternative, distinct from a correctness requirement.
- `question`: something the available material cannot settle.

Tag findings `[stat]`, `[causal]`, `[diag]`, `[code]`, or `[repro]` as useful. State which important checks produced no finding. Do not manufacture issues to make the review look thorough, or equate an unexecuted static review with verified correctness.

Report the brief's path, counts by severity, and the most consequential finding. Leave the analysis, specification, and decisions unchanged.
