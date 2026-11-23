#!/usr/bin/env python3
"""Check required fields, citation metadata, and a literature run's internal consistency.

Identifier lookups check bibliographic identity, not full-text access or support for a research claim.

    verify.py <run-dir> [--mailto you@example.com] [--mailto-to crossref|datacite|both|neither]
                        [--threshold 0.90] [--offline]

Exits non-zero listing what it found, and touches nothing.

One distinction it is careful about: a record the API says does not exist is a *failure*, while a
record it could not reach because the network is down is *unchecked*. Collapsing those would let a
flaky connection read as a clean run, or a fabrication read as a network blip.

Standard library only, so it runs wherever the agent runs.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import NamedTuple

DOI = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
ARXIV = re.compile(r"^(arxiv:)?(\d{4}\.\d{4,5})(v\d+)?$", re.I)
PMID = re.compile(r"^\d{1,8}$")
UA = "dss-litsearch-verify/0.2"


class Unreachable(Exception):
    """The source could not be contacted. Not the same as 'the record does not exist'."""


def get(url: str, mailto: str | None = None, tries: int = 3) -> bytes:
    ua = f"{UA} mailto:{mailto}" if mailto else UA
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url)
            # A redirect may point to a service the researcher did not select.
            req.add_unredirected_header("User-Agent", ua)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return b""                      # a real answer: no such record
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(2 ** attempt)        # back off and retry
                continue
            raise Unreachable(f"HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise Unreachable(str(e)) from e
    raise Unreachable("retries exhausted")


def normalise(text: str) -> str:
    """Lowercase, strip punctuation and collapse whitespace, so formatting differences don't count."""
    return " ".join(re.sub(r"[^\w\s]", " ", (text or "").lower()).split())


def canonical_id(identifier: str) -> str:
    """Normalize supported bare identifiers without conflating arXiv versions."""
    return re.sub(r"^arxiv:", "", identifier.strip().lower())


def bibliography_ids(text: str, suffix: str) -> set[str]:
    """Read the identifier fields emitted by the skill, not arbitrary numbers in prose."""
    if suffix == ".bib":
        values = re.findall(r'\b(?:doi|pmid|eprint)\s*=\s*[{\"]([^}\"]+)', text, re.I)
    else:
        values = re.findall(r"^(?:DO|AN)\s+-\s+(.+)$", text, re.I | re.M)
    values += re.findall(r"https?://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)/?", text, re.I)
    values += re.findall(r"https?://arxiv\.org/abs/([\d.]+(?:v\d+)?)", text, re.I)
    return {canonical_id(v) for v in values}


class RetractionCheck(NamedTuple):
    source: str
    notices: tuple[str, ...] = ()
    unavailable: str = ""


def crossref_retractions(record: dict, doi: str, source: str = "Crossref") -> RetractionCheck:
    # updated-by points from the original work to its notice. update-to points back.
    if str(record.get("DOI", "")).lower() != doi.lower():
        return RetractionCheck(source, unavailable="response does not identify the requested DOI")
    updates = record.get("updated-by", [])
    notices = []
    incomplete = not isinstance(updates, list)
    for item in updates if isinstance(updates, list) else []:
        if not isinstance(item, dict) or not item.get("type"):
            incomplete = True
        elif item["type"] == "retraction":
            target = item.get("DOI") or ""
            if isinstance(target, str) and DOI.fullmatch(target):
                notices.append(f"https://doi.org/{target}")
            else:
                notices.append(f"notice DOI unavailable (article: https://doi.org/{doi})")
    if incomplete and not notices:
        return RetractionCheck(source, unavailable="unreadable update metadata")
    return RetractionCheck(source, tuple(dict.fromkeys(notices)))


