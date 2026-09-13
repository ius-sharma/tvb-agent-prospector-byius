# TVB Autonomous Prospecting Agent

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://tvb-agent-prospector.streamlit.app/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Unit%20Tests-12%2F12%20Passing-brightgreen.svg)](tests/test_pipeline.py)
[![Code Style](https://img.shields.io/badge/Architecture-Linear%2FVercel%20Aesthetic-black.svg)](app.py)

> **Live Demo:** [https://tvb-agent-prospector.streamlit.app/](https://tvb-agent-prospector.streamlit.app/)  
> An autonomous lead discovery, enrichment, and executive deliverability verification platform built for **The Venture Build (TVB)** Agentic & Automation screening assignment.

---

## Executive Summary

The TVB Prospecting Agent continuously monitors, parses, and audits early-stage technology scale-ups across international venture ecosystems to surface high-potential prospects matching TVB's investment and venture-building mandate:

* **Funding / Revenue Window:** \$1,000,000 to \$5,000,000 USD (Seed, Early Scale-Up, Pre-Series A)
* **Target Profile:** Scalable B2B technology platforms & enterprise software across 6 core TVB Orbits
* **Target Geography:** Strictly Non-US Headquarters across 5 strategic hubs (UK, Pan-Europe, India, Middle East/MENA, Southeast Asia)
* **Executive Leadership:** Identifies named Founder or CEO with authentic corporate email
* **Deliverability Guarantee:** Active DNS MX network verification handshake protocol (zero generic or parked emails)
* **High-Throughput Volume:** Guaranteed minimum bar of 15+ qualified leads per run with zero repetitive leads across sessions

---

## Architectural Workflow

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              HYBRID MULTI-SOURCE INGESTION                             │
│  ┌────────────────────────┐  ┌──────────────────────────────┐  ┌────────────────────┐  │
│  │ 31 Real-Time RSS Feeds │  │ Autonomous DDGS Metasearch   │  │ 41 Vetted Scale-Up │  │
│  │ (UK, EU, IN, ME, SEA)  │  │ (Dynamic Orbit/Hub Vectors)  │  │ Benchmark Pool     │  │
│  └───────────┬────────────┘  └──────────────┬───────────────┘  └─────────┬──────────┘  │
└──────────────┼──────────────────────────────┼────────────────────────────┼─────────────┘
               ▼                              ▼                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          DEEP ENRICHMENT & PARSING ENGINE                              │
│  • Article Text Extraction (BeautifulSoup)  • Multi-Currency Normalizer (USD, EUR,     │
│  • Founder & Title NLP Extraction           • GBP, INR Crore)                          │
└─────────────────────────────────────────────┬──────────────────────────────────────────┘
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                 EXECUTIVE DELIVERABILITY PROTOCOL & ANTI-PARKING SHIELD                │
│  • Direct Mailto Extraction (`direct_extraction`)                                      │
│  • Transparent Pattern Derivation (`pattern_inference`)                                │
│  • Anti-Generic Filtering (blocks `info@`, `support@`, `sales@`, disposable domains)  │
│  • Parked MX Fingerprint Rejection (blocks GoDaddy/Namecheap/Sedo parking servers)     │
│  • Live Network DNS MX Handshake Verification (`dnspython` + in-memory LRU Cache)      │
└─────────────────────────────────────────────┬──────────────────────────────────────────┘
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        STRICT 5-GATE COMPLIANCE SCREENING ENGINE                       │
│  [1] $1M-$5M Funding  [2] B2B Tech Platform  [3] Non-US HQ  [4] Active Entity          │
│  [5] Executive Founder + Active DNS MX Deliverability                                  │
└─────────────────────────────────────────────┬──────────────────────────────────────────┘
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     SESSION MEMORY & ZERO-OVERLAP DEDUPLICATION                        │
│  Maintains `session_seen_domains` across iterations to guarantee 100% fresh, unique   │
│  leads on consecutive runs without repetition until entire candidate pools are cycled. │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Capabilities

### 1. Multi-Source Hybrid Ingestion
* **31 Real-Time Venture Radars:** Live RSS and deal feeds continuously monitoring announcements across:
  * **UK Hub:** *UK Tech News*, *Tech Funding News*, *Startups Magazine UK*, *UKTN Early Stage Deals*.
  * **Pan-Europe & Nordics:** *Tech.eu*, *Sifted Seed Radar*, *Silicon Canals*, *EU-Startups*, *Nordic 9*.
  * **DACH & France:** *Gründerszene*, *FrenchWeb*, *Maddyness*, *Trending Topics*, *Startupticker Switzerland*.
  * **India Hub:** *Inc42 Funding Pulse*, *YourStory Scale-Up*, *Entrackr Venture Tracker*.
  * **Middle East (MENA):** *Wamda*, *Magnitt Venture Alerts*.
  * **Southeast Asia:** *Tech in Asia*, *e27 Emerging Ventures*.
* **Dynamic Search Vectors:** Executes real-time metasearch queries via `ddgs` targeting specific TVB Orbits and Hub combinations.
* **41-Scale-Up Vetted Benchmark Pool:** Curated cache in `data/verified_seeds.json` ensuring 100% operational uptime and reliable performance even during third-party search throttling.

### 2. Multi-Currency Normalization & Regex Safety
* Converts and normalizes cross-border venture rounds directly into USD:
  * **EUR (€ / EUR):** Converted at standard `$1.08/EUR` rate (e.g., `€4.2M` $\rightarrow$ `$4,536,000 USD`).
  * **GBP (£ / GBP):** Converted at standard `$1.30/GBP` rate (e.g., `£3.0M` $\rightarrow$ `$3,900,000 USD`).
  * **INR (₹ / Crore):** Converted at `1 INR = $0.012 USD` (`1 Crore = $120,000 USD`). Example: `₹25 Cr` $\rightarrow$ **`$3,000,000 USD`**.
* **False-Positive Guardrails:** Non-monetary integers (e.g. *"raised with 4 angel investors"*, *"founded 3 years ago"*) are strictly rejected (`0.0`) and never misclassified as funding.

### 3. Deliverability Protocol & Anti-Parking Shield
* **DNS MX Deliverability Handshake:** Every domain undergoes live MX resolution using `dnspython` to confirm mail exchange server availability.
* **Anti-Parking Shield:** Actively detects and filters out default parking and monetization MX servers (GoDaddy `secureserver.net`, Namecheap `registrar-servers.com`, Sedo, Bodis, HugeDomains, Dan.com) and RFC 7505 Null MX records.
* **Transparent Contact Provenance:**
  * `direct_extraction`: Email directly extracted from press releases, mailto links, or published articles.
  * `pattern_inference`: Derived from verified executive name and authenticated business domain with full audit transparency.
* **Generic Inbox Blocklist:** Automatically rejects unhelpful generic addresses (`info@`, `sales@`, `support@`, `admin@`, `press@`).

### 4. Zero-Overlap Session Memory
* Dynamically records every domain surfaced during the active session in `session_seen_domains`.
* Subsequent discovery runs strictly exclude seen companies, ensuring reviewers see **100% fresh, unique scale-ups** across consecutive runs.

### 5. Interactive Compliance Inspector & Telemetry
* **4-Stage Live Execution Tracker:** Real-time visual progress from Vector Routing $\rightarrow$ Radar Crawling $\rightarrow$ Founder & MX Handshake $\rightarrow$ TVB Screening.
* **Live Event Telemetry Console:** Real-time audit logs of domain handshakes and feed events.
* **Deep Compliance Inspector:** Interactive rule-by-rule audit breakdown (Funding, Platform, Location, Contact, Entity status) with 1-click CSV export.

---

## App Structure

```text
TVB-AGENT/
├── .streamlit/
│   └── config.toml            # Server settings, theme styling & CSRF protection
├── app.py                     # Streamlit application UI, telemetry, and data tables
├── data/
│   └── verified_seeds.json    # 41 curated & verified non-US scale-up candidates
├── src/
│   ├── __init__.py
│   ├── discovery.py           # Multi-feed RSS crawler, live DDGS metasearch, pipeline runner
│   ├── enrichment.py          # Email deliverability, DNS MX protocol, founder extraction
│   ├── tvb_context.py         # TVB investment criteria, orbit definitions, target hubs
│   └── validator.py           # Strict 5-gate qualification rules and compliance audits
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py       # 12 comprehensive automated unit tests
├── requirements.txt           # Categorized production dependencies
└── README.md                  # Comprehensive system documentation
```

---

## Installation & Local Setup

### Prerequisites
* **Python 3.10+** (Tested on Python 3.11 and 3.12)
* Active internet connection (for live RSS ingestion, DDGS metasearch, and DNS MX lookups)

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ius-sharma/TVB-AGENT.git
   cd TVB-AGENT
   ```

2. **Create and activate a virtual environment:**
   * **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   * **Windows (Command Prompt):**
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate.bat
     ```
   * **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Verify environment integrity:**
   ```bash
   pip check
   ```

5. **Launch the Streamlit dashboard:**
   ```bash
   streamlit run app.py
   ```
   Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Automated Test Suite

The test suite validates compliance rules, currency parsing, generic email rejection, geographic boundaries, parked domain rejection, and pipeline execution schemas:

```bash
# Run the complete test suite
python -m unittest discover tests

# Or run tests directly
python -m unittest tests/test_pipeline.py
```

### Test Coverage Breakdown (12 Tests Passing):
1. `test_parse_funding_amount_millions`: Verifies multi-currency strings (`$3.5M`, `2 million`, `€4.2M`, `₹25 Cr`) and confirms non-funding numbers return `0.0`.
2. `test_generic_email_detection`: Ensures `info@`, `support@`, and `sales@` are blocked while executive emails pass.
3. `test_acquired_company_is_disqualified`: Rejects non-standalone and acquired entities.
4. `test_pipeline_shape_without_live_search`: Verifies dictionary contracts and guaranteed $\ge 15$ qualified leads.
5. `test_us_headquarters_is_disqualified`: Rejects US headquarters (San Francisco, Austin) and verifies foreign engineering team bypass leaks are strictly blocked.
6. `test_non_tech_platform_fails`: Filters out non-tech brick-and-mortar operations.
7. `test_contact_resolver_direct_vs_pattern`: Confirms transparent provenance tagging (`direct_extraction` vs `pattern_inference`).
8. `test_candidate_with_out_of_range_funding_fails`: Flags out-of-bracket funding amounts ($25M).
9. `test_fully_qualified_candidate_passes`: Validates end-to-end 100% compliance pass.
10. `test_session_deduplication_excludes_seen_domains`: Verifies that previously seen domains are strictly excluded from subsequent runs.
11. `test_parked_mx_domain_is_rejected`: Validates that parked/reseller MX hosts (`secureserver.net`, etc.) return `False`.
12. `test_infer_company_domain_zero_hallucination`: Confirms unverified companies return `""` and never hallucinate a fake domain.

---

## TVB Screening Criteria Reference

| Criteria Gate | TVB Specification | Implementation / Validation Rule |
| :--- | :--- | :--- |
| **Funding / Revenue** | \$1M – \$5M USD | `TVB_CRITERIA["funding_revenue_min_usd"] <= amount <= TVB_CRITERIA["funding_revenue_max_usd"]` |
| **Business Model** | Scalable B2B Tech Platform | Keyword classification across 6 TVB Orbits; brick-and-mortar filter |
| **Target Geography** | Minimal to no US presence | Disqualifies US HQs; prioritizes UK, Europe, India, MENA, and SE Asia |
| **Leadership** | Founder / CEO Identified | Extracts verified executive name from press mentions or corporate metadata |
| **Deliverability** | Non-generic, valid MX | Rejects generic prefixes; confirms active DNS MX records via `dnspython` |
| **Entity Health** | Active & Standalone | Rejects acquired, merged, or defunct entities |

---

## Engineering Trade-offs & Design Decisions

1. **DNS MX Verification vs. Active SMTP RCPT TO Handshake:**  
   Conducting active SMTP probes (`RCPT TO`) on live mail servers often triggers IP blacklisting, spam traps, and rate limits. The agent verifies mail server reachability and domain configuration via live DNS MX queries while enforcing anti-generic and anti-parking rules.
2. **Hybrid Ingestion Architecture (Live Feeds + Benchmark Pool):**  
   External web search APIs are subject to transient rate-limiting. By combining 31 real-time RSS feeds with a curated benchmark cache of 41 verified non-US scale-ups, the system guarantees 100% demo stability and always delivers 15+ qualified leads.
3. **Session Deduplication:**  
   Session memory stores seen domains in `st.session_state.session_seen_domains`, preventing repetitive results across multiple clicks while allowing full exploration of the scale-up dataset.

