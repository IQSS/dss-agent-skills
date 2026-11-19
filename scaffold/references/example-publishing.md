# Example: a publishing project

For a guide, report, slide deck, or other document. Preserve the collaborators' chosen writing and build tools. This example uses Markdown and a PDF build; `example-shared.md` describes shared context files.

```text
document-project/
├── CLAUDE.md
├── STATUS.md
├── TASKS.md
├── README.md
├── source/
├── assets/
├── output/
└── docs/
    ├── briefs/
    ├── responses/
    └── notes/
```

For Pandoc/XeLaTeX, add a `template.tex` and a command such as `just build`; for Quarto, use its project configuration. Include filters only when needed. Record the tools, installed/licensed fonts, and exact build command. Do not assume a commercial font or copy a template from an unavailable private project. Use the supplied design or available fonts, and disclose substitutions.

A minimal recipe can be adapted after the source exists:

```just
build:
    mkdir -p output
    pandoc source/report.md --pdf-engine=xelatex -o output/report.pdf
```

For a custom Pandoc-driven TeX template using caption/longtable, include this compatibility block before the document begins:

```tex
\makeatletter
\@ifundefined{c@none}{\newcounter{none}}{}
\makeatother
```

Check the rendered artifact, not just the exit status: fonts, code sizes, table wrapping, labels, and page breaks can fail visually. A monospace font may need a smaller nominal size than body text. Build on the actual host and inspect any substituted glyphs.

Keep source editable and outputs reproducible. If an exact PDF was delivered, retain that version as a dated snapshot; later edits create another deliverable. Decide whether built outputs belong in Git or a release archive. Use the platform's normal viewer when previewing; do not assume the macOS `open` command exists.

Credentials are normally unnecessary for a document build. Add them only for a specific authorized build input or publishing service; preparing a document does not authorize deployment.