def pubmed_retractions(record: dict, pmid: str) -> RetractionCheck:
    references = record.get("references")
    types = record.get("pubtype")
    notices = []
    incomplete = not isinstance(references, list) or not isinstance(types, list)
    for ref in references if isinstance(references, list) else []:
        if not isinstance(ref, dict) or not isinstance(ref.get("reftype"), str):
            incomplete = True
        elif ref["reftype"].lower() == "retraction in":
            target = str(ref.get("pmid") or "")
            notice = ref.get("refsource") or "notice identifier unavailable"
            if PMID.fullmatch(target):
                notice = f"https://pubmed.ncbi.nlm.nih.gov/{target}/"
            notices.append(notice)
    if not notices and isinstance(types, list) and "Retracted Publication" in types:
        notices.append(f"marked as retracted, notice unavailable (article: https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
    if incomplete and not notices:
        return RetractionCheck("PubMed", unavailable="incomplete retraction metadata")
    return RetractionCheck("PubMed", tuple(dict.fromkeys(notices)))


def journal_retractions(doi: str, contact: str | None) -> RetractionCheck:
    if not DOI.fullmatch(doi):
        return RetractionCheck("arXiv", unavailable="no published DOI to check")
    try:
        raw = get(f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}", contact)
        if raw:
            record = json.loads(raw)["message"]
            return crossref_retractions(record, doi, source=f"Crossref (journal DOI {doi})")
    except (Unreachable, ValueError, KeyError, TypeError, AttributeError) as error:
        return RetractionCheck("Crossref", unavailable=f"journal DOI {doi}: {error}")
    return RetractionCheck("Crossref", unavailable=f"no record for journal DOI {doi}")


def crossref_versions(record: dict, identifier: str) -> dict:
    if str(record.get("DOI", "")).casefold() != identifier.casefold():
        return {}
    relations = record.get("relation") or {}
    if not isinstance(relations, dict):
        relations = {}
    if record.get("type") == "journal-article":
        kind, relation = "article", "has-preprint"
    elif (record.get("subtype") in ("preprint", "working-paper") or "is-preprint-of" in relations
          or (record.get("type") == "posted-content" and not record.get("subtype"))):
        kind, relation = "preprint", "is-preprint-of"
    else:
        return {}
    entries = relations.get(relation)
    if not isinstance(entries, list):
        entries = []
    linked = [r["id"].casefold() for r in entries
              if isinstance(r, dict) and r.get("id-type") == "doi"
              and isinstance(r.get("id"), str) and DOI.fullmatch(r["id"])]
    return {"kind": kind, "version_dois": linked}


def preprint_pairs(records: dict) -> tuple[set, set]:
    """Find included preprint/article pairs. Similar titles suggest review only."""
    articles_by_doi = defaultdict(set)
    articles_by_preprint = defaultdict(set)
    articles_by_author = defaultdict(list)
    for ident, item in records.items():
        if item.get("kind") != "article":
            continue
        articles_by_doi[(item.get("doi") or ident).casefold()].add(ident)
        for doi in item.get("version_dois", []):
            articles_by_preprint[doi].add(ident)
        author = normalise(item.get("author"))
        if author:
            articles_by_author[author].append(ident)

    confirmed, possible = set(), set()
    for ident, item in records.items():
        if item.get("kind") != "preprint":
            continue
        for doi in item.get("version_dois", []):
            confirmed.update((ident, article) for article in articles_by_doi.get(doi, ()))
        own_doi = (item.get("doi") or ident).casefold()
        confirmed.update((ident, article) for article in articles_by_preprint.get(own_doi, ()))
        title = normalise(item.get("title"))
        for article in articles_by_author.get(normalise(item.get("author")), ()):
            other = normalise(records[article].get("title"))
            if title and other and SequenceMatcher(None, title, other).ratio() >= 0.9:
                possible.add((ident, article))
    return confirmed, possible - confirmed


def fetch(identifier: str, mailto: str | None, mailto_to: str = "crossref") -> dict | None:
    """Return citation metadata and the source-specific retraction check for this identifier."""
    ident = identifier.strip()
    if DOI.match(ident):
        raw = get(f"https://api.crossref.org/works/{urllib.parse.quote(ident)}",
                  mailto if mailto_to in ("crossref", "both") else None)
        if not raw:
            # Crossref is one registration agency among several. Zenodo, Dryad, OSF and figshare
            # register with DataCite, and a Crossref 404 for one of those is not evidence of
            # anything. Ask DataCite before calling a record non-existent -- a false accusation
            # of fabrication costs more than the extra request.
            raw = get(f"https://api.datacite.org/dois/{urllib.parse.quote(ident)}",
                      mailto if mailto_to in ("datacite", "both") else None)
            if not raw:
                return None
            a = json.loads(raw)["data"]["attributes"]
            titles = a.get("titles") or [{}]
            creators = a.get("creators") or [{}]
            fam = creators[0].get("familyName") or (creators[0].get("name") or "").split(",")[0]
            types = a.get("types") or {}
            resource_type = types.get("resourceTypeGeneral") if isinstance(types, dict) else None
            return {"title": titles[0].get("title", ""), "author": fam,
                    "year": a.get("publicationYear"),
                    "kind": {"Preprint": "preprint", "JournalArticle": "article"}.get(resource_type),
                    "retraction": RetractionCheck("DataCite", unavailable="check the repository record for notices")}
        m = json.loads(raw)["message"]
        dates = m.get("published-print") or m.get("published-online") or m.get("issued") or {}
        parts = (dates.get("date-parts") or [[None]])[0]
        authors = m.get("author") or [{}]
        return {"title": (m.get("title") or [""])[0],
                "author": authors[0].get("family", ""),
                "year": parts[0] if parts else None,
                **crossref_versions(m, ident),
                "retraction": crossref_retractions(m, ident)}
    if ARXIV.match(ident):
        match = ARXIV.match(ident)
        bare = match.group(2) + (match.group(3) or "")
        raw = get(f"https://export.arxiv.org/api/query?id_list={bare}")
        root = ET.fromstring(raw) if raw else None
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entry = root.find("a:entry", ns) if root is not None else None
        if entry is None or entry.find("a:title", ns) is None:
            return None
        entry_id = entry.findtext("a:id", "", ns)
        if "/api/errors" in entry_id:
            return None
        name = entry.find("a:author/a:name", ns)
        published = (entry.findtext("a:published", "", ns) or "")[:4]
        journal_doi = entry.findtext("{http://arxiv.org/schemas/atom}doi", "").strip()
        contact = mailto if mailto_to in ("crossref", "both") else None
        return {"title": entry.findtext("a:title", "", ns),
                "author": (name.text or "").split()[-1] if name is not None and name.text else "",
                "year": int(published) if published.isdigit() else None,
                "kind": "preprint", "version_dois": [journal_doi.casefold()] if DOI.fullmatch(journal_doi) else [],
                "retraction": journal_retractions(journal_doi, contact)}
    if PMID.match(ident):
        raw = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                  f"?db=pubmed&retmode=json&id={ident}")
        if not raw:
            return None
        rec = (json.loads(raw).get("result") or {}).get(ident)
        if not rec or "error" in rec:
            return None
        year = re.match(r"(\d{4})", rec.get("pubdate", "") or "")
        pubtypes = rec.get("pubtype") or []
        kind = ""
        if "Preprint" in pubtypes:
            kind = "preprint"
        elif "Journal Article" in pubtypes:
            kind = "article"
        doi = next((a["value"] for a in rec.get("articleids") or []
                    if isinstance(a, dict) and a.get("idtype") == "doi"
                    and isinstance(a.get("value"), str) and DOI.fullmatch(a["value"])), "")
        return {"title": rec.get("title", ""),
                "author": (rec.get("sortfirstauthor", "") or "").split(" ", 1)[0],
                "year": int(year.group(1)) if year else None,
                "kind": kind, "doi": doi,
                "retraction": pubmed_retractions(rec, ident)}
    raise ValueError(f"unrecognized identifier form: {identifier!r}")


