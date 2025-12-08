from __future__ import annotations
from typing import Dict, Any, List
import json

from models import AIUseCase
from finops.finops_config import load_finops_config
from llm.lm_interface import chat_completion
from storage.vector_db_manager import VectorDBManager
import re

PLATFORMS = [
    {
        "name": "MS Copilot Studio",
        "category": "Low-code conversational AI",
        "strengths": [
            "Fast prototyping",
            "Strong M365 integration",
        ],
        "bestFor": [
            "FAQ-style conversational AI for engineers",
            "Lightweight RAG on internal docs",
        ],
        "costBand": "Medium",
    },
    {
        "name": "Aiden Internal AI",
        "category": "Enterprise AI gateway",
        "strengths": [
            "Central governance and logging",
            "Multi-model routing",
        ],
        "bestFor": [
            "Bank-wide RAG & talk2data",
            "Leadership dashboards & analysis",
        ],
        "costBand": "Medium-High",
    },
    {
        "name": "Agentic Aidlets on Aiden",
        "category": "Agentic workflows",
        "strengths": [
            "Multi-step ops automation",
        ],
        "bestFor": [
            "Ops transformation workflows",
        ],
        "costBand": "High",
    },
    {
        "name": "Custom RAG on PCF",
        "category": "Full-code custom solution",
        "strengths": [
            "Maximum control & flexibility",
        ],
        "bestFor": [
            "High-value production use cases needing deep integration",
        ],
        "costBand": "Medium-High",
    },
]

HYPOTHETICAL_USECASES = [
    {
        "UseCaseID": "HYP-001",
        "UseCaseName": "KYC document triage copilot",
        "ProjectStage": "Pilot",
        "FundingModel": "Central",
        "EstimatedBudgetGBP": 250000,
        "DeliveryLeadType": "Internal Build",
        "ValueMagnitude": "H",
        "ChangeType": "Optimise",
        "ProjectDescription": "GenAI copilot that extracts KYC document data and guides analysts.",
    },
    {
        "UseCaseID": "HYP-002",
        "UseCaseName": "Contact centre intent router",
        "ProjectStage": "Production",
        "FundingModel": "Local",
        "EstimatedBudgetGBP": 150000,
        "DeliveryLeadType": "Hybrid",
        "ValueMagnitude": "M",
        "ChangeType": "Scale",
        "ProjectDescription": "Intent classification and knowledge answers for inbound calls.",
    },
    {
        "UseCaseID": "HYP-003",
        "UseCaseName": "Risk policy Q&A RAG",
        "ProjectStage": "POC",
        "FundingModel": "Central",
        "EstimatedBudgetGBP": 120000,
        "DeliveryLeadType": "Internal Build",
        "ValueMagnitude": "M",
        "ChangeType": "Optimise",
        "ProjectDescription": "Policy search and citation bot for risk teams using internal docs.",
    },
    {
        "UseCaseID": "HYP-004",
        "UseCaseName": "Trader research copilot",
        "ProjectStage": "Pilot",
        "FundingModel": "Co-funded",
        "EstimatedBudgetGBP": 400000,
        "DeliveryLeadType": "Hybrid",
        "ValueMagnitude": "VH",
        "ChangeType": "Reinvent",
        "ProjectDescription": "Retrieval and summarisation across research, pricing, and news feeds.",
    },
    {
        "UseCaseID": "HYP-005",
        "UseCaseName": "Operations automation agent",
        "ProjectStage": "Discovery",
        "FundingModel": "Local",
        "EstimatedBudgetGBP": 80000,
        "DeliveryLeadType": "Internal Build",
        "ValueMagnitude": "M",
        "ChangeType": "Scale",
        "ProjectDescription": "Agentic workflow handling reconciliations, lookups, and ticket updates.",
    },
]

SYSTEM_PROMPT = """
You are an internal AI advisor for the bank.

Goal: for each GenAI use case, recommend the most appropriate platform and design
pattern based on:
- project stage
- value magnitude and type
- change type (Optimise / Scale / Reinvent)
- whether it is transformational
- funding model (Local vs Central vs Co-funded)
- estimated budget
- rough cost & risk
- environment (Prod vs Lower), AI platform type, and number of users
- admin-configured decision factors: prioritize financial benefit first, then cost control, then production readiness

Prefer simple / governed options (e.g. Copilot Studio) for early-stage & lower value,
and more powerful options (Aiden, Agentic Aidlets, custom RAG on PCF) for high-value
and transformational use cases. Consider funding model and budget when weighing hosted vs
custom builds. Use similar real/hypothetical use cases to justify the choice.

Strict rules to avoid hallucination:
- Only use the fields provided in the payload (usecase, similarUsecases, hypotheticalUsecases, platforms).
- If a field is missing, state that it is unknown instead of guessing.
- Keep recommendations specific to the bank's platforms listed in `platforms`.

Respond in STRICT JSON:
{
  "recommendedPlatform": "...",
  "recommendedPattern": "...",
  "summary": "...",
  "rationale": "...",
  "estimatedCostBand": "Low|Medium|High",
  "riskNotes": "...",
  "nextSteps": ["...", "..."],
  "bestExistingUsecase": {
    "id": "...",
    "reason": "... reference budget/funding/env/benefit ...",
    "similarityNote": "why this is the closest analogue"
  },
  "explanation": "brief rationale grounded in provided fields and decision factors"
}
"""


