"""Employee and visa data models."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class VisaType(str, Enum):
    """Supported visa categories."""

    H1B = "H-1B"
    H1B1 = "H-1B1"
    L1A = "L-1A"
    L1B = "L-1B"
    O1 = "O-1"
    TN = "TN"
    E1 = "E-1"
    E2 = "E-2"
    E3 = "E-3"
    J1 = "J-1"
    F1_OPT = "F-1 OPT"
    F1_STEM_OPT = "F-1 STEM OPT"
    EAD = "EAD"
    GREEN_CARD = "Green Card"
    CITIZEN = "US Citizen"


class VisaStatus(str, Enum):
    """Current status of an employee's visa/work authorization."""

    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    PENDING_RENEWAL = "pending_renewal"
    PENDING_INITIAL = "pending_initial"
    REVOKED = "revoked"


class Employee(BaseModel):
    """An employee whose immigration status is tracked."""

    id: str = Field(description="Unique employee identifier")
    first_name: str
    last_name: str
    email: str
    department: str = ""
    job_title: str = ""
    hire_date: date | None = None
    country_of_citizenship: str
    visa_type: VisaType
    visa_status: VisaStatus = VisaStatus.ACTIVE
    visa_expiration_date: date | None = None
    work_authorization_start: date | None = None
    work_authorization_end: date | None = None
    i9_completed: bool = False
    i9_expiration_date: date | None = None
    lca_wage_level: int | None = Field(default=None, ge=1, le=4)
    actual_wage: float | None = None
    prevailing_wage: float | None = None
    worksite_city: str = ""
    worksite_state: str = ""
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def days_until_visa_expiration(self, as_of: date | None = None) -> int | None:
        """Return the number of days until the visa expires, or None if no expiration."""
        if self.visa_expiration_date is None:
            return None
        reference = as_of or date.today()
        return (self.visa_expiration_date - reference).days

    def days_until_i9_expiration(self, as_of: date | None = None) -> int | None:
        """Return the number of days until I-9 reverification is needed."""
        if self.i9_expiration_date is None:
            return None
        reference = as_of or date.today()
        return (self.i9_expiration_date - reference).days
