from __future__ import annotations

import datetime
from typing import cast

from flanks.base import BaseClient
from flanks.report.models import Report, ReportTemplate


class ReportClient(BaseClient):
    """Client for Report API (beta)."""

    async def list_templates(self) -> list[ReportTemplate]:
        """List all available report templates."""
        response = await self._transport.api_call("/report/v1/list-templates", method="GET")
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [ReportTemplate.model_validate(item) for item in response.get("templates", [])]

    async def build_report(
        self,
        template_id: str,
        language: str,
        start_date: datetime.date,
        end_date: datetime.date,
        credentials_token: str,
        **kwargs: str | datetime.date,
    ) -> Report:
        """Build a new report."""
        extra_fields = {
            k: v.isoformat() if isinstance(v, datetime.date) else v for k, v in kwargs.items()
        }
        response = await self._transport.api_call(
            "/report/v1/build-report",
            {
                "template_id": template_id,
                "language": language,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "credentials_token": credentials_token,
                **extra_fields,
            },
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Report.model_validate(response)

    async def get_status(self, report_id: str) -> Report:
        """Get the status of a report."""
        response = await self._transport.api_call(
            "/report/v1/get-report-status",
            {"report_id": report_id},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Report.model_validate(response)

    async def get_content_url(self, report_id: str) -> str:
        """Get the content URL for a completed report."""
        response = await self._transport.api_call(
            "/report/v1/get-report-content",
            {"report_id": report_id},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return cast(str, response["url"])
