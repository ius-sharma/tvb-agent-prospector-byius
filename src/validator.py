"""
TVB Criteria Validator Module.
Strictly validates candidate companies against TVB's 4 core parameters:
1. Funding or Revenue between $1M and $5M USD
2. Tech-related platform
3. Minimal to no presence in the US
4. Founder / CEO contact availability (with verified email)
"""

import re
from typing import Dict, Any, Tuple
from src.tvb_context import TVB_CRITERIA, TVB_HUBS
from src.enrichment import verify_executive_email


US_LOCATIONS = {
    # Full country names
    "united states", "usa", "u.s.", "u.s.a.", "united states of america",
    # Major US states & territories
    "california", "texas", "new york", "massachusetts", "washington", "florida",
    "illinois", "colorado", "delaware", "georgia", "north carolina", "virginia",
    "pennsylvania", "ohio", "michigan", "new jersey", "connecticut", "utah", "arizona",
    # Two-letter state abbreviations
    "ca", "tx", "ny", "ma", "wa", "fl", "il", "co", "de", "ga", "nc", "va", "pa", "nj",
    # Major US tech metro centers
    "san francisco", "sf bay area", "bay area", "silicon valley", "austin", "seattle",
    "boston", "new york city", "nyc", "chicago", "los angeles", "la", "san jose",
    "palo alto", "mountain view", "sunnyvale", "menlo park", "cupertino", "san diego",
    "miami", "denver", "boulder", "atlanta", "dallas", "houston"
}

DISQUALIFYING_US_PRESENCE_SIGNALS = {
    "strong us presence", "major us presence", "headquartered in us",
    "us headquarters", "relocated to us", "moved to us", "primary market in us",
    "incorporated in delaware with us operations", "majority us team",
    "us-based team", "primary clinical deployment in us"
}

INACTIVE_SIGNALS = {
    "acquired by", "shut down", "shutdown", "closed down", "no longer operating",
    "defunct", "inactive"
}


def parse_funding_amount(text: str) -> float:
    """
    Extracts numerical funding amount in USD from strings like '$3.5M', '€2.5M', '£3M', '₹25 Cr', '3500000'.
    Normalizes GBP, EUR, and INR Crores to USD.
    Guarantees that non-funding numbers (e.g. '4 angel investors', '3 years ago') are never falsely converted.
    """
    if not text:
        return 0.0

    text_str = str(text).strip()

    # Check if already a pure number (e.g. 3500000 or 3500000.0)
    clean_num = text_str.replace(",", "").replace("$", "").strip()
    try:
        val = float(clean_num)
        if val >= 100_000:
            return val
    except ValueError:
        pass

    # Check for billions first to reject mega rounds
    billion_match = re.search(r'(?:([$€£₹])|(USD|EUR|GBP|INR))\s*(\d+(?:\.\d+)?)\s*(b|billion|bn)\b', text_str, re.IGNORECASE)
    if billion_match:
        val = float(billion_match.group(3))
        mult = 1.30 if (billion_match.group(1) == '£' or billion_match.group(2) == 'GBP') else (1.08 if (billion_match.group(1) == '€' or billion_match.group(2) == 'EUR') else 1.0)
        return val * 1_000_000_000 * mult

    # Pattern 1: Explicit Currency Symbol/Code with number and unit (e.g. $3.5M, €4.2M, £2.8m, ₹25 Cr)
    m = re.search(r'(?:([$€£₹])|(USD|EUR|GBP|INR))\s*(\d+(?:\.\d+)?)\s*(m|million|mn|k|crore|cr)?\b', text_str, re.IGNORECASE)
    if m:
        sym = m.group(1) or ""
        code = (m.group(2) or "").upper()
        val = float(m.group(3))
        unit = (m.group(4) or "").lower()

        if sym == '£' or code == 'GBP':
            mult = 1.30
        elif sym == '€' or code == 'EUR':
            mult = 1.08
        elif sym == '₹' or code == 'INR' or unit in ["crore", "cr"]:
            mult = 0.012
        else:
            mult = 1.00

        if unit in ["crore", "cr"]:
            return val * 10_000_000 * mult
        elif unit in ["m", "million", "mn"]:
            return val * 1_000_000 * mult
        elif unit == "k":
            return val * 1_000 * mult
        elif sym or code:
            if 1.0 <= val <= 25.0:
                return val * 1_000_000 * mult
            elif val >= 100_000:
                return val * mult

    # Pattern 2: Number followed explicitly by funding unit (e.g. "raised 2.5 million", "seed of 3m")
    m2 = re.search(r'\b(\d+(?:\.\d+)?)\s*(million|mn)\b', text_str, re.IGNORECASE)
    if m2:
        val = float(m2.group(1))
        return val * 1_000_000

    # Pattern 3: Indian Crores without explicit symbol (e.g. "raised 25 crore in seed")
    m3 = re.search(r'\b(\d+(?:\.\d+)?)\s*(crore|cr)\b', text_str, re.IGNORECASE)
    if m3:
        val = float(m3.group(1))
        return val * 10_000_000 * 0.012

    # Non-monetary numbers ("4 angel investors", "founded 3 years ago") are safely rejected as 0.0
    return 0.0


def is_tech_platform(description: str, sector: str) -> bool:
    """Checks if company operates a tech-related platform or software."""
    combined = f"{description} {sector}".lower()
    tech_keywords = [
        "platform", "software", "saas", "ai", "api", "cloud", "app", "tech",
        "algorithm", "data", "automation", "security", "digital", "developer",
        "infrastructure", "machine learning", "fintech", "healthtech", "edtech"
    ]
    return any(kw in combined for kw in tech_keywords)


