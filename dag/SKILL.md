---
name: dag
description: "Render a supplied dagitty causal diagram as a PDF, verify adjustment sets, and refine the visual layout. Use for causal DAGs with a specified exposure and outcome, not to invent the causal structure or draw a general flowchart."
compatibility: "Requires R with dagitty for adjustment-set checks, XeLaTeX with TikZ/standalone, and a PDF rasterizer such as pdftoppm for visual inspection. Check available fonts or use the template’s installed-font fallback. Commands must use the host’s supported runtime and permissions."
---

# /dag

Render one causal DAG from a dagitty `.dag` source into a TikZ figure using the bundled template and an adaptive legend. Derive visual roles from the supplied causal question so colours distinguish adjustment variables, mediators, exposures, and outcomes. Render and inspect the figure, then refine the layout until labels and connections are easy to read.

## Source of truth

The TikZ scaffold — palette, node/edge styles, and legend helper macros — lives at `template.tex` beside this file and is the **single** source of truth for the visual identity. This skill orchestrates parsing, role derivation, layout, and placement; it injects nodes/edges/legend/caption into the template's `<< >>` markers and does **not** restate hex values or styles. If the look needs to change, edit `template.tex`, not this doc.

Output goes to `outputs/figures/` under the project root by default, or beside the `.dag` file if no such directory exists. Pass `--out <dir>` to override. This is a default, not a convention looked up elsewhere. The causal vocabulary (exposure, outcome, minimal sufficient adjustment set, mediator, back-door path) is dagitty's; cross-reference rather than redefine.

## Workflow

### 1. Parse args

| Arg form | Meaning |
|---|---|
| (none) | Auto-detect: a single `*.dag` under `dags/` (or cwd). If 0 or >1, list candidates and ask. |
| `<path.dag>` | Use that file. Resolve relative to the project root (supplied project path or repository root) if not absolute. Use other explicitly supplied paths only within the authorized scope. |
| `--exposure <name>` / `--outcome <name>` | Override / supply the focal contrast when the `.dag` doesn't tag it (see § 3). Names match node labels (quote multi-word). |
| `--caption "<text>"` | Override the default caption (the red `MSAS = {…}` listing) with custom text under the figure. |
| `--out <path>` | Override the output PDF location (§ 7). |
| `--no-refine` | Render the seeded layout once, skip the iterate loop (fast preview). |

### 2. Parse the `.dag`

dagitty format: a `dag { … }` block with an optional `bb="xmin,ymin,xmax,ymax"`, node lines `"Name" [<tags>,pos="x,y"]`, and edge lines `"A" -> "B"`. Extract, per node: label, the role tags present (`exposure`, `outcome`, `latent`, `adjusted`, or none), and `pos`. Extract the directed edge list. Build the adjacency so you can compute ancestors/descendants in § 3–4.

**dagitty `pos` is y-DOWN.** Negate y when seeding TikZ coordinates (§ 5). Treat `pos` as a *layout seed only* — the analyst's dagitty canvas is rarely the cleanest figure (e.g. nodes that read better swapped or aligned to a row); the refine loop in § 6 is what produces the final layout.

### 3. Identify the exposure→outcome question

A DAG figure answers **one** exposure→outcome question; the roles depend on it.

- **Exposure / outcome:** from the `exposure` / `outcome` tags. If either is missing, take it from `--exposure`/`--outcome`. If still unknown, ask — do not guess the focal contrast.
- If the `.dag` tags multiple exposures (a teaching graph), this single-figure skill renders **one**; ask which, or take `--exposure`. (Multi-panel "same graph, N exposures" layouts exist but are bespoke — out of scope here.)

### 4. Derive node roles and edge classes from the structure

Compute over the parsed graph, given exposure `E` and outcome `O`. Let `D = descendants(E)`, `A = ancestors(O)`.

