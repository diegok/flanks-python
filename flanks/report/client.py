from __future__ import annotations

import datetime
from typing import Any, cast

from flanks.base import BaseClient
from flanks.report.models import Report, ReportTemplate


class ReportClient(BaseClient):
    """Client for Report API (beta)."""

    async def list_templates(self) -> list[ReportTemplate]:
        """List all available report templates."""
        response = await self._transport.api_call("/report/v1/list-templates", {})
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [ReportTemplate.model_validate(item) for item in response.get("items", [])]

    async def build_report(
        self,
        template_id: int,
        query: dict[str, Any],
        template_attributes: dict[str, Any],
        *,
        language: str = "en",
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
    ) -> Report:
        """Build a new report.

        Args:
            template_id: Template identifier
            query: Filtering criteria with optional labels
            template_attributes: Template-specific generation settings
            language: Language code (en, es, fr). Defaults to "en"
            start_date: Report start date (optional)
            end_date: Report end date. Defaults to today
        """
        body: dict[str, Any] = {
            "template_id": template_id,
            "query": query,
            "template_attributes": template_attributes,
            "language": language,
        }
        if start_date is not None:
            body["start_date"] = start_date.isoformat()
        if end_date is not None:
            body["end_date"] = end_date.isoformat()

        response = await self._transport.api_call("/report/v1/build-report", body)
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Report.model_validate(response)

    async def get_status(self, report_id: int) -> Report:
        """Get the status of a report."""
        response = await self._transport.api_call(
            "/report/v1/get-report-status",
            {"report_id": report_id},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Report.model_validate(response)

    async def get_content_url(self, report_id: int) -> str:
        """Get the content URL for a completed report."""
        response = await self._transport.api_call(
            "/report/v1/get-report-content",
            {"report_id": report_id},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return cast(str, response["url"])
