"""
Helper functions for leader question answering.

Provides direct answers for common data queries and formats analytics data
for LLM consumption.
"""

import re
from typing import Dict, Any, Optional


def classify_question_intent(question: str) -> Optional[str]:
    """
    Classify question into predefined categories for direct answers.
    
    Returns category name if matched, None otherwise.
    Only handles common, unambiguous data queries.
    """
    q_lower = question.lower()
    
    # Pattern 1: User count queries
    if re.search(r'how many.*users.*(platform|each)', q_lower):
        return 'users_per_platform'
    
    # Pattern 2: Total count queries
    if re.search(r'(how many|total).*(rows?|records?|use.?cases?|entries)', q_lower):
        return 'total_count'
    
    # Pattern 3: Best ROI query
    if re.search(r'(which|what).*(platform|solution).*(best|highest|top).*roi', q_lower):
        return 'best_roi'
    
    # Pattern 4: Cost comparison
    if re.search(r'(compare|comparison).*(cost|spend|budget)', q_lower):
        return 'cost_comparison'
    
    # Pattern 5: Platform distribution
    if re.search(r'(classify|categorize|breakdown|distribute).*(platform|type)', q_lower):
        return 'platform_distribution'
    
    # Pattern 6: Strongest/best performing investment
    if re.search(r'(which|what).*(ai|platform|investment|solution).*(strongest|best|top|highest|delivering|performing).*(result|value|performance|return)', q_lower):
        return 'strongest_investment'
    if re.search(r'(strongest|best|top|highest).*(ai|platform|investment|solution)', q_lower):
        return 'strongest_investment'
    
    # No match - send to LLM
    return None


def format_users_per_platform(analytics: Dict[str, Any]) -> str:
    """Format user distribution by platform."""
    users_data = analytics.get('users_per_platform', {})
    use_cases_data = analytics.get('use_cases_per_platform', {})
    total_users = sum(users_data.values())
    
    lines = ["**Platform User Distribution:**\n"]
    
    # Sort by user count descending
    sorted_platforms = sorted(users_data.items(), key=lambda x: x[1], reverse=True)
    
    for platform, user_count in sorted_platforms:
        use_case_count = use_cases_data.get(platform, 0)
        percentage = (user_count / total_users * 100) if total_users > 0 else 0
        lines.append(f"• **{platform}**: {user_count:,} users across {use_case_count} use cases ({percentage:.1f}%)")
    
    lines.append(f"\n**Total**: {total_users:,} users across all platforms")
    
    return "\n".join(lines)


def format_total_count(analytics: Dict[str, Any]) -> str:
    """Format total count response."""
    total = analytics.get('total_use_cases', 0)
    users_data = analytics.get('users_per_platform', {})
    total_users = sum(users_data.values())
    platforms = len(users_data)
    
    return (
        f"**Database Summary:**\n\n"
        f"• **Total Use Cases**: {total:,}\n"
        f"• **Total Users**: {total_users:,}\n"
        f"• **Platforms**: {platforms}\n\n"
        f"Use any follow-up questions to drill into specific platforms or metrics."
    )


def format_best_roi(analytics: Dict[str, Any]) -> str:
    """Format best ROI platform response."""
    roi_data = analytics.get('roi_by_platform', {})
    
    if not roi_data:
        return "ROI data not available in the current analytics."
    
    # Find platform with highest calculated ROI
    best_platform = max(roi_data.items(), key=lambda x: x[1].get('calculated_roi', 0))
    platform_name, platform_roi = best_platform
    
    roi_value = platform_roi.get('calculated_roi', 0)
    total_benefit = platform_roi.get('total_benefit', 0)
    total_budget = platform_roi.get('total_budget', 0)
    use_case_count = platform_roi.get('use_case_count', 0)
    
    lines = [
        f"**Best ROI Platform: {platform_name}**\n",
        f"• **ROI**: {roi_value:.2f}x",
        f"• **Total Benefit**: £{total_benefit:,.2f}",
        f"• **Total Budget**: £{total_budget:,.2f}",
        f"• **Use Cases**: {use_case_count}",
        f"\nThis means for every £1 invested in {platform_name}, we're seeing £{roi_value:.2f} in returns."
    ]
    
    return "\n".join(lines)


def format_cost_comparison(analytics: Dict[str, Any]) -> str:
    """Format cost comparison across platforms."""
    cost_data = analytics.get('cost_analysis', {})
    
    if not cost_data:
        return "Cost analysis data not available."
    
    lines = ["**Platform Cost Comparison:**\n"]
    
    # Sort by total cost descending
    sorted_platforms = sorted(
        cost_data.items(),
        key=lambda x: x[1].get('total_cost_to_date', 0),
        reverse=True
    )
    
    for platform, data in sorted_platforms:
        total_cost = data.get('total_cost_to_date', 0)
        avg_cost_per_user = data.get('average_cost_per_user', 0)
        total_users = data.get('total_users', 0)
        
        lines.append(
            f"• **{platform}**: £{total_cost:,.2f} total (£{avg_cost_per_user:.2f}/user, {total_users:,} users)"
        )
    
    return "\n".join(lines)


def format_platform_distribution(analytics: Dict[str, Any]) -> str:
    """Format platform distribution with all key metrics."""
    use_cases_data = analytics.get('use_cases_per_platform', {})
    users_data = analytics.get('users_per_platform', {})
    budget_data = analytics.get('budget_by_platform', {})
    
    total_cases = analytics.get('total_use_cases', 0)
    
    lines = [f"**Platform Distribution** (Total: {total_cases} use cases)\n"]
    
    for platform in use_cases_data.keys():
        cases = use_cases_data.get(platform, 0)
        users = users_data.get(platform, 0)
        budget = budget_data.get(platform, 0)
        
        lines.append(
            f"• **{platform}**: {cases} use cases, {users:,} users, £{budget:,.0f} budget"
        )
    
    return "\n".join(lines)


