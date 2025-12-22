from enum import Enum

from pydantic import BaseModel, ConfigDict


class ReportStatus(str, Enum):
    """Report generation status."""

    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"


class ReportTemplate(BaseModel):
    """A report template."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    template_id: str
    name: str | None = None
    description: str | None = None


class Report(BaseModel):
    """A generated report."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    report_id: str
    template_id: str | None = None
    status: ReportStatus
    created_at: str | None = None
    error_message: str | None = None
