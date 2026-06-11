"""
Scoring service - calculates compliance score based on issues found.
"""
from typing import List
from app.checkers.rules import Issue


SEVERITY_WEIGHTS = {
    "critical": 10,
    "serious": 7,
    "moderate": 4,
    "minor": 1,
}

PRIORITY_ORDER = {
    "critical": 0,
    "serious": 1,
    "moderate": 2,
    "minor": 3,
}

IMPACT_GROUP_LABELS = {
    "blind": "视障用户 (Screen reader users)",
    "low_vision": "低视力用户 (Low vision users)",
    "color_blind": "色盲/色弱用户 (Color blind users)",
    "motor": "键盘/运动障碍用户 (Keyboard/motor impaired users)",
    "cognitive": "认知障碍用户 (Cognitive impaired users)",
}


def calculate_score(issues: List[Issue], total_elements: int = 100) -> float:
    """
    Calculate compliance score (0-100).
    Deducts points based on severity and number of issues.
    """
    if not issues:
        return 100.0

    total_deduction = 0
    for issue in issues:
        weight = SEVERITY_WEIGHTS.get(issue.severity, 1)
        total_deduction += weight

    max_possible_deduction = total_elements * SEVERITY_WEIGHTS["critical"]
    score = max(0, 100 - (total_deduction / max(max_possible_deduction, 1)) * 100)

    # Apply floor based on critical issues count
    critical_count = sum(1 for i in issues if i.severity == "critical")
    if critical_count > 5:
        score = min(score, 30.0)
    elif critical_count > 0:
        score = min(score, 60.0)

    return round(score, 1)


def prioritize_issues(issues: List[Issue]) -> List[Issue]:
    """Sort issues by priority: severity first, then impact group breadth."""
    def sort_key(issue: Issue):
        severity_order = PRIORITY_ORDER.get(issue.severity, 3)
        # Broader impact (affecting more groups) gets higher priority
        group_count = len(issue.impact_group.split(","))
        return (severity_order, -group_count, issue.wcag_level == "AA")

    return sorted(issues, key=sort_key)


def get_issue_summary(issues: List[Issue]) -> dict:
    """Generate summary statistics for issues."""
    summary = {
        "total": len(issues),
        "by_severity": {"critical": 0, "serious": 0, "moderate": 0, "minor": 0},
        "by_level": {"A": 0, "AA": 0},
        "by_impact_group": {},
        "by_rule": {},
        "by_region": {},
    }

    for issue in issues:
        summary["by_severity"][issue.severity] = summary["by_severity"].get(issue.severity, 0) + 1
        summary["by_level"][issue.wcag_level] = summary["by_level"].get(issue.wcag_level, 0) + 1

        for group in issue.impact_group.split(","):
            group = group.strip()
            summary["by_impact_group"][group] = summary["by_impact_group"].get(group, 0) + 1

        summary["by_rule"][issue.rule_id] = summary["by_rule"].get(issue.rule_id, 0) + 1
        summary["by_region"][issue.page_region] = summary["by_region"].get(issue.page_region, 0) + 1

    return summary
