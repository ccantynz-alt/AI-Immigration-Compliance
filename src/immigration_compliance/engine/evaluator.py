"""Compliance evaluator that runs rules against employee records."""

from __future__ import annotations

import uuid
from datetime import date

from immigration_compliance.engine.rules import DEFAULT_RULES, ComplianceRule
from immigration_compliance.models.compliance import (
    ComplianceAlert,
    ComplianceReport,
    RiskLevel,
    RuleViolation,
)
from immigration_compliance.models.employee import Employee


class ComplianceEvaluator:
    """Evaluates a set of compliance rules against employee records."""

    def __init__(self, rules: list[ComplianceRule] | None = None):
        self.rules = rules if rules is not None else list(DEFAULT_RULES)

    def evaluate_employee(
        self, employee: Employee, as_of: date | None = None
    ) -> list[RuleViolation]:
        """Evaluate all rules against a single employee."""
        violations: list[RuleViolation] = []
        for rule in self.rules:
            violation = rule.evaluate(employee, as_of)
            if violation is not None:
                violations.append(violation)
        return violations

    def evaluate_all(
        self, employees: list[Employee], as_of: date | None = None
    ) -> ComplianceReport:
        """Evaluate all rules against all employees and produce a report."""
        all_violations: list[RuleViolation] = []
        compliant_count = 0
        non_compliant_ids: set[str] = set()
        expiring_soon_count = 0

        for emp in employees:
            violations = self.evaluate_employee(emp, as_of)
            all_violations.extend(violations)

            if violations:
                non_compliant_ids.add(emp.id)
            else:
                compliant_count += 1

            days = emp.days_until_visa_expiration(as_of)
            if days is not None and 0 < days <= 90:
                expiring_soon_count += 1

        risk_summary: dict[RiskLevel, int] = {}
        for v in all_violations:
            risk_summary[v.risk_level] = risk_summary.get(v.risk_level, 0) + 1

        alerts = [
            ComplianceAlert(
                id=str(uuid.uuid4()),
                title=f"{v.rule_name}: {v.description}",
                description=v.recommendation,
                risk_level=v.risk_level,
                employee_id=v.employee_id,
            )
            for v in all_violations
            if v.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH)
        ]

        return ComplianceReport(
            report_id=str(uuid.uuid4()),
            total_employees=len(employees),
            compliant_count=compliant_count,
            non_compliant_count=len(non_compliant_ids),
            expiring_soon_count=expiring_soon_count,
            violations=all_violations,
            alerts=alerts,
            risk_summary=risk_summary,
        )
