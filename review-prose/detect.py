#!/usr/bin/env python3
"""Find sentences a reader has to decode, in finished prose.

The defect: a sentence that carries its argument in a pattern rather than in words, so the writer
reads compression and the reader reads a puzzle. Three shapes, all of which feel like good writing
to the person who wrote them, which is why this is a script and not a habit.

    detect.py <file.md> [--conventions <file>] [--max-words 55]

Reports; changes nothing. Every hit needs contextual review; the false-positive rate varies with the text.
The detector suggests passages to inspect, not edits to apply automatically.

Two rules keep the report focused and its locations accurate:

  * Fence-aware. A `# comment` at column 0 inside a code block is not a heading, and a regex that
    thinks it is will silently truncate a chapter and give you a wrong baseline.
  * Narrow. Semicolons and repeated words are common in clear prose, so patterns combine several
    conditions rather than flagging either feature alone.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
STOP = set("the a an of to in is are and or it that this for with as be by on not you your we my i"
           " they them he she".split())

# Tech-marketing register. Extend with --conventions.
AD_COPY = (r"ergonomic", r"daily.driver", r"battle.tested", r"under the hood", r"out of the box",
           r"heavy lifting", r"center of gravity", r"maintenance posture", r"game.?chang",
           r"table stakes", r"killer feature", r"mileage", r"\bsticky\b", r"wins on ",
           r"earns (its|the) ", r"seamless", r"frictionless", r"turnkey", r"supercharge", r"best.in.class",
           r"delve", r"realm of", r"navigate the compl", r"it'?s worth noting", r"it is worth noting",
           r"tapestry", r"landscape of", r"testament to", r"at the end of the day")


def prose(text: str) -> str:
    """Blank out comments and fenced code, preserving line numbering so hits stay addressable.

    Fence-aware, because a `# comment` at column 0 inside a code block is not a heading. Blanked
    rather than dropped so reported line numbers still match the source file.
    """
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    out, inside, char = [], False, None
    for line in text.splitlines():
        m = FENCE.match(line)
        if m:
            if not inside:
                inside, char = True, m.group(1)[0]
            elif line.strip()[0] == char:
                inside = False
            out.append("")
            continue
        out.append("" if inside else line)
    return "\n".join(out)


def headings(text: str):
    """(line, level, title) for every heading, from text already run through prose()."""
    out = []
    for i, ln in enumerate(text.splitlines(), 1):
        m = re.match(r"^(#{1,3}) (.+)", ln)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()))
    return out


def enclosing(heads, line: int) -> str:
    """Chapter and section for a line: the H1 it falls under, then the nearest subheading.

    Both are included because a subheading can recur in different chapters.
    """
    chapter = section = ""
    for n, level, title in heads:
        if n > line:
            break
        if level == 1:
            chapter, section = title, ""
        else:
            section = title
    return " > ".join(x for x in (chapter, section) if x)


def sentences(text: str):
    """Every prose sentence, with the paragraph it sits in, so the tell can be checked."""
    buf, start = [], 0
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip():
            if not buf:
                start = n
            buf.append(line)
            continue
        yield from _split(buf, start)
        buf = []
    yield from _split(buf, start)


def _split(buf, start: int):
    p = " ".join(buf).strip()
    if not p or p.startswith(("#", "|", "!", "[^", ":::", "```")):
        return
    parts = [s.strip().lstrip(">-*_ ") for s in re.split(r"(?<=[.!?])\s+", p)]
    for i, s in enumerate(parts):
        if len(s.split()) >= 3:
            yield s, (parts[i - 1] if i else None), start


def shapes(sent: str):
    """The three shapes. Each returns a reason, or None."""
    w = sent.split()
    if not (4 <= len(w) <= 24):
        return None
    # 1. A definite article closing on an abstract noun the reader was never given.
    if re.search(r"\b(is|are|was|were)\s+the\s+\w+[.,]", sent):
        return "ends on `the <noun>` -- the noun of what?"
    if re.search(r",\s*not\s+the\s+\w+\b", sent):
        return "contrast on a compressed noun (`X, not the Y`)"
    # 3. A bare abstract noun as the object: no article, so no article gives it away.
    if re.search(r"\b(about|for|with|into|toward)\s+\w{5,}\.$", sent) \
       and not re.search(r"\b(the|a|an|your|my|its|this|that|each|every|any)\s+\w+\.$", sent):
        return "bare abstract noun as the object -- no article to flag it"
    # 2. A noun handed from one clause to the next. On its own this is ordinary English. It becomes
    # the defect when two other things are true, and both are about what the reader has to supply:
    #
    #   * No connective. A comma or semicolon juxtaposes the clauses and leaves the reader to infer
    #     the relation. "and", "so", "because" state it.
    #   * The second clause asserts an identity with a copula and a definite article -- "is the X" --
    #     rather than describing an effect with an ordinary verb ("reads as", "becomes", "produces").
    #
    # "...is decoration, and decoration in this register reads as ad copy" is fine on both counts.
    # "...is decoration; decoration in this register is the ad copy" fails both, and is the shape
    # worth reporting.
    m = re.match(r"^(.{10,}?)([;,])\s+(.{10,})$", sent)
    if m:
        sep, second = m.group(2), m.group(3)
        a = [re.sub(r"[^\w]", "", x.lower()) for x in m.group(1).split()]
        b = [re.sub(r"[^\w]", "", x.lower()) for x in second.split()]
        tail = {x for x in a[-3:] if x and x not in STOP and len(x) > 3}
        head = {x for x in b[:3] if x and x not in STOP and len(x) > 3}
        if tail & head:
            connective = re.match(r"^(and|but|so|because|since|while|which|whereas|then|yet|or)\b",
                                  second, re.I)
            identity = re.search(r"\b(is|are|was|were)\s+(the|a|an)\s+\w+", second)
            if not connective and identity:
                return ("hands a noun across the boundary, with no connective and an "
                        "`is the <noun>` identity claim")
            if not connective and sep == ";":
                return "hands a noun across a semicolon with no connective"
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--conventions", type=Path,
                    help="the author's own style file; its banned phrases are added to the scan")
    ap.add_argument("--max-words", type=int, default=55,
                    help="report sentences longer than this (default 55)")
    args = ap.parse_args()
    if not args.file.is_file():
        sys.exit(f"error: no file at {args.file}")

    text = prose(args.file.read_text(errors="replace"))
    heads = headings(text)
    sents = list(sentences(text))
    words = len(text.split())

    banned = list(AD_COPY)
    if args.conventions and args.conventions.is_file():
        for line in args.conventions.read_text(errors="replace").splitlines():
            for q in re.findall(r'"([^"]{3,30})"\s*(?:/|→|->)', line):
                banned.append(re.escape(q))

    print(f"{args.file.name}: {words} words of prose, {len(sents)} sentences\n")

    print("== decode-me sentences (each needs a human decision; expect false positives)")
    n = 0
    for sent, prev, line in sents:
        why = shapes(sent)
        if not why:
            continue
        n += 1
        where = enclosing(heads, line)
        print(f"  [{why}]  line {line}" + (f", {where}" if where else ""))
        print(f"     {sent}")
        if prev and len(prev.split()) >= 6:
            print(f"     previous: {prev[:110]}")
        print()
    print(f"  {n} to rule on\n" if n else "  none\n")

    print("== banned phrasing")
    hits = [(p, m.group(0)) for p in banned for m in re.finditer(p, text, re.I)]
    for p, got in hits:
        print(f"  {got!r}  (pattern {p})")
    print(f"  {len(hits)} found\n" if hits else "  none\n")

    print("== length")
    L = [len(s.split()) for s, _, _ in sents]
    longs = [s for s, _, _ in sents if len(s.split()) > args.max_words]
    print(f"  median {statistics.median(L):.0f}  mean {statistics.mean(L):.1f}  "
          f"over {args.max_words} words: {len(longs)}")
    for s in longs[:10]:
        print(f"     [{len(s.split())}w] {s[:110]}")
    print()

    print("== em-dashes")
    lines = [l for l in text.splitlines() if "—" in l]
    listy = sum(l.count("—") for l in lines if re.match(r"^\s*[-*|]\s", l))
    body = [l for l in lines if not re.match(r"^\s*[-*|]\s", l)]
    pairs = sum(1 for l in body for s in re.split(r"(?<=[.!?])\s+", l) if s.count("—") >= 2)
    singles = sum(1 for l in body for s in re.split(r"(?<=[.!?])\s+", l) if s.count("—") == 1)
    print(f"  {listy} in list/table entries (term -- definition; conventional, leave them)")
    print(f"  {singles} single dashes in prose (appositives and list lead-ins; usually fine)")
    print(f"  {pairs} matched pairs in prose -- the parenthetical-subclause pattern")
    if pairs:
        print(f"     one per {words // max(pairs, 1)} words. Judge against this document's own "
              "register, not an absolute.")


if __name__ == "__main__":
    main()
