"""
Analytics queries for ChromaDB.

Provides high-level analytics functions to query aggregated data from the vector database,
supporting production-ready analytics comparable to Snowflake Cortex AI.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
from storage.vector_db_manager import VectorDBManager


def get_users_per_platform(vdb: VectorDBManager) -> Dict[str, int]:
    """
    Get total number of users grouped by platform type (AIType).
    
    Returns:
        Dictionary mapping platform name to total user count
        Example: {"AI Gateway": 1500, "Aiden": 2300, ...}
    """
    all_docs = vdb.get_all_documents()
    
    platform_users = defaultdict(int)
    for doc in all_docs:
        metadata = doc.get("metadata", {})
        platform = metadata.get("AIType", "Unknown")
        users = metadata.get("NumberOfUsers", 0)
        
        # Handle None and convert to int
        if users is None:
            users = 0
        try:
            users = int(users)
        except (ValueError, TypeError):
            users = 0
            
        platform_users[platform] += users
    
    return dict(platform_users)


def get_count_per_platform(vdb: VectorDBManager) -> Dict[str, int]:
    """
    Get count of use cases per platform type.
    
    Returns:
        Dictionary mapping platform name to use case count
    """
    all_docs = vdb.get_all_documents()
    
    platform_count = defaultdict(int)
    for doc in all_docs:
        metadata = doc.get("metadata", {})
        platform = metadata.get("AIType", "Unknown")
        platform_count[platform] += 1
    
    return dict(platform_count)


def get_budget_by_platform(vdb: VectorDBManager) -> Dict[str, float]:
    """
    Get total estimated budget grouped by platform type.
    
    Returns:
        Dictionary mapping platform name to total budget in GBP
    """
    all_docs = vdb.get_all_documents()
    
    platform_budget = defaultdict(float)
    for doc in all_docs:
        metadata = doc.get("metadata", {})
        platform = metadata.get("AIType", "Unknown")
        budget = metadata.get("EstimatedBudgetGBP", 0)
        
        if budget is None:
            budget = 0
        try:
            budget = float(budget)
        except (ValueError, TypeError):
            budget = 0.0
            
        platform_budget[platform] += budget
    
    return dict(platform_budget)


def get_benefit_by_platform(vdb: VectorDBManager) -> Dict[str, float]:
    """
    Get total benefit value per annum grouped by platform type.
    
    Returns:
        Dictionary mapping platform name to total benefit value
    """
    all_docs = vdb.get_all_documents()
    
    platform_benefit = defaultdict(float)
    for doc in all_docs:
        metadata = doc.get("metadata", {})
        platform = metadata.get("AIType", "Unknown")
        benefit = metadata.get("BenefitValuePerAnnum", 0)
        
        if benefit is None:
            benefit = 0
        try:
            benefit = float(benefit)
        except (ValueError, TypeError):
            benefit = 0.0
            
        platform_benefit[platform] += benefit
    
    return dict(platform_benefit)


def get_roi_by_platform(vdb: VectorDBManager) -> Dict[str, Dict[str, Any]]:
    """
    Calculate ROI statistics by platform type.
    
    Returns:
        Dictionary with platform-level ROI analysis including:
        - average_roi: Mean ROI across use cases
        - total_benefit: Total benefit value
        - total_budget: Total estimated budget
        - calculated_roi: Total benefit / Total budget
        - use_case_count: Number of use cases
    """
    all_docs = vdb.get_all_documents()
    
    platform_data = defaultdict(lambda: {
        "total_benefit": 0.0,
        "total_budget": 0.0,
        "roi_sum": 0.0,
        "roi_count": 0,
        "use_case_count": 0
    })
    
    for doc in all_docs:
        metadata = doc.get("metadata", {})
        platform = metadata.get("AIType", "Unknown")
        
        benefit = metadata.get("BenefitValuePerAnnum", 0) or 0
        budget = metadata.get("EstimatedBudgetGBP", 0) or 0
        roi = metadata.get("ROIPerAnnum")
        
        try:
            benefit = float(benefit)
        except (ValueError, TypeError):
            benefit = 0.0
            
        try:
            budget = float(budget)
        except (ValueError, TypeError):
            budget = 0.0
        
        platform_data[platform]["total_benefit"] += benefit
        platform_data[platform]["total_budget"] += budget
        platform_data[platform]["use_case_count"] += 1
        
        if roi is not None:
            try:
                roi = float(roi)
                platform_data[platform]["roi_sum"] += roi
                platform_data[platform]["roi_count"] += 1
            except (ValueError, TypeError):
                pass
    
    # Calculate final statistics
    result = {}
    for platform, data in platform_data.items():
        avg_roi = data["roi_sum"] / data["roi_count"] if data["roi_count"] > 0 else 0.0
        calculated_roi = (data["total_benefit"] / data["total_budget"]) if data["total_budget"] > 0 else 0.0
        
        result[platform] = {
            "average_roi": round(avg_roi, 2),
            "total_benefit": round(data["total_benefit"], 2),
            "total_budget": round(data["total_budget"], 2),
            "calculated_roi": round(calculated_roi, 2),
            "use_case_count": data["use_case_count"]
        }
    
    return result


def get_environment_distribution(vdb: VectorDBManager) -> Dict[str, Dict[str, int]]:
    """
    Get distribution of use cases by environment (Production/Lower) for each platform.
    
    Returns:
        Nested dictionary: {platform: {environment: count}}
    """
    all_docs = vdb.get_all_documents()
    
    distribution = defaultdict(lambda: defaultdict(int))
    
    for doc in all_docs:
        metadata = doc.get("metadata", {})
        platform = metadata.get("AIType", "Unknown")
        environment = metadata.get("Environment", "Unknown")
        
        distribution[platform][environment] += 1
    
    return {k: dict(v) for k, v in distribution.items()}


def get_cost_analysis(vdb: VectorDBManager) -> Dict[str, Dict[str, Any]]:
    """
    Comprehensive cost analysis by platform.
    
    Returns:
        Dictionary with detailed cost metrics per platform including:
        - total_cost_to_date
        - total_last_month_cost
        - average_cost_per_user
        - use_case_count
    """
    all_docs = vdb.get_all_documents()
    
    platform_costs = defaultdict(lambda: {
        "total_cost_to_date": 0.0,
        "total_last_month": 0.0,
        "total_last_3_months": 0.0,
        "total_users": 0,
        "use_case_count": 0
    })
    
    for doc in all_docs:
        metadata = doc.get("metadata", {})
        platform = metadata.get("AIType", "Unknown")
        
        cost_to_date = metadata.get("CostToDateGBP", 0) or 0
        last_month = metadata.get("LastMonthCostGBP", 0) or 0
        last_3_months = metadata.get("LastThreeMonthsCostGBP", 0) or 0
        users = metadata.get("NumberOfUsers", 0) or 0
        
        try:
            cost_to_date = float(cost_to_date)
        except (ValueError, TypeError):
            cost_to_date = 0.0
            
        try:
            last_month = float(last_month)
        except (ValueError, TypeError):
            last_month = 0.0
            
        try:
            last_3_months = float(last_3_months)
        except (ValueError, TypeError):
            last_3_months = 0.0
            
        try:
            users = int(users)
        except (ValueError, TypeError):
            users = 0
        
        platform_costs[platform]["total_cost_to_date"] += cost_to_date
        platform_costs[platform]["total_last_month"] += last_month
        platform_costs[platform]["total_last_3_months"] += last_3_months
        platform_costs[platform]["total_users"] += users
        platform_costs[platform]["use_case_count"] += 1
    
    # Calculate averages
    result = {}
    for platform, data in platform_costs.items():
        avg_cost_per_user = (data["total_cost_to_date"] / data["total_users"]) if data["total_users"] > 0 else 0.0
        
        result[platform] = {
            "total_cost_to_date": round(data["total_cost_to_date"], 2),
            "total_last_month_cost": round(data["total_last_month"], 2),
            "total_last_3_months_cost": round(data["total_last_3_months"], 2),
            "average_cost_per_user": round(avg_cost_per_user, 2),
            "total_users": data["total_users"],
            "use_case_count": data["use_case_count"]
        }
    
    return result


def get_comprehensive_analytics(vdb: VectorDBManager) -> Dict[str, Any]:
    """
    Get all analytics in one call for efficiency.
    
    Returns:
        Comprehensive analytics dictionary with all metrics
    """
    return {
        "total_use_cases": vdb.get_total_count(),
        "users_per_platform": get_users_per_platform(vdb),
        "use_cases_per_platform": get_count_per_platform(vdb),
        "budget_by_platform": get_budget_by_platform(vdb),
        "benefit_by_platform": get_benefit_by_platform(vdb),
        "roi_by_platform": get_roi_by_platform(vdb),
        "environment_distribution": get_environment_distribution(vdb),
        "cost_analysis": get_cost_analysis(vdb)
    }
