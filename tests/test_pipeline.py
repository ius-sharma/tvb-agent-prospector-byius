import unittest

from src.discovery import TVBDiscoveryAgent
from src.enrichment import is_generic_email
from src.validator import has_disqualifying_status, parse_funding_amount, validate_tvb_candidate


class ValidatorTests(unittest.TestCase):
    def test_parse_funding_amount_millions(self):
        self.assertEqual(parse_funding_amount("$3.5M"), 3_500_000)
        self.assertEqual(parse_funding_amount("2 million"), 2_000_000)

    def test_generic_email_detection(self):
        self.assertTrue(is_generic_email("info@example.com"))
        self.assertFalse(is_generic_email("founder@example.com"))

    def test_acquired_company_is_disqualified(self):
        candidate = {
            "company_name": "ExampleCo acquired by BuyerCo",
            "description": "B2B SaaS platform",
            "funding_revenue_usd": 2_000_000,
            "headquarters": "London, United Kingdom",
            "executive_name": "Jane Founder",
            "verified_email": "jane@example.com",
        }
        self.assertTrue(has_disqualifying_status(candidate))

    def test_pipeline_shape_without_live_search(self):
        result = TVBDiscoveryAgent().run_pipeline(include_live_search=False)
        self.assertIn("qualified", result)
        self.assertIn("needs_review", result)
        self.assertIn("queries", result)
        self.assertGreaterEqual(result["qualified_count"], 15)


class QualificationTests(unittest.TestCase):
    def test_candidate_with_out_of_range_funding_fails(self):
        candidate = {
            "company_name": "TooBig AI",
            "description": "AI automation platform",
            "funding_revenue_usd": 25_000_000,
            "headquarters": "Bengaluru, India",
            "executive_name": "Asha Founder",
            "verified_email": "asha@example.com",
        }
        is_qualified, audit = validate_tvb_candidate(candidate)
        self.assertFalse(is_qualified)
        self.assertFalse(audit["funding_valid"])


if __name__ == "__main__":
    unittest.main()
