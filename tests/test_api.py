"""Tests for the FastAPI endpoints."""

from fastapi.testclient import TestClient

from immigration_compliance.api.app import app, service

client = TestClient(app)

SAMPLE_EMPLOYEE = {
    "id": "EMP100",
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice@example.com",
    "country_of_citizenship": "Canada",
    "visa_type": "TN",
    "visa_status": "active",
    "visa_expiration_date": "2028-01-01",
    "i9_completed": True,
}


def setup_function():
    """Clear service state before each test."""
    service._employees.clear()


class TestHealthEndpoint:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestEmployeeEndpoints:
    def test_create_employee(self):
        resp = client.post("/employees", json=SAMPLE_EMPLOYEE)
        assert resp.status_code == 201
        assert resp.json()["id"] == "EMP100"

    def test_create_duplicate_employee(self):
        client.post("/employees", json=SAMPLE_EMPLOYEE)
        resp = client.post("/employees", json=SAMPLE_EMPLOYEE)
        assert resp.status_code == 409

    def test_list_employees(self):
        client.post("/employees", json=SAMPLE_EMPLOYEE)
        resp = client.get("/employees")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_employee(self):
        client.post("/employees", json=SAMPLE_EMPLOYEE)
        resp = client.get("/employees/EMP100")
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Alice"

    def test_get_employee_not_found(self):
        resp = client.get("/employees/NONEXISTENT")
        assert resp.status_code == 404

    def test_delete_employee(self):
        client.post("/employees", json=SAMPLE_EMPLOYEE)
        resp = client.delete("/employees/EMP100")
        assert resp.status_code == 204

    def test_delete_employee_not_found(self):
        resp = client.delete("/employees/NONEXISTENT")
        assert resp.status_code == 404


class TestComplianceEndpoints:
    def test_check_employee_compliance(self):
        client.post("/employees", json=SAMPLE_EMPLOYEE)
        resp = client.post("/compliance/check/EMP100", json={})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_check_nonexistent_employee(self):
        resp = client.post("/compliance/check/NONEXISTENT", json={})
        assert resp.status_code == 404

    def test_generate_report(self):
        client.post("/employees", json=SAMPLE_EMPLOYEE)
        resp = client.post("/compliance/report", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_employees"] == 1
        assert "violations" in data
        assert "risk_summary" in data