def check(run: Path, mailto: str | None, threshold: float, offline: bool,
          mailto_to: str = "crossref") -> tuple[list[str], list[str]]:
    problems: list[str] = []
    unchecked: list[str] = []

    for name in ("protocol.md", "queries.md", "screening.csv", "evidence.csv",
                 "unverified.md", "references.bib", "references.ris", "README.md"):
        if not (run / name).exists():
            problems.append(f"{name} is missing from the run directory")
    if not (run / "raw").is_dir():
        problems.append("raw/ is missing: the API responses are the run's evidence")
    if not (run / "evidence.csv").exists():
        return problems, unchecked

    with (run / "evidence.csv").open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        rows = list(reader)
    required = {"id", "title", "author", "year", "evidence", "source"}
    missing_fields = sorted(required - fields)
    if missing_fields:
        problems.append("evidence.csv missing required columns: " + ", ".join(missing_fields))
        return problems, unchecked

    # 1. Every row has an identifier, and no two rows share one.
    seen: dict[str, int] = {}
    for i, row in enumerate(rows, start=2):
        for field in sorted(required):
            if not (row.get(field) or "").strip():
                problems.append(f"evidence.csv line {i}: missing {field}")
        if row.get("evidence") not in {"title", "abstract", "fulltext"}:
            problems.append(f"evidence.csv line {i}: evidence must be title, abstract, or fulltext")
        if not re.fullmatch(r"\d{4}", row.get("year") or ""):
            problems.append(f"evidence.csv line {i}: year must contain four digits")
        ident = canonical_id(row.get("id") or "")
        if not ident:
            problems.append(f"evidence.csv line {i}: no identifier — it belongs in unverified.md")
        elif not (DOI.fullmatch(ident) or ARXIV.fullmatch(ident) or PMID.fullmatch(ident)):
            problems.append(f"evidence.csv line {i}: unsupported identifier form: {ident!r}")
        elif ident in seen:
            problems.append(f"evidence.csv line {i}: identifier {ident} also on line {seen[ident]}")
        else:
            seen[ident] = i

    # 2. Every identifier resolves, and the record matches what the evidence table claims. This is the
    # check the whole skill exists for.
    if not offline:
        records = {}
        for ident, line in seen.items():
            try:
                found = fetch(ident, mailto, mailto_to)
            except Unreachable as e:
                unchecked.append(f"{ident}: could not reach the source ({e})")
                continue
            except (KeyError, TypeError, IndexError, AttributeError, json.JSONDecodeError, ET.ParseError) as e:
                unchecked.append(f"{ident}: source response could not be interpreted ({e})")
                continue
            except ValueError as e:
                problems.append(f"evidence.csv line {line}: {e}")
                continue
            if found is None:
                problems.append(f"evidence.csv line {line}: {ident} does not resolve — "
                                "no matching record found; investigate or move it to unverified.md")
                continue
            unavailable = [key for key in ("title", "author", "year") if not found.get(key)]
            if unavailable:
                unchecked.append(f"{ident}: source metadata missing {', '.join(unavailable)}")
            records[ident] = found
            claimed = rows[line - 2]
            status = found["retraction"]
            if status.unavailable:
                unchecked.append(f"{ident}: retraction status unchecked ({status.source}: {status.unavailable})")
            elif status.notices:
                notice = f"{ident}: retraction flagged by {status.source}: " + ", ".join(status.notices)
                reason = (claimed.get("retraction_inclusion_reason") or "").strip()
                if reason:
                    print(f"  {notice}. Researcher's reason for inclusion: {reason}")
                else:
                    problems.append(f"{notice}. Review with the researcher before inclusion.")
            else:
                print(f"  {ident}: no retraction notice found in {status.source}")
            if claimed.get("title") and found.get("title"):
                ratio = SequenceMatcher(None, normalise(claimed["title"]),
                                        normalise(found["title"])).ratio()
                if ratio < threshold:
                    problems.append(f"evidence.csv line {line}: title does not match the record "
                                    f"({ratio:.2f}) — the evidence table says {claimed['title'][:60]!r}, "
                                    f"{ident} is {found['title'][:60]!r}")
            if found.get("year") and not re.fullmatch(r"\d{4}", str(found["year"])):
                unchecked.append(f"{ident}: source year could not be interpreted")
            elif re.fullmatch(r"\d{4}", claimed.get("year") or "") and found.get("year"):
                # One year of slack: online-first and issue dates legitimately differ.
                if abs(int(claimed["year"]) - int(found["year"])) > 1:
                    problems.append(f"evidence.csv line {line}: year {claimed['year']} vs "
                                    f"{found['year']} on the record")
            if claimed.get("author") and found.get("author"):
                if not re.search(r"\b" + re.escape(normalise(found["author"])) + r"\b",
                                 normalise(claimed["author"])):
                    problems.append(f"evidence.csv line {line}: first author {claimed['author']!r} "
                                    f"is not {found['author']!r} on the record")

        confirmed, possible = preprint_pairs(records)
        for preprint, article in sorted(confirmed):
            problems.append(f"evidence.csv includes linked versions {preprint} and {article}. "
                            "Keep both in screening.csv and cite the version that supplied the evidence once.")
        for preprint, article in sorted(possible):
            print(f"  Possible versions: {preprint} and {article} have similar titles and authors. "
                  "Review the source records and keep them separate until confirmed.")

    # 3. Both bibliographies carry the evidence table's identifiers.
    ids = set(seen)
    for fname in ("references.bib", "references.ris"):
        path = run / fname
        if not path.exists():
            continue
        text = path.read_text()
        cited = bibliography_ids(text, path.suffix)
        for extra in sorted(cited - ids):
            problems.append(f"{fname} cites {extra}, which is not in evidence.csv")
        for missing in sorted(ids - cited):
            problems.append(f"evidence.csv includes {missing}, which is not in {fname}")

    # 4. Each recorded query links to its saved response.
    queries = (run / "queries.md").read_text().splitlines() if (run / "queries.md").exists() else []
    query_rows = [line for line in queries if line.strip().startswith("-")]
    if not query_rows:
        problems.append("queries.md has no query records")
    for line in query_rows:
        responses = re.findall(r"\]\((raw/[^)]+)\)", line)
        if not responses:
            problems.append("queries.md query has no saved-response link: " + line[:80])
        for response in responses:
            path = (run / response).resolve()
            if not path.is_relative_to((run / "raw").resolve()) or not path.is_file():
                problems.append(f"queries.md response is missing or outside raw/: {response}")

    # 5. The screening tally and the evidence table agree on how many records were included.
    if (run / "screening.csv").exists():
        with (run / "screening.csv").open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            scr = list(reader)
        col = next((c for c in ("decision", "status", "stage") if c in columns), None)
        if not col:
            problems.append("screening.csv has no usable decision, stage, or status column")
        if col:
            included = sum(1 for r in scr if (r.get(col) or "").strip().lower() == "included")
            if included != len(rows):
                problems.append(f"screening.csv marks {included} records included, "
                                f"but evidence.csv has {len(rows)} rows")
    return problems, unchecked


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path, help="the run directory to check")
    ap.add_argument("--mailto", help="optional contact email for the selected services")
    ap.add_argument("--mailto-to", choices=("crossref", "datacite", "both", "neither"),
                    default="crossref", help="who receives --mailto (default: Crossref only)")
    ap.add_argument("--threshold", type=float, default=0.90, help="title similarity floor")
    ap.add_argument("--offline", action="store_true",
                    help="structural checks only; skips every network lookup")
    args = ap.parse_args()

    run = args.run.resolve()
    if not run.is_dir():
        sys.exit(f"error: no run directory at {run}")

    if not 0 <= args.threshold <= 1:
        ap.error("--threshold must be between 0 and 1")
    try:
        problems, unchecked = check(run, args.mailto, args.threshold, args.offline, args.mailto_to)
    except (OSError, UnicodeError, csv.Error) as error:
        sys.exit(f"error reading run files: {error}")

    for u in unchecked:
        print(f"  unchecked: {u}")
    if problems:
        print(f"{len(problems)} problem(s) in {run.name}:")
        for p in problems[:40]:
            print(f"  - {p}")
        if len(problems) > 40:
            print(f"  … and {len(problems) - 40} more")
        sys.exit(1)
    if unchecked:
        print(f"{len(unchecked)} record(s) could not be checked; the run is not verified.")
        sys.exit(2)
    with (run / "evidence.csv").open(newline="", encoding="utf-8-sig") as handle:
        n = len(list(csv.DictReader(handle)))
    scope = "structure only (--offline), retractions unchecked" if args.offline else "every identifier resolved"
    print(f"{run.name}: {n} records pass ({scope}); required metadata present, "
          "bibliography identifiers agree, query-response links exist, screening counts reconcile. "
          "Full-text access and claim support require separate review.")


if __name__ == "__main__":
    main()
