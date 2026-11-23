"""Check how retraction metadata affects an included paper and the search report."""
import contextlib
import csv
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


helper = Path(__file__).resolve().parents[1] / "litsearch" / "verify.py"
spec = importlib.util.spec_from_file_location("litsearch_verify", helper)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

ARTICLE = "10.1234/paper"
NOTICE = "10.1234/retraction"
ARTICLE_RECORD = {"DOI": ARTICLE, "title": ["Example article"], "author": [{"family": "Lee"}],
                  "issued": {"date-parts": [[2024]]}}


class RetractionChecks(unittest.TestCase):
    def run_check(self, record, reason=None):
        # Omit the new column entirely unless the researcher records a reason.
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            for name in ("protocol.md", "unverified.md", "README.md"):
                (run / name).touch()
            (run / "raw").mkdir()
            (run / "raw/query.json").write_text("{}")
            (run / "queries.md").write_text("- [response](raw/query.json)\n")
            (run / "screening.csv").write_text(f"id,decision\n{ARTICLE},included\n")
            (run / "references.bib").write_text("@article{paper, doi={" + ARTICLE + "}}")
            (run / "references.ris").write_text(f"TY  - JOUR\nDO  - {ARTICLE}\nER  -\n")
            row = dict(id=ARTICLE, title="Example article", author="Lee", year="2024",
                       evidence="abstract", source="Crossref")
            if reason is not None:
                row["retraction_inclusion_reason"] = reason
            with (run / "evidence.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            output = io.StringIO()
            with patch.object(verify, "get") as get, contextlib.redirect_stdout(output):
                if isinstance(record, Exception):
                    get.side_effect = record
                else:
                    get.return_value = json.dumps({"message": record}).encode()
                problems, unchecked = verify.check(run, None, 0.9, False)
            return problems, unchecked, output.getvalue()

    def test_retraction_stays_visible_after_inclusion_decision(self):
        record = {**ARTICLE_RECORD, "updated-by": [{"type": "correction", "DOI": "10.1234/erratum"},
                                                   {"type": "retraction", "DOI": NOTICE}]}
        problems, unchecked, _ = self.run_check(record)
        self.assertEqual(unchecked, [])
        self.assertIn("https://doi.org/" + NOTICE, problems[0])
        self.assertNotIn("erratum", problems[0])
        reason = "The review studies retraction notices."
        problems, unchecked, report = self.run_check(record, reason)
        self.assertEqual((problems, unchecked), ([], []))
        self.assertIn("https://doi.org/" + NOTICE, report)
        self.assertIn(reason, report)

    def test_outgoing_notice_and_correction_do_not_flag_the_article(self):
        record = {**ARTICLE_RECORD, "update-to": [{"type": "retraction", "DOI": "10.1234/other"}],
                  "updated-by": [{"type": "correction", "DOI": "10.1234/erratum"}]}
        problems, unchecked, report = self.run_check(record)
        self.assertEqual((problems, unchecked), ([], []))
        self.assertIn("no retraction notice found in Crossref", report)

    def test_unreachable_or_malformed_metadata_remains_unchecked(self):
        for response in (verify.Unreachable("timeout"), {**ARTICLE_RECORD, "updated-by": None}):
            with self.subTest(response=response):
                problems, unchecked, report = self.run_check(response)
                self.assertEqual(problems, [])
                self.assertTrue(unchecked)
                self.assertNotIn("no retraction notice", report)

    def test_pubmed_distinguishes_notice_direction_and_missing_notice_id(self):
        refs = [{"reftype": "Retraction of", "pmid": 1234},
                {"reftype": "Retraction in", "pmid": 5678}]
        status = verify.pubmed_retractions({"pubtype": [], "references": refs}, "111")
        self.assertEqual(status.notices, ("https://pubmed.ncbi.nlm.nih.gov/5678/",))
        status = verify.pubmed_retractions({"pubtype": ["Retraction Notice"], "references": refs[:1]}, "111")
        self.assertFalse(status.notices or status.unavailable)
        status = verify.pubmed_retractions({"pubtype": ["Retracted Publication"]}, "111")
        self.assertIn("notice unavailable", status.notices[0])

    def test_arxiv_identifies_the_journal_version_and_respects_contact_choice(self):
        atom = ('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">'
                '<entry><id>https://arxiv.org/abs/2401.01234v2</id><title>Paper</title>'
                '<arxiv:doi>' + ARTICLE + '</arxiv:doi></entry></feed>').encode()
        record = {**ARTICLE_RECORD, "updated-by": [{"type": "retraction", "DOI": NOTICE}]}
        for recipient, crossref_address in [("both", "reader@example.org"), ("datacite", None)]:
            with self.subTest(recipient=recipient):
                with patch.object(verify, "get", side_effect=[atom, json.dumps({"message": record})]) as get:
                    result = verify.fetch("arxiv:2401.01234v2", "reader@example.org", recipient)
                self.assertEqual(len(get.call_args_list[0].args), 1)
                self.assertEqual(get.call_args_list[1].args[1], crossref_address)
                self.assertIn(ARTICLE, result["retraction"].source)
                self.assertEqual(result["retraction"].notices, ("https://doi.org/" + NOTICE,))
        with patch.object(verify, "get", side_effect=[atom, verify.Unreachable("timeout")]):
            result = verify.fetch("arxiv:2401.01234v2", None)
        self.assertEqual(result["title"], "Paper")
        self.assertIn("timeout", result["retraction"].unavailable)
        self.assertTrue(verify.journal_retractions("", None).unavailable)

    def test_datacite_resolution_preserves_the_unchecked_retraction_status(self):
        record = {"data": {"attributes": {"titles": [{"title": "Dataset"}], "publicationYear": 2024}}}
        with patch.object(verify, "get", side_effect=[b"", json.dumps(record)]):
            result = verify.fetch(ARTICLE, None)
        self.assertEqual(result["title"], "Dataset")
        self.assertTrue(result["retraction"].unavailable)
