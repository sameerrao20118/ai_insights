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
    with st.expander("Decision factors (from finops_config.json)"):
        st.caption("Weights and heuristics follow FinOps best practice. Adjust weights to experiment; resets apply per session.")
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
    col1, col2, col3 = st.columns(3)
    col1.metric("Total use-cases", len(df))
    col2.metric("Teams covered", df["Team"].nunique() if "Team" in df else 0)
    total_budget = df["EstimatedBudgetGBP"].fillna(0).sum() if "EstimatedBudgetGBP" in df else 0
    col3.metric("Total est. budget (GBP)", f"{int(total_budget):,}")

    if "Environment" in df:
        env_counts = df["Environment"].fillna("Unknown").value_counts().reset_index(name="count").rename(columns={"index": "Environment"})
        env_fig = px.bar(env_counts, x="Environment", y="count", title="Environments (Prod/Lower)")
        st.plotly_chart(env_fig, use_container_width=True)

    if "AIType" in df:
        ai_counts = df["AIType"].fillna("Unknown").value_counts().reset_index(name="count").rename(columns={"index": "AIType"})
        ai_fig = px.pie(ai_counts, names="AIType", values="count", title="AI platform mix")
        st.plotly_chart(ai_fig, use_container_width=True)

    if "BenefitValuePerAnnum" in df:
        benefit_fig = px.histogram(
            df,
            x="BenefitValuePerAnnum",
            nbins=10,
            title="Benefit value per annum distribution",
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
    
    # Professional enterprise CSS styling
    st.markdown("""
    <style>
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #5A287F 0%, #42166C 100%);
        padding: 1.5rem 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .header-content {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    
    .header-logo {
        height: 50px;
        width: auto;
    }
    
    .header-title {
        color: white;
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .header-subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.95rem;
        margin: 0.25rem 0 0 0;
    }
    
    /* Enhanced sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
    }
    
    [data-testid="stSidebar"] .sidebar-content {
        padding: 1rem;
    }
    
    /* Enhanced metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #5A287F;
        font-weight: 600;
    }
    
    /* Enhanced tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #F8F9FA;
        border-radius: 4px;
        padding: 0 24px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #5A287F !important;
        color: white !important;
    }
    
    /* Enhanced expanders */
    .streamlit-expanderHeader {
        background-color: #F8F9FA;
        border-radius: 4px;
        font-weight: 500;
    }
    
    /* Professional button styling */
    .stButton > button {
        background-color: #5A287F;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #42166C;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Card-like containers */
    .element-container {
        background-color: white;
    }
    
    /* Professional spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render branded header
    try:
        header_col1, header_col2 = st.columns([1, 8])
        with header_col1:
            st.image("assets/natwest_logo.png", width=140)
        with header_col2:
            st.markdown("""
            <div style="padding-top: 0.5rem;">
                <h1 style="color: #5A287F; margin: 0; font-size: 2rem; font-weight: 600;">AI Usage Insights</h1>
                <p style="color: #6C757D; margin: 0.5rem 0 0 0; font-size: 1rem;">Enterprise AI Catalogue & Platform Recommendations</p>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        # Fallback if logo not found
        st.markdown("""
        <div style="background: linear-gradient(135deg, #5A287F 0%, #42166C 100%); 
                    padding: 1.5rem 2rem; border-radius: 8px; margin-bottom: 2rem; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h1 style="color: white; margin: 0; font-size: 1.8rem; font-weight: 600;">AI Usage Insights</h1>
            <p style="color: rgba(255, 255, 255, 0.9); margin: 0.25rem 0 0 0; font-size: 0.95rem;">
                Enterprise AI Catalogue & Platform Recommendations
            </p>
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
    if st.button("Answer leader question", type="secondary"):
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
                    st.success(parsed.get("answer", raw_answer))
                    expl = parsed.get("explanation")
                    if expl:
                        with st.expander("Show explanation"):
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
    if st.button("Send to LLM", type="primary"):
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

    st.markdown("### Ad-hoc platform recommendation (manual inputs)")
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

        adhoc_submit = st.form_submit_button("Get recommendation from manual inputs")

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

    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: #5A287F; margin: 0; font-size: 1.5rem; font-weight: 600;">AI Insights Hub</h2>
        <p style="color: #6C757D; font-size: 0.85rem; margin: 0.5rem 0;">Enterprise Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
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