def has_minimal_us_presence(headquarters: str, location_notes: str) -> bool:
    """
    Strictly verifies that the company is headquartered outside the US and operates
    with minimal to no US footprint, preventing US entities from leaking through.
    """
    if not headquarters:
        return False

    hq_lower = headquarters.strip().lower()
    notes_lower = (location_notes or "").strip().lower()

    # 1. Direct Headquarters Check: Any US city, state, or country name in HQ is an immediate reject
    for loc in US_LOCATIONS:
        if len(loc) <= 2:
            pattern = rf"(?:^|[\s,;/\-])(?:{re.escape(loc)})(?:$|[\s,;/\-])"
        else:
            pattern = rf"\b{re.escape(loc)}\b"

        if re.search(pattern, hq_lower):
            return False

    # 2. Strong/Disqualifying US Presence in location notes
    for signal in DISQUALIFYING_US_PRESENCE_SIGNALS:
        if signal in notes_lower:
            return False

    # 3. Positively identify non-US hub origin or international headquarters
    non_us_found = False
    for hub_name, cities_countries in TVB_HUBS.items():
        if any(c.lower() in hq_lower or c.lower() in notes_lower for c in cities_countries):
            non_us_found = True
            break

    if non_us_found:
        return True

    # 4. If no explicit hub match, ensure no residual US references exist in HQ
    has_us = any(
        re.search(rf"\b{re.escape(loc)}\b", hq_lower)
        for loc in US_LOCATIONS if len(loc) > 2
    )
    return not has_us


def has_disqualifying_status(candidate: Dict[str, Any]) -> bool:
    """Rejects companies that clearly are not active standalone prospects anymore."""
    combined = " ".join(
        str(candidate.get(key, ""))
        for key in ("company_name", "description", "funding_evidence", "status_notes")
    ).lower()
    return any(signal in combined for signal in INACTIVE_SIGNALS)


def collect_source_urls(candidate: Dict[str, Any]) -> list:
    """Normalizes available source/evidence URLs for audit display."""
    urls = []
    for key in ("source_url", "funding_source_url", "contact_source_url", "website"):
        value = candidate.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            urls.append(value)

    for value in candidate.get("source_urls", []) or []:
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            urls.append(value)

    deduped = []
    seen = set()
    for url in urls:
        if url not in seen:
            deduped.append(url)
            seen.add(url)
    return deduped


def validate_tvb_candidate(candidate: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Comprehensive qualification against all TVB rules.
    Returns (is_qualified, audit_report).
    """
    reasons = []
    warnings = []

    active_valid = not has_disqualifying_status(candidate)
    if not active_valid:
        reasons.append("Company appears acquired, inactive, or no longer a standalone prospect.")
    
    # 1. Funding / Revenue Check ($1M - $5M)
    funding_usd = parse_funding_amount(candidate.get("funding_revenue_usd", 0))
    if funding_usd == 0:
        funding_usd = parse_funding_amount(candidate.get("funding_evidence", ""))
        
    funding_valid = (TVB_CRITERIA["funding_revenue_min_usd"] <= funding_usd <= TVB_CRITERIA["funding_revenue_max_usd"])
    if not funding_valid:
        reasons.append(f"Funding ${funding_usd:,.0f} is outside the $1M-$5M USD range.")

    # 2. Tech Platform Check
    tech_valid = is_tech_platform(
        candidate.get("description", ""),
        candidate.get("orbit", "") + " " + candidate.get("sub_sector", "")
    )
    if not tech_valid:
        reasons.append("Does not clearly operate a scalable tech-related platform.")

    # 3. US Presence Check (Minimal to None)
    hq = candidate.get("headquarters", "")
    us_notes = candidate.get("us_presence", "")
    non_us_valid = has_minimal_us_presence(hq, us_notes)
    if not non_us_valid:
        reasons.append(f"Headquartered in US or strong US presence detected ({hq}).")

    # 4. Executive Contact & Verified Email Check
    exec_name = candidate.get("executive_name", "").strip()
    raw_email = candidate.get("verified_email", "")
    
    email_verification = verify_executive_email(raw_email)
    contact_valid = bool(exec_name) and email_verification["verified"]
    
    if not exec_name:
        reasons.append("CEO or Co-founder name is missing.")
    if not email_verification["verified"]:
        reasons.append(f"Executive email unverified: {email_verification.get('reason')}")

    source_urls = collect_source_urls(candidate)
    if not source_urls:
        warnings.append("No source URL attached; keep this lead in review before external use.")

    is_qualified = funding_valid and tech_valid and non_us_valid and contact_valid and active_valid
    
    audit_report = {
        "is_qualified": is_qualified,
        "funding_valid": funding_valid,
        "parsed_funding_usd": funding_usd,
        "tech_valid": tech_valid,
        "non_us_valid": non_us_valid,
        "contact_valid": contact_valid,
        "active_valid": active_valid,
        "contact_provenance": candidate.get("contact_provenance", "verified_seed"),
        "contact_audit_note": candidate.get("contact_audit_note", email_verification.get("reason", "")),
        "source_urls": source_urls,
        "email_details": email_verification,
        "disqualification_reasons": reasons,
        "warnings": warnings,
    }
    
    return is_qualified, audit_report
