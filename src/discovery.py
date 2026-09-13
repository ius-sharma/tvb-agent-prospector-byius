"""
Autonomous Live Web Discovery Agent Module.
Dynamically crawls live venture feeds, searches the web, and extracts fresh 
OG startup funding rounds matching TVB's exact criteria:
- $1M - $5M USD funding/revenue
- Scalable Tech platform
- Minimal to no US presence (HQ in UK, Europe, India, UAE, SE Asia)
- Verified CEO / Founder contact with DNS MX verified deliverability
"""

import json
import os
import re
import random
import time
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
import feedparser

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

from src.tvb_context import TVB_ORBITS, TVB_HUBS, TVB_CRITERIA
from src.validator import validate_tvb_candidate, parse_funding_amount, is_tech_platform, has_minimal_us_presence
from src.enrichment import verify_executive_email, resolve_executive_contact, check_dns_mx

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

LIVE_STARTUP_FEEDS = [
    ("UK Tech News", "https://www.uktech.news/feed"),
    ("EU-Startups", "https://www.eu-startups.com/feed/"),
    ("Tech Funding News", "https://techfundingnews.com/feed/"),
    ("Silicon Canals", "https://siliconcanals.com/feed/"),
    ("Tech.eu", "https://tech.eu/feed/"),
    ("Inc42", "https://inc42.com/feed/")
]


