"""Check which services receive a supplied contact email, without using the network."""
import importlib.util
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch


skill_path = Path(__file__).resolve().parents[1] / "litsearch" / "verify.py"
spec = importlib.util.spec_from_file_location("litsearch_verify", skill_path)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class ContactPreferences(unittest.TestCase):
    def test_citation_lookups_and_redirects_respect_recipients(self):
        email = "reader@example.org"
        crossref = "api.crossref.org"
        datacite = "api.datacite.org"
        expected_hosts = [crossref, datacite, "eutils.ncbi.nlm.nih.gov", "export.arxiv.org"]
        missing = urllib.error.HTTPError("", 404, "Not Found", {}, None)
        self.addCleanup(missing.close)
        for address, options, recipients in [
            (None, {}, set()),
            (None, {"mailto_to": "both"}, set()),
            (email, {}, {crossref}),
            (email, {"mailto_to": "crossref"}, {crossref}),
            (email, {"mailto_to": "datacite"}, {datacite}),
            (email, {"mailto_to": "both"}, {crossref, datacite}),
            (email, {"mailto_to": "neither"}, set()),
        ]:
            with self.subTest(address=address, options=options):
                with patch("urllib.request.urlopen", side_effect=missing) as send:
                    for identifier in ("10.1234/example", "12345678", "2401.01234"):
                        self.assertIsNone(verify.fetch(identifier, address, **options))

                requests = [call.args[0] for call in send.call_args_list]
                self.assertEqual([request.host for request in requests], expected_hosts)
                for request in requests:
                    self.assertEqual(email in request.get_header("User-agent"), request.host in recipients)
                    self.assertNotIn(email, request.full_url)
                    redirected = urllib.request.HTTPRedirectHandler().redirect_request(
                        request, None, 302, "Found", {}, "https://example.org/record")
                    self.assertNotIn(email, str(redirected.header_items()))
