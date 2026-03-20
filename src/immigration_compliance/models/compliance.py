"""Compliance assessment and reporting models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk level for compliance findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RuleViolation(BaseModel):
    """A specific compliance rule violation found during assessment."""

    rule_id: str = Field(description="Unique identifier for the compliance rule")
    rule_name: str
    description: str
    risk_level: RiskLevel
    employee_id: str
    recommendation: str = ""
    deadline: datetime | None = None


class ComplianceAlert(BaseModel):
    """An actionable alert generated from compliance monitoring."""

    id: str
    title: str
    description: str
    risk_level: RiskLevel
    employee_id: str | None = None
    case_id: str | None = None
    is_resolved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None


class ComplianceReport(BaseModel):
    """Summary report of an organization's immigration compliance status."""

    report_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_employees: int = 0
    compliant_count: int = 0
    non_compliant_count: int = 0
    expiring_soon_count: int = 0
    violations: list[RuleViolation] = Field(default_factory=list)
    alerts: list[ComplianceAlert] = Field(default_factory=list)
    risk_summary: dict[RiskLevel, int] = Field(default_factory=dict)

    @property
    def compliance_rate(self) -> float:
        if self.total_employees == 0:
            return 100.0
        return (self.compliant_count / self.total_employees) * 100.0

    @property
    def has_critical_issues(self) -> bool:
        return self.risk_summary.get(RiskLevel.CRITICAL, 0) > 0