def format_strongest_investment(analytics: Dict[str, Any]) -> str:
    """
    Identify and format the strongest performing AI investment.
    
    Analyzes ROI, benefit, and cost data to determine which platform
    is delivering the strongest results.
    """
    roi_data = analytics.get('roi_by_platform', {})
    benefit_data = analytics.get('benefit_by_platform', {})
    
    if not roi_data and not benefit_data:
        return "Performance data not available in the current analytics."
    
    # Strategy: Find platform with highest calculated ROI
    # (total_benefit / total_budget ratio)
    best_platform = None
    best_roi = 0
    
    if roi_data:
        for platform_name, platform_roi in roi_data.items():
            calculated_roi = platform_roi.get('calculated_roi', 0)
            if calculated_roi > best_roi:
                best_roi = calculated_roi
                best_platform = platform_name
    
    # Fallback: if no ROI data, use highest benefit
    if not best_platform and benefit_data:
        best_platform = max(benefit_data.items(), key=lambda x: x[1])[0]
        best_roi = roi_data.get(best_platform, {}).get('calculated_roi', 0) if roi_data else 0
    
    if not best_platform:
        return "Unable to determine strongest investment from available data."
    
    # Get detailed metrics for the best platform
    platform_metrics = roi_data.get(best_platform, {}) if roi_data else {}
    roi_value = platform_metrics.get('calculated_roi', 0)
    total_benefit = platform_metrics.get('total_benefit', 0)
    total_budget = platform_metrics.get('total_budget', 0)
    use_case_count = platform_metrics.get('use_case_count', 0)
    
    # Get user count if available
    users_data = analytics.get('users_per_platform', {})
    total_users = users_data.get(best_platform, 0)
    
    lines = [
        f"**{best_platform}** is delivering the strongest results.\n"
    ]
    
    # Add key metrics
    metrics = []
    if roi_value > 0:
        metrics.append(f"• **ROI**: {roi_value:.2f}x return on investment")
    if total_benefit > 0:
        metrics.append(f"• **Annual Benefit**: £{total_benefit:,.2f}")
    if total_budget > 0:
        metrics.append(f"• **Total Budget**: £{total_budget:,.2f}")
    if use_case_count > 0:
        metrics.append(f"• **Use Cases**: {use_case_count}")
    if total_users > 0:
        metrics.append(f"• **Users**: {total_users:,}")
    
    lines.extend(metrics)
    
    # Add interpretation
    if roi_value > 0:
        lines.append(
            f"\nThis means for every £1 invested in {best_platform}, "
            f"we're generating £{roi_value:.2f} in annual benefits."
        )
    
    return "\n".join(lines)


def get_direct_answer(question: str, analytics: Dict[str, Any]) -> Optional[str]:
    """
    Get direct answer for common questions using structured data.
    
    Returns formatted answer string if question matches pattern, None otherwise.
    """
    intent = classify_question_intent(question)
    
    if not intent:
        return None
    
    # Map intents to formatters
    formatters = {
        'users_per_platform': format_users_per_platform,
        'total_count': format_total_count,
        'best_roi': format_best_roi,
        'cost_comparison': format_cost_comparison,
        'platform_distribution': format_platform_distribution,
        'strongest_investment': format_strongest_investment,
    }
    
    formatter = formatters.get(intent)
    if formatter:
        return formatter(analytics)
    
    return None


def format_analytics_for_llm(analytics: Dict[str, Any]) -> str:
    """
    Format analytics data in a clear, structured way for LLM consumption.
    
    This makes it EASY for the LLM to extract any data it needs without
    having to parse complex JSON structures.
    """
    if not analytics:
        return "No analytics data available."
    
    # Build a human-readable analytics summary
    summary_parts = []
    
    # 1. Overall totals
    total_cases = analytics.get('total_use_cases', 0)
    users_per_platform = analytics.get('users_per_platform', {})
    total_users = sum(users_per_platform.values())
    
    summary_parts.append(f"=== OVERALL TOTALS ===")
    summary_parts.append(f"Total Use Cases: {total_cases}")
    summary_parts.append(f"Total Users: {total_users:,}")
    summary_parts.append(f"Number of Platforms: {len(users_per_platform)}")
    summary_parts.append("")
    
    # 2. Per-platform breakdown
    summary_parts.append("=== PLATFORM BREAKDOWN ===")
    
    use_cases_per_platform = analytics.get('use_cases_per_platform', {})
    budget_by_platform = analytics.get('budget_by_platform', {})
    benefit_by_platform = analytics.get('benefit_by_platform', {})
    roi_by_platform = analytics.get('roi_by_platform', {})
    cost_analysis = analytics.get('cost_analysis', {})
    
    for platform in sorted(users_per_platform.keys()):
        summary_parts.append(f"\n{platform}:")
        summary_parts.append(f"  - Use Cases: {use_cases_per_platform.get(platform, 0)}")
        summary_parts.append(f"  - Users: {users_per_platform.get(platform, 0):,}")
        summary_parts.append(f"  - Budget: £{budget_by_platform.get(platform, 0):,.2f}")
        summary_parts.append(f"  - Benefit: £{benefit_by_platform.get(platform, 0):,.2f}")
        
        if platform in roi_by_platform:
            roi_info = roi_by_platform[platform]
            summary_parts.append(f"  - ROI: {roi_info.get('calculated_roi', 0):.2f}x")
        
        if platform in cost_analysis:
            cost_info = cost_analysis[platform]
            summary_parts.append(f"  - Cost per User: £{cost_info.get('average_cost_per_user', 0):.2f}")
    
    return "\n".join(summary_parts)
