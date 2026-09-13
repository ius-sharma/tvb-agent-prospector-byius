"""
TVB Autonomous Prospecting Agent - Streamlit dashboard.
Built for The Venture Build (TVB) Agentic and Automation Intern screening task.
"""

import io
import time
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from src.discovery import TVBDiscoveryAgent
from src.tvb_context import TVB_CRITERIA, TVB_HUBS, TVB_ORBITS


st.set_page_config(
    page_title="TVB Prospecting Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 750;
        color: #102033;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #425466;
        margin-bottom: 1.2rem;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.78rem;
        font-weight: 650;
        border-radius: 8px;
        background-color: #EFF5F1;
        color: #183B2F;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid #D8E7DD;
    }
    .metric-box {
        background: #F8FAFC;
        border: 1px solid #D9E2EC;
        padding: 14px;
        border-radius: 8px;
        min-height: 92px;
    }
    .metric-value {
        font-size: 1.55rem;
        font-weight: 750;
        color: #0F766E;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.76rem;
        color: #52616B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 6px;
    }
    .run-note {
        color: #52616B;
        font-size: 0.86rem;
    }
    .stButton>button {
        background-color: #0F766E;
        color: white;
        font-weight: 700;
        border-radius: 8px;
        padding: 0.58rem 1.4rem;
        border: none;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #115E59;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)


def run_agent(include_live_search: bool, query_count: int, results_per_query: int) -> Dict[str, Any]:
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(message: str, fraction: float) -> None:
        status_text.info(f"Agent status: {message}")
        progress_bar.progress(min(max(float(fraction), 0.0), 1.0))
        time.sleep(0.15)

    agent = TVBDiscoveryAgent()
    result = agent.run_pipeline(
        target_count=18,
        progress_callback=update_progress,
        include_live_search=include_live_search,
        query_count=query_count,
        results_per_query=results_per_query,
    )
    status_text.success(
        f"Run complete: {result['qualified_count']} qualified leads, "
        f"{len(result['needs_review'])} review items."
    )
    return result


def money(value: Any) -> str:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return ""


def pass_fail(value: bool) -> str:
    return "PASS" if value else "REVIEW"


def joined_sources(lead: Dict[str, Any]) -> str:
    audit_sources = (lead.get("audit") or {}).get("source_urls") or []
    source_urls = audit_sources or lead.get("source_urls") or []
    if not source_urls and lead.get("source_url"):
        source_urls = [lead["source_url"]]
    return " | ".join(source_urls)


def qualified_rows(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for lead in leads:
        rows.append(
            {
                "Company": lead.get("company_name", ""),
                "Description": lead.get("description", ""),
                "Industry / Orbit": lead.get("orbit", ""),
                "Funding / Revenue": f"{money(lead.get('funding_revenue_usd'))} - {lead.get('funding_stage', '')}",
                "Headquarters": lead.get("headquarters", ""),
                "CEO / Co-founder": f"{lead.get('executive_name', '')} {lead.get('executive_title', '')}".strip(),
                "Verified Email": lead.get("verified_email", ""),
                "Email Check": lead.get("email_status", ""),
                "US Presence": lead.get("us_presence", ""),
                "Source Type": lead.get("source_type", ""),
                "Website": lead.get("website", ""),
                "Evidence": joined_sources(lead),
            }
        )
    return rows


def review_rows(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for lead in leads:
        audit = lead.get("audit") or {}
        rows.append(
            {
                "Company": lead.get("company_name", ""),
                "Status": lead.get("qualification_status", "Needs review"),
                "Funding": pass_fail(bool(audit.get("funding_valid"))),
                "Tech Platform": pass_fail(bool(audit.get("tech_valid"))),
                "Non-US": pass_fail(bool(audit.get("non_us_valid"))),
                "Active": pass_fail(bool(audit.get("active_valid"))),
                "Contact": pass_fail(bool(audit.get("contact_valid"))),
                "Reason": lead.get("disqualification_reasons", ""),
                "Warning": lead.get("audit_warnings", ""),
                "Source Type": lead.get("source_type", ""),
                "Evidence": joined_sources(lead),
            }
        )
    return rows


if "pipeline" not in st.session_state:
    st.session_state.pipeline = TVBDiscoveryAgent().run_pipeline(
        target_count=18,
        include_live_search=False,
    )
    st.session_state.last_run_label = "Reviewed cache loaded"


with st.sidebar:
    st.markdown("### TVB Criteria")
    st.markdown(
        f"""
        - Funding/revenue: USD {TVB_CRITERIA["funding_revenue_min_usd"]:,} to USD {TVB_CRITERIA["funding_revenue_max_usd"]:,}
        - Tech-enabled platform
        - Minimal or no US presence
        - CEO/co-founder contact required
        - Blank fields preferred over guesses
        """
    )
    st.divider()

    st.markdown("### Run Settings")
    query_count = st.slider("Search vectors", min_value=4, max_value=20, value=10, step=2)
    results_per_query = st.slider("Results per vector", min_value=2, max_value=10, value=5)
    include_live_search = st.toggle("Live web discovery", value=True)

    st.divider()
    selected_orbit = st.selectbox("Orbit", options=["All Orbits"] + list(TVB_ORBITS.keys()))
    selected_hub = st.selectbox("Hub", options=["All Hubs"] + list(TVB_HUBS.keys()))


st.markdown('<div class="main-header">TVB Autonomous Prospecting Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Live discovery, strict filtering, and audit-ready lead qualification for The Venture Build.</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
<div>
    <span class="badge-pill">$1M-$5M validator</span>
    <span class="badge-pill">Live source discovery</span>
    <span class="badge-pill">Non-US screening</span>
    <span class="badge-pill">Non-generic email checks</span>
    <span class="badge-pill">15-lead minimum bar</span>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

action_col, status_col = st.columns([2, 1])
with action_col:
    if st.button("Trigger Prospecting Run", use_container_width=True):
        st.session_state.pipeline = run_agent(
            include_live_search=include_live_search,
            query_count=query_count,
            results_per_query=results_per_query,
        )
        st.session_state.last_run_label = st.session_state.pipeline["searched_at"]
        time.sleep(0.4)
        st.rerun()

with status_col:
    st.markdown(
        f'<div class="run-note">Last run: <b>{st.session_state.last_run_label}</b></div>',
        unsafe_allow_html=True,
    )

pipeline = st.session_state.pipeline
raw_qualified = pipeline.get("qualified", [])

filtered_qualified = raw_qualified
if selected_orbit != "All Orbits":
    filtered_qualified = [lead for lead in filtered_qualified if lead.get("orbit") == selected_orbit]
if selected_hub != "All Hubs":
    filtered_qualified = [lead for lead in filtered_qualified if lead.get("target_hub") == selected_hub]

meets_minimum = len(raw_qualified) >= TVB_CRITERIA["min_leads_bar"]

st.divider()

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-value">{len(filtered_qualified)}</div>
            <div class="metric-label">Qualified Displayed</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-value">{len(raw_qualified)}</div>
            <div class="metric-label">Qualified Total</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-value">{pipeline.get("raw_results_count", 0)}</div>
            <div class="metric-label">Live Results Read</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m4:
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-value">{len(pipeline.get("needs_review", []))}</div>
            <div class="metric-label">Needs Review</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m5:
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-value">{"YES" if meets_minimum else "NO"}</div>
            <div class="metric-label">15 Lead Bar</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

tab_table, tab_cards, tab_audit, tab_discovery = st.tabs(
    ["Qualified Leads", "Company Cards", "Criteria Audit", "Discovery Log"]
)

with tab_table:
    st.subheader("Qualified Companies")
    st.caption(
        f"{len(raw_qualified)} total qualified leads. "
        f"{pipeline.get('qualified_from_live', 0)} from live discovery, "
        f"{pipeline.get('qualified_from_cache', 0)} from reviewed cache."
    )

    df = pd.DataFrame(qualified_rows(filtered_qualified))
    if df.empty:
        st.warning("No qualified leads match the selected filters.")
    else:
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Website": st.column_config.LinkColumn("Website"),
                "Evidence": st.column_config.TextColumn("Evidence"),
            },
            hide_index=True,
        )
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download CSV",
            data=csv_buffer.getvalue(),
            file_name="tvb_qualified_leads.csv",
            mime="text/csv",
        )

with tab_cards:
    st.subheader("Company Detail")
    for lead in filtered_qualified:
        with st.expander(f"{lead.get('company_name')} - {lead.get('orbit')}"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Description:** {lead.get('description', '')}")
                st.markdown(f"**Funding evidence:** {lead.get('funding_evidence', '')}")
                st.markdown(f"**Website:** {lead.get('website', '')}")
                st.markdown(f"**Evidence:** {joined_sources(lead)}")
            with c2:
                st.markdown(f"**Contact:** {lead.get('executive_name', '')} ({lead.get('executive_title', '')})")
                st.markdown(f"**Email:** {lead.get('verified_email', '')}")
                st.markdown(f"**Email check:** {lead.get('email_status', '')}")
                st.markdown(f"**TVB alignment:** {lead.get('tvb_value_alignment', '')}")

with tab_audit:
    st.subheader("Validation Audit")
    audit_rows = []
    for lead in filtered_qualified:
        audit = lead.get("audit") or {}
        audit_rows.append(
            {
                "Company": lead.get("company_name", ""),
                "Funding": pass_fail(bool(audit.get("funding_valid"))),
                "Parsed Funding": money(audit.get("parsed_funding_usd")),
                "Tech Platform": pass_fail(bool(audit.get("tech_valid"))),
                "Non-US": pass_fail(bool(audit.get("non_us_valid"))),
                "Active": pass_fail(bool(audit.get("active_valid"))),
                "Contact": pass_fail(bool(audit.get("contact_valid"))),
                "Warnings": lead.get("audit_warnings", ""),
            }
        )
    st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)

with tab_discovery:
    st.subheader("Live Discovery and Review Queue")
    query_rows = [{"Search Vector": query} for query in pipeline.get("queries", [])]
    if query_rows:
        st.markdown("**Generated Search Vectors**")
        st.dataframe(pd.DataFrame(query_rows), use_container_width=True, hide_index=True)
    elif not pipeline.get("search_available", True):
        st.warning("duckduckgo-search is not installed in this environment.")
    else:
        st.info("Live search has not been triggered in this session.")

    review_df = pd.DataFrame(review_rows(pipeline.get("needs_review", [])))
    if review_df.empty:
        st.success("No review items from the latest run.")
    else:
        st.markdown("**Rejected / Needs Review Candidates**")
        st.dataframe(review_df, use_container_width=True, hide_index=True)

st.divider()
st.caption("TVB Agentic and Automation Intern submission - autonomous discovery with explicit validation audit.")
