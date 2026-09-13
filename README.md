# TVB Autonomous Prospecting Agent

An autonomous lead discovery, extraction, and executive deliverability verification dashboard engineered for **The Venture Build (TVB)** Agentic and Automation Intern screening assignment.

The platform continuously identifies, enriches, and audits high-growth non-US technology scale-ups that strictly adhere to TVB's investment and incubation profile:

- **Funding / Revenue:** \$1,000,000 to \$5,000,000 USD (Seed, Early Scale-Up, Pre-Series A)
- **Sector Alignment:** Scalable B2B technology platforms and SaaS businesses
- **Geography:** Non-US Headquarters with minimal or no US operational footprint
- **Executive Contact:** Verified CEO or Co-founder with validated, non-generic email
- **Deliverability Assurance:** Active DNS MX network handshake protocol with transparent provenance tracking
- **Pipeline Throughput:** Guaranteed minimum bar of 15+ qualified leads per execution run

---

## Architecture & Core Capabilities

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               MULTI-SOURCE HYBRID INGESTION                            │
│  ┌────────────────────────┐  ┌──────────────────────────────┐  ┌────────────────────┐  │
│  │ 31 Real-Time RSS Feeds │  │ Autonomous DDGS Metasearch   │  │ 41 Vetted Scale-Up │  │
│  │ (UK, EU, IN, ME, SEA)  │  │ (Dynamic Orbit/Hub Vectors)  │  │ Benchmark Pool     │  │
│  └───────────┬────────────┘  └──────────────┬───────────────┘  └─────────┬──────────┘  │
└──────────────┼──────────────────────────────┼────────────────────────────┼─────────────┘
               ▼                              ▼                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DEEP ENRICHMENT & PARSING ENGINE                                │
│  • Article Text Extraction (BeautifulSoup)  • Multi-Currency Normalization (USD, EUR,  │
│  • Founder & Title Recognition Patterns     • GBP, INR Crore)                          │
└─────────────────────────────────────────────┬──────────────────────────────────────────┘
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                  EXECUTIVE CONTACT DELIVERABILITY & PROVENANCE PROTOCOL                 │
│  • Direct Mailto Extraction (`direct_extraction`)                                      │
│  • Transparent Pattern Derivation (`pattern_inference`)                                │
│  • Anti-Generic Filtering (blocks `info@`, `support@`, `sales@`, disposable domains)  │
│  • Live Network DNS MX Handshake Verification (`dnspython` + in-memory LRU Cache)      │
└─────────────────────────────────────────────┬──────────────────────────────────────────┘
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          STRICT 5-GATE COMPLIANCE VALIDATOR                            │
│  [1] $1M-$5M Funding  [2] B2B Tech Platform  [3] Non-US HQ  [4] Active Entity          │
│  [5] Executive Founder + Active DNS MX Deliverability                                  │
└─────────────────────────────────────────────┬──────────────────────────────────────────┘
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     SESSION MEMORY & ZERO-OVERLAP DEDUPLICATION                        │
│  Tracks `session_seen_domains` across discovery iterations to guarantee 100% unique    │
│  candidates on successive runs until target pools are exhausted.                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Multi-Source Ingestion Engine
- **31 Live Venture News Feeds:** Monitors real-time venture activity across UK (*UKTN, Tech Funding News*), Pan-Europe & Nordics (*Tech.eu, Sifted Seed Radar, Silicon Canals, EU-Startups, Nordic 9*), DACH & France (*Gründerszene, FrenchWeb, Maddyness, Trending Topics*), India (*Inc42, YourStory, Entrackr*), Middle East (*Wamda, Magnitt*), and Southeast Asia (*Tech in Asia, e27*).
- **Dynamic Search Vectors:** Generates structured search queries utilizing `ddgs` targeting specific TVB Orbits and international hubs.
- **Curated Benchmark Cache:** 41 pre-audited scale-ups in `data/verified_seeds.json` ensuring operational stability even under external search throttling.

### 2. Deliverability & Provenance Verification
- Rejects generic inboxes (`info@`, `sales@`, `support@`, `press@`) and disposable email providers.
- Conducts live DNS MX queries to confirm mail exchange server reachability (`dnspython` with an in-memory `MX_CACHE`).
- Maintains strict provenance tags:
  - `direct_extraction`: Email directly parsed from press releases or executive contact pages.
  - `pattern_inference`: Derived using authenticated company domain patterns (`first@domain`) with explicit audit transparency.

### 3. Session Memory & Zero-Overlap Deduplication
- Remembers previously surfaced companies in `session_seen_domains`.
- Subsequent discovery runs exclude any domain already presented during the active session, ensuring zero duplicate leads between successive runs.

### 4. Real-Time Telemetry & Interactive Audit Inspector
- Live 4-stage visual progress tracking in Streamlit UI (Vector Routing $\rightarrow$ Radar Crawling $\rightarrow$ Founder & MX Handshake $\rightarrow$ TVB Screening).
- Expandable event telemetry console capturing real-time network handshakes.
- Interactive candidate compliance inspector offering rule-by-rule audit breakdowns and 1-click CSV export.

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
│   └── test_pipeline.py       # 9 comprehensive unit tests (validator, pipeline, email checks)
├── requirements.txt           # Categorized production dependencies
└── README.md                  # System documentation and architecture guide
```

---

## Installation & Local Setup

### Prerequisites
- **Python 3.10+** (Tested on Python 3.11 and 3.12)
- Active internet connection (for live RSS ingestion, DDGS metasearch, and DNS MX checks)

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ius-sharma/TVB-AGENT.git
   cd TVB-AGENT
   ```

2. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt):**
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate.bat
     ```
   - **macOS / Linux:**
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

The test suite validates compliance rules, currency parsing, generic email rejection, geographic boundaries, and pipeline execution shapes:

```bash
# Run the complete test suite
python -m unittest discover tests

# Or run tests directly
python -m unittest tests/test_pipeline.py
```

### Test Coverage Highlights:
- `test_parse_funding_amount_millions`: Verifies multi-currency strings (`$3.5M`, `2 million`, `€4.2M`).
- `test_generic_email_detection`: Ensures `info@`, `support@`, and `sales@` are blocked.
- `test_acquired_company_is_disqualified`: Rejects non-standalone and acquired entities.
- `test_pipeline_shape_without_live_search`: Verifies dictionary contracts and guaranteed $\ge 15$ qualified leads.
- `test_us_headquarters_is_disqualified`: Rejects US locations while admitting valid international hubs.
- `test_non_tech_platform_fails`: Filters out non-tech brick-and-mortar operations.
- `test_contact_resolver_direct_vs_pattern`: Confirms transparent provenance tagging.
- `test_candidate_with_out_of_range_funding_fails`: Flags out-of-bracket funding amounts.
- `test_fully_qualified_candidate_passes`: Validates end-to-end 100% compliance pass.

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
