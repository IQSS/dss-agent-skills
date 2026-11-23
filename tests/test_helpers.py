"""Regression checks for literature verification and portable skill packaging."""
import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verify = load("litsearch_verify", "litsearch/verify.py")
portability = load("portability", "scripts/check-self-contained.py")


class LiteratureRun(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.checked_source = {"retraction": verify.RetractionCheck("Crossref")}
        self.row = dict(id="10.1234/example", title="Heat exposure and birthweight",
                        author="Smith", year="2024", evidence="abstract", source="crossref")
        for name in ("protocol.md", "unverified.md", "README.md"):
            (self.run / name).write_text("Test fixture\n", encoding="utf-8")
        (self.run / "raw").mkdir()
        (self.run / "raw/search.json").write_text("{}")
        (self.run / "queries.md").write_text("- Crossref; query=heat; [response](raw/search.json)\n")
        self.write_evidence([self.row])
        self.write_screening([dict(id=self.row["id"], decision="included", stage="abstract")])
        self.write_bibliography([self.row["id"]])

    def write_evidence(self, rows, fields=None):
        with (self.run / "evidence.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields or list(self.row), extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    def write_screening(self, rows):
        with (self.run / "screening.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "decision", "stage"])
            writer.writeheader()
            writer.writerows(rows)

    def write_bibliography(self, identifiers):
        bib, ris = [], []
        for index, ident in enumerate(identifiers):
            field = "doi" if verify.DOI.fullmatch(ident) else ("pmid" if verify.PMID.fullmatch(ident) else "eprint")
            bib.append("@article{ref%d, %s={%s}}" % (index, field, ident))
            ris.append("TY  - JOUR\n%s  - %s\nER  -" % ("DO" if field == "doi" else "AN", ident))
        (self.run / "references.bib").write_text("\n".join(bib))
        (self.run / "references.ris").write_text("\n".join(ris))

    def check(self, offline=True):
        return verify.check(self.run, None, 0.9, offline)

    def test_complete_run_with_matching_metadata(self):
        with patch.object(verify, "fetch", return_value={**self.checked_source, "title": self.row["title"], "author": "Smith", "year": 2024}):
            self.assertEqual(self.check(offline=False), ([], []))

    def test_missing_column_is_rejected(self):
        self.write_evidence([self.row], fields=["id", "evidence", "source"])
        problems, _ = self.check()
        self.assertTrue(any("missing required columns" in p for p in problems))

    def test_required_values_cannot_be_blank(self):
        for field in self.row:
            with self.subTest(field=field):
                self.write_evidence([dict(self.row, **{field: ""})])
                problems, _ = self.check()
                self.assertTrue(any("missing " + field in p for p in problems))

    def test_duplicate_and_bad_identifier_checked_offline(self):
        self.write_evidence([self.row, dict(self.row, id="10.1234/EXAMPLE")])
        self.assertTrue(any("also on line" in p for p in self.check()[0]))
        self.write_evidence([dict(self.row, id="not-an-identifier")])
        self.assertTrue(any("unsupported identifier" in p for p in self.check()[0]))

    def test_missing_source_metadata_remains_unchecked(self):
        with patch.object(verify, "fetch", return_value={**self.checked_source, "title": self.row["title"]}):
            problems, unchecked = self.check(offline=False)
        self.assertEqual(problems, [])
        self.assertTrue(any("missing author, year" in p for p in unchecked))

    def test_unreachable_and_malformed_sources_are_not_verified(self):
        for error in (verify.Unreachable("offline"), json.JSONDecodeError("bad response", "?", 0)):
            with self.subTest(error=type(error).__name__), patch.object(verify, "fetch", side_effect=error):
                problems, unchecked = self.check(offline=False)
                self.assertEqual(problems, [])
                self.assertTrue(unchecked)

    def test_unresolved_record_differs_from_network_failure(self):
        with patch.object(verify, "fetch", return_value=None):
            problems, unchecked = self.check(offline=False)
        self.assertTrue(any("does not resolve" in p for p in problems))
        self.assertEqual(unchecked, [])

    def test_title_author_and_year_mismatch_detected(self):
        with patch.object(verify, "fetch", return_value={**self.checked_source, "title": "A different paper", "author": "Jones", "year": 2020}):
            problems, _ = self.check(offline=False)
        self.assertTrue(any("title does not match" in p for p in problems))
        self.assertTrue(any("first author" in p for p in problems))
        self.assertTrue(any("year" in p for p in problems))

    def test_author_substring_is_not_a_match(self):
        self.write_evidence([dict(self.row, author="Smithson")])
        with patch.object(verify, "fetch", return_value={**self.checked_source, "title": self.row["title"], "author": "Smith", "year": 2024}):
            self.assertTrue(any("first author" in p for p in self.check(offline=False)[0]))

    def test_online_first_year_tolerance(self):
        with patch.object(verify, "fetch", return_value={**self.checked_source, "title": self.row["title"], "author": "Smith", "year": "2023"}):
            self.assertEqual(self.check(offline=False), ([], []))

    def test_all_identifier_types_required_in_both_bibliographies(self):
        ids = [self.row["id"], "12345678", "2401.01234v2"]
        self.write_evidence([dict(self.row, id=ident) for ident in ids])
        self.write_screening([dict(id=ident, decision="included", stage="abstract") for ident in ids])
        self.write_bibliography(ids)
        self.assertEqual(self.check(), ([], []))
        (self.run / "references.ris").write_text("TY  - JOUR\nDO  - " + ids[0] + "\nER  -\n")
        problems, _ = self.check()
        self.assertTrue(any("12345678" in p and "references.ris" in p for p in problems))
        self.assertTrue(any("2401.01234v2" in p and "references.ris" in p for p in problems))

    def test_numbers_inside_doi_are_not_extra_identifiers(self):
        text = "@article{x, doi={10.1234/2401.01234}, year={2024}}"
        self.assertEqual(verify.bibliography_ids(text, ".bib"), {"10.1234/2401.01234"})

    def test_queries_must_link_existing_response_within_raw(self):
        for target in ("raw/missing.json", "raw/../protocol.md"):
            with self.subTest(target=target):
                (self.run / "queries.md").write_text("- query=heat; [response](" + target + ")\n")
                self.assertTrue(any("missing or outside raw" in p for p in self.check()[0]))

    def test_screening_counts_and_zero_results(self):
        self.write_screening([dict(id=self.row["id"], decision="excluded", stage="abstract")])
        self.assertTrue(any("marks 0 records included" in p for p in self.check()[0]))
        self.write_evidence([])
        self.write_bibliography([])
        self.assertEqual(self.check(), ([], []))

    def test_offline_cli_does_not_claim_live_verification(self):
        result = subprocess.run([sys.executable, str(ROOT / "litsearch/verify.py"), str(self.run), "--offline"],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("structure only", result.stdout)
        self.assertNotIn("every identifier resolved", result.stdout)

    def test_arxiv_requested_version_is_preserved(self):
        atom = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/2401.01234v2</id><title>A title</title><author><name>Jane Smith</name></author><published>2024-01-03</published></entry></feed>'
        with patch.object(verify, "get", return_value=atom) as get:
            result = verify.fetch("arxiv:2401.01234v2", None)
        self.assertIn("id_list=2401.01234v2", get.call_args.args[0])
        self.assertEqual(result["author"], "Smith")

    def test_doi_falls_back_to_datacite(self):
        record = {"data": {"attributes": {"titles": [{"title": self.row["title"]}],
                  "creators": [{"familyName": "Smith"}], "publicationYear": 2024}}}
        with patch.object(verify, "get", side_effect=[b"", json.dumps(record).encode()]) as get:
            found = verify.fetch(self.row["id"], None)
        self.assertEqual(found["year"], 2024)
        self.assertIn("api.datacite.org", get.call_args.args[0])


class Portability(unittest.TestCase):
    def test_project_instructions_allowed_but_private_dependency_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "sample"
            skill.mkdir()
            source = skill / "SKILL.md"
            source.write_text("---\nname: sample\ndescription: Review a supplied project.\n---\nRead the project's AGENTS.md.\n")
            self.assertEqual(portability.check_skill(skill), [])
            sample_path = "/" + "Users/example/hidden/settings.md"
            source.write_text(source.read_text() + f"Read {sample_path}.\n")
            self.assertTrue(portability.check_skill(skill))

    def test_bundled_reference_is_also_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "sample"
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: sample\ndescription: Use a supplied template.\n---\nRead references/template.md.\n")
            sample_path = "~/" + ".config/example-tool/settings.md"
            (skill / "references/template.md").write_text(f"Read {sample_path}.\n")
            self.assertTrue(any("private" in p for p in portability.check_skill(skill)))

    def test_external_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            skill = base / "sample"
            skill.mkdir()
            (base / "private.md").write_text("Private file")
            (skill / "SKILL.md").write_text("---\nname: sample\ndescription: Review input.\n---\nRead linked.md.\n")
            (skill / "linked.md").symlink_to(base / "private.md")
            self.assertTrue(any("links outside" in p for p in portability.check_skill(skill)))

    def test_source_check_catches_comments_and_runtime_output(self):
        for text in ("# See docs/" + "notes/draft.md", 'print("private ' + 'development site")'):
            with self.subTest(text=text):
                self.assertTrue(portability.check_public_text(text))

    def test_source_check_accepts_public_product_documentation(self):
        text = "Read the supplied project instructions and bundled references/example-paper.md."
        self.assertEqual(portability.check_public_text(text), [])

    def test_excluded_text_is_not_echoed_in_failure_output(self):
        excluded = "example-unpublished-project"
        problems = portability.check_public_text(f"See {excluded}.", (excluded,))
        self.assertTrue(problems)
        self.assertNotIn(excluded, "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
