"""
Test Data Generator for AI Insights Platform

Generates realistic test data to validate production-ready analytics and LLM queries.
Supports generating 1000+ users per platform type for comprehensive testing.
"""

import argparse
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from models import AIUseCase
from storage.vector_db_manager import VectorDBManager


# Platform types
PLATFORMS = ["AI Gateway", "Aiden", "Co-pilot", "Duo", "3rd Party"]

# Environment types
ENVIRONMENTS = ["Production", "Lower", "Both"]

# Sample teams
TEAMS = [
    "Retail Banking", "Commercial Banking", "Investment Banking", 
    "Technology", "Risk Management", "Operations", 
    "Customer Service", "Marketing", "Finance", "HR"
]

# Sample use case templates
USE_CASE_TEMPLATES = [
    {"name": "Code Completion", "desc": "AI-powered code completion for developers"},
    {"name": "Customer Service Bot", "desc": "Automated customer query handling"},
    {"name": "Document Processing", "desc": "Automated document analysis and extraction"},
    {"name": "Risk Analysis", "desc": "AI-driven risk assessment and prediction"},
    {"name": "Fraud Detection", "desc": "Real-time fraud detection system"},
    {"name": "Credit Scoring", "desc": "AI-enhanced credit scoring model"},
    {"name": "Chatbot Assistant", "desc": "Conversational AI for internal tools"},
    {"name": "Data Analytics", "desc": "Automated insights from business data"},
    {"name": "Email Classification", "desc": "Intelligent email routing and categorization"},
    {"name": "Report Generation", "desc": "Automated report creation and summarization"}
]


def generate_use_case(
    platform: str,
    team: str,
    case_num: int,
    use_case_template: Dict[str, str]
) -> AIUseCase:
    """Generate a single realistic use case."""
    
    # Generate realistic metrics
    num_users = random.randint(10, 5000)
    environment = random.choice(ENVIRONMENTS)
    
    # Budget varies by platform and user count
    base_budget = num_users * random.uniform(50, 500)
    budget = round(base_budget + random.uniform(-base_budget * 0.3, base_budget * 0.5), 2)
    
    # Benefit should be somewhat correlated with budget and users
    benefit_multiplier = random.uniform(0.8, 2.5)  # ROI between 0.8 and 2.5
    benefit = round(budget * benefit_multiplier, 2)
    
    # Costs
    months_running = random.randint(1, 24)
    cost_to_date = round(budget * (months_running / 12) * random.uniform(0.7, 1.3), 2)
    last_month_cost = round(budget / 12 * random.uniform(0.8, 1.2), 2)
    last_3_months_cost = round(last_month_cost * 3 * random.uniform(0.9, 1.1), 2)
    last_year_cost = min(cost_to_date, round(budget * random.uniform(0.9, 1.1), 2))
    
    # Calculate derived metrics
    benefit_cost = benefit - budget if budget > 0 else 0
    roi = round((benefit / budget) if budget > 0 else 0, 2)
    budget_overrun = cost_to_date > budget
    
    # Start date
    start_date = (datetime.now() - timedelta(days=months_running * 30)).strftime("%Y-%m-%d")
    
    use_case_id = f"TEST-{platform.replace(' ', '')[:4].upper()}-{team.replace(' ', '')[:3].upper()}-{case_num:04d}"
    use_case_name = f"{use_case_template['name']} - {team}"
    
    return AIUseCase(
        UseCaseName=use_case_name,
        UseCaseID=use_case_id,
        FunctionID=f"FN-{team.replace(' ', '')[:3].upper()}",
        Environment=environment,
        Team=team,
        KeyContact=f"contact.{team.lower().replace(' ', '.')}@natwest.com",
        ProjectDescription=use_case_template['desc'],
        EstimatedBudgetGBP=budget,
        BenefitValuePerAnnum=benefit,
        AIType=platform,
        NumberOfUsers=num_users,
        UsageStartDate=start_date,
        CostToDateGBP=cost_to_date,
        LastMonthCostGBP=last_month_cost,
        LastThreeMonthsCostGBP=last_3_months_cost,
        LastYearCostGBP=last_year_cost,
        BenefitCostPerAnnum=benefit_cost,
        ROIPerAnnum=roi,
        BudgetOverrun=budget_overrun
    )


