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
from llm.lm_interface import chat_completion
from models import AIUseCase
from platform_logic.platform_recommender import recommend_for_usecase
from llm.prompts import (
    CATALOGUE_CHAT_SYSTEM_PROMPT,
    LEADER_QA_SYSTEM_PROMPT,
    PROMPT_NOTES,
)

APP_NAME = "AI Usage Insights"
WEIGHT_LABELS = {
    "financial_benefit": "Financial benefit (higher is better)",
    "cost_efficiency": "Cost efficiency / cost control",
    "production_readiness": "Production readiness",
    "governance_risk": "Governance & risk",
    "user_adoption": "User adoption",
    "solution_applicability": "Solution applicability to problem (e.g., dev/CI/CD fit)",
}


def _usecases_to_df(usecases: List[AIUseCase]) -> pd.DataFrame:
    df = pd.DataFrame([u.model_dump() for u in usecases])
    return df


def _get_prompt(session_key: str, label: str, default: str) -> str:
    if session_key not in st.session_state:
        st.session_state[session_key] = default
    return st.session_state[session_key]


def _get_decision_factors() -> dict:
    base_cfg = load_finops_config()
    overrides = st.session_state.get("finops_overrides", {})
    merged_weights = {**base_cfg.get("weights", {}), **overrides.get("weights", {})}
    return {**base_cfg, "weights": merged_weights}


def _parse_llm_json(raw: str) -> dict:
    import json

    if isinstance(raw, dict):
        return {
            "answer": raw.get("answer"),
            "explanation": raw.get("explanation"),
        }
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"answer": raw, "explanation": ""}


def _normalize_recommendation(raw_rec: Any) -> dict:
    """Ensure recommendation is a dict with sane defaults."""
    import json

    rec = raw_rec
    if isinstance(raw_rec, str):
        try:
            rec = json.loads(raw_rec)
        except Exception:
            rec = {}
    if not isinstance(rec, dict):
        rec = {}
    rec.setdefault("recommendedPlatform", "")
    rec.setdefault("recommendedPattern", "")
    rec.setdefault("summary", "")
    rec.setdefault("rationale", "")
    rec.setdefault("riskNotes", "")
    rec.setdefault("nextSteps", [])
    return rec


from typing import Optional, Tuple, Any


def _parse_budget_filter(text: str) -> Tuple[Optional[float], Optional[float]]:
    """Return (min_budget, max_budget) in GBP based on a loose text hint."""
    if not text:
        return (None, None)
    t = text.lower().replace(",", "").strip()
    num = None
    if "m" in t:
        try:
            num = float(t.split("m")[0].split()[-1]) * 1_000_000
        except Exception:
            num = None
    elif "k" in t:
        try:
            num = float(t.split("k")[0].split()[-1]) * 1_000
        except Exception:
            num = None
    else:
        import re

        m = re.search(r"([0-9]+(?:\.[0-9]+)?)", t)
        if m:
            num = float(m.group(1))

    if num is None:
        return (None, None)

    if any(token in t for token in ["under", "<", "less", "below"]):
        return (None, num)
    if any(token in t for token in [">", "over", "more", "above"]):
        return (num, None)
    return (None, None)


def _apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    subset = df.copy()
    ai_type = filters.get("AIType")
    environment = filters.get("Environment")
    budget_notes = filters.get("BudgetNotes") or ""

    if ai_type:
        subset = subset[subset["AIType"] == ai_type]
    if environment:
        subset = subset[subset["Environment"] == environment]

    min_budget, max_budget = _parse_budget_filter(budget_notes)
    if "EstimatedBudgetGBP" in subset:
        if min_budget is not None:
            subset = subset[subset["EstimatedBudgetGBP"].fillna(0) >= min_budget]
        if max_budget is not None:
            subset = subset[subset["EstimatedBudgetGBP"].fillna(0) <= max_budget]

    return subset


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


def _answer_leader_question(question: str, df: pd.DataFrame, usecases: List[AIUseCase]) -> str:
    factors = _get_decision_factors()
    overrun_count = int(df["BudgetOverrun"].fillna(False).sum()) if "BudgetOverrun" in df else 0
    overrun_rate = (overrun_count / len(df)) if len(df) > 0 else 0.0
    context = {
        "metrics": {
            "total": len(df),
            "teams": df["Team"].nunique() if "Team" in df else 0,
            "total_est_budget": float(df["EstimatedBudgetGBP"].fillna(0).sum()) if "EstimatedBudgetGBP" in df else 0.0,
            "env_mix": df["Environment"].fillna("Unknown").value_counts().to_dict() if "Environment" in df else {},
            "ai_type_mix": df["AIType"].fillna("Unknown").value_counts().to_dict() if "AIType" in df else {},
            "benefit_distribution": df["BenefitValuePerAnnum"].dropna().describe().to_dict()
            if "BenefitValuePerAnnum" in df
            else {},
            "roi_distribution": df["ROIPerAnnum"].dropna().describe().to_dict() if "ROIPerAnnum" in df else {},
            "budget_overrun_count": overrun_count,
            "budget_overrun_rate": overrun_rate,
        },
        "sample_usecases": [u.model_dump() for u in usecases[:12]],
        "decision_factors": factors,
        "question": question,
    }
    system = _get_prompt("leader_qa_prompt", "Leader Q&A system prompt", LEADER_QA_SYSTEM_PROMPT)
    user = f"Question: {question}\nCatalogue context:\n{context}"
    return chat_completion(system, user)


