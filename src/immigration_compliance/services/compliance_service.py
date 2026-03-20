"""Service layer coordinating compliance evaluation and employee management."""

from __future__ import annotations

from datetime import date

from immigration_compliance.engine.evaluator import ComplianceEvaluator
from immigration_compliance.models.compliance import ComplianceReport, RuleViolation
from immigration_compliance.models.employee import Employee


class ComplianceService:
    """Manages employees and runs compliance evaluations."""

    def __init__(self, evaluator: ComplianceEvaluator | None = None):
        self.evaluator = evaluator or ComplianceEvaluator()
        self._employees: dict[str, Employee] = {}

    def add_employee(self, employee: Employee) -> Employee:
        self._employees[employee.id] = employee
        return employee

    def get_employee(self, employee_id: str) -> Employee | None:
        return self._employees.get(employee_id)

    def list_employees(self) -> list[Employee]:
        return list(self._employees.values())

    def remove_employee(self, employee_id: str) -> bool:
        return self._employees.pop(employee_id, None) is not None

    def check_employee(
        self, employee_id: str, as_of: date | None = None
    ) -> list[RuleViolation]:
        """Run compliance check on a single employee."""
        employee = self._employees.get(employee_id)
        if employee is None:
            raise ValueError(f"Employee {employee_id} not found")
        return self.evaluator.evaluate_employee(employee, as_of)

    def generate_report(self, as_of: date | None = None) -> ComplianceReport:
        """Generate a full compliance report for all employees."""
        return self.evaluator.evaluate_all(self.list_employees(), as_of)
