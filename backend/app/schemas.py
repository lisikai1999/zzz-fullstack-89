from pydantic import BaseModel, HttpUrl
from typing import Optional, List


class ScanRequest(BaseModel):
    url: str


class IssueResponse(BaseModel):
    id: Optional[int] = None
    rule_id: str
    rule_name: str
    severity: str
    wcag_level: str
    wcag_criterion: str
    element_selector: str
    element_html: str
    element_tag: str
    page_region: str
    description: str
    impact_group: str
    fix_suggestion: str
    fix_code: str = ""
    contrast_actual: Optional[float] = None
    contrast_required: Optional[float] = None
    suggested_color: Optional[str] = None


class ScanSummary(BaseModel):
    total: int
    by_severity: dict
    by_level: dict
    by_impact_group: dict
    by_rule: dict
    by_region: dict


class ScanResponse(BaseModel):
    id: int
    url: str
    scan_time: str
    page_title: str
    score: float
    total_issues: int
    level_a_issues: int
    level_aa_issues: int
    issues: List[IssueResponse]
    summary: ScanSummary


class ScanHistoryItem(BaseModel):
    id: int
    url: str
    scan_time: str
    score: float
    total_issues: int
    page_title: Optional[str] = None
