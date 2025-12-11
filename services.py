import json
import pandas as pd
from typing import List, Any, Optional, Tuple, Dict

from admin.admin_utils import get_vdb
from finops.finops_config import load_finops_config
from llm.lm_interface import chat_completion
from models import AIUseCase
from llm.prompts import (
    CATALOGUE_CHAT_SYSTEM_PROMPT,
    LEADER_QA_SYSTEM_PROMPT,
)

def usecases_to_df(usecases: List[AIUseCase]) -> pd.DataFrame:
    df = pd.DataFrame([u.model_dump() for u in usecases])
    return df

def parse_llm_json(raw: str) -> dict:
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

def normalize_recommendation(raw_rec: Any) -> dict:
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

def parse_budget_filter(text: str) -> Tuple[Optional[float], Optional[float]]:
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

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    subset = df.copy()
    ai_type = filters.get("AIType")
    environment = filters.get("Environment")
    budget_notes = filters.get("BudgetNotes") or ""

    if ai_type:
        subset = subset[subset["AIType"] == ai_type]
    if environment:
        subset = subset[subset["Environment"] == environment]

    min_budget, max_budget = parse_budget_filter(budget_notes)
    if "EstimatedBudgetGBP" in subset:
        if min_budget is not None:
            subset = subset[subset["EstimatedBudgetGBP"].fillna(0) >= min_budget]
        if max_budget is not None:
            subset = subset[subset["EstimatedBudgetGBP"].fillna(0) <= max_budget]

    return subset

def load_all_usecases() -> List[AIUseCase]:
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

def answer_leader_question(question: str, df: pd.DataFrame, usecases: List[AIUseCase], decision_factors: dict, system_prompt_override: str = None) -> str:
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
        "decision_factors": decision_factors,
        "question": question,
    }
    system = system_prompt_override or LEADER_QA_SYSTEM_PROMPT
    
    # Use new interface
    from llm.lm_interface import LLMInterface, LeaderInsightAnswer
    llm = LLMInterface()
    
    # We pass the context as the payload
    payload = {
        "question": question,
        "context": context
    }
    
    # For Leader QA, we often just want text, but the plan asked for JSON structure.
    # The prompt might need adjustment, but we'll try to enforce JSON.
    try:
        result: LeaderInsightAnswer = llm.chat_completion_json(
            system_prompt=system,
            payload=payload,
            answer_model=LeaderInsightAnswer
        )
        # Return raw JSON string to match previous signature expectations of 'api.py' which parses it
        return json.dumps(result.model_dump())
    except Exception:
        user = f"Question: {question}\nCatalogue context:\n{context}"
        return llm.chat_completion([
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ])

def chat_with_catalogue(question: str, df: pd.DataFrame, usecases: List[AIUseCase], user_filters: dict, decision_factors: dict, system_prompt_override: str = None) -> dict:
    filtered_df = apply_filters(df, user_filters)
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
        "decision_factors": decision_factors,
        "aggregates": {
            "benefit_by_ai_type": agg_benefit,
            "budget_by_ai_type": agg_budget,
            "overspend_notes": overspend,
        },
        "metrics": metrics,
        "sample_usecases": sample_usecases,
    }

    system_prompt = system_prompt_override or CATALOGUE_CHAT_SYSTEM_PROMPT
    
    # Use the new class-based interface for structured JSON
    from llm.lm_interface import LLMInterface, CatalogueChatAnswer
    llm = LLMInterface()
    
    try:
        # Structured output
        result: CatalogueChatAnswer = llm.chat_completion_json(
            system_prompt=system_prompt,
            payload=payload,
            answer_model=CatalogueChatAnswer
        )
        return result.model_dump()
    except Exception:
        # Fallback to text (not ideal but safe)
        user_prompt = json.dumps(payload, indent=2)
        raw_reply = llm.chat_completion([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        return parse_llm_json(raw_reply)
