---
name: eda
description: "Create a first-look exploratory report for a CSV, TSV, Excel, or Parquet dataset using the bundled Quarto template. Use for distributions, missingness, data-quality checks, and optional outcome or group comparisons; not for post-model diagnostics."
compatibility: "Requires Quarto and R, with a LaTeX distribution providing XeLaTeX for the PDF output (MacTeX, TeX Live or TinyTeX). The report's R packages are listed in template.qmd; use the project’s existing package environment, including renv if configured."
---

# /eda

Render a self-contained exploratory PDF for a new dataset — typed against the use case of a consulting or collaboration intake where you've just received data and need to get oriented quickly.

## Source of truth

The report template lives at `template.qmd` and is the **single** source of truth for what an EDA report contains. This skill orchestrates how the template is invoked (shape-aware output placement, parameter wiring, render); it does not duplicate the template's content.

Where the rendered PDF lands is a default, set out in § 3 below, not a convention looked up elsewhere. `--out <dir>` overrides it.

## Workflow

### 1. Parse args

| Arg form | Meaning |
|---|---|
| (none) | Auto-detect the dataset. Search `data/processed/*.csv` first, then `data/raw/*.{csv,tsv,xlsx,parquet}`. If exactly one match, use it. If 0 or >1, prompt for the path. |
| `<path>` | Use the given path. Resolve relative to the project root (identified from the supplied path, repository, or project documentation) if not absolute. |
| `<path> outcome=<col> exposures=<col,col,...> grouping=<col,col,...>` | Layer optional focus params on top. These unlock the parameterized sections of the report. |

Respect the authorized data scope; an explicitly supplied external dataset need not be moved into a prescribed folder.

### 2. Detect project shape

Read the project's documented output conventions. Do not require a particular marker file, parent directory, or shape label. If no convention is recorded, use the defaults below and state that choice.

### 3. Pick the output location

| Shape | Output path |
|---|---|
| paper / data / consulting | `outputs/eda/<YYYY-MM-DD>-<data-stem>.pdf` |
| minimal | `./eda-<data-stem>.pdf` |

An existing output convention takes precedence over these defaults. If the project distinguishes working artefacts from things sent to a client, this is a **working**
artefact: an auto-generated first look belongs with the working output, not in whatever directory
holds copies that have actually been delivered.

Create the directory if needed. Use `<data-stem>` = basename of the data file without extension.

### 4. Inspect the dataset briefly

Before rendering, do a fast read of the dataset to:

1. Confirm it's readable and not empty.
2. Get the column count and types (so you can flag in the user message anything weird, e.g. "this is a 200-column file; the per-column section will be long").
3. If the user provided `outcome=`, `exposures=`, or `grouping=` params, verify those column names exist in the cleaned-names version (`janitor::clean_names()` is applied inside the report). If a named column doesn't exist, stop and ask the user to correct it.

Use the project's supported R invocation for the small input check. Do not print confidential rows when column names and summaries are sufficient.

### 5. Render

Locate `template.qmd` relative to this skill's installation, then copy it into a temporary directory within the approved project scope. Preserve the project's package-library activation when rendering from that directory; verify that Quarto uses the intended R environment. Use the project's runtime wrapper if noninteractive R requires one. Supply absolute paths and quote paths containing spaces:

```sh
quarto render <scratch>/template.qmd \
  -P "data_path:<abs-path-to-data>" \
  -P outcome:<col-or-null> \
  -P exposures:<comma-separated-or-null> \
  -P grouping:<comma-separated-or-null> \
  -P title:"EDA: <data-stem>" \
  --output <output-filename> \
  --output-dir "<absolute-output-dir>"
```

Then move the rendered PDF to the final output path picked in § 3 if `--output` placement doesn't land it there directly.

If rendering fails, inspect the Quarto output and report the cause. The template lists missing R packages; add them through the project's existing package-management method when authorized, record their versions, and rerun. Other common causes are an unreadable data file or a parameter naming a nonexistent column. Do not print sensitive data from an error log.

