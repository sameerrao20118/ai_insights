from typing import Optional
from pydantic import BaseModel, ConfigDict


class AIUseCase(BaseModel):
    UseCaseName: str
    UseCaseID: str
    FunctionID: Optional[str] = None
    Environment: Optional[str] = None  # Production / Lower Environment
    Team: str
    KeyContact: str
    ProjectDescription: str
    EstimatedBudgetGBP: Optional[float] = None
    BenefitValuePerAnnum: Optional[float] = None
    AIType: Optional[str] = None  # AI Gateway / Aiden / Copilot / Duo / 3rd Party
    NumberOfUsers: Optional[int] = None
    UsageStartDate: Optional[str] = None
    CostToDateGBP: Optional[float] = None
    LastMonthCostGBP: Optional[float] = None
    LastThreeMonthsCostGBP: Optional[float] = None
    LastYearCostGBP: Optional[float] = None
    BenefitCostPerAnnum: Optional[float] = None
    ROIPerAnnum: Optional[float] = None
    BudgetOverrun: Optional[bool] = None

    model_config = ConfigDict(extra="ignore")
