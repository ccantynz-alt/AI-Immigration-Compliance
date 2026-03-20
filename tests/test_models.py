"""Tests for data models."""

from datetime import date

from immigration_compliance.models.employee import Employee, VisaStatus, VisaType
from immigration_compliance.models.case import Case, CaseStatus
from immigration_compliance.models.compliance import (
    ComplianceReport,
    RiskLevel,
    RuleViolation,
)


def _make_employee(**kwargs):
    defaults = {
        "id": "EMP001",
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "country_of_citizenship": "India",
        "visa_type": VisaType.H1B,
    }
    defaults.update(kwargs)
    return Employee(**defaults)


class TestEmployee:
    def test_full_name(self):
        emp = _make_employee()
        assert emp.full_name == "Jane Doe"

    def test_days_until_visa_expiration(self):
        emp = _make_employee(visa_expiration_date=date(2026, 6, 1))
        days = emp.days_until_visa_expiration(as_of=date(2026, 3, 1))
        assert days == 92

    def test_days_until_visa_expiration_none(self):
        emp = _make_employee(visa_expiration_date=None)
        assert emp.days_until_visa_expiration() is None

    def test_days_until_i9_expiration(self):
        emp = _make_employee(i9_expiration_date=date(2026, 4, 1))
        days = emp.days_until_i9_expiration(as_of=date(2026, 3, 1))
        assert days == 31


class TestCase:
    def test_is_active(self):
        case = Case(
            id="CASE001",
            employee_id="EMP001",
            case_type="H-1B Extension",
            status=CaseStatus.PENDING,
        )
        assert case.is_active is True

    def test_is_not_active(self):
        case = Case(
            id="CASE002",
            employee_id="EMP001",
            case_type="H-1B Extension",
            status=CaseStatus.APPROVED,
        )
        assert case.is_active is False

    def test_requires_attention(self):
        case = Case(
            id="CASE003",
            employee_id="EMP001",
            case_type="H-1B Extension",
            status=CaseStatus.RFE_RECEIVED,
        )
        assert case.requires_attention is True


class TestComplianceReport:
    def test_compliance_rate(self):
        report = ComplianceReport(
            report_id="RPT001",
            total_employees=10,
            compliant_count=8,
            non_compliant_count=2,
        )
        assert report.compliance_rate == 80.0

    def test_compliance_rate_no_employees(self):
        report = ComplianceReport(report_id="RPT002")
        assert report.compliance_rate == 100.0

    def test_has_critical_issues(self):
        report = ComplianceReport(
            report_id="RPT003",
            risk_summary={RiskLevel.CRITICAL: 1, RiskLevel.HIGH: 2},
        )
        assert report.has_critical_issues is True

    def test_no_critical_issues(self):
        report = ComplianceReport(
            report_id="RPT004",
            risk_summary={RiskLevel.MEDIUM: 3},
        )
        assert report.has_critical_issues is False
