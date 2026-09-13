"""
TVB Context & Criteria Reference
Defines the parameters, Orbits, and Hubs derived from TVB's official documentation.
"""

from typing import Dict, List

# TVB Target Profile Parameters
TVB_CRITERIA = {
    "funding_revenue_min_usd": 1_000_000,
    "funding_revenue_max_usd": 5_000_000,
    "tech_focus": True,
    "us_presence": "minimal_to_none",  # TVB targets companies seeking US market entry
    "require_founder_contact": True,
    "min_leads_bar": 15
}

# TVB Vertical Orbits (Target Sectors)
TVB_ORBITS: Dict[str, List[str]] = {
    "AI & Automation": [
        "Applied AI", "AI Agents", "Enterprise Automation", "LLM Workflows", "Computer Vision"
    ],
    "Cybersecurity": [
        "Cloud Security", "Compliance Automation", "Risk Management", "Vulnerability Scanning", "Zero Trust"
    ],
    "Healthcare & Life Sciences": [
        "Digital Health", "Care Coordination", "Health Tech", "Clinical Workflow", "Telemedicine"
    ],
    "Fintech & Payments": [
        "Embedded Finance", "Cross-Border Payments", "FinTech SaaS", "Payment Infrastructure", "Compliance RegTech"
    ],
    "Education & Workforce": [
        "EdTech", "Workforce Upskilling", "Skills-based Education", "Enterprise Learning"
    ],
    "Travel & Logistics": [
        "TravelTech", "Booking Infrastructure", "Logistics Tech", "Mobility Platforms"
    ],
    "Enterprise SaaS & Digital Twin": [
        "B2B SaaS", "Digital Twin", "Developer Tools", "Data Infrastructure", "Industrial IoT"
    ]
}

# TVB Target Regional Hubs (Strictly Non-US Focus)
TVB_HUBS: Dict[str, List[str]] = {
    "India Hub": ["India", "Bengaluru", "Delhi NCR", "Hyderabad", "Mumbai", "Pune"],
    "UK Hub": ["United Kingdom", "London", "Cambridge", "Manchester", "Edinburgh"],
    "Europe Hub": ["France", "Germany", "Estonia", "Netherlands", "Sweden", "Paris", "Berlin", "Amsterdam"],
    "UAE & MENA Hub": ["United Arab Emirates", "Dubai", "Abu Dhabi", "Saudi Arabia", "Riyadh"],
    "Southeast Asia Hub": ["Singapore", "Malaysia", "Indonesia", "Vietnam"]
}

# Generic email prefixes that MUST be rejected to ensure zero fake/generic data
GENERIC_EMAIL_PREFIXES = {
    "info", "support", "contact", "sales", "help", "hello", "hi", "admin",
    "office", "team", "inquiry", "inquiries", "jobs", "careers", "billing",
    "press", "media", "feedback", "marketing", "general", "service"
}