def _infer_applicability(usecase: AIUseCase) -> tuple[float, List[str]]:
    text = f"{usecase.UseCaseName} {usecase.ProjectDescription}".lower()
    hits = [kw for kw in ["code", "coding", "developer", "devops", "pipeline", "ci/cd", "gitlab", "test", "testing"] if kw in text]
    score = 1.0 if hits else 0.0
    return score, hits


def recommend_for_usecase(usecase: AIUseCase, decision_factors: Dict[str, Any] | None = None) -> Dict[str, Any]:
    vdb = VectorDBManager()
    query_text = f"{usecase.UseCaseName} {usecase.ProjectDescription} {usecase.Team} {usecase.AIType} {usecase.Environment}"
    similar = vdb.search_similar(query_text, k=5)

    factors = decision_factors or load_finops_config()
    applicability_score, applicability_hits = _infer_applicability(usecase)

    user_payload = {
        "usecase": usecase.model_dump(),
        "similarUsecases": [r["metadata"] for r in similar],
        "hypotheticalUsecases": HYPOTHETICAL_USECASES,
        "platforms": PLATFORMS,
        "decision_factors": factors,
        "decision_factors_hint": (
            "Prioritize financial benefit > cost control > production readiness > governance risk > user adoption > solution applicability. "
            "Do not invent numbers; state unknowns."
        ),
        "applicability": {"score": applicability_score, "hits": applicability_hits},
    }

    user_prompt = json.dumps(user_payload, indent=2)
    raw = chat_completion(SYSTEM_PROMPT, user_prompt)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    # Fallbacks to keep UI safe
    parsed.setdefault("recommendedPlatform", parsed.get("recommendedPlatform", ""))
    parsed.setdefault("recommendedPattern", parsed.get("recommendedPattern", ""))
    parsed.setdefault("summary", raw[:300] if isinstance(raw, str) else parsed.get("summary", ""))
    parsed.setdefault("rationale", parsed.get("rationale", parsed.get("summary", "")))
    parsed.setdefault("estimatedCostBand", parsed.get("estimatedCostBand", ""))
    parsed.setdefault("riskNotes", parsed.get("riskNotes", ""))
    parsed.setdefault("nextSteps", parsed.get("nextSteps", []))
    parsed.setdefault("bestExistingUsecase", {"id": None, "reason": "No best match returned"})
    parsed["similar"] = similar

    # If no platform was returned, use a deterministic fallback.
    if not parsed.get("recommendedPlatform"):
        fallback = _fallback_recommendation(usecase)
        fallback["similar"] = similar
        return fallback

    return parsed


def _fallback_recommendation(usecase: AIUseCase) -> Dict[str, Any]:
    """Rule-based fallback if the LLM does not return a platform."""
    benefit = usecase.BenefitValuePerAnnum or 0
    budget = usecase.EstimatedBudgetGBP or 0
    users = usecase.NumberOfUsers or 0
    env = (usecase.Environment or "Unknown").lower()
    applicability_score, _ = _infer_applicability(usecase)

    if applicability_score >= 0.5:
        platform = "MS Copilot Studio"
        pattern = "Dev productivity / CI-CD copilot"
    elif benefit >= 500_000 or budget >= 200_000 or users > 100 or env == "production":
        platform = "Aiden Internal AI"
        pattern = "Enterprise AI gateway with governance and routing"
    elif budget <= 100_000 and users <= 50:
        platform = "MS Copilot Studio"
        pattern = "Low-code copilot with M365 integration"
    else:
        platform = "Custom RAG on PCF"
        pattern = "Retrieval-augmented generation on PCF"

    rationale = (
        f"Selected {platform} based on benefit £{int(benefit):,}, budget £{int(budget):,}, users {users}, env {env}."
    )
    return {
        "recommendedPlatform": platform,
        "recommendedPattern": pattern,
        "summary": rationale,
        "rationale": rationale,
        "estimatedCostBand": "Medium",
        "riskNotes": "",
        "nextSteps": [],
        "bestExistingUsecase": {"id": None, "reason": "Fallback heuristic"},
    }
