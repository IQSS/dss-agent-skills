---
name: targets
description: "Build, run, inspect, and revise R pipelines with targets, including cached outputs, explicit file dependencies, dynamic branching, and optional crew workers. Use when analyses need repeatable stages that rebuild when their dependencies change."
compatibility: "Requires R and targets; crew is optional for parallel workers. Use the project's package environment and command runner. Long runs need a supported durable scheduler; pueue is one local option."
---

# Maintain a targets pipeline

Preserve the project's scientific specification, paths, and environment. Discover its existing manifest and helper functions before adding a new pipeline. `_targets.R` and `_targets/` are the default manifest and cache locations, but targets supports other configured locations.

## Define runnable stages

Each target should perform a coherent operation with explicit dependencies and a saved return value. Helpers belong in the project's existing code directory; no particular `_startup/` layout is required. Track input files with `format = "file"`, then refer to that file target in the consuming target.

This minimal example assumes a CSV with `outcome` and `exposure` columns. The formula illustrates dependency tracking, not a prescribed scientific method:

```r
library(targets)

tar_option_set(format = "rds")

list(
  tar_target(input_file, "data/observations.csv", format = "file"),
  tar_target(observations, read.csv(input_file)),
  tar_target(fit, lm(outcome ~ exposure, data = observations)),
  tar_target(coefficients, coef(fit))
)
```

Run from the documented project root or use the project's established root-resolution method. Replace the inputs, transformations, method, and outputs with the approved analysis. A configuration file that changes the computation should be a tracked input too. Declaring a file target is not enough: downstream code must reference it and read its actual contents.

Keep manifest evaluation cheap. Define or source helper functions at the top, but put expensive data loading and fitting inside targets. Declare needed worker packages with `tar_option_set(packages = ...)`. For large objects, consider `memory = "transient"` and `garbage_collection = TRUE`, then check their effect on the actual workload.

## Run and inspect

Use the project's command surface if it has one. An example `justfile` can provide:

```just
default:
    @just --list

analysis:
    Rscript -e 'targets::tar_make()'

status:
    Rscript -e 'targets::tar_outdated()'

manifest:
    Rscript -e 'targets::tar_manifest()'
```

These commands assume ordinary Rscript execution works on the host. If the project requires a pseudo-terminal or another runtime wrapper, use that wrapper in the recipes. In environments where detached R subprocesses hang, use the documented foreground route with `callr_function = NULL` and no crew controller until a small test establishes that workers operate correctly. Do not bypass agent permissions to make the example run.

First run a small representative pipeline in the foreground. For a long run, submit the tested command to the approved scheduler; with pueue, for example, `pueue add --print-task-id -- just analysis`. Save its ID and verify status, logs, and expected outputs. Queue success and scientific validity are separate checks.

Useful R inspection functions:

```r
targets::tar_manifest()                 # declared stages and commands
targets::tar_outdated()                 # stages considered out of date
targets::tar_progress()                 # stage progress
targets::tar_meta(fields = c(error, warnings))
targets::tar_read(coefficients)         # retrieve a saved value
targets::tar_load(coefficients)         # load a saved value into the session
```

Do not query or mutate the live store from a target that is currently executing. Use the supported monitoring interface from outside the computation.

## Add parallelism only when useful

Independent targets can run in separate `crew` workers. Start conservatively and make the worker count configurable:

```r
workers <- as.integer(Sys.getenv("CREW_WORKERS", unset = "1"))
stopifnot(length(workers) == 1L, !is.na(workers), workers >= 1L)
tar_option_set(
  controller = crew::crew_controller_local(workers = workers)
)
```

Budget both CPU and memory. Worker count times each fit's concurrent chains/threads should fit within the resources allocated to the project, leaving room for other work. Stan sampling is often CPU-intensive; do not assume that oversubscribing workers is inexpensive. Benchmark a small set before scaling up, including worker startup and peak memory.

One target that loops over 200 fits remains one target. Use dynamic branching, such as `pattern = map(specifications)`, or appropriate static branches when the fits should be independently scheduled and cached. The branch input should identify the scenario and seed so completed results can be reconciled after interruption.

## Diagnose unexpected reruns

Check changed input contents, function definitions, target commands, globals, package versions, and execution settings. A source file's modification time alone does not prove the computation changed. Targets tracks relevant code and object hashes; downstream stages can remain current when a rebuilt target returns an unchanged value.

If a target needs a deliberate rerun, use a named-target operation:

```r
targets::tar_invalidate(names = tidyselect::all_of("fit"))
```

This removes metadata for the selected target and forces it to rerun next time. Its saved files remain, but normal reads are unavailable until the metadata is rebuilt. `tar_destroy()` operates on parts of the data store, not named targets; do not use it as routine invalidation. Whole-store destruction needs an explicit reason and authorization. See [tar_invalidate](https://docs.ropensci.org/targets/reference/tar_invalidate.html) and [tar_destroy](https://docs.ropensci.org/targets/reference/tar_destroy.html).

## Preserve recoverability

Keep the cache out of Git. If the project is cloud-synced, use the service's supported exclusion mechanism before populating a new cache, or place it outside the synced tree. For Dropbox on macOS, apply and verify `com.dropbox.ignored` on the empty cache directory first. Do not apply that platform-specific command on other systems or retrofit exclusions onto a populated synchronized cache without a recovery plan.

On restart, targets reuses completed, up-to-date targets. An unfinished fit generally starts again unless its fitting software supports checkpoints. For long simulations, save independently completed repetitions as branches or outputs and document what can resume. Test recovery on a small interrupted run before relying on it for expensive work.

Report what changed, what was executed, which outputs were checked, and remaining limitations. Do not infer methodological correctness from a pipeline completing. The [targets manual](https://books.ropensci.org/targets/) documents branching, storage, and supported execution modes.
