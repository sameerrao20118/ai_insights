"""
Excel data source implementation.
"""
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

from .base import DataSource
from models import AIUseCase
from finops.finops_metrics import add_finops_metrics


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


class ExcelSource(DataSource):
    """Excel file data source implementation."""

    def __init__(self, file_path: Path = EXCEL_PATH):
        self.file_path = file_path

    def load_all_usecases(self) -> List[AIUseCase]:
        """Load all use cases from Excel file."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Expected Excel file at {self.file_path} was not found.")

        df = pd.read_excel(self.file_path)
        # Keep only known columns before computing derived metrics
        df = df[list(COLUMN_MAPPING.keys())].copy()
        df = add_finops_metrics(df)
        
        usecases: List[AIUseCase] = []
        for _, row in df.iterrows():
            if pd.isna(row.get("Use-Case Name", "")):
                continue
            uc = _row_to_usecase(row)
            usecases.append(uc)

        return usecases

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the Excel file."""
        if not self.file_path.exists():
            return {
                "source_type": "excel",
                "file_exists": False,
                "file_path": str(self.file_path),
            }

        df = pd.read_excel(self.file_path)
        return {
            "source_type": "excel",
            "file_exists": True,
            "file_path": str(self.file_path),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
        }

    def validate_connection(self) -> bool:
        """Validate that the Excel file exists and is readable."""
        try:
            if not self.file_path.exists():
                return False
            # Try to read it
            pd.read_excel(self.file_path, nrows=1)
            return True
        except Exception:
            return False

    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the Excel source for display."""
        metadata = self.get_metadata()
        return {
            "type": "Excel File",
            "location": str(self.file_path),
            "status": "Connected" if metadata.get("file_exists") else "Not Found",
            "records": metadata.get("row_count", 0),
        }
