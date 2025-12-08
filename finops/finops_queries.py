from __future__ import annotations

from typing import Optional

import pandas as pd


def top_usecases_by_metric(
    df: pd.DataFrame,
    metric: str,
    n: int = 10,
    team: Optional[str] = None,
    ai_type: Optional[str] = None,
) -> pd.DataFrame:
    """
    Return top N use-cases by a metric (e.g. ROIPerAnnum or BenefitCostPerAnnum) with optional filters.
    """
    subset = df
    if team and "Team" in subset:
        subset = subset[subset["Team"].str.contains(team, case=False, na=False)]
    if ai_type and "AIType" in subset:
        subset = subset[subset["AIType"].str.contains(ai_type, case=False, na=False)]

    if metric not in subset.columns:
        return subset.head(0)

    subset = subset.dropna(subset=[metric])
    subset = subset.sort_values(metric, ascending=False)
    return subset.head(n)


def team_finops_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarise budget, cost to date, benefit and ROI per team.
    """
    if "Team" not in df:
        return df.head(0)

    grouped = (
        df.groupby("Team", dropna=False)
        .agg(
            total_budget=("EstimatedBudgetGBP", "sum"),
            total_cost_to_date=("CostToDateGBP", "sum"),
            total_benefit=("BenefitValuePerAnnum", "sum"),
            avg_roi=("ROIPerAnnum", "mean"),
        )
        .reset_index()
    )
    return grouped

