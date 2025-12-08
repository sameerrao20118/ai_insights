from __future__ import annotations

from typing import Optional

import pandas as pd

# Column names as they appear in the Excel / DataFrame
COL_BUDGET = "Estimated Budget (GBP)"
COL_BENEFIT = "Benefit Value per annum"
COL_COST_YEAR = "Last 1 Year Cost (GBP)"
COL_COST_TD = "Cost till date (GBP)"


def compute_benefit_cost_ratio(row: pd.Series) -> Optional[float]:
    """
    Benefit / Cost per annum = benefit / last_1_year_cost.
    """
    benefit = row.get(COL_BENEFIT)
    cost = row.get(COL_COST_YEAR)
    if pd.isna(benefit) or pd.isna(cost) or cost <= 0:
        return None
    return float(benefit) / float(cost)


def compute_roi(row: pd.Series) -> Optional[float]:
    """
    ROI per annum = (benefit - last_1_year_cost) / last_1_year_cost.
    """
    benefit = row.get(COL_BENEFIT)
    cost = row.get(COL_COST_YEAR)
    if pd.isna(benefit) or pd.isna(cost) or cost <= 0:
        return None
    return (float(benefit) - float(cost)) / float(cost)


def compute_budget_overrun(row: pd.Series) -> Optional[bool]:
    """
    Budget overrun flag: True if cost till date > estimated budget.
    """
    budget = row.get(COL_BUDGET)
    cost_td = row.get(COL_COST_TD)
    if pd.isna(budget) or pd.isna(cost_td):
        return None
    return bool(float(cost_td) > float(budget))


def add_finops_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived FinOps columns onto the tracker dataframe.

    New columns:
      - ComputedBenefitCostPerAnnum
      - ROIPerAnnum
      - BudgetOverrun
    """
    df = df.copy()
    df["ComputedBenefitCostPerAnnum"] = df.apply(compute_benefit_cost_ratio, axis=1)
    df["ROIPerAnnum"] = df.apply(compute_roi, axis=1)
    df["BudgetOverrun"] = df.apply(compute_budget_overrun, axis=1)
    return df
