"""
Autonomous web discovery agent module.

The agent generates TVB-specific search vectors, records live web findings, converts
search snippets into candidate records, and validates every candidate before it can
enter the qualified lead table.
"""

import json
import os
import random
import re
import time
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

try:
    from ddgs import DDGS

    DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS

        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False

from src.enrichment import extract_emails, verify_executive_email
from src.tvb_context import TVB_HUBS, TVB_ORBITS
from src.validator import parse_funding_amount, validate_tvb_candidate


FUNDING_PATTERN = re.compile(
    r"(?P<amount>[$€£]?\s?\d+(?:\.\d+)?\s?(?:m|mn|million|k)?)",
    re.IGNORECASE,
)


class TVBDiscoveryAgent:
    """
    Autonomous prospecting agent for TVB's screening assignment.

    The reviewed cache keeps the hosted demo stable, while every triggered run also
    performs live web discovery and shows the audit trail for newly found candidates.
    """

    def __init__(self, seeds_file: str = "data/verified_seeds.json", random_seed: int = 42):
        self.seeds_file = seeds_file
        self.random = random.Random(random_seed)
        self.reviewed_cache = self._load_reviewed_cache()

    def _load_reviewed_cache(self) -> List[Dict[str, Any]]:
        """Loads reviewed fallback candidates for stable hosted demos."""
        if os.path.exists(self.seeds_file):
            try:
                with open(self.seeds_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                    return records if isinstance(records, list) else []
            except Exception as exc:
                print(f"Error loading reviewed cache: {exc}")
        return []

    def generate_search_queries(self, count: int = 10) -> List[str]:
        """Generates dynamic queries combining TVB Orbits and non-US hubs."""
        queries = []
        orbit_keys = list(TVB_ORBITS.keys())
        hub_keys = list(TVB_HUBS.keys())

        templates = [
            '"{subsector}" startup raised "$1M" OR "$2M" OR "$3M" OR "$4M" "{hub}" founder',
            '"{orbit}" seed round "$2 million" OR "$3 million" "{hub}" CEO email',
            '"{hub}" tech platform "$1.5M" OR "$3M" funding announcement co-founder',
            '"{subsector}" SaaS "{hub}" "raised" "seed" founder email',
            '"{hub}" startup "raised $4 million" "CEO" "platform"',
        ]

        for _ in range(max(count, 1)):
            orbit = self.random.choice(orbit_keys)
            subsector = self.random.choice(TVB_ORBITS[orbit])
            hub = self.random.choice(hub_keys)
            hub_location = self.random.choice(TVB_HUBS[hub])
            template = self.random.choice(templates)
            queries.append(
                template.format(
                    orbit=orbit,
                    subsector=subsector,
                    hub=hub_location,
                )
            )

        return list(dict.fromkeys(queries))

    def run_live_web_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Performs a live DuckDuckGo search and normalizes result fields."""
        if not DDGS_AVAILABLE:
            return []

        results = []
        try:
            with DDGS() as ddgs:
                for item in ddgs.text(query, max_results=max_results):
                    href = item.get("href") or item.get("url") or ""
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "href": href,
                            "body": item.get("body", ""),
                            "query": query,
                        }
                    )
        except Exception as exc:
            print(f"Web search error on query '{query}': {exc}")

        return results

    def _domain_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host

    def _guess_company_name(self, title: str, domain: str) -> str:
        title = title or ""
        cleaned = re.split(r"\s[-|:]\s", title, maxsplit=1)[0].strip()
        cleaned = re.sub(
            r"\b(raises?|raised|secures?|secured|announces?|funding|seed round|pre-series a)\b.*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip(" -:|")
        if cleaned:
            return cleaned[:80]

        domain_root = domain.split(".")[0] if domain else "Unknown company"
        return domain_root.replace("-", " ").title()

    def _classify_orbit(self, text: str) -> Tuple[str, str]:
        lowered = text.lower()
        best_orbit = "Enterprise SaaS & Digital Twin"
        best_subsector = "Tech Platform"

        for orbit, subsectors in TVB_ORBITS.items():
            if orbit.lower().replace("&", "and") in lowered:
                best_orbit = orbit
                best_subsector = subsectors[0]
            for subsector in subsectors:
                if subsector.lower() in lowered:
                    return orbit, subsector

        keyword_map = {
            "ai": ("AI & Automation", "Applied AI"),
            "automation": ("AI & Automation", "Enterprise Automation"),
            "security": ("Cybersecurity", "Cloud Security"),
            "health": ("Healthcare & Life Sciences", "Digital Health"),
            "fintech": ("Fintech & Payments", "FinTech SaaS"),
            "payment": ("Fintech & Payments", "Payment Infrastructure"),
            "education": ("Education & Workforce", "EdTech"),
            "learning": ("Education & Workforce", "Enterprise Learning"),
            "travel": ("Travel & Logistics", "TravelTech"),
            "logistics": ("Travel & Logistics", "Logistics Tech"),
            "saas": ("Enterprise SaaS & Digital Twin", "B2B SaaS"),
        }
        for keyword, labels in keyword_map.items():
            if keyword in lowered:
                return labels

        return best_orbit, best_subsector

    def _classify_hub(self, text: str) -> Tuple[str, str]:
        lowered = text.lower()
        for hub_name, locations in TVB_HUBS.items():
            for location in locations:
                if location.lower() in lowered:
                    return hub_name, location
        return "Review Required", ""

    def _extract_funding_evidence(self, text: str) -> Tuple[float, str]:
        match = FUNDING_PATTERN.search(text or "")
        if not match:
            return 0.0, ""
        evidence = match.group("amount")
        return parse_funding_amount(evidence), evidence

    def _pick_verified_email(self, text: str) -> Tuple[str, str]:
        for email in extract_emails(text):
            check = verify_executive_email(email)
            if check["verified"]:
                return check["email"], check["reason"]
        return "", "No non-generic, MX-confirmed executive email found in search text."

    def _candidate_from_search_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        title = item.get("title", "")
        body = item.get("body", "")
        href = item.get("href", "")
        query = item.get("query", "")
        domain = self._domain_from_url(href)
        combined = f"{title} {body}"
        orbit, subsector = self._classify_orbit(combined)
        target_hub, headquarters = self._classify_hub(combined)
        funding_usd, funding_evidence = self._extract_funding_evidence(combined)
        verified_email, email_status = self._pick_verified_email(combined)

        return {
            "company_name": self._guess_company_name(title, domain),
            "website": href,
            "domain": domain,
            "orbit": orbit,
            "sub_sector": subsector,
            "description": body,
            "funding_revenue_usd": funding_usd,
            "funding_stage": "Discovered from search result",
            "funding_evidence": funding_evidence,
            "headquarters": headquarters,
            "target_hub": target_hub,
            "us_presence": "Review required from live source",
            "executive_name": "",
            "executive_title": "",
            "verified_email": verified_email,
            "email_status": email_status,
            "tvb_value_alignment": f"Potential fit for TVB {orbit} if all validation checks pass.",
            "source_type": "Live web discovery",
            "source_url": href,
            "source_urls": [href] if href else [],
            "discovery_query": query,
        }

    def _reviewed_cache_candidates(self) -> List[Dict[str, Any]]:
        records = []
        for lead in self.reviewed_cache:
            record = dict(lead)
            record.setdefault("source_type", "Reviewed cache")
            record.setdefault("source_urls", [])
            record.setdefault("discovery_query", "Reviewed fallback dataset")
            records.append(record)
        return records

    def _dedupe_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped = []
        seen = set()
        for candidate in candidates:
            key = (
                candidate.get("domain")
                or candidate.get("website")
                or candidate.get("company_name", "")
            ).lower()
            if not key or key in seen:
                continue
            deduped.append(candidate)
            seen.add(key)
        return deduped

    def _validate_all(self, candidates: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        qualified = []
        needs_review = []

        for candidate in candidates:
            record = dict(candidate)
            is_qualified, audit = validate_tvb_candidate(record)
            record["audit"] = audit
            record["qualification_status"] = "Qualified" if is_qualified else "Needs review"
            record["disqualification_reasons"] = "; ".join(audit["disqualification_reasons"])
            record["audit_warnings"] = "; ".join(audit["warnings"])
            if is_qualified:
                qualified.append(record)
            else:
                needs_review.append(record)

        return qualified, needs_review

    def run_pipeline(
        self,
        target_count: int = 15,
        progress_callback=None,
        include_live_search: bool = True,
        query_count: int = 10,
        results_per_query: int = 5,
    ) -> Dict[str, Any]:
        """
        Runs the complete prospecting pipeline and returns an auditable result object.
        """
        if progress_callback:
            progress_callback("Loading reviewed fallback dataset...", 0.05)

        live_candidates = []
        raw_results = []
        queries = []

        if include_live_search:
            queries = self.generate_search_queries(count=query_count)
            if progress_callback:
                progress_callback("Generated TVB orbit and hub search vectors.", 0.15)

            for index, query in enumerate(queries):
                if progress_callback:
                    progress = 0.15 + (0.45 * ((index + 1) / max(len(queries), 1)))
                    progress_callback(f"Searching: {query[:80]}", min(progress, 0.60))

                search_items = self.run_live_web_search(query, max_results=results_per_query)
                raw_results.extend(search_items)
                live_candidates.extend(self._candidate_from_search_result(item) for item in search_items)

        if progress_callback:
            progress_callback("Merging live discoveries with reviewed fallback records...", 0.70)

        all_candidates = self._dedupe_candidates(live_candidates + self._reviewed_cache_candidates())

        if progress_callback:
            progress_callback(f"Validating {len(all_candidates)} candidate companies against TVB criteria...", 0.82)

        qualified, needs_review = self._validate_all(all_candidates)
        selected = qualified[: max(target_count, 15)]

        if progress_callback:
            progress_callback(f"Qualified {len(selected)} leads; logged {len(needs_review)} review items.", 1.0)

        return {
            "qualified": selected,
            "needs_review": needs_review,
            "live_discoveries": live_candidates,
            "queries": queries,
            "raw_results_count": len(raw_results),
            "qualified_count": len(selected),
            "qualified_from_live": sum(1 for lead in selected if lead.get("source_type") == "Live web discovery"),
            "qualified_from_cache": sum(1 for lead in selected if lead.get("source_type") == "Reviewed cache"),
            "searched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "search_available": DDGS_AVAILABLE,
        }

    def discover_and_qualify_leads(self, target_count: int = 15, progress_callback=None) -> List[Dict[str, Any]]:
        """
        Backwards-compatible list API used by older versions of the Streamlit app.
        """
        result = self.run_pipeline(target_count=target_count, progress_callback=progress_callback)
        return result["qualified"]
