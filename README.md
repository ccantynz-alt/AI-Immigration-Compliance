# AI Immigration Compliance

AI-powered immigration compliance monitoring and risk assessment system for organizations managing international employees.

## Features

- **Employee Tracking** — Manage employee immigration records including visa types, expiration dates, and work authorizations
- **Automated Compliance Rules** — Evaluate employees against configurable compliance rules:
  - Visa expiration monitoring (critical/high/medium thresholds)
  - I-9 form completion and reverification tracking
  - LCA wage compliance for H-1B and related visa types
  - Work authorization gap detection
- **Risk Assessment** — Automated risk scoring (Critical, High, Medium, Low, Info)
- **Compliance Reports** — Generate organization-wide compliance reports with violation details and alerts
- **REST API** — FastAPI-based endpoints for integration with HR systems

## Quick Start

### Installation

```bash
pip install -e ".[dev]"
```

### Run the API Server

```bash
uvicorn immigration_compliance.api.app:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Run Tests

```bash
pytest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/employees` | Create employee record |
| GET | `/employees` | List all employees |
| GET | `/employees/{id}` | Get employee by ID |
| DELETE | `/employees/{id}` | Delete employee |
| POST | `/compliance/check/{id}` | Check compliance for an employee |
| POST | `/compliance/report` | Generate full compliance report |

## Project Structure

```
src/immigration_compliance/
├── models/          # Pydantic data models (Employee, Case, Compliance)
├── engine/          # Compliance rule engine and evaluator
├── services/        # Business logic layer
└── api/             # FastAPI application and endpoints
```

## Compliance Rules

| Rule | ID | Description |
|------|----|-------------|
| Visa Expiration | VISA_EXP_001 | Monitors visa expiration with tiered alerts |
| I-9 Compliance | I9_001 | Tracks I-9 completion and reverification |
| Wage Compliance | WAGE_001 | Validates LCA wage requirements for H-1B |
| Work Auth Gap | AUTH_GAP_001 | Detects gaps in work authorization |

## License

MIT
