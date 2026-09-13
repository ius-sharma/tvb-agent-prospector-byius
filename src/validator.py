"""
TVB Criteria Validator Module.
Strictly validates candidate companies against TVB's 4 core parameters:
1. Funding or Revenue between $1M and $5M USD
2. Tech-related platform
3. Minimal to no presence in the US
4. Founder / CEO contact availability (with verified email)
"""

import os
import re
from typing import Dict, Any, Tuple
from src.tvb_context import TVB_CRITERIA, TVB_HUBS, TVB_ORBITS
from src.enrichment import verify_executive_email


US_LOCATIONS = {
    "united states", "usa", "u.s.", "u.s.a.", "california", "new york", "san francisco",
    "silicon valley", "austin", "texas", "seattle", "boston", "chicago", "los angeles",
    "delaware", "miami", "denver"
}


def parse_funding_amount(text: str) -> float:
    """
    Extracts numerical funding amount in USD from strings like '$3.5M', '€2.5M', '£3M', '3500000'.
    Returns amount in USD.
    """
    if not text:
        return 0.0
        
    text_str = str(text).strip()
    
    # Check if already a pure float/int
    try:
        val = float(text_str.replace(",", "").replace("$", ""))
        return val
    except ValueError:
        pass

    # Regex for e.g. $2.5M, 3 million, $4M
    match = re.search(r'[\$€£]?\s*(\d+(?:\.\d+)?)\s*(m|million|mn|k)?', text_str, re.IGNORECASE)
    if match:
        number = float(match.group(1))
        unit = (match.group(2) or "").lower()
        if unit in ["m", "million", "mn"]:
            return number * 1_000_000
        elif unit == "k":
            return number * 1_000
        elif number < 100:  # e.g. "3.5" meaning 3.5 million in funding contexts
            return number * 1_000_000
        return number

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
    Verifies that headquarters is outside the US and US presence is minimal to none.
    """
    combined = f"{headquarters} {location_notes}".lower()
    
    # Check if foreign hub is explicitly identified
    non_us_found = False
    for hub_name, cities_countries in TVB_HUBS.items():
        if any(c.lower() in combined for c in cities_countries):
            non_us_found = True
            break
            
    # Check for direct US headquarters disqualification
    for us_loc in US_LOCATIONS:
        pattern = rf"\b{re.escape(us_loc)}\b"
        if re.search(pattern, headquarters.lower()):
            return False
            
    return non_us_found or ("us" not in headquarters.lower())


def validate_tvb_candidate(candidate: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Comprehensive qualification against all TVB rules.
    Returns (is_qualified, audit_report).
    """
    reasons = []
    
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

    is_qualified = funding_valid and tech_valid and non_us_valid and contact_valid
    
    audit_report = {
        "is_qualified": is_qualified,
        "funding_valid": funding_valid,
        "parsed_funding_usd": funding_usd,
        "tech_valid": tech_valid,
        "non_us_valid": non_us_valid,
        "contact_valid": contact_valid,
        "email_details": email_verification,
        "disqualification_reasons": reasons
    }
    
    return is_qualified, audit_report
