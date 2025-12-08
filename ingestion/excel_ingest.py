from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd

from finops.finops_metrics import add_finops_metrics
from models import AIUseCase
from storage.vector_db_manager import VectorDBManager

EXCEL_PATH = Path("data/BankWide AI Project Tracker.xlsx")


COLUMN_MAPPING = {
    "Use-Case Name": "UseCaseName",
    "Use-Case ID": "UseCaseID",
    "Function ID": "FunctionID",
    "Production/Lower Environment": "Environment",
    "Team": "Team",
    "Use Case Project Manager / Key Contact": "KeyContact",
    "Project Description": "ProjectDescription",
    "Estimated Budget (GBP)": "EstimatedBudgetGBP",
    "Benefit Value per annum": "BenefitValuePerAnnum",
    "AI Type (AI Gateway / Aiden / CO-pilot / Duo / 3rd Party)": "AIType",
    "Number of Users": "NumberOfUsers",
    "Usage Start Date": "UsageStartDate",
    "Cost till date (GBP)": "CostToDateGBP",
    "Last Month Cost (GBP)": "LastMonthCostGBP",
    "Last 3 Months Cost (GBP)": "LastThreeMonthsCostGBP",
    "Last 1 Year Cost (GBP)": "LastYearCostGBP",
}


_STRING_FIELDS = {
    "UseCaseName",
    "UseCaseID",
    "FunctionID",
    "Environment",
    "Team",
    "KeyContact",
    "ProjectDescription",
    "AIType",
    "UsageStartDate",
}


def _normalize_string(value) -> str | None:
    """Convert Excel values to clean strings, turning NaN into None."""
    if pd.isna(value):
        return None
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _row_to_usecase(row: pd.Series) -> AIUseCase:
    data = {}
    for orig, new in COLUMN_MAPPING.items():
        if orig not in row:
            continue
        value = row[orig]
        if new in _STRING_FIELDS:
            data[new] = _normalize_string(value)
        elif new == "NumberOfUsers":
            if pd.isna(value):
                data[new] = None
            else:
                try:
                    data[new] = int(value)
                except (TypeError, ValueError):
                    data[new] = None
        else:
            data[new] = value if not pd.isna(value) else None
    # Derived metrics computed in code (not trusted from Excel)
    if "ComputedBenefitCostPerAnnum" in row:
        data["BenefitCostPerAnnum"] = row["ComputedBenefitCostPerAnnum"]
    if "ROIPerAnnum" in row:
        data["ROIPerAnnum"] = row["ROIPerAnnum"]
    if "BudgetOverrun" in row:
        data["BudgetOverrun"] = bool(row["BudgetOverrun"])
    return AIUseCase(**data)


def ingest_excel(vdb: Optional[VectorDBManager] = None) -> List[AIUseCase]:
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Expected Excel file at {EXCEL_PATH} was not found.")

    df = pd.read_excel(EXCEL_PATH)
    # Keep only known columns before computing derived metrics
    df = df[list(COLUMN_MAPPING.keys())].copy()
    df = add_finops_metrics(df)
    usecases: List[AIUseCase] = []
    for _, row in df.iterrows():
        if pd.isna(row.get("Use Case Name", "")):
            continue
        uc = _row_to_usecase(row)
        usecases.append(uc)

    if vdb is None:
        vdb = VectorDBManager()
    docs = []
    for uc in usecases:
        meta = uc.model_dump()
        docs.append(
            {
                "id": meta["UseCaseID"],
                "title": meta["UseCaseName"],
                "content": f"{meta['UseCaseName']} - {meta['ProjectDescription']}",
                "metadata": meta,
            }
        )
    vdb.add_documents(docs)
    return usecases


if __name__ == "__main__":
    ingest_excel()
    print("Ingestion complete.")
