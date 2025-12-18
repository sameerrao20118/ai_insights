import datetime as dt
from typing import List, Any

import pandas as pd
import plotly.express as px
import streamlit as st

from admin_components.bulk_import_tab import render_bulk_import_tab
from admin_components.dashboard_tab import render_dashboard_tab
from admin_components.manual_add_tab import render_manual_add_tab
from admin.admin_utils import get_vdb
from finops.finops_config import load_finops_config
import json
from models import AIUseCase
from platform_logic.platform_recommender import recommend_for_usecase
from llm.prompts import (
    CATALOGUE_CHAT_SYSTEM_PROMPT,
    LEADER_QA_SYSTEM_PROMPT,
    PROMPT_NOTES,
)
import services

APP_NAME = "AI Usage Insights"
WEIGHT_LABELS = {
    "financial_benefit": "Financial benefit (higher is better)",
    "cost_efficiency": "Cost efficiency / cost control",
    "production_readiness": "Production readiness",
    "governance_risk": "Governance & risk",
    "user_adoption": "User adoption",
    "solution_applicability": "Solution applicability to problem (e.g., dev/CI/CD fit)",
}

def _get_prompt(session_key: str, label: str, default: str) -> str:
    if session_key not in st.session_state:
        st.session_state[session_key] = default
    return st.session_state[session_key]


def _get_decision_factors() -> dict:
    base_cfg = load_finops_config()
    overrides = st.session_state.get("finops_overrides", {})
    merged_weights = {**base_cfg.get("weights", {}), **overrides.get("weights", {})}
    return {**base_cfg, "weights": merged_weights}


def _render_prompt_config() -> None:
    with st.expander("Prompt configuration (tune response behaviour)"):
        st.caption(PROMPT_NOTES)
        leader_prompt = st.text_area(
            "Leader Q&A system prompt",
            value=_get_prompt("leader_qa_prompt", "Leader Q&A system prompt", LEADER_QA_SYSTEM_PROMPT),
            height=120,
        )
        chat_prompt = st.text_area(
            "Catalogue chat system prompt",
            value=_get_prompt("catalogue_chat_prompt", "Catalogue chat system prompt", CATALOGUE_CHAT_SYSTEM_PROMPT),
            height=120,
        )
        if st.button("Save prompts"):
            st.session_state["leader_qa_prompt"] = leader_prompt
            st.session_state["catalogue_chat_prompt"] = chat_prompt
            st.success("Prompts updated for this session.")

    finops = _get_decision_factors()
    base_finops = load_finops_config()
    with st.expander("⚙️ Decision Factors for Platform Recommendations"):
        st.info("ℹ️ **Scope**: These weights are used ONLY for **Ad-hoc Platform Recommendation** (bottom of page). They do NOT affect Leader Questions or Catalogue Chat, which analyze actual performance data (ROI, benefits, costs).")
        st.caption("Adjust weights to experiment with platform recommendation logic. Changes apply per session only.")
        st.write("Base config:")
        st.json(base_finops)

        overrides = st.session_state.get("finops_overrides", {"weights": {}})
        updated_weights = {}
        for key, label in WEIGHT_LABELS.items():
            current = finops["weights"].get(key, 0.0)
            updated_weights[key] = st.slider(
                f"Weight: {label}",
                0.0,
                1.0,
                current,
                0.05,
                key=f"weight_slider_{key}",
            )

        col_save, col_reset = st.columns(2)
        if col_save.button("Apply weights (session only)"):
            st.session_state["finops_overrides"] = {"weights": updated_weights}
            st.success("Decision weights updated for this session.")
        if col_reset.button("Reset to finops_config.json"):
            st.session_state["finops_overrides"] = {"weights": {}}
            st.info("Decision weights reset to config defaults.")