def generate_test_data(
    users_per_platform: int = 1000,
    use_cases_per_platform: int = 50,
    platforms: List[str] = None
) -> List[AIUseCase]:
    """
    Generate comprehensive test data.
    
    Args:
        users_per_platform: Target number of users per platform (will be distributed across use cases)
        use_cases_per_platform: Number of use cases to generate per platform
        platforms: List of platforms to generate data for (default: all platforms)
    
    Returns:
        List of generated AIUseCase objects
    """
    if platforms is None:
        platforms = PLATFORMS
    
    all_use_cases = []
    
    for platform in platforms:
        print(f"Generating {use_cases_per_platform} use cases for {platform}...")
        
        platform_users = 0
        for i in range(use_cases_per_platform):
            team = random.choice(TEAMS)
            template = random.choice(USE_CASE_TEMPLATES)
            
            use_case = generate_use_case(platform, team, i + 1, template)
            platform_users += use_case.NumberOfUsers or 0
            all_use_cases.append(use_case)
        
        print(f"  Generated {platform_users:,} total users for {platform}")
    
    return all_use_cases


def ingest_test_data(use_cases: List[AIUseCase], vdb: VectorDBManager = None) -> int:
    """
    Ingest generated test data into ChromaDB.
    
    Args:
        use_cases: List of use cases to ingest
        vdb: VectorDBManager instance (creates new if None)
    
    Returns:
        Number of documents ingested
    """
    if vdb is None:
        vdb = VectorDBManager()
    
    docs = []
    for uc in use_cases:
        meta = uc.model_dump()
        docs.append({
            "id": meta["UseCaseID"],
            "content": f"{meta['UseCaseName']} - {meta['ProjectDescription']} - Platform: {meta['AIType']} - Team: {meta['Team']}",
            "metadata": meta
        })
    
    vdb.add_documents(docs)
    return len(docs)


def main():
    parser = argparse.ArgumentParser(description="Generate test data for AI Insights platform")
    parser.add_argument(
        "--users-per-platform",
        type=int,
        default=1000,
        help="Target number of users per platform (default: 1000)"
    )
    parser.add_argument(
        "--use-cases-per-platform",
        type=int,
        default=50,
        help="Number of use cases per platform (default: 50)"
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=PLATFORMS,
        default=PLATFORMS,
        help="Platforms to generate data for"
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Ingest generated data into ChromaDB"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save generated data to JSON file"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("AI Insights Test Data Generator")
    print(f"{'='*60}\n")
    
    # Generate data
    use_cases = generate_test_data(
        users_per_platform=args.users_per_platform,
        use_cases_per_platform=args.use_cases_per_platform,
        platforms=args.platforms
    )
    
    total_users = sum(uc.NumberOfUsers or 0 for uc in use_cases)
    total_budget = sum(uc.EstimatedBudgetGBP or 0 for uc in use_cases)
    total_benefit = sum(uc.BenefitValuePerAnnum or 0 for uc in use_cases)
    
    print(f"\n{'='*60}")
    print("Generation Summary:")
    print(f"{'='*60}")
    print(f"Total Use Cases: {len(use_cases)}")
    print(f"Total Users: {total_users:,}")
    print(f"Total Budget: £{total_budget:,.2f}")
    print(f"Total Benefit: £{total_benefit:,.2f}")
    print(f"Overall ROI: {(total_benefit / total_budget):.2f}x" if total_budget > 0 else "N/A")
    
    # Platform breakdown
    print(f"\nPlatform Breakdown:")
    for platform in args.platforms:
        platform_cases = [uc for uc in use_cases if uc.AIType == platform]
        platform_users = sum(uc.NumberOfUsers or 0 for uc in platform_cases)
        print(f"  {platform}: {len(platform_cases)} use cases, {platform_users:,} users")
    
    # Save to file if requested
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump([uc.model_dump() for uc in use_cases], f, indent=2, default=str)
        print(f"\nData saved to: {args.output}")
    
    # Ingest if requested
    if args.ingest:
        print(f"\nIngesting data into ChromaDB...")
        count = ingest_test_data(use_cases)
        print(f"✅ Ingested {count} documents successfully!")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
