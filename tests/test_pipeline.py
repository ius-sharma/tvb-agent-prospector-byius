import unittest
from bs4 import BeautifulSoup

from src.discovery import TVBDiscoveryAgent
from src.enrichment import is_generic_email, resolve_executive_contact, MX_CACHE
from src.validator import (
    has_disqualifying_status,
    parse_funding_amount,
    validate_tvb_candidate,
    is_tech_platform,
    has_minimal_us_presence,
)


# Pre-warm common test domains in MX_CACHE for deterministic, sub-second test execution
MX_CACHE["example.com"] = True
MX_CACHE["synthesia.io"] = True
MX_CACHE["qure.ai"] = True


class ValidatorTests(unittest.TestCase):
    def test_parse_funding_amount_millions(self):
        self.assertEqual(parse_funding_amount("$3.5M"), 3_500_000)
        self.assertEqual(parse_funding_amount("2 million"), 2_000_000)
        self.assertEqual(parse_funding_amount("€4.2M"), 4_200_000)

    def test_generic_email_detection(self):
        self.assertTrue(is_generic_email("info@example.com"))
        self.assertTrue(is_generic_email("support@company.co"))
        self.assertTrue(is_generic_email("sales@startup.io"))
        self.assertFalse(is_generic_email("founder@example.com"))
        self.assertFalse(is_generic_email("victor@synthesia.io"))

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

    def test_us_headquarters_is_disqualified(self):
        self.assertFalse(has_minimal_us_presence("San Francisco, CA, USA", "Headquarters"))
        self.assertFalse(has_minimal_us_presence("Austin, Texas", "US operations"))
        self.assertTrue(has_minimal_us_presence("London, United Kingdom", "No US office"))
        self.assertTrue(has_minimal_us_presence("Bengaluru, India", "Targeting US entry"))

    def test_non_tech_platform_fails(self):
        self.assertFalse(is_tech_platform("Local brick-and-mortar bakery store", "Food & Beverage"))
        self.assertTrue(is_tech_platform("AI-driven cloud vulnerability scanner", "Cybersecurity"))

    def test_contact_resolver_direct_vs_pattern(self):
        # Direct mailto extraction
        soup = BeautifulSoup('<a href="mailto:victor@synthesia.io">Contact Victor</a>', 'html.parser')
        res = resolve_executive_contact(soup, "Victor Riparbelli announcement", "synthesia.io", "Victor Riparbelli")
        self.assertTrue(res["verified"])
        self.assertEqual(res["source"], "direct_extraction")
        self.assertEqual(res["email"], "victor@synthesia.io")

        # Pattern derivation fallback with explicit provenance
        soup_empty = BeautifulSoup('<p>Victor Riparbelli raised a seed round.</p>', 'html.parser')
        res2 = resolve_executive_contact(soup_empty, "Press release text", "synthesia.io", "Victor Riparbelli")
        self.assertTrue(res2["verified"])
        self.assertEqual(res2["source"], "pattern_inference")
        self.assertEqual(res2["email"], "victor@synthesia.io")


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

    def test_fully_qualified_candidate_passes(self):
        candidate = {
            "company_name": "AgenticFlow",
            "description": "Autonomous enterprise workflow platform and API",
            "orbit": "AI & Automation",
            "sub_sector": "AI Agents",
            "funding_revenue_usd": 3_200_000,
            "headquarters": "London, United Kingdom",
            "executive_name": "Oliver Twist",
            "verified_email": "oliver@synthesia.io",
        }
        is_qualified, audit = validate_tvb_candidate(candidate)
        self.assertTrue(is_qualified)
        self.assertTrue(audit["funding_valid"])
        self.assertTrue(audit["tech_valid"])
        self.assertTrue(audit["non_us_valid"])
        self.assertTrue(audit["contact_valid"])


if __name__ == "__main__":
    unittest.main()
