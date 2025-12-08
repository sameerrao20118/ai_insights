import json
from pathlib import Path
from typing import Any, Dict, Union

DEFAULT_CONFIG: Dict[str, Any] = {
    "weights": {
        "financial_benefit": 0.5,
        "cost_efficiency": 0.2,
        "production_readiness": 0.15,
        "governance_risk": 0.1,
        "user_adoption": 0.05,
        "solution_applicability": 0.1,
    },
    "heuristics": [
        "Prioritise use cases with clear, quantified financial benefit over pure cost.",
        "Favour production-grade deployments with monitoring, logging, and rollback plans.",
        "Prefer governed platforms (AI Gateway/Aiden) when data sensitivity is high.",
        "Reward cost per active user efficiency; flag expensive low-adoption workloads.",
        "Penalise solutions lacking observability, SLOs, or incident handling.",
        "For developer/CI/CD or code-generation workloads, favour copilot-style solutions with tight tool integration.",
    ],
}


def load_finops_config(path: Union[str, Path] = "finops_config.json") -> Dict[str, Any]:
    cfg_path = Path(path)
    if not cfg_path.exists():
        return DEFAULT_CONFIG
    try:
        with cfg_path.open() as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return DEFAULT_CONFIG
        return {**DEFAULT_CONFIG, **data, "weights": {**DEFAULT_CONFIG["weights"], **data.get("weights", {})}}
    except Exception:
        return DEFAULT_CONFIG
