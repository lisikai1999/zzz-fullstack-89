from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List
from app.database import get_db
from app.models.scan import ScanResult, AccessibilityIssue
from app.schemas import ScanRequest, ScanResponse, IssueResponse, ScanSummary, ScanHistoryItem
from app.services.scanner import fetch_page, extract_inline_styles
from app.services.scoring import calculate_score, prioritize_issues, get_issue_summary
from app.checkers.rules import AccessibilityChecker

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def scan_url(request: ScanRequest, db: AsyncSession = Depends(get_db)):
    """Run WCAG accessibility scan on a URL."""
    url = request.url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        html, page_title = await fetch_page(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    styles = extract_inline_styles(html)
    checker = AccessibilityChecker(html, url, styles)
    issues = checker.run_all_checks()
    issues = prioritize_issues(issues)

    score = calculate_score(issues)
    summary = get_issue_summary(issues)

    level_a = sum(1 for i in issues if i.wcag_level == "A")
    level_aa = sum(1 for i in issues if i.wcag_level == "AA")

    # Save to database
    scan_result = ScanResult(
        url=url,
        total_issues=len(issues),
        score=score,
        level_a_issues=level_a,
        level_aa_issues=level_aa,
        page_title=page_title,
        html_snapshot=html[:100000],
    )
    db.add(scan_result)
    await db.flush()

    db_issues = []
    for issue in issues:
        db_issue = AccessibilityIssue(
            scan_id=scan_result.id,
            rule_id=issue.rule_id,
            rule_name=issue.rule_name,
            severity=issue.severity,
            wcag_level=issue.wcag_level,
            wcag_criterion=issue.wcag_criterion,
            element_selector=issue.element_selector,
            element_html=issue.element_html[:500],
            element_tag=issue.element_tag,
            page_region=issue.page_region,
            description=issue.description,
            impact_group=issue.impact_group,
            fix_suggestion=issue.fix_suggestion,
            fix_code=issue.fix_code,
            contrast_actual=issue.contrast_actual,
            contrast_required=issue.contrast_required,
            suggested_color=issue.suggested_color,
        )
        db.add(db_issue)
        db_issues.append(db_issue)

    await db.commit()
    await db.refresh(scan_result)

    issue_responses = [
        IssueResponse(
            id=idx,
            rule_id=i.rule_id,
            rule_name=i.rule_name,
            severity=i.severity,
            wcag_level=i.wcag_level,
            wcag_criterion=i.wcag_criterion,
            element_selector=i.element_selector,
            element_html=i.element_html,
            element_tag=i.element_tag,
            page_region=i.page_region,
            description=i.description,
            impact_group=i.impact_group,
            fix_suggestion=i.fix_suggestion,
            fix_code=i.fix_code,
            contrast_actual=i.contrast_actual,
            contrast_required=i.contrast_required,
            suggested_color=i.suggested_color,
        )
        for idx, i in enumerate(issues)
    ]

    return ScanResponse(
        id=scan_result.id,
        url=url,
        scan_time=str(scan_result.scan_time),
        page_title=page_title,
        score=score,
        total_issues=len(issues),
        level_a_issues=level_a,
        level_aa_issues=level_aa,
        issues=issue_responses,
        summary=ScanSummary(**summary),
    )


@router.get("/scan/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: int, db: AsyncSession = Depends(get_db)):
    """Get a previous scan result by ID."""
    result = await db.execute(select(ScanResult).where(ScanResult.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    issues_result = await db.execute(
        select(AccessibilityIssue)
        .where(AccessibilityIssue.scan_id == scan_id)
        .order_by(AccessibilityIssue.id)
    )
    issues = issues_result.scalars().all()

    issue_responses = [
        IssueResponse(
            id=i.id,
            rule_id=i.rule_id,
            rule_name=i.rule_name,
            severity=i.severity,
            wcag_level=i.wcag_level,
            wcag_criterion=i.wcag_criterion,
            element_selector=i.element_selector,
            element_html=i.element_html,
            element_tag=i.element_tag,
            page_region=i.page_region,
            description=i.description,
            impact_group=i.impact_group,
            fix_suggestion=i.fix_suggestion,
            fix_code=i.fix_code or "",
            contrast_actual=i.contrast_actual,
            contrast_required=i.contrast_required,
            suggested_color=i.suggested_color,
        )
        for i in issues
    ]

    summary_data = {
        "total": len(issues),
        "by_severity": {},
        "by_level": {"A": scan.level_a_issues, "AA": scan.level_aa_issues},
        "by_impact_group": {},
        "by_rule": {},
        "by_region": {},
    }
    for i in issues:
        summary_data["by_severity"][i.severity] = summary_data["by_severity"].get(i.severity, 0) + 1
        for g in i.impact_group.split(","):
            g = g.strip()
            summary_data["by_impact_group"][g] = summary_data["by_impact_group"].get(g, 0) + 1
        summary_data["by_rule"][i.rule_id] = summary_data["by_rule"].get(i.rule_id, 0) + 1
        summary_data["by_region"][i.page_region] = summary_data["by_region"].get(i.page_region, 0) + 1

    return ScanResponse(
        id=scan.id,
        url=scan.url,
        scan_time=str(scan.scan_time),
        page_title=scan.page_title or "",
        score=scan.score,
        total_issues=scan.total_issues,
        level_a_issues=scan.level_a_issues,
        level_aa_issues=scan.level_aa_issues,
        issues=issue_responses,
        summary=ScanSummary(**summary_data),
    )


@router.get("/scans", response_model=List[ScanHistoryItem])
async def list_scans(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List scan history."""
    result = await db.execute(
        select(ScanResult)
        .order_by(desc(ScanResult.scan_time))
        .limit(limit)
        .offset(offset)
    )
    scans = result.scalars().all()
    return [
        ScanHistoryItem(
            id=s.id,
            url=s.url,
            scan_time=str(s.scan_time),
            score=s.score,
            total_issues=s.total_issues,
            page_title=s.page_title,
        )
        for s in scans
    ]


@router.get("/scan/{scan_id}/html")
async def get_scan_html(scan_id: int, db: AsyncSession = Depends(get_db)):
    """Get the HTML snapshot for a scan (for preview rendering)."""
    result = await db.execute(select(ScanResult).where(ScanResult.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"html": scan.html_snapshot}
