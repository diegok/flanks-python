import datetime

import httpx
import pytest
import respx

from flanks import FlanksClient
from flanks.report.models import Report, ReportStatus, ReportTemplate


class TestReportModels:
    def test_parses_template(self) -> None:
        template = ReportTemplate.model_validate(
            {
                "template_id": "tpl_123",
                "name": "Monthly Report",
                "description": "Monthly financial report",
            }
        )
        assert template.template_id == "tpl_123"
        assert template.name == "Monthly Report"

    def test_parses_report(self) -> None:
        report = Report.model_validate(
            {
                "report_id": "rpt_123",
                "template_id": "tpl_456",
                "status": "Completed",
                "created_at": "2024-01-15T10:30:00Z",
            }
        )
        assert report.report_id == "rpt_123"
        assert report.status == ReportStatus.COMPLETED


class TestReportClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_templates(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.get("https://api.test.flanks.io/report/v1/list-templates").mock(
            return_value=httpx.Response(
                200,
                json={
                    "templates": [
                        {"template_id": "tpl1", "name": "Template One"},
                        {"template_id": "tpl2", "name": "Template Two"},
                    ]
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            templates = await client.report.list_templates()

        assert len(templates) == 2
        assert templates[0].template_id == "tpl1"
        assert templates[1].name == "Template Two"

    @respx.mock
    @pytest.mark.asyncio
    async def test_build_report(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/report/v1/build-report").mock(
            return_value=httpx.Response(
                200,
                json={
                    "report_id": "rpt_new",
                    "template_id": "tpl1",
                    "status": "Processing",
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            report = await client.report.build_report(
                "tpl1",
                language="en",
                start_date=datetime.date(2024, 1, 1),
                end_date=datetime.date(2024, 12, 31),
                credentials_token="cred_token",
            )

        assert report.report_id == "rpt_new"
        assert report.status == ReportStatus.PROCESSING

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["template_id"] == "tpl1"
        assert request_body["language"] == "en"
        assert request_body["start_date"] == "2024-01-01"
        assert request_body["end_date"] == "2024-12-31"
        assert request_body["credentials_token"] == "cred_token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_status(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/report/v1/get-report-status").mock(
            return_value=httpx.Response(
                200,
                json={
                    "report_id": "rpt_123",
                    "status": "Completed",
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            report = await client.report.get_status("rpt_123")

        assert report.report_id == "rpt_123"
        assert report.status == ReportStatus.COMPLETED

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_content_url(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/report/v1/get-report-content").mock(
            return_value=httpx.Response(
                200,
                json={"url": "https://example.com/report.pdf"},
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            url = await client.report.get_content_url("rpt_123")

        assert url == "https://example.com/report.pdf"

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["report_id"] == "rpt_123"
