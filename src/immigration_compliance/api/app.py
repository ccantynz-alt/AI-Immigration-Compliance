"""FastAPI application for immigration compliance API."""

from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from immigration_compliance.models.compliance import ComplianceReport, RuleViolation
from immigration_compliance.models.employee import Employee
from immigration_compliance.services.compliance_service import ComplianceService

app = FastAPI(
    title="AI Immigration Compliance",
    description="AI-powered immigration compliance monitoring and risk assessment",
    version="0.1.0",
)

# In-memory service instance (swap for DI in production)
service = ComplianceService()


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class ComplianceCheckRequest(BaseModel):
    as_of: date | None = None


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse()


# --- Employee endpoints ---


@app.post("/employees", response_model=Employee, status_code=201)
def create_employee(employee: Employee) -> Employee:
    if service.get_employee(employee.id):
        raise HTTPException(status_code=409, detail=f"Employee {employee.id} already exists")
    return service.add_employee(employee)


@app.get("/employees", response_model=list[Employee])
def list_employees() -> list[Employee]:
    return service.list_employees()


@app.get("/employees/{employee_id}", response_model=Employee)
def get_employee(employee_id: str) -> Employee:
    emp = service.get_employee(employee_id)
    if emp is None:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return emp


@app.delete("/employees/{employee_id}", status_code=204)
def delete_employee(employee_id: str) -> None:
    if not service.remove_employee(employee_id):
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")


# --- Compliance endpoints ---


@app.post("/compliance/check/{employee_id}", response_model=list[RuleViolation])
def check_employee_compliance(
    employee_id: str, request: ComplianceCheckRequest | None = None
) -> list[RuleViolation]:
    as_of = request.as_of if request else None
    try:
        return service.check_employee(employee_id, as_of)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/compliance/report", response_model=ComplianceReport)
def generate_compliance_report(
    request: ComplianceCheckRequest | None = None,
) -> ComplianceReport:
    as_of = request.as_of if request else None
    return service.generate_report(as_of)
