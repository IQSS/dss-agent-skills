#!/usr/bin/env python3
"""Check site links, download contents, and the public publication boundary."""
from __future__ import annotations
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
LOCAL_FILES = {"AGENTS.md", "CLAUDE.md", "STATUS.md", "TASKS.md", "SPECIFICATION.md", "METHODOLOGY.md", "MEMORY.md"}
LOCAL_DIRS = {".git", ".claude", ".codex", ".agents", ".venv", "__pycache__"}
FORBIDDEN_TEXT = re.compile(r"/(?:Users|home)/[\w.-]+/|private (?:development|repository|checkout|site)|(?:AGENTS|CLAUDE|STATUS|TASKS|METHODOLOGY|SPECIFICATION|MEMORY)\.md", re.I)


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])


def main():
    problems = []
    pages = {}
    for path in SITE.rglob("*"):
        if path.name in LOCAL_FILES or LOCAL_DIRS.intersection(path.relative_to(SITE).parts):
            problems.append(f"Local file exposed: {path.relative_to(SITE)}")
        if path.suffix == ".html":
            text = path.read_text(encoding="utf-8")
            if FORBIDDEN_TEXT.search(text):
                problems.append(f"Non-public reference in {path.relative_to(SITE)}")
            parser = Page()
            parser.feed(text)
            pages[path.resolve()] = parser
    if not (SITE / "index.html").is_file():
        problems.append("Missing index.html")
    for path, page in pages.items():
        for link in page.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            target = unquote(parts.path)
            if target.startswith("/dss-agent-skills/"):
                destination = SITE / target.removeprefix("/dss-agent-skills/")
            elif target.startswith("/"):
                destination = SITE / target.lstrip("/")
            else:
                destination = path.parent / target if target else path
            if destination.is_dir():
                destination = destination / "index.html"
            destination = destination.resolve()
            if not destination.is_file():
                problems.append(f"{path.name}: missing local link {link}")
            elif parts.fragment and destination in pages and unquote(parts.fragment) not in pages[destination].ids:
                problems.append(f"{path.name}: missing anchor {link}")
    catalogue = json.loads((ROOT / "catalogue.json").read_text())
    expected = {item["name"] for item in catalogue}
    for name in expected | {"dss-agent-skills"}:
        archive_path = SITE / "downloads" / (name + ".zip")
        if not archive_path.is_file():
            problems.append(f"Missing download: {name}")
            continue
        with zipfile.ZipFile(archive_path) as archive:
            members = archive.namelist()
            if any(Path(member).name in LOCAL_FILES or LOCAL_DIRS.intersection(Path(member).parts) for member in members):
                problems.append(f"Local metadata in {name}.zip")
            found = {Path(member).parent.name for member in members if member.endswith("/SKILL.md")}
            wanted = expected if name == "dss-agent-skills" else {name}
            if found != wanted:
                problems.append(f"Wrong skill inventory in {name}.zip")
            for member in members:
                member_path = Path(member)
                if member_path.is_absolute() or ".." in member_path.parts:
                    problems.append(f"Unsafe archive path: {member}")
    for source in ("README.md", "CONTRIBUTING.md"):
        if FORBIDDEN_TEXT.search((ROOT / source).read_text()):
            problems.append(f"Non-public reference in {source}")
    for problem in problems:
        print(problem)
    if problems:
        raise SystemExit(1)
    print(f"Checked {len(pages)} HTML pages, local links, {len(expected) + 1} downloads, and public-text exclusions.")


if __name__ == "__main__":
    main()