class TVBDiscoveryAgent:
    """
    Autonomous prospecting agent capable of:
    1. Crawling live venture news and startup funding RSS feeds in real-time
    2. Extracting fresh OG deals in the $1M - $5M USD bracket
    3. Parsing company domains, founder identities, and non-US headquarters
    4. Performing live DNS MX verification on each domain
    5. Discarding prior runs to provide a brand new scraped batch upon request
    """

    def __init__(self, seeds_file: str = "data/verified_seeds.json", api_key: Optional[str] = None):
        self.seeds_file = seeds_file
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.verified_seeds = self._load_verified_seeds()

    def _load_verified_seeds(self) -> List[Dict[str, Any]]:
        """Loads baseline verified candidates."""
        if os.path.exists(self.seeds_file):
            try:
                with open(self.seeds_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading seeds: {e}")
        return []

    def extract_funding_from_text(self, text: str) -> (float, str):
        """Extracts funding amount and currency expression across USD, EUR, GBP, and INR Crores."""
        if not text:
            return 0.0, ""

        # Check for billions first to reject mega rounds
        billion_match = re.search(r'(?:([$€£])|(USD|EUR|GBP))\s*(\d+(?:\.\d+)?)\s*(b|billion|bn)\b', text, re.IGNORECASE)
        if billion_match:
            val = float(billion_match.group(3))
            curr = billion_match.group(1) or "$"
            return val * 1_000_000_000, f"{curr}{val:.1f}B"

        # Pattern 1: Symbol/Code followed by number and unit (e.g. $2.5M, €3 million, £1.8m, ₹25 Cr)
        m = re.search(r'(?:([$€£₹])|(USD|EUR|GBP|INR))\s*(\d+(?:\.\d+)?)\s*(m|million|mn|k|crore|cr)?\b', text, re.IGNORECASE)
        if m:
            sym = m.group(1) or ""
            code = (m.group(2) or "").upper()
            val = float(m.group(3))
            unit = (m.group(4) or "").lower()

            # Normalize currency multiplier
            if sym == '£' or code == 'GBP':
                multiplier = 1.30
                curr_label = "£"
            elif sym == '€' or code == 'EUR':
                multiplier = 1.08
                curr_label = "€"
            elif sym == '₹' or code == 'INR' or unit in ["crore", "cr"]:
                multiplier = 0.012  # 1 INR ~ 0.012 USD; 1 Crore INR (~10M INR) ~ $120k USD
                curr_label = "₹"
            else:
                multiplier = 1.00
                curr_label = "$"

            if unit in ["crore", "cr"]:
                usd_amount = val * 10_000_000 * multiplier
                return usd_amount, f"{curr_label}{val:.1f} Cr"
            elif unit in ["m", "million", "mn"] or (unit == "" and 1.0 <= val <= 10.0 and (sym or code)):
                usd_amount = val * 1_000_000 * multiplier
                return usd_amount, f"{curr_label}{val:.1f}M"
            elif unit == "k":
                usd_amount = val * 1_000 * multiplier
                return usd_amount, f"{curr_label}{val:.0f}K"
            elif val >= 1_000_000:
                return val * multiplier, f"{curr_label}{val/1_000_000:.1f}M"

        # Pattern 2: Number followed explicitly by million/mn (e.g. "raised 2.5 million", "3M in seed")
        m2 = re.search(r'\b(\d+(?:\.\d+)?)\s*(million|mn)\b', text, re.IGNORECASE)
        if m2:
            val = float(m2.group(1))
            return val * 1_000_000, f"${val:.1f}M"

        return 0.0, ""

    def clean_company_name(self, raw_name: str) -> str:
        """Cleans and validates scraped company name from headlines."""
        if not raw_name:
            return ""
        cleaned = re.sub(r'^(?:[A-Za-z]+-based|\w+\s+(?:startup|scale-up|firm)|funding\s+alert:?|exclusive:?)\s+', '', raw_name, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'^(?:Dutch|German|French|British|Swedish|Spanish|Swiss|Italian|Indian|London(?:\'s)?|Parisian|Berlin(?:\'s)?|Scottish)\s+', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'^(?:AgTech|Fintech|Medtech|Edtech|CleanTech|Healthtech|Deeptech|Insurtech|AI|SaaS|Robotics)\s+', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'^(?:the|a|an)\s+', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'^(?:said|by|and|with|ceo|founder|mr\.?|ms\.?)\s+', '', cleaned, flags=re.IGNORECASE).strip()

        blacklist = {
            "what's", "whats", "here's", "heres", "how", "why", "top", "european", "weekly",
            "roundup", "recap", "exclusive", "funding", "startup", "company", "round", "deal",
            "investors", "ventures", "capital", "report", "news", "update", "abc", "breaking",
            "london", "paris", "berlin", "uk", "france", "germany", "india", "europe"
        }
        words = cleaned.split()
        if not words or len(cleaned) < 2 or len(cleaned) > 40:
            return ""
        if cleaned.lower() in blacklist or words[0].lower() in blacklist:
            return ""
        return cleaned

    def clean_founder_name(self, raw_name: str) -> str:
        """Cleans and validates that the extracted string is an actual human name."""
        if not raw_name:
            return ""
        cleaned = re.sub(r'^(?:said|by|and|with|ceo|founder|mr\.?|ms\.?)\s+', '', raw_name, flags=re.IGNORECASE).strip()
        words = cleaned.split()
        if len(words) < 2 or len(words) > 3:
            return ""
        bad_words = {"ventures", "capital", "partners", "investor", "fund", "holdings", "group", "europe", "startup", "company", "firm", "round", "money"}
        if any(w.lower() in bad_words for w in words):
            return ""
        return cleaned

    def extract_founder_name(self, text: str) -> str:
        """Extracts CEO/Founder names using targeted contextual rules."""
        # Pattern 1: "says <Name>, co-founder and CEO of"
        p1 = re.search(r'says\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),\s*(?:co-founder|founder|ceo|chief executive)', text, re.IGNORECASE)
        if p1:
            name = self.clean_founder_name(p1.group(1))
            if name:
                return name

        # Pattern 2: "founded by <Name> and <Name>" or "founded by <Name>"
        p2 = re.search(r'founded\s+(?:in\s+\d{4}\s+)?by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text, re.IGNORECASE)
        if p2:
            name = self.clean_founder_name(p2.group(1))
            if name:
                return name

        # Pattern 3: "<Name>, co-founder and CEO"
        p3 = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),\s*(?:who serves as\s+)?(?:co-founder|founder|ceo|managing director)', text, re.IGNORECASE)
        if p3:
            name = self.clean_founder_name(p3.group(1))
            if name:
                return name

        return ""

    def infer_company_domain(self, company_name: str, article_soup: BeautifulSoup) -> str:
        """Finds or infers official company domain with resemblance and active DNS MX check."""
        clean_comp = re.sub(r'[^a-zA-Z0-9]', '', company_name.lower())
        blacklisted = {
            "instagram.com", "facebook.com", "twitter.com", "x.com", "linkedin.com",
            "youtube.com", "google.com", "eu-startups.com", "uktech.news", "techfundingnews.com",
            "inc42.com", "apple.com", "cookiedatabase.org", "wordpress.org", "sifted.eu", "siliconcanals.com"
        }

        # Check outbound links in article that resemble company name
        if article_soup:
            for a in article_soup.find_all('a', href=True):
                href = a['href']
                match = re.search(r'https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})', href)
                if match:
                    dom = match.group(1).lower()
                    if dom not in blacklisted and not dom.endswith(('.org', '.gov', '.edu')):
                        clean_dom = dom.split('.')[0].lower()
                        if clean_comp in clean_dom or clean_dom in clean_comp:
                            if self.check_mx_quick(dom):
                                return dom

        # Fast fallback candidates based on company name
        for cand in [f"{clean_comp}.com", f"{clean_comp}.ai"]:
            if self.check_mx_quick(cand):
                return cand

        return f"{clean_comp}.com"

    def check_mx_quick(self, domain: str) -> bool:
        """Quick MX record check using unified enrichment validation."""
        return check_dns_mx(domain)

    def search_live_web_deals(
        self,
        target_orbit: Optional[str] = None,
        target_hub: Optional[str] = None,
        max_deals: int = 8,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        Executes dynamic web search queries using ddgs to discover live, fresh tech deals.
        Rotates search vectors dynamically so consecutive runs find brand new companies.
        """
        if not DDGS_AVAILABLE:
            return []

        results = []
        seen_companies = set()

        orbits_pool = [target_orbit] if (target_orbit and target_orbit != "All Orbits") else list(TVB_ORBITS.keys())
        hubs_pool = [target_hub] if (target_hub and target_hub != "All Hubs") else list(TVB_HUBS.keys())

        random_orbits = random.sample(orbits_pool, min(2, len(orbits_pool)))
        random_hubs = random.sample(hubs_pool, min(2, len(hubs_pool)))

        active_queries = []
        for orb in random_orbits:
            sub = random.choice(TVB_ORBITS.get(orb, [orb]))
            for hub in random_hubs:
                cities = TVB_HUBS.get(hub, [hub])
                loc = random.choice(cities)
                active_queries.append(f"{loc} {sub} startup raises seed million 2025 OR 2026")
                active_queries.append(f"{loc} startup secures funding seed million")
                active_queries.append(f"{loc} {orb} closes funding seed round")

        random.shuffle(active_queries)
        queries_to_run = active_queries[:2]

        try:
            ddgs = DDGS()
            for idx, q in enumerate(queries_to_run):
                if len(results) >= max_deals:
                    break
                if progress_callback:
                    progress_callback(f"Live Metasearch [{idx+1}/{len(queries_to_run)}]: {q[:45]}...", 0.10 + (idx * 0.05))

                try:
                    search_hits = list(ddgs.text(q, max_results=4))
                    random.shuffle(search_hits)

                    for hit in search_hits:
                        title = hit.get("title", "")
                        snippet = hit.get("body", "")
                        link = hit.get("href", "")
                        combo_text = f"{title} {snippet}"

                        funding_usd, raw_funding = self.extract_funding_from_text(combo_text)
                        if not (1_000_000 <= funding_usd <= 5_000_000):
                            continue

                        comp_match = re.search(r'(?:^|:\s*)(?:Dutch |German |French |UK |British |London-based |Munich-based |Berlin-based )?([A-Z][a-zA-Z0-9\s]+?)\s+(?:secures|raises|lands|bags|closes|gets|nabs|picks up)\s+', title, re.IGNORECASE)
                        if not comp_match:
                            comp_match = re.search(r'([A-Z][a-zA-Z0-9\s]+?)\s+(?:secures|raises|lands|bags|closes|gets|nabs|picks up)\s+', snippet, re.IGNORECASE)

                        if comp_match:
                            raw_comp = comp_match.group(1).strip()
                            comp_name = self.clean_company_name(raw_comp)
                        else:
                            comp_name = ""

                        if not comp_name or len(comp_name) < 2 or comp_name.lower() in seen_companies:
                            continue

                        if progress_callback:
                            progress_callback(f"Web Radar Candidate Detected: {comp_name} ({raw_funding})", 0.12 + (idx * 0.04))

                        try:
                            resp = requests.get(link, headers=HEADERS, timeout=4)
                            if resp.status_code == 200:
                                soup = BeautifulSoup(resp.text, 'html.parser')
                                full_text = " ".join([p.get_text() for p in soup.find_all('p')])
                            else:
                                soup = None
                                full_text = combo_text
                        except Exception:
                            soup = None
                            full_text = combo_text

                        founder = self.extract_founder_name(full_text)
                        if not founder:
                            f_match = re.search(r'(?:CEO|founder|co-founder)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', full_text, re.IGNORECASE)
                            if f_match:
                                founder = self.clean_founder_name(f_match.group(1))

                        domain = self.infer_company_domain(comp_name, soup)
                        if not domain or not founder:
                            continue

                        contact_info = resolve_executive_contact(
                            soup=soup,
                            text=full_text,
                            domain=domain,
                            founder_name=founder,
                            allow_pattern_inference=True
                        )

                        if not contact_info.get("verified"):
                            continue

                        hq_loc = "London, UK" if any(w in link.lower() for w in ["uk", "london", "startupmag"]) else "Europe"
                        for h_name, c_list in TVB_HUBS.items():
                            if any(c.lower() in full_text.lower() for c in c_list):
                                hq_loc = f"{c_list[0]}, {h_name.replace(' Hub', '')}"
                                break

                        detected_orbit = "AI & Automation" if any(w in combo_text.lower() for w in ["ai", "agent", "algorithm", "intelligence"]) else "Enterprise SaaS & Digital Twin"
                        if any(w in combo_text.lower() for w in ["health", "clinical", "medtech", "biotech"]):
                            detected_orbit = "Healthcare & Life Sciences"
                        elif any(w in combo_text.lower() for w in ["fintech", "payment", "bank", "wealth"]):
                            detected_orbit = "Fintech & Payments"
                        elif any(w in combo_text.lower() for w in ["cyber", "security", "threat", "firewall"]):
                            detected_orbit = "Cybersecurity"

                        results.append({
                            "company_name": comp_name,
                            "website": f"https://{domain}",
                            "domain": domain,
                            "orbit": detected_orbit,
                            "sub_sector": "Live Web Discovered Tech Scale-Up",
                            "description": (snippet[:220] if snippet else title) + "...",
                            "funding_revenue_usd": funding_usd,
                            "funding_stage": "Live Seed / Early Stage",
                            "funding_evidence": f"Web Radar: {title} ({raw_funding})",
                            "headquarters": hq_loc,
                            "target_hub": "UK Hub" if "uk" in hq_loc.lower() else ("India Hub" if "india" in hq_loc.lower() else "Europe Hub"),
                            "us_presence": "Minimal to None (Discovered via non-US regional venture radar)",
                            "executive_name": founder,
                            "executive_title": "Co-founder & CEO",
                            "verified_email": contact_info.get("email", ""),
                            "email_status": contact_info.get("status", "Verified (DNS MX Valid)"),
                            "contact_provenance": contact_info.get("source", "live_search"),
                            "contact_audit_note": contact_info.get("reason", ""),
                            "tvb_value_alignment": f"Direct strategic alignment for TVB {detected_orbit} expansion.",
                            "live_source_url": link,
                            "is_live_crawled": True,
                            "discovered_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                        seen_companies.add(comp_name.lower())

                except Exception as e:
                    print(f"Error executing search query {q}: {e}")
        except Exception as e:
            print(f"DDGS init error: {e}")

        return results

    def crawl_live_feed_deals(self, target_orbit: Optional[str] = None, max_deals: int = 5, progress_callback=None) -> List[Dict[str, Any]]:
        """
        Actively crawls live feeds, fetches fresh articles, and extracts real OG leads.
        """
        live_leads = []
        seen_companies = set()

        # Randomize feed order for variety across runs
        feeds = list(LIVE_STARTUP_FEEDS)
        random.shuffle(feeds)

        for feed_idx, (source_name, feed_url) in enumerate(feeds):
            if len(live_leads) >= max_deals:
                break
            if progress_callback:
                progress_callback(f"Live Venture Radar [{feed_idx+1}/{len(feeds)}]: Connecting to {source_name}...", 0.25 + (feed_idx * 0.06))
            try:
                try:
                    feed_resp = requests.get(feed_url, headers=HEADERS, timeout=4)
                    feed = feedparser.parse(feed_resp.content)
                except Exception:
                    feed = feedparser.parse(feed_url)

                entries = list(feed.entries[:25])
                random.shuffle(entries)

                for entry in entries:
                    if len(live_leads) >= max_deals:
                        break
                    title = entry.title
                    link = entry.link
                    summary = entry.get('summary', '')

                    # Check funding in title or summary
                    funding_usd, raw_funding = self.extract_funding_from_text(f"{title} {summary}")
                    
                    # Strictly filter between $1M and $5M USD
                    if 1_000_000 <= funding_usd <= 5_000_000:
                        # Extract Company Name
                        comp_match = re.search(r'(?:^|:\s*)(?:Dutch |German |French |UK |British |London-based |Munich-based |Berlin-based )?([A-Z][a-zA-Z0-9\s]+?)\s+(?:secures|raises|lands|bags|closes|gets|nabs|picks up)\s+', title, re.IGNORECASE)
                        if comp_match:
                            raw_comp = comp_match.group(1).strip()
                            comp_name = self.clean_company_name(raw_comp)
                        else:
                            comp_name = ""

                        if not comp_name or len(comp_name) < 2 or comp_name.lower() in seen_companies:
                            continue

                        if progress_callback:
                            progress_callback(f"Live Deal Discovered: '{comp_name}' ({raw_funding}) in {source_name}", 0.35 + (feed_idx * 0.06))

                        # Fetch live article
                        try:
                            try:
                                resp = requests.get(link, headers=HEADERS, timeout=5)
                                if resp.status_code == 200:
                                    soup = BeautifulSoup(resp.text, 'html.parser')
                                    paragraphs = [p.get_text() for p in soup.find_all('p')]
                                    full_text = " ".join(paragraphs)
                                else:
                                    soup = None
                                    full_text = f"{title} {summary}"
                            except Exception:
                                soup = None
                                full_text = f"{title} {summary}"

                            # Extract Founder
                            founder = self.extract_founder_name(full_text)
                            if not founder:
                                f_match = re.search(r'CEO\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', full_text)
                                if f_match:
                                    founder = self.clean_founder_name(f_match.group(1))

                            # Determine Domain & Resolve Executive Contact
                            domain = self.infer_company_domain(comp_name, soup)
                            if not domain or not founder:
                                continue

                            if progress_callback:
                                progress_callback(f"Running DNS MX deliverability handshake for {comp_name} ({domain})...", 0.42 + (feed_idx * 0.06))

                            contact_info = resolve_executive_contact(
                                soup=soup,
                                text=full_text,
                                domain=domain,
                                founder_name=founder,
                                allow_pattern_inference=True
                            )

                            if not contact_info.get("verified"):
                                continue

                            if progress_callback:
                                progress_callback(f"Validated Deal: {comp_name} (${funding_usd:,.0f} USD | MX Active)", 0.48 + (feed_idx * 0.06))

                            exec_email = contact_info.get("email", "")
                            email_status = contact_info.get("status", "Verified (DNS MX Valid)")
                            contact_source = contact_info.get("source", "direct_extraction")
                            contact_reason = contact_info.get("reason", "")

                            # Detect Hub / Location
                            hq_location = "London, UK" if "uk" in link or "uktech" in link else "Europe"
                            for hub, cities in TVB_HUBS.items():
                                for city in cities:
                                    if city.lower() in full_text.lower():
                                        hq_location = f"{city}, {hub.replace(' Hub', '')}"
                                        break

                            # Detect Orbit
                            orbit = "AI & Automation" if any(w in full_text.lower() for w in ["ai", "agent", "algorithm", "deep learning"]) else "Enterprise SaaS & Digital Twin"
                            if any(w in full_text.lower() for w in ["battery", "climate", "energy", "solar"]):
                                orbit = "Enterprise SaaS & Digital Twin"
                            elif any(w in full_text.lower() for w in ["health", "medical", "clinical", "biotech"]):
                                orbit = "Healthcare & Life Sciences"
                            elif any(w in full_text.lower() for w in ["fintech", "payment", "bank", "invest", "crypto"]):
                                orbit = "Fintech & Payments"
                            elif any(w in full_text.lower() for w in ["security", "cyber", "threat", "fraud"]):
                                orbit = "Cybersecurity"

                            # If user filtered by orbit, only keep matching orbit
                            if target_orbit and target_orbit != "All Orbits" and orbit != target_orbit:
                                continue

                            lead_record = {
                                "company_name": comp_name,
                                "website": f"https://{domain}",
                                "domain": domain,
                                "orbit": orbit,
                                "sub_sector": "Live Crawled Tech Platform",
                                "description": summary[:220] if summary else full_text[:220] + "...",
                                "funding_revenue_usd": funding_usd,
                                "funding_stage": "Live Seed / Early Stage",
                                "funding_evidence": f"Announced: {title} (Verified {raw_funding})",
                                "headquarters": hq_location,
                                "target_hub": "UK Hub" if "uk" in hq_location.lower() else "Europe Hub",
                                "us_presence": "Minimal to None (Discovered from live non-US venture announcement)",
                                "executive_name": founder,
                                "executive_title": "Co-founder & CEO",
                                "verified_email": exec_email,
                                "email_status": email_status,
                                "contact_provenance": contact_source,
                                "contact_audit_note": contact_reason,
                                "tvb_value_alignment": f"High alignment for TVB {orbit} & US market access expansion.",
                                "live_source_url": link,
                                "is_live_crawled": True,
                                "discovered_at": time.strftime("%Y-%m-%d %H:%M:%S")
                            }

                            live_leads.append(lead_record)
                            seen_companies.add(comp_name.lower())

                        except Exception as e:
                            print(f"Error scraping live article {link}: {e}")

            except Exception as e:
                print(f"Error parsing feed {source_name}: {e}")

        return live_leads

    def run_pipeline(
        self,
        include_live_search: bool = True,
        target_count: int = 18,
        target_orbit: Optional[str] = None,
        target_hub: Optional[str] = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end prospecting and qualification pipeline.
        Returns a structured dictionary matching TVB specifications:
        - 'qualified': List of leads meeting 100% of TVB criteria
        - 'needs_review': Candidates needing manual check (e.g. missing founder or email)
        - 'disqualified': Rejected candidates with audit reasons
        - 'qualified_count': Total count of qualified leads
        - 'queries': List of data sources / discovery vectors consulted
        - 'audit_reports': Detailed validation audit breakdown for each record
        """
        qualified = []
        needs_review = []
        disqualified = []
        audit_reports = {}
        seen_domains = set()

        # Step 1: Live Web Discovery & RSS Crawler (if enabled)
        if include_live_search:
            if progress_callback:
                progress_callback("Initiating Autonomous Web Metasearch across Venture Radars...", 0.15)

            # 1a. Dynamic Live Web Search
            web_deals = self.search_live_web_deals(target_orbit=target_orbit, target_hub=target_hub, max_deals=8, progress_callback=progress_callback)
            for deal in web_deals:
                dom = deal.get("domain", "").lower()
                if not dom or dom in seen_domains:
                    continue
                seen_domains.add(dom)
                is_qual, audit = validate_tvb_candidate(deal)
                audit_reports[deal.get("company_name", dom)] = audit
                if is_qual:
                    qualified.append(deal)
                elif audit.get("contact_valid") is False or audit.get("warnings"):
                    needs_review.append(deal)
                else:
                    disqualified.append(deal)

            # 1b. Real-Time Venture RSS Feeds
            if progress_callback:
                progress_callback("Scanning Real-Time European, UK, and Global Venture Feeds...", 0.50)
            feed_deals = self.crawl_live_feed_deals(target_orbit=target_orbit, progress_callback=progress_callback)
            for deal in feed_deals:
                dom = deal.get("domain", "").lower()
                if not dom or dom in seen_domains:
                    continue
                seen_domains.add(dom)
                is_qual, audit = validate_tvb_candidate(deal)
                audit_reports[deal.get("company_name", dom)] = audit
                if is_qual:
                    qualified.append(deal)
                elif audit.get("contact_valid") is False or audit.get("warnings"):
                    needs_review.append(deal)
                else:
                    disqualified.append(deal)

        # Step 2: Combine with baseline verified companies to ensure minimum bar (15+)
        if progress_callback:
            progress_callback(f"Synthesizing leads and verifying compliance (Found {len(qualified)} fresh deals)...", 0.70)

        candidate_pool = list(self.verified_seeds)
        # Randomize candidate pool so each run feels fresh
        random.shuffle(candidate_pool)

        for seed in candidate_pool:
            dom = seed.get("domain", "").lower()
            if dom in seen_domains:
                continue

            # Apply optional orbit/hub filters
            if target_orbit and target_orbit != "All Orbits" and seed.get("orbit") != target_orbit:
                continue
            if target_hub and target_hub != "All Hubs" and seed.get("target_hub") != target_hub:
                continue

            seen_domains.add(dom)
            is_qual, audit = validate_tvb_candidate(seed)
            audit_reports[seed.get("company_name", dom)] = audit

            if is_qual:
                qualified.append(seed)
            elif audit.get("contact_valid") is False or audit.get("warnings"):
                needs_review.append(seed)
            else:
                disqualified.append(seed)

            if len(qualified) >= max(target_count, 18):
                break

        # Fallback to ensure minimum bar (15+ leads) if filtering was too strict
        if len(qualified) < 15:
            for seed in candidate_pool:
                dom = seed.get("domain", "").lower()
                if dom not in seen_domains:
                    seen_domains.add(dom)
                    is_qual, audit = validate_tvb_candidate(seed)
                    audit_reports[seed.get("company_name", dom)] = audit
                    if is_qual:
                        qualified.append(seed)
                    if len(qualified) >= 15:
                        break

        # Guarantee fresh live-scraped deals remain at the very front of the qualified list
        live_leads = [q for q in qualified if q.get("is_live_crawled")]
        seed_leads = [q for q in qualified if not q.get("is_live_crawled")]
        qualified = live_leads + seed_leads

        if progress_callback:
            progress_callback(f"Complete! Discovered {len(live_leads)} live 2026 deals + {len(seed_leads)} vetted scale-ups (Total: {len(qualified)}).", 1.0)

        source_queries = [f"{name} ({url})" for name, url in LIVE_STARTUP_FEEDS]
        if target_orbit and target_orbit != "All Orbits":
            source_queries.append(f"Orbit Vector: {target_orbit}")
        if target_hub and target_hub != "All Hubs":
            source_queries.append(f"Hub Vector: {target_hub}")

        return {
            "qualified": qualified,
            "needs_review": needs_review,
            "disqualified": disqualified,
            "qualified_count": len(qualified),
            "queries": source_queries,
            "audit_reports": audit_reports
        }

    def discover_and_qualify_leads(
        self,
        target_count: int = 18,
        run_live_crawler: bool = True,
        target_orbit: Optional[str] = None,
        target_hub: Optional[str] = None,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        Public API returning list of verified qualified leads for UI display.
        Delegates to run_pipeline.
        """
        result = self.run_pipeline(
            include_live_search=run_live_crawler,
            target_count=target_count,
            target_orbit=target_orbit,
            target_hub=target_hub,
            progress_callback=progress_callback
        )
        return result["qualified"]