### 6. Report

Output one paragraph:

- Absolute path of the rendered PDF.
- Dataset stem + dims (rows × cols).
- Which optional sections were included (baseline always; outcome / exposures / grouping if params were supplied).
- One-line pointer to next step: "rerun with `/eda <path> outcome=<col>` to focus the report on that outcome."

Do **not** dump the PDF contents or list every section header — the user can open the file.

## What the report covers

See `template.qmd` for the authoritative list. At a high level:

**Always-on:**
- Dataset overview (rows, cols, source path)
- Per-column profile table (type, n distinct, % missing, summary stats or top levels)
- Variable type heatmap (`visdat::vis_dat`)
- Missingness by variable and pattern map (`naniar::gg_miss_var`, `vis_miss`, `gg_miss_upset`)
- Univariate distributions (histograms for numeric, bar charts for categorical with top-20 cap)
- Spearman correlation matrix (`corrplot`)
- Outlier scan (faceted boxplots)
- Pairwise structure for top 6 numeric variables (`GGally::ggpairs`)
- Data-quality flags (constant columns, suspiciously high-cardinality categoricals)

The variable-type and missingness heatmaps show all rows up to 800,000 cells (rows × columns). Above that limit, both use the same reproducible random sample, keeping all columns and as many whole rows as fit. With 20 columns, each heatmap can show 40,000 rows. With 40 columns, it can show 20,000. Each heatmap states how many rows it shows. Use the full-data missingness chart for rates, including missing values too rare to appear in the sample. Counts, summaries, and group comparisons use the whole dataset.

**Parameterized (only if param supplied):**
- `outcome=<col>` shows the outcome distribution. For a categorical outcome, add `grouping=` to compare it within each named group. For example, `outcome=employment_status grouping=region` shows the share in each employment category within each region. Text, factors, logical values, and numeric outcomes coded 0/1 are treated as categorical. Other numeric outcomes retain the histogram and boxplot by the first group.
- `exposures=<col,col,...>` plots each exposure against the outcome. For a categorical outcome, point size shows how many observations share each combination. For a continuous outcome, the scatterplot includes a GAM smoother.
- `grouping=<col,col,...>` gives counts for each grouping variable. Supply exactly two to compare the second within the first. For example, `grouping=site,treatment` shows one row per site, with the total number of observations, the number missing treatment status, and the count and percentage in each treatment category. Percentages and the adjacent stacked bars use observations with recorded treatment status. A site with no recorded status has a missing count and no percentage. Wide tables show three categories at a time.

## Constraints

- Always run `janitor::clean_names()` on the loaded data before any analysis. The user's params should reference the *cleaned* names.
- Supported formats: csv, tsv (auto-delim), xlsx (sheet 1 by default), parquet. Reject other formats with a clear error.
- PDF output only, via Quarto's default XeLaTeX rendering. `template.qmd` carries a small
  compatibility block in `header-includes` for TeX Live 2026+, with which
  pandoc's caption-less tables error with `No counter 'none' defined` unless `none` is a real
  counter. Do not remove it.
- This skill renders the report; it does NOT modify the data. The data file is read-only as far as the skill is concerned.
- Don't commit the rendered PDF without asking. Whether generated output belongs in version control is the project's call, not this skill's, and the user may want to look at it first.

## Things to NOT do

- Don't duplicate or rewrite `template.qmd` in the skill body — the qmd is the source of truth.
- Don't auto-detect "outcome" or "grouping" from the data. The user supplies these explicitly. Always-on baseline runs without them.
- Don't render to HTML or DOCX unless the user explicitly asks. PDF is the default.
- Don't auto-add the rendered output to git. Let the user decide.
- Don't follow up with a methodology-doc or analysis-plan write — that's a separate, user-initiated step.
