"""
Test Analytics Queries

Validates that all analytics query functions work correctly with the ChromaDB.
"""

import sys
from storage.vector_db_manager import VectorDBManager
from storage.analytics_queries import (
    get_users_per_platform,
    get_count_per_platform,
    get_budget_by_platform,
    get_benefit_by_platform,
    get_roi_by_platform,
    get_environment_distribution,
    get_cost_analysis,
    get_comprehensive_analytics
)


def main():
    print("="*60)
    print("Testing Analytics Queries")
    print("="*60)
    
    # Initialize VectorDB
    try:
        vdb = VectorDBManager()
        print("\n✅ VectorDB initialized successfully")
    except Exception as e:
        print(f"\n❌ Failed to initialize VectorDB: {e}")
        sys.exit(1)
    
    # Test total count
    print(f"\n{'='*60}")
    print("Test 1: Total Document Count")
    print(f"{'='*60}")
    try:
        total = vdb.get_total_count()
        print(f"✅ Total documents: {total}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test users per platform
    print(f"\n{'='*60}")
    print("Test 2: Users Per Platform")
    print(f"{'='*60}")
    try:
        users = get_users_per_platform(vdb)
        print("✅ Results:")
        for platform, count in users.items():
            print(f"   {platform}: {count:,} users")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test count per platform
    print(f"\n{'='*60}")
    print("Test 3: Use Case Count Per Platform")
    print(f"{'='*60}")
    try:
        counts = get_count_per_platform(vdb)
        print("✅ Results:")
        for platform, count in counts.items():
            print(f"   {platform}: {count} use cases")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test budget by platform
    print(f"\n{'='*60}")
    print("Test 4: Budget By Platform")
    print(f"{'='*60}")
    try:
        budgets = get_budget_by_platform(vdb)
        print("✅ Results:")
        for platform, budget in budgets.items():
            print(f"   {platform}: £{budget:,.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test benefit by platform
    print(f"\n{'='*60}")
    print("Test 5: Benefit By Platform")
    print(f"{'='*60}")
    try:
        benefits = get_benefit_by_platform(vdb)
        print("✅ Results:")
        for platform, benefit in benefits.items():
            print(f"   {platform}: £{benefit:,.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test ROI by platform
    print(f"\n{'='*60}")
    print("Test 6: ROI Analysis By Platform")
    print(f"{'='*60}")
    try:
        roi_data = get_roi_by_platform(vdb)
        print("✅ Results:")
        for platform, data in roi_data.items():
            print(f"\n   {platform}:")
            print(f"      Use Cases: {data['use_case_count']}")
            print(f"      Total Budget: £{data['total_budget']:,.2f}")
            print(f"      Total Benefit: £{data['total_benefit']:,.2f}")
            print(f"      Average ROI: {data['average_roi']:.2f}x")
            print(f"      Calculated ROI: {data['calculated_roi']:.2f}x")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test environment distribution
    print(f"\n{'='*60}")
    print("Test 7: Environment Distribution")
    print(f"{'='*60}")
    try:
        env_dist = get_environment_distribution(vdb)
        print("✅ Results:")
        for platform, envs in env_dist.items():
            print(f"\n   {platform}:")
            for env, count in envs.items():
                print(f"      {env}: {count} use cases")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test cost analysis
    print(f"\n{'='*60}")
    print("Test 8: Cost Analysis")
    print(f"{'='*60}")
    try:
        costs = get_cost_analysis(vdb)
        print("✅ Results:")
        for platform, data in costs.items():
            print(f"\n   {platform}:")
            print(f"      Use Cases: {data['use_case_count']}")
            print(f"      Total Users: {data['total_users']:,}")
            print(f"      Cost to Date: £{data['total_cost_to_date']:,.2f}")
            print(f"      Last Month: £{data['total_last_month_cost']:,.2f}")
            print(f"      Avg Cost/User: £{data['average_cost_per_user']:,.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test comprehensive analytics
    print(f"\n{'='*60}")
    print("Test 9: Comprehensive Analytics (All in One)")
    print(f"{'='*60}")
    try:
        analytics = get_comprehensive_analytics(vdb)
        print("✅ Successfully retrieved comprehensive analytics")
        print(f"   Total Use Cases: {analytics['total_use_cases']}")
        print(f"   Platforms Analyzed: {len(analytics['users_per_platform'])}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("All Tests Completed!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