def _render_leader_dashboards(df: pd.DataFrame) -> None:
    st.markdown("### Leader dashboards")
    
    # Styled metrics container
    st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total use-cases", len(df))
    col2.metric("Teams covered", df["Team"].nunique() if "Team" in df else 0)
    total_budget = df["EstimatedBudgetGBP"].fillna(0).sum() if "EstimatedBudgetGBP" in df else 0
    col3.metric("Total est. budget (GBP)", f"{int(total_budget):,}")
    st.markdown('</div>', unsafe_allow_html=True)

    # Brand colors for charts
    brand_colors = ["#5A287F", "#7B4BA6", "#9D72CC", "#C4B5FD", "#E9D5FF", "#F3E8FF"]
    
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        if "Environment" in df:
            env_counts = df["Environment"].fillna("Unknown").value_counts().reset_index(name="count").rename(columns={"index": "Environment"})
            env_fig = px.bar(
                env_counts, 
                x="Environment", 
                y="count", 
                title="Environments (Prod/Lower)",
                color_discrete_sequence=[brand_colors[0]]
            )
            env_fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="Inter",
                title_font_color="#2D3748",
                yaxis_gridcolor="#E2E8F0"
            )
            st.plotly_chart(env_fig, use_container_width=True)

    with col_chart2:
        if "AIType" in df:
            ai_counts = df["AIType"].fillna("Unknown").value_counts().reset_index(name="count").rename(columns={"index": "AIType"})
            ai_fig = px.pie(
                ai_counts, 
                names="AIType", 
                values="count", 
                title="AI platform mix",
                color_discrete_sequence=brand_colors
            )
            ai_fig.update_layout(
                font_family="Inter",
                title_font_color="#2D3748"
            )
            st.plotly_chart(ai_fig, use_container_width=True)

    if "BenefitValuePerAnnum" in df:
        benefit_fig = px.histogram(
            df,
            x="BenefitValuePerAnnum",
            nbins=10,
            title="Benefit value per annum distribution",
            color_discrete_sequence=[brand_colors[1]]
        )
        benefit_fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font_family="Inter",
            title_font_color="#2D3748",
            yaxis_gridcolor="#E2E8F0",
            bargap=0.1
        )
        st.plotly_chart(benefit_fig, use_container_width=True)


def _format_last_ingest() -> str:
    ts = st.session_state.get("last_ingest_time")
    count = st.session_state.get("last_ingest_count")
    if not ts:
        return "Not run yet"
    return f"{count or 0} records @ {ts.strftime('%d %b %Y, %H:%M')}"


