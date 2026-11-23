"""Exercise preprint matching through the literature run checker."""
import csv
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote


helper = Path(__file__).resolve().parents[1] / "litsearch" / "verify.py"
spec = importlib.util.spec_from_file_location("litsearch_verify", helper)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

PREPRINT = "10.1234/preprint"
ARTICLE = "10.1234/article"


def record(doi, title, year, kind, relations):
    return {"DOI": doi, "title": [title], "issued": {"date-parts": [[year]]},
            "type": kind, "author": [{"family": "Cole"}], "relation": relations}


def doi_link(doi):
    return [{"id-type": "doi", "id": doi.upper()}]


class PreprintVersions(unittest.TestCase):
    def check_run(self, records, included):
        def lookup(url, contact=None):
            doi = unquote(url.split("/works/")[1])
            return json.dumps({"message": records[doi]}).encode()

        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            for name in ("protocol.md", "README.md", "unverified.md"):
                (run / name).touch()
            (run / "raw").mkdir()
            (run / "raw/query.json").write_text(json.dumps(list(records.values())))
            (run / "queries.md").write_text("- [query](raw/query.json)\n")
            with (run / "screening.csv").open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["id", "stage", "decision", "reason"])
                for doi in records:
                    decision = "included" if doi in included else "duplicate"
                    reason = "" if doi in included else f"Same study as {included[0]}. See raw/query.json."
                    writer.writerow([doi, "abstract", decision, reason])
            with (run / "evidence.csv").open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["id", "title", "author", "year", "source", "evidence"])
                for doi in included:
                    item = records[doi]
                    writer.writerow([doi, item["title"][0], "Cole", item["issued"]["date-parts"][0][0],
                                     "Crossref", "abstract"])
            (run / "references.bib").write_text("\n".join(
                "@article{ref%d, doi={%s}}" % (i, doi) for i, doi in enumerate(included)))
            (run / "references.ris").write_text("\n".join(f"TY  - JOUR\nDO  - {doi}\nER  -" for doi in included))
            before = {p: p.read_bytes() for p in run.rglob("*") if p.is_file()}
            report = io.StringIO()
            with patch.object(verify, "get", side_effect=lookup), redirect_stdout(report):
                problems, unchecked = verify.check(run, None, 0.9, False)
            self.assertEqual(before, {p: p.read_bytes() for p in run.rglob("*") if p.is_file()})
            self.assertEqual(unchecked, [])
            return problems, report.getvalue()

    def test_explicit_link_from_either_version_counts_the_study_once(self):
        for source in (PREPRINT, ARTICLE):
            with self.subTest(source=source):
                records = {PREPRINT: record(PREPRINT, "An early working title", 2023, "posted-content", {}),
                           ARTICLE: record(ARTICLE, "A completely revised title", 2025, "journal-article", {})}
                if source == PREPRINT:
                    records[source]["relation"]["is-preprint-of"] = doi_link(ARTICLE)
                else:
                    records[source]["relation"]["has-preprint"] = doi_link(PREPRINT)
                problems, _ = self.check_run(records, [ARTICLE, PREPRINT])
                self.assertEqual(len(problems), 1)
                self.assertIn(PREPRINT, problems[0])
                self.assertIn(ARTICLE, problems[0])
                for chosen in (ARTICLE, PREPRINT):
                    self.assertEqual(self.check_run(records, [chosen])[0], [])

    def test_similar_titles_flag_review_without_combining_records(self):
        records = {PREPRINT: record(PREPRINT, "Local wages and employment", 2023, "posted-content",
                                   {"references": doi_link(ARTICLE)}),
                   ARTICLE: record(ARTICLE, "Local wages and employment.", 2025, "journal-article", {})}
        problems, report = self.check_run(records, list(records))
        self.assertEqual(problems, [])
        self.assertIn(f"Possible versions: {PREPRINT} and {ARTICLE}", report)

    def test_arxiv_journal_doi_matches_article_indexed_by_pmid(self):
        xml = (f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">'
               f'<entry><id>https://arxiv.org/abs/2401.12345v2</id><title>Draft</title>'
               f'<arxiv:doi>{ARTICLE.upper()}</arxiv:doi></entry></feed>').encode()
        pmid = "12345678"
        pubmed = {"result": {pmid: {"pubtype": ["Journal Article"], "references": [],
                                   "articleids": [{"idtype": "doi", "value": ARTICLE}]}}}
        replies = [xml, json.dumps({"message": {"DOI": ARTICLE}}), json.dumps(pubmed)]
        with patch.object(verify, "get", side_effect=replies):
            records = {"2401.12345v2": verify.fetch("2401.12345v2", None),
                       pmid: verify.fetch(pmid, None)}
        self.assertEqual(verify.preprint_pairs(records), ({("2401.12345v2", pmid)}, set()))
