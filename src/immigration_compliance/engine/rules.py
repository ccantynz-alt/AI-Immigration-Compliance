"""Compliance rules that can be evaluated against employee records."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from immigration_compliance.models.compliance import RiskLevel, RuleViolation
from immigration_compliance.models.employee import Employee, VisaStatus, VisaType


class ComplianceRule(ABC):
    """Base class for all compliance rules."""

    rule_id: str
    rule_name: str

    @abstractmethod
    def evaluate(self, employee: Employee, as_of: date | None = None) -> RuleViolation | None:
        """Evaluate this rule against an employee. Returns a violation if non-compliant."""


class VisaExpirationRule(ComplianceRule):
    """Check if an employee's visa is expired or expiring soon."""

    rule_id = "VISA_EXP_001"
    rule_name = "Visa Expiration Check"

    def __init__(self, critical_days: int = 0, high_days: int = 30, medium_days: int = 90):
        self.critical_days = critical_days
        self.high_days = high_days
        self.medium_days = medium_days

    def evaluate(self, employee: Employee, as_of: date | None = None) -> RuleViolation | None:
        # Citizens and green card holders without expiration dates are exempt
        if employee.visa_type in (VisaType.CITIZEN, VisaType.GREEN_CARD):
            if employee.visa_expiration_date is None:
                return None

        days_left = employee.days_until_visa_expiration(as_of)
        if days_left is None:
            return None

        if days_left <= self.critical_days:
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                description=(
                    f"Visa expired {abs(days_left)} days ago"
                    if days_left < 0
                    else "Visa expires today"
                ),
                risk_level=RiskLevel.CRITICAL,
                employee_id=employee.id,
                recommendation="Immediately consult immigration counsel. Employee may not be authorized to work.",
            )

        if days_left <= self.high_days:
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                description=f"Visa expires in {days_left} days",
                risk_level=RiskLevel.HIGH,
                employee_id=employee.id,
                recommendation="Initiate renewal or extension process immediately.",
            )

        if days_left <= self.medium_days:
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                description=f"Visa expires in {days_left} days",
                risk_level=RiskLevel.MEDIUM,
                employee_id=employee.id,
                recommendation="Begin planning renewal or extension with immigration counsel.",
            )

        return None


class I9ComplianceRule(ComplianceRule):
    """Check I-9 form completion and reverification deadlines."""

    rule_id = "I9_001"
    rule_name = "I-9 Compliance Check"

    def __init__(self, warning_days: int = 30):
        self.warning_days = warning_days

    def evaluate(self, employee: Employee, as_of: date | None = None) -> RuleViolation | None:
        if not employee.i9_completed:
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                description="I-9 form has not been completed",
                risk_level=RiskLevel.CRITICAL,
                employee_id=employee.id,
                recommendation="Complete Form I-9 within 3 business days of hire date.",
            )

        days_left = employee.days_until_i9_expiration(as_of)
        if days_left is not None and days_left <= 0:
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                description="I-9 reverification is overdue",
                risk_level=RiskLevel.CRITICAL,
                employee_id=employee.id,
                recommendation="Complete I-9 reverification immediately.",
            )

        if days_left is not None and days_left <= self.warning_days:
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                description=f"I-9 reverification due in {days_left} days",
                risk_level=RiskLevel.HIGH,
                employee_id=employee.id,
                recommendation="Schedule I-9 reverification with employee.",
            )

        return None


class WageComplianceRule(ComplianceRule):
    """Check that LCA wage requirements are met for H-1B and related visas."""

    rule_id = "WAGE_001"
    rule_name = "LCA Wage Compliance Check"

    APPLICABLE_VISA_TYPES = {VisaType.H1B, VisaType.H1B1, VisaType.E3}

    def evaluate(self, employee: Employee, as_of: date | None = None) -> RuleViolation | None:
        if employee.visa_type not in self.APPLICABLE_VISA_TYPES:
            return None

        if employee.actual_wage is None or employee.prevailing_wage is None:
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                description="Wage information is missing for LCA-required visa type",
                risk_level=RiskLevel.HIGH,
                employee_id=employee.id,
                recommendation="Record actual and prevailing wage data for LCA compliance.",
            )

        if employee.actual_wage < employee.prevailing_wage:
            deficit = employee.prevailing_wage - employee.actual_wage
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                description=(
                    f"Actual wage (${employee.actual_wage:,.2f}) is below prevailing wage "
                    f"(${employee.prevailing_wage:,.2f}) by ${deficit:,.2f}"
                ),
                risk_level=RiskLevel.CRITICAL,
                employee_id=employee.id,
                recommendation=(
                    "Immediately adjust compensation to at least the prevailing wage. "
                    "Back pay may be required."
                ),
            )

        return None


class WorkAuthorizationGapRule(ComplianceRule):
    """Check for gaps in work authorization."""

    rule_id = "AUTH_GAP_001"
    rule_name = "Work Authorization Gap Check"

    def evaluate(self, employee: Employee, as_of: date | None = None) -> RuleViolation | None:
        if employee.visa_type == VisaType.CITIZEN:
            return None

        reference = as_of or date.today()

        if employee.work_authorization_end is not None:
            if employee.work_authorization_end < reference:
                gap_days = (reference - employee.work_authorization_end).days
                return RuleViolation(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    description=f"Work authorization expired {gap_days} days ago",
                    risk_level=RiskLevel.CRITICAL,
                    employee_id=employee.id,
                    recommendation="Employee may not be authorized to work. Consult counsel immediately.",
                )

        if employee.work_authorization_start is not None:
            if employee.work_authorization_start > reference:
                return RuleViolation(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    description="Work authorization has not yet started",
                    risk_level=RiskLevel.HIGH,
                    employee_id=employee.id,
                    recommendation="Employee cannot begin work until authorization start date.",
                )

        return None


# Default rule set
DEFAULT_RULES: list[ComplianceRule] = [
    VisaExpirationRule(),
    I9ComplianceRule(),
    WageComplianceRule(),
    WorkAuthorizationGapRule(),
]
