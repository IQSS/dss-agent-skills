#!/usr/bin/env python3
"""Check known portability risks, plugin inventory, and local maintainer-file exclusions.

These static checks cannot prove runtime isolation or scientific correctness.
User-supplied project files are valid inputs; private author configuration is not.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

TEXT = {".md", ".py", ".qmd", ".tex", ".R", ".sh", ".txt", ".json", ".toml", ".yml", ".yaml"}
AUTHOR_PATH = re.compile(r"/(?:Users|home)/(?!<)[\w.-]+/|(?:~|\$HOME)/\.config/[\w.-]+")
INTERNAL_REFERENCE = re.compile(
    r"\bprivate (?:dev(?:elopment)? (?:site|repo(?:sitory)?)|repo(?:sitory)?|checkout|site)\b"
    r"|\b(?:docs/(?:notes|findings)/|work-history\.(?:md|txt))", re.I
)
UNSAFE_PERMISSION = re.compile(r"dangerouslyDisableSandbox|--dangerously-skip-permissions")
SECRET_REF = re.compile(r"op://([^/\s]+)|gopass show -o\s+([^/\s]+)")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
METADATA = ("AGENTS.md", "CLAUDE.md", "STATUS.md", "TASKS.md", "SPECIFICATION.md",
            "METHODOLOGY.md", "MEMORY.md")
LOCAL_SETTINGS = (".claude", ".codex", ".agents")
BINARIES = ("xelatex", "quarto", "pandoc", "rscript", "dagitty", "pueue", "jq",
            "python3", "crew", "targets")


def check_skill(directory: Path, username: str | None = None) -> list[str]:
    problems = []
    source = (directory / "SKILL.md").read_text(encoding="utf-8")
    front = FRONTMATTER.match(source)
    if not front:
        problems.append("SKILL.md has no YAML frontmatter")
    else:
        name = re.search(r"^name:\s*([^\s]+)", front[1], re.M)
        if not name or name[1] != directory.name:
            problems.append("frontmatter name must match the skill directory")
        if not re.search(r"^description:\s*\S", front[1], re.M):
            problems.append("frontmatter needs a description")
        if any(re.search(rf"\b{tool}\b", source, re.I) for tool in BINARIES):
            if not re.search(r"^compatibility:\s*\S", front[1], re.M):
                problems.append("declare the external software in compatibility")

    texts = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() and not path.resolve().is_relative_to(directory.resolve()):
            problems.append(f"{path.relative_to(directory)} links outside the skill")
            continue
        if not path.is_file() or path.suffix not in TEXT:
            continue
        texts[path] = path.read_text(encoding="utf-8")
        for number, line in enumerate(texts[path].splitlines(), 1):
            location = f"{path.relative_to(directory)}:{number}"
            if AUTHOR_PATH.search(line):
                problems.append(f"{location}: depends on a private home or workspace path")
            if username and re.search(rf"\b{re.escape(username)}\b", line):
                problems.append(f"{location}: contains the supplied private account name")
            if UNSAFE_PERMISSION.search(line):
                problems.append(f"{location}: prescribes a host-specific permission bypass")
            for match in SECRET_REF.finditer(line):
                vault = next(part for part in match.groups() if part is not None)
                if not (vault.startswith("<") and vault.endswith(">")):
                    problems.append(f"{location}: replace the private secrets-store name with a placeholder")
    # References can route to other references; each bundled resource needs a mention.
    combined = "\n".join(texts.values())
    for path in directory.rglob("*"):
        if path.is_file() and path.name != "SKILL.md" and "__pycache__" not in path.parts:
            if path.name not in combined:
                problems.append(f"{path.relative_to(directory)} has no reference in the skill documents")
    return problems


def check_plugin(root: Path, manifest: Path) -> list[str]:
    problems = []
    data = json.loads(manifest.read_text(encoding="utf-8"))
    paths = data.get("skills", [])
    if not isinstance(paths, list) or not paths:
        return ["plugin manifest must list its skill directories"]
    listed = []
    for item in paths:
        path = (root / item).resolve()
        if not item.startswith("./") or not path.is_relative_to(root.resolve()):
            problems.append(f"plugin skill path must stay within this repository: {item}")
        elif not (path / "SKILL.md").is_file():
            problems.append(f"plugin skill path has no SKILL.md: {item}")
        listed.append(path)
    actual = {path.parent.resolve() for path in root.glob("*/SKILL.md")}
    if set(listed) != actual:
        problems.append("plugin skill inventory does not match the repository")
    if len(listed) != len(set(listed)):
        problems.append("plugin lists a skill more than once")
    marketplace = root / ".claude-plugin/marketplace.json"
    market = json.loads(marketplace.read_text(encoding="utf-8"))
    plugins = market.get("plugins", [])
    if len(plugins) != 1 or plugins[0].get("name") != data.get("name") or plugins[0].get("source") != "./":
        problems.append("marketplace must expose the local plugin with its manifest name")
    if any("skills" in item for item in plugins):
        problems.append("keep the skill inventory in plugin.json rather than duplicating it")
    return problems


def check_metadata(root: Path) -> list[str]:
    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=True).stdout
    problems = []
    for name in (*METADATA, *(name + "/local-settings.json" for name in LOCAL_SETTINGS)):
        result = subprocess.run(["git", "-C", str(root), "check-ignore", "--no-index", "-q", name])
        if result.returncode != 0:
            problems.append(f"maintainer path is not gitignored: {name}")
    for name in git("ls-files", "-z").split("\0"):
        if name and (Path(name).name in METADATA or any(part in LOCAL_SETTINGS for part in Path(name).parts)):
            problems.append(f"maintainer context or settings are tracked: {name}")
    return problems


def check_public_text(text: str, excluded: tuple[str, ...] = ()) -> list[str]:
    problems = []
    for number, line in enumerate(text.splitlines(), 1):
        if AUTHOR_PATH.search(line):
            problems.append(f"{number}: machine-specific path")
        if INTERNAL_REFERENCE.search(line):
            problems.append(f"{number}: non-public documentation reference")
        if any(value.casefold() in line.casefold() for value in excluded):
            problems.append(f"{number}: excluded publication text")
    return problems


def check_public_source(root: Path, excluded: tuple[str, ...] = ()) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        text=True, capture_output=True, check=True,
    )
    problems = []
    for name in sorted(set(result.stdout.split("\0")) - {""}):
        path = root / name
        if path.is_symlink():
            problems.append(f"{name}: source must not depend on a symlink")
            continue
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        problems.extend(f"{name}:{item}" for item in check_public_text(text, excluded))
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--plugin", type=Path)
    parser.add_argument("--username", help="optional private account name to flag before publication")
    parser.add_argument("--check-metadata", action="store_true")
    parser.add_argument("--check-public-source", action="store_true")
    parser.add_argument("--exclude-text", action="append", default=[],
                        help="additional text to reject without echoing it in check results")
    args = parser.parse_args()
    root = args.root.resolve()
    skills = sorted(path.parent for path in root.glob("*/SKILL.md"))
    problems = [] if skills else ["no skills found"]
    for directory in skills:
        problems.extend(f"{directory.name}: {item}" for item in check_skill(directory, args.username))
    try:
        if args.plugin:
            manifest = args.plugin if args.plugin.is_absolute() else root / args.plugin
            problems.extend(check_plugin(root, manifest))
        if args.check_metadata:
            problems.extend(check_metadata(root))
        if args.check_public_source:
            excluded = tuple(args.exclude_text) + ((args.username,) if args.username else ())
            problems.extend(check_public_source(root, excluded))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        problems.append(f"could not finish repository checks: {error}")
    for problem in problems:
        print(problem)
    if problems:
        raise SystemExit(1)
    print(f"{len(skills)} skills pass the static portability and selected repository checks.")


if __name__ == "__main__":
    main()
