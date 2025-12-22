from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class CredentialStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    ERROR = "error"
    EXPIRED = "expired"


class Credential(BaseModel):
    """A stored credential."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    credentials_token: str
    entity_id: str
    status: CredentialStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CredentialStatusResponse(BaseModel):
    """Response from get_status endpoint."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    credentials_token: str
    status: CredentialStatus
    entity_id: str | None = None
