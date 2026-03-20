"""Immigration case tracking models."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class CaseStatus(str, Enum):
    """Status of an immigration case or petition."""

    DRAFT = "draft"
    FILED = "filed"
    PENDING = "pending"
    RFE_RECEIVED = "rfe_received"
    RFE_RESPONDED = "rfe_responded"
    APPROVED = "approved"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    APPEALED = "appealed"


class Case(BaseModel):
    """An immigration case or petition being tracked."""

    id: str = Field(description="Unique case identifier")
    employee_id: str = Field(description="Associated employee ID")
    case_type: str = Field(description="Type of petition (e.g., H-1B Initial, H-1B Extension)")
    receipt_number: str | None = None
    status: CaseStatus = CaseStatus.DRAFT
    priority_date: date | None = None
    filed_date: date | None = None
    decision_date: date | None = None
    expiration_date: date | None = None
    attorney_name: str = ""
    attorney_email: str = ""
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_active(self) -> bool:
        return self.status in (
            CaseStatus.FILED,
            CaseStatus.PENDING,
            CaseStatus.RFE_RECEIVED,
            CaseStatus.RFE_RESPONDED,
            CaseStatus.APPEALED,
        )

    @property
    def requires_attention(self) -> bool:
        return self.status == CaseStatus.RFE_RECEIVED