def _chat_with_catalogue(question: str, df: pd.DataFrame, usecases: List[AIUseCase], user_filters: dict) -> dict:
    factors = _get_decision_factors()
    filtered_df = _apply_filters(df, user_filters)
    if filtered_df.empty:
        suggestion = (
            "No records matched. Try adding AI Type, Environment (Prod/Lower), a budget threshold "
            "(e.g., 'under 1M'), or include team or benefit keywords."
        )
        return {"answer": suggestion, "explanation": suggestion}

    agg_benefit = {}
    agg_budget = {}
    if "AIType" in filtered_df and "BenefitValuePerAnnum" in filtered_df:
        agg_benefit = (
            filtered_df.groupby("AIType")["BenefitValuePerAnnum"].sum().sort_values(ascending=False).to_dict()
        )
    if "AIType" in filtered_df and "EstimatedBudgetGBP" in filtered_df:
        agg_budget = (
            filtered_df.groupby("AIType")["EstimatedBudgetGBP"].sum().sort_values(ascending=False).to_dict()
        )

    overspend = []
    if agg_benefit and agg_budget:
        for ai_type, spend in agg_budget.items():
            benefit = agg_benefit.get(ai_type, 0)
            if spend > benefit and benefit > 0:
                overspend.append(
                    {"ai_type": ai_type, "spend": spend, "benefit": benefit, "note": "Spend exceeds benefit"}
                )

    filtered_ids = set(filtered_df["UseCaseID"].tolist()) if "UseCaseID" in filtered_df else set()
    filtered_usecases = [u for u in usecases if u.UseCaseID in filtered_ids] if filtered_ids else usecases
    sample_usecases = [u.model_dump() for u in filtered_usecases[:12]]
    metrics = {
        "count": len(filtered_df),
        "roi_distribution": filtered_df["ROIPerAnnum"].dropna().describe().to_dict()
        if "ROIPerAnnum" in filtered_df
        else {},
        "budget_overrun_count": int(filtered_df["BudgetOverrun"].fillna(False).sum())
        if "BudgetOverrun" in filtered_df
        else 0,
    }

    payload = {
        "question": question,
        "filters": user_filters,
        "decision_factors": factors,
        "aggregates": {
            "benefit_by_ai_type": agg_benefit,
            "budget_by_ai_type": agg_budget,
            "overspend_notes": overspend,
        },
        "metrics": metrics,
        "sample_usecases": sample_usecases,
    }

    system_prompt = _get_prompt("catalogue_chat_prompt", "Catalogue chat system prompt", CATALOGUE_CHAT_SYSTEM_PROMPT)
    user_prompt = json.dumps(payload, indent=2)
    raw_reply = chat_completion(system_prompt, user_prompt)
    parsed = _parse_llm_json(raw_reply)
    parsed.setdefault(
        "explanation",
        {
            "filters": user_filters,
            "decision_factors": factors,
            "aggregates": payload["aggregates"],
        },
    )
    return parsed


def _load_all_usecases() -> List[AIUseCase]:
    vdb = get_vdb()
    if not vdb:
        return []

    results = vdb.search_similar("all use cases", k=500)
    seen = {}
    for r in results:
        meta = dict(r["metadata"])
        if not meta:
            continue
        uid = meta.get("UseCaseID")
        if uid and uid not in seen:
            seen[uid] = AIUseCase(**meta)
    return list(seen.values())


def _format_last_ingest() -> str:
    ts = st.session_state.get("last_ingest_time")
    count = st.session_state.get("last_ingest_count")
    if not ts:
        return "Not run yet"
    return f"{count or 0} records @ {ts.strftime('%d %b %Y, %H:%M')}"


def _render_global_header() -> None:
    st.title(APP_NAME)
    st.caption("Bank-wide AI catalogue with leader-ready insights and platform recommendations.")

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

    usecases = _load_all_usecases()
    if not usecases:
        st.warning("No use-cases found. Go to 'Bulk Import' first.")
        return

    df = _usecases_to_df(usecases)
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
                    raw_answer = _answer_leader_question(leader_q, df, usecases)
                    parsed = _parse_llm_json(raw_answer)
                    st.success(parsed.get("answer", raw_answer))
                    expl = parsed.get("explanation")
                    if expl:
                        with st.expander("Show explanation"):
                            st.write(expl)
                except Exception as exc:  # noqa: BLE001
                    st.error("Could not generate an answer. Check your OpenAI credentials and try again.")
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
                    raw_reply = _chat_with_catalogue(chat_q, df, usecases, filters)
                    parsed = _parse_llm_json(raw_reply)
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
                    st.error("Chat request failed. Verify OpenAI credentials and try again.")
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
            rec = _normalize_recommendation(rec_raw)
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
        page_title="AI Usage Insights – AI Catalogue & Platform Advisor",
        layout="wide",
    )

    st.sidebar.title(APP_NAME)
    st.sidebar.info("Refresh the catalogue from Excel, then explore insights and platform recommendations.")
    page = st.sidebar.radio(
        "Navigate",
        [
            "Dashboard",
            "Bulk Import",
            "Manual Add",
            "Leader Insights",
        ],
    )

    _render_global_header()

    if page == "Dashboard":
        render_dashboard_tab()
    elif page == "Bulk Import":
        render_bulk_import_tab()
    elif page == "Manual Add":
        render_manual_add_tab()
    elif page == "Leader Insights":
        render_leader_insights()