def _render_global_header() -> None:
    """Renders professional NatWest-branded header with enterprise styling."""
    
    # Professional enterprise CSS styling with production-grade enhancements
    st.markdown("""
    <style>
    /* Import professional font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* Apply font globally */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        color: #2C3E50;
    }
    
    /* Global Background */
    .stApp {
        background-color: #FAFBFC;
    }

    /* Enhanced sidebar width */
    [data-testid="stSidebar"] {
        width: calc(21rem + 40px) !important;
        min-width: calc(21rem + 40px) !important;
        background-color: #FFFFFF !important;
        border-right: 1px solid #E0E0E0;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        width: calc(21rem + 40px) !important;
        min-width: calc(21rem + 40px) !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    
    /* Sidebar Navigation Links */
    [data-testid="stSidebar"] .stRadio > label {
        font-weight: 700;
        color: #5A287F;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-bottom: 4px;
        transition: all 0.2s ease;
        border: 1px solid transparent;
        color: #4A5568;
        font-weight: 500;
    }
    
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
        background-color: #F8F9FA;
        color: #5A287F;
    }

    /* Active Selection Styling */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] [data-checked="true"] {
        background-color: #F3EBFA !important;
        color: #5A287F !important;
        border-color: #E6DAF2 !important;
        font-weight: 600;
    }
    
    /* Main H1/H2 Styling */
    h1, h2, h3 {
        color: #2D3748;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    h1 { font-size: 2.2rem; }
    h2 { font-size: 1.6rem; margin-top: 1.5rem; margin-bottom: 1rem; }
    h3 { font-size: 1.25rem; font-weight: 600; color: #4A5568; margin-top: 1rem; }

    /* Cards / Containers */
    div.block-container {
        padding-top: 3rem;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: #718096;
        font-weight: 500;
    }

    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #5A287F;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 0px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: nowrap;
        background-color: transparent;
        border: none;
        color: #718096;
        font-weight: 500;
        padding: 0 0.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        color: #5A287F !important;
        border-bottom: 2px solid #5A287F;
        font-weight: 600;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div, 
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        border-radius: 6px;
        border: 1px solid #CBD5E0;
        background-color: white;
        color: #2D3748;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #5A287F;
        box-shadow: 0 0 0 1px #5A287F;
    }
    
    /* Buttons */
    div.stButton > button {
        background-color: #5A287F;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 4px rgba(90, 40, 127, 0.2);
        transition: all 0.2s;
    }
    
    div.stButton > button:hover {
        background-color: #42166C;
        box-shadow: 0 4px 6px rgba(90, 40, 127, 0.3);
        transform: translateY(-1px);
    }
    
    div.stButton > button:active {
        transform: translateY(0);
    }
    
    /* Secondary buttons (outlined) - Hacky, requires targeting specific button types if applied via type="secondary" */
    button[kind="secondary"] {
        background-color: white !important;
        color: #5A287F !important;
        border: 1px solid #5A287F !important;
        box-shadow: none !important;
    }
    
    button[kind="secondary"]:hover {
        background-color: #F3EBFA !important;
    }

    /* DataFrames */
    .stDataFrame {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Charts */
    .js-plotly-plot .plotly .modebar {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    
    # Render branded header with NatWest logo and LEFT alignment
    header_col1, header_col2 = st.columns([0.12, 0.88])
    
    with header_col1:
        try:
            st.image("assets/natwest_logo.png", width=60)
        except Exception:
            # Fallback to gradient icon if logo not found
            st.markdown("""
            <div style="
                width: 50px; 
                height: 50px; 
                background: linear-gradient(135deg, #5A287F 0%, #7B4BA6 100%);
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                color: white;
                font-size: 24px;
                box-shadow: 0 4px 6px rgba(90, 40, 127, 0.2);
            ">NW</div>
            """, unsafe_allow_html=True)
    
    with header_col2:
        st.markdown("""
        <div style="padding-top: 0.5rem;">
            <h1 style="
                color: #2C3E50; 
                margin: 0; 
                font-size: 2.2rem; 
                font-weight: 700;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                letter-spacing: -0.5px;
            ">AI Usage Insights</h1>
            <p style="
                color: #6C757D; 
                margin: 0.25rem 0 0 0; 
                font-size: 0.95rem;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-weight: 400;
            ">Enterprise AI Catalogue & Recommendations</p>
        </div>
        """, unsafe_allow_html=True)

    
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("Last ingest", _format_last_ingest())
    col2.metric("Environment", "Streamlit")
    col3.metric("Vector DB", "Chroma + OpenAI")



def render_leader_insights():
    st.subheader("Leader Insights – Platform & Pattern Advisor")
    st.write(
        "Pick a use-case from the catalogue and get a recommendation for which platform/"
        "design pattern to use. Recommendations factor in environment, platform type, funding, budget, risk, and similar use-cases."
    )
    with st.sidebar:
        _render_prompt_config()

    usecases = services.load_all_usecases()
    if not usecases:
        st.warning("No use-cases found. Go to 'Bulk Import' first.")
        return

    df = services.usecases_to_df(usecases)
    _render_leader_dashboards(df)

    st.markdown("### Ask a quick question")
    leader_q = st.text_input(
        "Leader question",
        placeholder="Which AI investment is delivering the strongest results? Where are we spending the most?",
    )
    if st.button("Render Insights", type="primary"):
        if not leader_q.strip():
            st.info("Enter a question to analyze the catalogue.")
        else:
            with st.spinner("Synthesizing an answer from the catalogue..."):
                try:
                    leader_prompt = st.session_state.get("leader_qa_prompt")
                    raw_answer = services.answer_leader_question(
                        leader_q, 
                        df, 
                        usecases, 
                        _get_decision_factors(),
                        system_prompt_override=leader_prompt
                    )
                    parsed = services.parse_llm_json(raw_answer)
                    
                    # Show only the answer prominently
                    answer_text = parsed.get("answer", raw_answer)
                    st.markdown(answer_text)
                    
                    # Hide explanation in expander (collapsed by default)
                    expl = parsed.get("explanation")
                    if expl:
                        with st.expander("Show explanation", expanded=False):
                            st.write(expl)
                except Exception as exc:  # noqa: BLE001
                    st.error("Could not generate an answer. Check your OpenAI/Ollama credentials and try again.")
                    st.caption(str(exc))

    st.markdown("### Chat with the catalogue")
    col_ctx1, col_ctx2, col_ctx3 = st.columns(3)
    ctx_ai_type = col_ctx1.selectbox("AI Type filter (optional)", ["", "AI Gateway", "Aiden", "Co-pilot", "Duo", "3rd Party", "Other"])
    ctx_env = col_ctx2.selectbox("Environment filter (optional)", ["", "Production", "Lower", "Both", "Unknown"])
    ctx_budget = col_ctx3.text_input("Budget notes (e.g., >100k, under 1M)", value="")
    chat_q = st.text_area(
        "Ask anything about the indexed AI use-cases",
        placeholder="e.g., Which AI types have the highest benefits? Where are we overspending relative to benefit?",
    )
    if st.button("Submit", type="primary"):
        if not chat_q.strip():
            st.info("Enter a chat question to continue.")
        else:
            filters = {
                "AIType": ctx_ai_type or None,
                "Environment": ctx_env or None,
                "BudgetNotes": ctx_budget or None,
            }
            with st.spinner("Chatting with the catalogue..."):
                try:
                    chat_prompt = st.session_state.get("catalogue_chat_prompt")
                    raw_reply = services.chat_with_catalogue(
                        chat_q, 
                        df, 
                        usecases, 
                        filters, 
                        _get_decision_factors(),
                        system_prompt_override=chat_prompt
                    )
                    parsed = services.parse_llm_json(raw_reply)
                    answer = parsed.get("answer", raw_reply)
                    if not isinstance(answer, str):
                        answer = str(answer)
                    st.write(answer)
                    expl = parsed.get("explanation")
                    if expl and str(expl).strip():
                        expl_str = expl if isinstance(expl, str) else str(expl)
                        with st.expander("Show explanation"):
                            st.write(expl_str)
                except Exception as exc:  # noqa: BLE001
                    st.error("Chat request failed. Verify OpenAI/Ollama credentials and try again.")
                    st.caption(str(exc))

    labels = [f"{u.UseCaseID} – {u.UseCaseName} ({u.Team})" for u in usecases]
    idx = st.selectbox(
        "Select a use case",
        list(range(len(labels))),
        format_func=lambda i: labels[i],
        help="Use cases come from the indexed catalogue.",
    )
    selected = usecases[idx]

    st.markdown(
        f"**Team:** {selected.Team} · **Env:** {selected.Environment or 'Unknown'} · "
        f"AI Type: {selected.AIType or 'Unknown'} · Budget: {selected.EstimatedBudgetGBP or 'N/A'}"
    )
    st.caption(selected.ProjectDescription)


    st.markdown("###Ad-hoc platform recommendation (manual inputs)")
    st.info("ℹ️ **Uses Decision Factors**: This feature uses the decision weights (configured in Config tab) to recommend which AI platform to use. It does NOT analyze existing portfolio performance.")
    with st.form("ad_hoc_reco_form"):
        col_a1, col_a2 = st.columns(2)
        adhoc_name = col_a1.text_input("Use-Case Name", value=selected.UseCaseName)
        adhoc_id = col_a2.text_input("Use-Case ID", value=selected.UseCaseID)

        col_a3, col_a4 = st.columns(2)
        adhoc_team = col_a3.text_input("Team", value=selected.Team)
        env_options = ["Production", "Lower", "Both", "Unknown"]
        current_env = selected.Environment or "Unknown"
        if current_env not in env_options:
            current_env = "Unknown"  # fall back when data has unexpected values (e.g., "Paused")
        adhoc_env = col_a4.selectbox(
            "Environment",
            env_options,
            index=env_options.index(current_env),
        )

        adhoc_desc = st.text_area("Project description", value=selected.ProjectDescription, height=100)

        col_a5, col_a6 = st.columns(2)
        adhoc_budget = col_a5.number_input(
            "Estimated Budget (GBP)", min_value=0.0, value=float(selected.EstimatedBudgetGBP or 0.0), step=10000.0
        )
        adhoc_users = col_a6.number_input("Number of Users", min_value=0, value=int(selected.NumberOfUsers or 0), step=10)

        st.caption("AI platform will be recommended automatically; no manual selection is needed.")

        adhoc_submit = st.form_submit_button("Get recommendation from manual inputs", type="primary")

    if adhoc_submit:
        try:
            adhoc_uc = AIUseCase(
                UseCaseName=adhoc_name,
                UseCaseID=adhoc_id,
                FunctionID=selected.FunctionID,
                Environment=adhoc_env if adhoc_env != "Unknown" else None,
                Team=adhoc_team,
                KeyContact=selected.KeyContact,
                ProjectDescription=adhoc_desc,
                EstimatedBudgetGBP=adhoc_budget or None,
                BenefitValuePerAnnum=selected.BenefitValuePerAnnum,
                AIType=None,
                NumberOfUsers=adhoc_users or None,
                UsageStartDate=selected.UsageStartDate,
                CostToDateGBP=selected.CostToDateGBP,
                LastMonthCostGBP=selected.LastMonthCostGBP,
                LastThreeMonthsCostGBP=selected.LastThreeMonthsCostGBP,
                LastYearCostGBP=selected.LastYearCostGBP,
                BenefitCostPerAnnum=selected.BenefitCostPerAnnum,
            )
            rec_raw = recommend_for_usecase(adhoc_uc, decision_factors=_get_decision_factors())
            rec = services.normalize_recommendation(rec_raw)
            platform = rec.get("recommendedPlatform") or "Not provided"
            pattern = rec.get("recommendedPattern") or "Not provided"

            st.success(f"Platform: {platform}")
            st.write(f"Pattern: {pattern}")
            with st.expander("Show recommendation details"):
                st.markdown("**Summary**")
                st.write(rec.get("summary", "Not provided"))
                st.markdown("**Rationale**")
                st.write(rec.get("rationale", "Not provided"))
                st.markdown("**Risks**")
                st.write(rec.get("riskNotes", "Not provided"))
                st.markdown("**Next steps**")
                if rec.get("nextSteps"):
                    st.write(rec["nextSteps"])
                else:
                    st.write("No next steps provided.")
                st.markdown("**Raw response**")
                st.json(rec)
        except Exception as exc:
            st.error("Unable to generate recommendation from manual inputs.")
            st.caption(str(exc))




def main():
    st.set_page_config(
        page_title="NatWest | AI Usage Insights",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded",
    )


    # Clean sidebar - no header duplication
    st.sidebar.markdown("---")
    st.sidebar.info("💡 Navigate using the menu below to explore AI initiatives, import data, and access leadership insights.")
    
    
    page = st.sidebar.radio(
        "📋 Navigation",
        [
            "📊 Dashboard",
            "📤 Bulk Import",
            "➕ Manual Add",
            "🎯 Leader Insights",
        ],
        label_visibility="visible"
    )
    
    # Extract clean page name (remove emoji)
    page_clean = page.split(" ", 1)[1] if " " in page else page

    _render_global_header()

    if page_clean == "Dashboard":
        render_dashboard_tab()
    elif page_clean == "Bulk Import":
        render_bulk_import_tab()
    elif page_clean == "Manual Add":
        render_manual_add_tab()
    elif page_clean == "Leader Insights":
        render_leader_insights()