**Node roles** (→ template style):
- `exposure` → **exposure**; `outcome` → **outcome**.
- nodes tagged `latent`/unobserved → **latent** (a latent node may still sit on the causal path — that affects its *edges*, not its fill).
- **mediator**: observed node in `D ∩ A` (on a directed E⇝O path). *Do not adjust.*
- **msas** (adjustment set): the measured confounders to condition on. **Run `dagitty::adjustmentSets()` — mandatory before the confirm round; never derive the MSAS by heuristic.** Use the host's working R invocation (see § Running R below).
  ```r
  library(dagitty)
  g <- dagitty(readLines("<path-to.dag>") |> paste(collapse="\n"))
  print(adjustmentSets(g, type="minimal"))
  ```
  Several minimal sufficient sets may be returned. Use the project's specified set if it is valid, or present the alternatives for selection. An empty set means no adjustment is needed; no valid set means adjustment cannot identify the requested effect under this graph. Never conflate those results. **Proxy confounders** — nodes that belong in the set because a latent common cause links them to `O` via the back-door `E ← proxy ← latent → O` — are correctly surfaced by dagitty and would be missed by any pure-graph heuristic. Give a proxy the `msas` fill but a **grey** edge (see `conf` below).
- **obs**: remaining observed nodes (present, neither confounder nor mediator).

**Edge classes** (→ template style):
- **causal** (green): edge lying on a directed E⇝O path (source and target both on such a path, edge advances toward `O`). Drawn LAST so it sits on top.
- **conf** (red): edge from a **direct common cause** — an `msas` node with edges to **both** `E` and `O` — into `E` or `O`. Reserve red for these back-door-forming edges. An `msas` node pointing to only one of `E`/`O` (a proxy confounder, or one whose other links run to mediators/covariates) keeps its salmon fill but draws **grey** (`other`). Don't redden *every* out-edge of an adjustment-set node — that over-marks the figure.
- **latentedge** (amber dashed): *optional* highlight for an edge out of a latent confounder (a latent pointing toward both the exposure side and the outcome). Default OFF — only when it sharpens the story (for example, edges from an unobserved common cause); otherwise such edges are `other`.
- **other** (grey): everything else.

**Confirm in one round.** The `.dag` does not fully encode visual intent — whether to highlight a latent edge, which edges to bend. Present the verified role assignment compactly (a short `node → role` table sourced from the dagitty output + an edge-class tally) and ask the user to confirm or adjust **before** rendering. State the assumed exposure/outcome so a misdetection is caught here.

### 5. Generate ids, labels, coordinates → fill the template

- **ids:** short TikZ-safe identifiers from labels (initials or first word; keep a label→id map, ensure uniqueness).
- **labels:** the full names, wrapping long ones with `\\` at word boundaries to keep boxes ~1–3 lines (escape `&` → `\&`, `%`, `_`). Use `{\scriptsize …}` for optional small-print qualifiers.
- **coordinates (seed):** affine-map the dagitty `pos` (y negated) onto a ~11 cm × ~7 cm canvas. This is the *starting* layout.
- Emit `\node[<role>] (<id>) at (<x>,<y>) {<Label>};` into `<<NODES>>`; emit edges grouped `other → conf → latentedge → causal` (causal last) into `<<EDGES>>`, default straight (`--`) with `to[bend left/right=…]` added during refinement.
- **legend (adaptive):** into `<<LEGEND>>`, emit two nodes in the small `legend` style — a `\textbf{Nodes:}` line with a `\lentry{<role>}{<caption>}` **only for roles present**, and a `\textbf{Edges:}` line with `\eentry{<color>}{<caption>}` (or `\eentrydash{lineamber}{…}` for latent) **only for classes present**. Don't show a mediator swatch if there are no mediators. Keep it a compact footer (small font, small swatches) — not a banner that competes with the graph. Use the `\lentry`/`\eentry` wrappers rather than bare `\lnode`/`\ledge` — they `\mbox` each swatch to its caption so a wrapped legend breaks between entries instead of hyphenating mid-phrase. Vertical centring of swatches is handled by `\swnode` / `\swdash` / `\swrule` in the template; don't hand-tune per figure. If they need adjustment, compare offsets in the completed figure at high resolution, preserving its actual font settings.
- **caption:** the default caption is the **adjustment set listed in red** — `\node[anno, text=linered] {MSAS = \{\,<set>\,\}};` (wrap with `\\` if long), echoing the `msas` node colour so the figure is self-contained. Do **not** write a prose takeaway sentence. `--caption "<text>"` overrides with custom text; state explicitly whether the selected set is empty or no valid adjustment set exists.

### 6. Render-inspect-refine loop (the layout artistry)

This is the core. Build, look, adjust, repeat — do not ship the seeded layout blind.

