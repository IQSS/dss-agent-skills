#!/usr/bin/env python3
"""Generate skill catalogue pages and downloadable bundles from reviewed source."""
from __future__ import annotations
import html
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_FILES = {"AGENTS.md", "CLAUDE.md", "STATUS.md", "TASKS.md", "SPECIFICATION.md", "METHODOLOGY.md", "MEMORY.md"}
LOCAL_DIRS = {".git", ".claude", ".codex", ".agents", ".venv", "__pycache__"}
REPOSITORY = "https://github.com/IQSS/dss-agent-skills"


def source_files(folder):
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(folder)
        if path.name == ".DS_Store" or "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink() or path.name in LOCAL_FILES or LOCAL_DIRS.intersection(relative.parts):
            raise ValueError(f"Non-distributable file in skill: {relative}")
        yield path


def bundle(destination, members):
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, source in members:
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())


def build_library(catalogue):
    """Embed catalogue data and ordinary links for the illustrated homepage."""
    entries = []
    links = []
    for item in catalogue:
        entry = {key: value for key, value in item.items() if key != "library"}
        entry.update({
            "coverTitle": item["title"],
            "icon": "plan.svg",
            "cover": "#bac8ad",
            "edge": "#6b7d61",
            "steps": item["outcomes"][:3],
            "example": item["prompt"].split("\n", 1)[-1],
        })
        entry.update(item.get("library", {}))
        if not re.fullmatch(r"[a-z0-9-]+\.svg", entry["icon"]):
            raise ValueError("Invalid library illustration filename")
        if not (ROOT / "assets/library" / entry["icon"]).is_file():
            raise ValueError(f"Missing library illustration: {entry['icon']}")
        entries.append(entry)
        links.append(
            f'<li><a href="skills/{item["name"]}.html">'
            f'{html.escape(item["title"])}</a></li>'
        )
    data = json.dumps(entries, ensure_ascii=False).replace("<", "\\u003c")
    content = (
        '```{=html}\n<script id="library-data" type="application/json">\n'
        + data + '\n</script>\n'
        '<details id="library-index" class="library-index" open>\n'
        '<summary>Browse all skills as a list</summary>\n<ul>\n'
        + "\n".join(links) + '\n</ul>\n</details>\n```\n'
    )
    (ROOT / "_library.qmd").write_text(content, encoding="utf-8")


def build():
    catalogue = json.loads((ROOT / "catalogue.json").read_text())
    manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    names = [item["name"] for item in catalogue]
    if len(set(names)) != len(names) or set(names) != {Path(path).name for path in manifest["skills"]}:
        raise ValueError("Catalogue must match the plugin's skill inventory")
    build_library(catalogue)
    pages, downloads = ROOT / "skills", ROOT / "downloads"
    pages.mkdir(exist_ok=True)
    downloads.mkdir(exist_ok=True)
    listing, combined, group = [], [], None
    for item in catalogue:
        name = item["name"]
        if not re.fullmatch(r"[a-z0-9-]+", name):
            raise ValueError("Invalid skill name")
        if group != item["group"]:
            if group is not None:
                listing.append("::::")
            group = item["group"]
            listing.extend(["", "## " + group, "", ":::: {.skill-grid}", ""])
        listing.extend([
            f"::: {{.skill-card #{name}}}",
            f'<p class="skill-name">{html.escape(name)}</p>', "",
            f"### [{item['title']}](skills/{name}.qmd)", "",
            item["summary"], "",
            f'<p class="skill-detail"><a href="skills/{name}.html">Example and requirements</a></p>',
            ":::", ""
        ])
        outcomes = "\n".join("- " + text for text in item["outcomes"])
        page = (
            "---\ntitle: " + json.dumps(item["title"]) + "\n---\n\n" +
            item["summary"] + "\n\n" +
            f"Skill: `{name}`\n\n" +
            '::: {.skill-actions}\n' +
            f"[Download this skill](../downloads/{name}.zip){{.btn .btn-primary}}\n" +
            f"[Read the instructions]({REPOSITORY}/blob/main/{name}/SKILL.md){{.btn .btn-outline-primary}}\n" +
            ":::\n\n## Example prompt\n\n```bash\n" + item["prompt"] + "\n```\n\n" +
            "Use this after [installing the collection](../installation.qmd). Adapt the filenames and research decisions to your project.\n\n" +
            "## What the agent does\n\n" + outcomes + "\n\n" +
            "## Requirements\n\n" + item["requirements"] + "\n\n" +
            f"[Browse the source and supporting files]({REPOSITORY}/tree/main/{name}).\n"
        )
        (pages / (name + ".qmd")).write_text(page, encoding="utf-8")
        members = [(f"{name}/{path.relative_to(ROOT / name).as_posix()}", path) for path in source_files(ROOT / name)]
        bundle(downloads / (name + ".zip"), [*members, (name + "/LICENSE", ROOT / "LICENSE")])
        combined.extend(("dss-agent-skills/" + target, path) for target, path in members)
    listing.append("::::\n")
    (ROOT / "_catalogue.qmd").write_text("\n".join(listing), encoding="utf-8")
    bundle(downloads / "dss-agent-skills.zip", [*combined, ("dss-agent-skills/LICENSE", ROOT / "LICENSE")])
    print(f"Prepared {len(names)} skill pages and {len(names) + 1} download bundles.")


if __name__ == "__main__":
    build()
