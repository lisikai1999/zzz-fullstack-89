from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False)
    scan_time = Column(DateTime, server_default=func.now())
    total_issues = Column(Integer, default=0)
    score = Column(Float, default=100.0)
    level_a_issues = Column(Integer, default=0)
    level_aa_issues = Column(Integer, default=0)
    page_title = Column(String(512))
    html_snapshot = Column(Text)


class AccessibilityIssue(Base):
    __tablename__ = "accessibility_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, nullable=False, index=True)
    rule_id = Column(String(64), nullable=False)
    rule_name = Column(String(256), nullable=False)
    severity = Column(String(16), nullable=False)  # critical, serious, moderate, minor
    wcag_level = Column(String(4), nullable=False)  # A, AA
    wcag_criterion = Column(String(16), nullable=False)
    element_selector = Column(Text)
    element_html = Column(Text)
    element_tag = Column(String(64))
    page_region = Column(String(64))  # header, nav, main, footer, aside, form
    description = Column(Text, nullable=False)
    impact_group = Column(String(64))  # blind, low_vision, color_blind, motor, cognitive
    fix_suggestion = Column(Text)
    fix_code = Column(Text)
    contrast_actual = Column(Float)
    contrast_required = Column(Float)
    suggested_color = Column(String(16))
