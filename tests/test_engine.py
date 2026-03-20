"""Tests for the compliance engine rules and evaluator."""

from datetime import date

from immigration_compliance.engine.evaluator import ComplianceEvaluator
from immigration_compliance.engine.rules import (
    I9ComplianceRule,
    VisaExpirationRule,
    WageComplianceRule,
    WorkAuthorizationGapRule,
)
from immigration_compliance.models.compliance import RiskLevel
from immigration_compliance.models.employee import Employee, VisaType


def _make_employee(**kwargs):
    defaults = {
        "id": "EMP001",
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "country_of_citizenship": "India",
        "visa_type": VisaType.H1B,
        "i9_completed": True,
    }
    defaults.update(kwargs)
    return Employee(**defaults)


class TestVisaExpirationRule:
    def test_expired_visa(self):
        rule = VisaExpirationRule()
        emp = _make_employee(visa_expiration_date=date(2026, 1, 1))
        violation = rule.evaluate(emp, as_of=date(2026, 3, 1))
        assert violation is not None
        assert violation.risk_level == RiskLevel.CRITICAL

    def test_expiring_in_20_days(self):
        rule = VisaExpirationRule()
        emp = _make_employee(visa_expiration_date=date(2026, 3, 21))
        violation = rule.evaluate(emp, as_of=date(2026, 3, 1))
        assert violation is not None
        assert violation.risk_level == RiskLevel.HIGH

    def test_expiring_in_60_days(self):
        rule = VisaExpirationRule()
        emp = _make_employee(visa_expiration_date=date(2026, 4, 30))
        violation = rule.evaluate(emp, as_of=date(2026, 3, 1))
        assert violation is not None
        assert violation.risk_level == RiskLevel.MEDIUM

    def test_far_future_expiration(self):
        rule = VisaExpirationRule()
        emp = _make_employee(visa_expiration_date=date(2028, 1, 1))
        violation = rule.evaluate(emp, as_of=date(2026, 3, 1))
        assert violation is None

    def test_citizen_no_expiration(self):
        rule = VisaExpirationRule()
        emp = _make_employee(visa_type=VisaType.CITIZEN, visa_expiration_date=None)
        violation = rule.evaluate(emp, as_of=date(2026, 3, 1))
        assert violation is None


class TestI9ComplianceRule:
    def test_i9_not_completed(self):
        rule = I9ComplianceRule()
        emp = _make_employee(i9_completed=False)
        violation = rule.evaluate(emp)
        assert violation is not None
        assert violation.risk_level == RiskLevel.CRITICAL

    def test_i9_reverification_overdue(self):
        rule = I9ComplianceRule()
        emp = _make_employee(i9_completed=True, i9_expiration_date=date(2026, 1, 1))
        violation = rule.evaluate(emp, as_of=date(2026, 3, 1))
        assert violation is not None
        assert violation.risk_level == RiskLevel.CRITICAL

    def test_i9_reverification_upcoming(self):
        rule = I9ComplianceRule()
        emp = _make_employee(i9_completed=True, i9_expiration_date=date(2026, 3, 20))
        violation = rule.evaluate(emp, as_of=date(2026, 3, 1))
        assert violation is not None
        assert violation.risk_level == RiskLevel.HIGH

    def test_i9_compliant(self):
        rule = I9ComplianceRule()
        emp = _make_employee(i9_completed=True)
        violation = rule.evaluate(emp, as_of=date(2026, 3, 1))
        assert violation is None


class TestWageComplianceRule:
    def test_wage_below_prevailing(self):
        rule = WageComplianceRule()
        emp = _make_employee(actual_wage=80000.0, prevailing_wage=90000.0)
        violation = rule.evaluate(emp)
        assert violation is not None
        assert violation.risk_level == RiskLevel.CRITICAL

    def test_wage_compliant(self):
        rule = WageComplianceRule()
        emp = _make_employee(actual_wage=100000.0, prevailing_wage=90000.0)
        violation = rule.evaluate(emp)
        assert violation is None

    def test_missing_wage_data(self):
        rule = WageComplianceRule()
        emp = _make_employee(actual_wage=None, prevailing_wage=None)
        violation = rule.evaluate(emp)
        assert violation is not None
        assert violation.risk_level == RiskLevel.HIGH

    def test_non_h1b_skipped(self):
        rule = WageComplianceRule()
        emp = _make_employee(visa_type=VisaType.L1A)
        violation = rule.evaluate(emp)
        assert violation is None


class TestWorkAuthorizationGapRule:
    def test_expired_authorization(self):
        rule = WorkAuthorizationGapRule()
        emp = _make_employee(work_authorization_end=date(2026, 1, 1))
        violation = rule.evaluate(emp, as_of=date(2026, 3, 1))
        assert violation is not None
        assert violation.risk_level == RiskLevel.CRITICAL

    def test_future_start(self):
        rule = WorkAuthorizationGapRule()
        emp = _make_employee(work_authorization_start=date(2026, 6, 1))
        violation = rule.evaluate(emp, as_of=date(2026, 3, 1))
        assert violation is not None
        assert violation.risk_level == RiskLevel.HIGH

    def test_citizen_exempt(self):
        rule = WorkAuthorizationGapRule()
        emp = _make_employee(visa_type=VisaType.CITIZEN)
        violation = rule.evaluate(emp, as_of=date(2026, 3, 1))
        assert violation is None


class TestComplianceEvaluator:
    def test_evaluate_employee_multiple_violations(self):
        evaluator = ComplianceEvaluator()
        emp = _make_employee(
            visa_expiration_date=date(2026, 1, 1),
            i9_completed=False,
            actual_wage=70000.0,
            prevailing_wage=90000.0,
        )
        violations = evaluator.evaluate_employee(emp, as_of=date(2026, 3, 1))
        assert len(violations) >= 3

    def test_evaluate_all_produces_report(self):
        evaluator = ComplianceEvaluator()
        employees = [
            _make_employee(id="EMP001", visa_expiration_date=date(2028, 1, 1)),
            _make_employee(id="EMP002", visa_expiration_date=date(2026, 1, 1)),
        ]
        report = evaluator.evaluate_all(employees, as_of=date(2026, 3, 1))
        assert report.total_employees == 2
        assert report.compliant_count >= 0
        assert report.non_compliant_count >= 0
        assert len(report.violations) > 0
