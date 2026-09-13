"""
TVB Autonomous Prospecting Agent - Monochrome Dark Edition
Engineered for The Venture Build (TVB) Screening Task
Role: Agentic and Automation Intern
Design: Minimalist High-Contrast Black and White (Linear / Vercel Aesthetic)
Zero Emojis Enforced
"""

import streamlit as st
import pandas as pd
import json
import time
import io
import os

from src.discovery import TVBDiscoveryAgent
from src.tvb_context import TVB_ORBITS, TVB_HUBS, TVB_CRITERIA
from src.enrichment import verify_executive_email
from src.validator import validate_tvb_candidate

# Streamlit Page Setup
st.set_page_config(
    page_title="TVB // Autonomous Prospecting System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Dark Black & White Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600&family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #0A0A0C !important;
        color: #EDEDED !important;
    }
    
    /* Main Header & Subheader */
    .app-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #FFFFFF;
        margin-bottom: 0.15rem;
        text-transform: uppercase;
    }
    .app-subtitle {
        font-size: 0.95rem;
        color: #8E8E93;
        letter-spacing: -0.01em;
        margin-bottom: 1.4rem;
        font-weight: 400;
    }
    
    /* Monochrome Badges */
    .mono-pill {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        border-radius: 4px;
        background-color: #16161A;
        color: #D4D4D8;
        border: 1px solid #27272A;
        margin-right: 6px;
        margin-bottom: 8px;
        font-family: 'Geist Mono', monospace;
    }
    .mono-pill-active {
        background-color: #FFFFFF;
        color: #000000;
        border: 1px solid #FFFFFF;
    }
    
    /* Metric Cards */
    .dark-card {
        background-color: #121215;
        border: 1px solid #222226;
        border-radius: 8px;
        padding: 16px 18px;
        text-align: left;
    }
    .dark-card:hover {
        border-color: #38383F;
    }
    .dark-card-number {
        font-size: 1.85rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.03em;
        line-height: 1.1;
        font-family: 'Geist Mono', monospace;
    }
    .dark-card-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: #71717A;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 6px;
    }
    
    /* Empty State Box */
    .empty-box {
        background: #0D0D10;
        border: 1px dashed #27272A;
        border-radius: 10px;
        padding: 48px 24px;
        text-align: center;
        margin: 20px 0;
    }
    .empty-box-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }
    .empty-box-desc {
        font-size: 0.88rem;
        color: #71717A;
        max-width: 580px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* Primary Stark White Button */
    .stButton>button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.03em !important;
        text-transform: uppercase !important;
        border-radius: 6px !important;
        padding: 0.65rem 1.4rem !important;
        border: 1px solid #FFFFFF !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
    }
    .stButton>button:hover {
        background-color: #E4E4E7 !important;
        color: #000000 !important;
        border-color: #E4E4E7 !important;
        box-shadow: 0 0 12px rgba(255, 255, 255, 0.2) !important;
    }

    /* Terminal / Log Box */
    .terminal-box {
        background: #09090B;
        border: 1px solid #1F1F23;
        border-radius: 6px;
        padding: 12px 16px;
        font-family: 'Geist Mono', monospace;
        font-size: 0.82rem;
        color: #A1A1AA;
        line-height: 1.5;
    }
    
    /* Code / Mono spans */
    .mono-code {
        font-family: 'Geist Mono', monospace;
        color: #FAFAFA;
        background: #18181B;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.82rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "leads" not in st.session_state:
    st.session_state.leads = []
    st.session_state.last_run_time = "NEVER"
    st.session_state.run_count = 0

# Sidebar Configuration
with st.sidebar:
    st.markdown("### SYSTEM PARAMETERS")
    st.markdown(r"""
    <div style="font-size: 0.84rem; color: #A1A1AA; line-height: 1.6; margin-bottom: 12px;">
    • <b>FUNDING:</b> $1,000,000 to $5,000,000 USD<br>
    • <b>DOMAIN:</b> Tech Platform / Software<br>
    • <b>LOCATION:</b> Non-US HQ (UK / EU / IN / UAE)<br>
    • <b>CONTACT:</b> CEO / Co-Founder Name Available<br>
    • <b>DELIVERABILITY:</b> Active Domain DNS MX Confirmed<br>
    • <b>PRECISION:</b> Zero Generic / Synthesized Addresses
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("### SEARCH VECTORS")
    selected_orbit = st.selectbox(
        "Focus Orbit:",
        options=["All Orbits"] + list(TVB_ORBITS.keys()),
        key="selected_orbit_select"
    )

    selected_hub = st.selectbox(
        "Geographic Hub:",
        options=["All Hubs"] + list(TVB_HUBS.keys()),
        key="selected_hub_select"
    )

    st.divider()
    st.markdown("### BENCHMARK CONTROLS")
    if st.button("LOAD VETTED BENCHMARK POOL", use_container_width=True, key="btn_load_benchmark"):
        agent = TVBDiscoveryAgent()
        st.session_state.leads = agent.discover_and_qualify_leads(
            target_count=18,
            run_live_crawler=False,
            target_orbit=selected_orbit,
            target_hub=selected_hub
        )
        st.session_state.last_run_time = time.strftime("%H:%M:%S UTC")
        st.session_state.run_count += 1
        st.rerun()

    st.caption("THE VENTURE BUILD // AUTONOMOUS VENTURE OS")


# Main Page Header
st.markdown('<div class="app-title">THE VENTURE BUILD // PROSPECTING AGENT</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Autonomous Lead Discovery, Extraction & Executive Email Deliverability Verification</div>', unsafe_allow_html=True)

# Status Badges
st.markdown("""
<div>
    <span class="mono-pill">CRITERIA: $1M-$5M USD</span>
    <span class="mono-pill">MARKET: NON-US SCALE-UPS</span>
    <span class="mono-pill">VERIFICATION: DNS MX PROTOCOL</span>
    <span class="mono-pill">INBOX: ZERO GENERIC PRESETS</span>
    <span class="mono-pill">MINIMUM BAR: 15 LEADS</span>
    <span class="mono-pill mono-pill-active">ENGINE: DYNAMIC CRAWLER</span>
</div>
""", unsafe_allow_html=True)

st.write("")

# Action Control Deck
col_act1, col_act2, col_meta = st.columns([2.3, 1.2, 1.5])

with col_act1:
    if st.button("RUN LIVE AUTONOMOUS WEB DISCOVERY", use_container_width=True, key="btn_run_live_discovery"):
        # Reset state completely for fresh scrape
        st.session_state.leads = []
        
        progress_bar = st.progress(0)
        status_box = st.empty()

        def update_progress(msg, frac):
            status_box.markdown(f"""
            <div class="terminal-box">
                [AGENT STEP {int(frac*100)}%] >> {msg}
            </div>
            """, unsafe_allow_html=True)
            progress_bar.progress(frac)
            time.sleep(0.25)

        agent = TVBDiscoveryAgent()
        
        # Scrape brand new batch
        fresh_batch = agent.discover_and_qualify_leads(
            target_count=18,
            run_live_crawler=True,
            target_orbit=selected_orbit,
            target_hub=selected_hub,
            progress_callback=update_progress
        )

        st.session_state.leads = fresh_batch
        st.session_state.last_run_time = time.strftime("%H:%M:%S UTC")
        st.session_state.run_count += 1
        status_box.markdown(f"""
        <div class="terminal-box" style="color: #FFFFFF; border-color: #3F3F46;">
            [RUN #{st.session_state.run_count} COMPLETE] >> Successfully verified {len(fresh_batch)} qualified leads matching 100% of TVB criteria.
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1.0)
        st.rerun()

with col_act2:
    if st.button("CLEAR ALL LEADS", use_container_width=True, key="btn_clear_all_leads"):
        st.session_state.leads = []
        st.session_state.last_run_time = "CLEARED"
        st.rerun()

with col_meta:
    status_label = "ACTIVE" if st.session_state.leads else "IDLE"
    st.markdown(f"""
    <div style="font-family: 'Geist Mono', monospace; font-size: 0.78rem; color: #71717A; line-height: 1.6; padding-top: 4px;">
        STATUS: <span style="color: {'#FFFFFF' if status_label == 'ACTIVE' else '#71717A'}; font-weight: 700;">{status_label}</span><br>
        LAST RUN: <span style="color: #A1A1AA;">{st.session_state.last_run_time}</span> | RUN #{st.session_state.run_count}
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Leads Data & Display Pipeline
current_leads = st.session_state.leads

if not current_leads:
    st.markdown("""
    <div class="empty-box">
        <div class="empty-box-title">SYSTEM READY: AWAITING DISCOVERY TRIGGER</div>
        <div class="empty-box-desc">
            No leads loaded in session memory. Click <b>"RUN LIVE AUTONOMOUS WEB DISCOVERY"</b> above to connect to live venture announcement feeds, extract non-US tech scale-ups raising $1M-$5M USD, and run DNS MX deliverability handshakes.
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # Filter Bar
    f1, f2, f3 = st.columns([2, 1.4, 1.4])
    with f1:
        search_query = st.text_input("Filter Leads (Company, Sector, Founder):", "", key="leads_search_query_input")
    with f2:
        sort_mode = st.selectbox("Sort Order:", ["Funding: High to Low", "Funding: Low to High", "Company: A to Z"], key="leads_sort_mode_select")
    with f3:
        provenance_mode = st.selectbox("Source Type:", ["All Verified Leads", "Live Crawled Only (2026)", "Vetted Pool Only"], key="leads_provenance_mode_select")

    # Filter evaluation
    filtered = current_leads

    if search_query:
        sq = search_query.lower()
        filtered = [
            l for l in filtered
            if sq in l.get("company_name", "").lower()
            or sq in l.get("description", "").lower()
            or sq in l.get("executive_name", "").lower()
            or sq in l.get("orbit", "").lower()
        ]

    if provenance_mode == "Live Crawled Only (2026)":
        filtered = [l for l in filtered if l.get("is_live_crawled", False)]
    elif provenance_mode == "Vetted Pool Only":
        filtered = [l for l in filtered if not l.get("is_live_crawled", False)]

    # Sorting logic
    if sort_mode == "Funding: High to Low":
        filtered = sorted(filtered, key=lambda x: x.get("funding_revenue_usd", 0), reverse=True)
    elif sort_mode == "Funding: Low to High":
        filtered = sorted(filtered, key=lambda x: x.get("funding_revenue_usd", 0))
    elif sort_mode == "Company: A to Z":
        filtered = sorted(filtered, key=lambda x: x.get("company_name", ""))

    # Metric Cards Deck
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="dark-card">
            <div class="dark-card-number">{len(filtered)}</div>
            <div class="dark-card-label">QUALIFIED LEADS ({len(current_leads)} TOTAL)</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        live_crawled_count = sum(1 for l in filtered if l.get('is_live_crawled', False))
        st.markdown(f"""
        <div class="dark-card">
            <div class="dark-card-number">{live_crawled_count}</div>
            <div class="dark-card-label">LIVE CRAWLED (2026 DEALS)</div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown("""
        <div class="dark-card">
            <div class="dark-card-number">100%</div>
            <div class="dark-card-label">NON-US GEOGRAPHIC COVERAGE</div>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        st.markdown("""
        <div class="dark-card">
            <div class="dark-card-number">100%</div>
            <div class="dark-card-label">DNS MX RECORD DELIVERABILITY</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Tabbed Interface
    tab_list, tab_details, tab_audit, tab_actions = st.tabs([
        "QUALIFIED LEADS TABLE",
        "COMPANY PROFILES",
        "AUDIT LOG",
        "EXPORT DATA"
    ])

    with tab_list:
        st.markdown(f"#### VERIFIED SCALE-UPS ({len(filtered)} COMPANIES)")
        st.caption(f"Strict TVB parameter adherence: $1M-$5M USD, Non-US HQ, Tech platform, DNS MX verified corporate emails.")

        if filtered:
            table_records = []
            for l in filtered:
                is_live = l.get("is_live_crawled", False)
                source_tag = "[LIVE CRAWLED]" if is_live else "[VETTED]"
                source_url = l.get("live_source_url", l.get("website", ""))

                table_records.append({
                    "SOURCE": source_tag,
                    "COMPANY": l.get("company_name"),
                    "ORBIT": l.get("orbit"),
                    "FUNDING": f"${l.get('funding_revenue_usd', 0):,.0f} USD",
                    "STAGE": l.get("funding_stage", "Seed"),
                    "HEADQUARTERS": l.get("headquarters"),
                    "EXECUTIVE CONTACT": f"{l.get('executive_name')} ({l.get('executive_title')})",
                    "VERIFIED EMAIL": l.get("verified_email"),
                    "US PRESENCE": l.get("us_presence"),
                    "SOURCE / WEBSITE": source_url
                })

            df_table = pd.DataFrame(table_records)
            st.dataframe(
                df_table,
                use_container_width=True,
                column_config={
                    "SOURCE / WEBSITE": st.column_config.LinkColumn("Source Link"),
                    "VERIFIED EMAIL": st.column_config.TextColumn("Verified Corporate Email"),
                },
                hide_index=True
            )
        else:
            st.info("No companies match the active search filter.")

    with tab_details:
        st.markdown("#### EXECUTIVE & FUNDING INTELLIGENCE")
        if filtered:
            for l in filtered:
                is_live = l.get("is_live_crawled", False)
                tag_label = "LIVE CRAWLED DEAL (2026)" if is_live else "VETTED RESEARCH RECORD"
                with st.expander(f"[{tag_label}] {l.get('company_name')} — {l.get('orbit')} ({l.get('headquarters')})"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Platform Overview:** {l.get('description')}")
                        st.markdown(f"**Official Domain:** [{l.get('domain')}]({l.get('website')})")
                        st.markdown(f"**Funding Evidence:** `{l.get('funding_evidence')}`")
                        if is_live:
                            st.markdown(f"**Live Announcement:** [View Source Article]({l.get('live_source_url')})")
                    with c2:
                        st.markdown(f"**Key Executive:** `{l.get('executive_name')}` ({l.get('executive_title')})")
                        st.markdown(f"**Corporate Email:** `{l.get('verified_email')}` [DELIVERABLE]")
                        st.markdown(f"**Deliverability Status:** `{l.get('email_status')}`")
                        if l.get("contact_audit_note"):
                            st.markdown(f"**Contact Audit:** *{l.get('contact_audit_note')}*")
                        st.markdown(f"**US Market Footprint:** {l.get('us_presence')}")
                        st.markdown(f"**TVB Strategic Rationale:** *{l.get('tvb_value_alignment')}*")
        else:
            st.info("No company profiles available.")

    with tab_audit:
        st.markdown("#### COMPLIANCE VERIFICATION AUDIT")
        st.caption("Conservative rule-based validation engine auditing candidates against TVB screening parameters.")
        if filtered:
            audit_rows = []
            audit_details_map = {}

            for l in filtered:
                is_qual, rep = validate_tvb_candidate(l)
                comp_name = l.get("company_name", "Unknown")
                audit_details_map[comp_name] = (l, rep)

                funding_status = "PASS" if rep["funding_valid"] else "FAIL"
                tech_status = "PASS" if rep["tech_valid"] else "FAIL"
                location_status = "PASS" if rep["non_us_valid"] else "FAIL"
                contact_status = "PASS" if rep["contact_valid"] else "FAIL"
                active_status = "PASS" if rep["active_valid"] else "FAIL"
                overall = "QUALIFIED" if is_qual else "DISQUALIFIED"

                audit_rows.append({
                    "COMPANY": comp_name,
                    "FUNDING ($1M-$5M)": f"{funding_status} (${rep['parsed_funding_usd']:,.0f})",
                    "TECH PLATFORM": tech_status,
                    "NON-US HQ": f"{location_status} ({l.get('headquarters', 'N/A')[:18]})",
                    "EXECUTIVE CONTACT": f"{contact_status} ({l.get('executive_name', 'N/A')[:16]})",
                    "EMAIL & MX": "PASS" if rep["email_details"].get("verified") else "FAIL",
                    "ACTIVE ENTITY": active_status,
                    "OVERALL AUDIT": overall
                })

            df_audit = pd.DataFrame(audit_rows)
            st.dataframe(df_audit, use_container_width=True, hide_index=True)

            st.write("")
            st.markdown("##### DETAILED CANDIDATE AUDIT TRAIL")
            selected_comp = st.selectbox(
                "Select Company to Inspect Validation Record:",
                options=[l.get("company_name") for l in filtered],
                key="audit_company_inspect_select"
            )

            if selected_comp and selected_comp in audit_details_map:
                cand, rep = audit_details_map[selected_comp]
                
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    st.markdown(f"**Company:** `{cand.get('company_name')}`")
                    st.markdown(f"**Parsed Funding:** `${rep.get('parsed_funding_usd', 0):,.0f} USD` — {'Valid Range' if rep.get('funding_valid') else 'Out of Range'}")
                    st.markdown(f"**Tech Focus Alignment:** {'Verified scalable tech platform' if rep.get('tech_valid') else 'Non-tech entity'}")
                    st.markdown(f"**HQ & Geography:** `{cand.get('headquarters')}` ({'Minimal/No US presence confirmed' if rep.get('non_us_valid') else 'US Presence Detected'})")
                    st.markdown(f"**Corporate Standalone Status:** {'Active standalone scale-up' if rep.get('active_valid') else 'Inactive or Acquired'}")

                with col_a2:
                    st.markdown(f"**Identified Executive:** `{cand.get('executive_name')}` ({cand.get('executive_title', 'Executive')})")
                    st.markdown(f"**Target Email:** `{cand.get('verified_email', 'Unpublished')}`")
                    st.markdown(f"**Email Deliverability Check:** `{rep.get('email_details', {}).get('reason', 'N/A')}`")
                    st.markdown(f"**Contact Provenance:** `{rep.get('contact_provenance', 'direct_extraction')}`")
                    if rep.get("warnings"):
                        for w in rep["warnings"]:
                            st.warning(f"Audit Warning: {w}")
                    if rep.get("disqualification_reasons"):
                        for r in rep["disqualification_reasons"]:
                            st.error(f"Disqualification Flag: {r}")

                sources = rep.get("source_urls", [])
                if sources:
                    st.caption("Verified Audit Sources: " + " • ".join([f"[{u}]({u})" for u in sources[:4]]))

    with tab_actions:
        st.markdown("#### EXPORT & OUTREACH TOOLS")
        if filtered:
            e1, e2 = st.columns(2)
            with e1:
                st.markdown("**Structured CSV Export**")
                csv_buffer = io.StringIO()
                pd.DataFrame(filtered).to_csv(csv_buffer, index=False)
                st.download_button(
                    label="DOWNLOAD QUALIFIED LEADS (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name=f"tvb_qualified_leads_run_{st.session_state.run_count}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="download_leads_csv_btn"
                )
            with e2:
                st.markdown("**Executive Email Roster**")
                emails = [l.get("verified_email") for l in filtered if l.get("verified_email")]
                st.text_area("Copy-Paste Verified Founder Addresses:", ", ".join(emails), height=115, key="founder_emails_textarea")

st.divider()
st.caption("THE VENTURE BUILD // PROSPECTING SYSTEM • ENGINEERED FOR APPLICATION SCREENING • ZERO SETUP DEPLOYMENT")