1. Write `<dag-stem>-tikz.tex` next to the `.dag` (in `dags/`).
2. Use the template's Inter font when available; it falls back to Latin Modern Sans. Honor an explicit project font choice in the generated copy.
3. Build (XeLaTeX twice; redirect caches so it works under the sandbox):
   ```sh
   cd <dags-dir>
   TEXMFVAR=$TMPDIR/texmf-var TEXMFCACHE=$TMPDIR/texmf-cache \
     xelatex -interaction=nonstopmode <stem>-tikz.tex >/dev/null && \
   TEXMFVAR=$TMPDIR/texmf-var TEXMFCACHE=$TMPDIR/texmf-cache \
     xelatex -interaction=nonstopmode <stem>-tikz.tex >/dev/null
   ```
   Use an approved writable scratch location for TeX caches. If the host blocks a required operation, use its normal permission process; do not change agent permission settings.
4. Rasterize and **look at it**: `pdftoppm -png -r 150 <stem>-tikz.pdf <stem>-tikz` then Read the PNG.
5. Check readability and fix the most consequential layout problem first:
   - node overlaps or boxes touching → spread that local cluster;
   - edges passing **through** unrelated nodes → reroute with `to[bend …]` or `out=/in=` angles, or nudge a node;
   - many crossings where a swap or a row-align removes them → move nodes;
   - label overflow / lopsided boxes → rewrap, adjust `minimum width`;
   - unbalanced whitespace, exposure not clearly left / outcome right → shift columns;
   - legend or caption colliding with the graph → move it down.
6. Regenerate, rebuild, re-inspect. **Cap at ~5–6 passes**; if still not clean, present the best version and say what's still rough rather than looping forever. Stop early once it reads cleanly — don't over-polish.

### 7. Place the output

- Keep the generated `<stem>-tikz.tex` in `dags/` (it's the reproducible build, versioned next to the `.dag`).
- Copy the final PDF to the shape-aware figures location:
  | Shape | Default PDF destination |
  |---|---|
  | paper | `outputs/figures/working/<stem>.pdf` (use `final/` if the user says it's publication/supplementary) |
  | other / minimal | next to the `.dag`, or `--out` |
- `--out` overrides. Clean up the xelatex aux files (`.aux`, `.log`) and the intermediate PNG. **Never silently overwrite** an existing PDF of a different name-stem — if the target exists, confirm overwrite vs version-suffix.

### 8. Report

One short paragraph: the exposure→outcome question rendered, the role tally (e.g. "1 exposure, 1 outcome, 4 in adjustment set, 2 mediators, 2 latent"), where the `.tex` and PDF landed, and how many refine passes it took.

## Things to NOT do

- **Do not duplicate the palette/styles** in generated files or this doc — they live in `template.tex`. Inject content into the markers; don't restate hex codes.
- **Do not transcribe dagitty `pos` and stop.** The seeded layout is the *start*; the § 6 loop is the deliverable. Shipping the raw dagitty positions is the failure mode this skill exists to prevent.
- **Do not assign roles silently.** Confirm the exposure/outcome and the proposed role/edge classification (§ 4) before rendering — the `.dag` underspecifies visual intent.
- **Do not derive the MSAS by heuristic.** Run `dagitty::adjustmentSets()` first, before the confirm round. A graph-structure heuristic misses proxy confounders and is not a substitute.
- **Do not author or edit the causal structure.** If the `.dag` is wrong or missing edges, flag it — don't fix the science. This skill draws the graph it's given.
- **Do not silently drop edges.** Render *every* edge in the `.dag` (a curated figure that omits edges for clarity is a different artifact). If the graph is too dense to read, say so and suggest the analyst prune the `.dag` — don't quietly omit edges to tidy the picture.
- **Do not render multi-exposure panels.** One figure = one exposure→outcome question. Offer to pick one; don't auto-compose a panel grid.
- **Do not loop forever on layout.** Cap the refine passes; present the best and name what's still rough.
- **Do not run R blindly.** See § Running R below; don't fire a bare `Rscript`.

## Running R

Use the project's working R environment and any documented runtime wrapper. Some host setups need a pseudo-terminal for noninteractive R; this is not a universal R requirement. If such a workaround is required, use the platform's supported wrapper and normal permission mechanism. Confirm the adjustment-set output and that the process exits; do not leave a hanging process merely because it wrote an artifact. Report a blocked check rather than guessing the adjustment set.
