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
                "template_id": 123,
                "name": "Monthly Report",
                "description": "Monthly financial report",
            }
        )
        assert template.template_id == 123
        assert template.name == "Monthly Report"

    def test_parses_report(self) -> None:
        report = Report.model_validate(
            {
                "report_id": 456,
                "template_id": 123,
                "status": "ready",
            }
        )
        assert report.report_id == 456
        assert report.status == ReportStatus.READY

    def test_all_status_values(self) -> None:
        for status_val in ["new", "payload", "file", "ready", "fail"]:
            report = Report.model_validate({"report_id": 1, "status": status_val})
            assert report.status is not None
            assert report.status.value == status_val


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

        respx.post("https://api.test.flanks.io/report/v1/list-templates").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [
                        {"template_id": 1, "name": "Template One", "description": "First"},
                        {"template_id": 2, "name": "Template Two", "description": "Second"},
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
        assert templates[0].template_id == 1
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
                    "report_id": 789,
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            report = await client.report.build_report(
                template_id=1,
                query={"connection_id_in": ["conn_123"]},
                template_attributes={"include_charts": True},
                language="en",
                start_date=datetime.date(2024, 1, 1),
                end_date=datetime.date(2024, 12, 31),
            )

        assert report.report_id == 789

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["template_id"] == 1
        assert request_body["query"] == {"connection_id_in": ["conn_123"]}
        assert request_body["template_attributes"] == {"include_charts": True}
        assert request_body["language"] == "en"
        assert request_body["start_date"] == "2024-01-01"
        assert request_body["end_date"] == "2024-12-31"

    @respx.mock
    @pytest.mark.asyncio
    async def test_build_report_minimal(self) -> None:
        """Test build_report with only required parameters."""
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/report/v1/build-report").mock(
            return_value=httpx.Response(200, json={"report_id": 100})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            report = await client.report.build_report(
                template_id=1,
                query={},
                template_attributes={},
            )

        assert report.report_id == 100

        # Verify request - should have defaults
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["language"] == "en"
        assert "start_date" not in request_body
        assert "end_date" not in request_body

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
                    "report_id": 123,
                    "template_id": 1,
                    "status": "ready",
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            report = await client.report.get_status(123)

        assert report.report_id == 123
        assert report.status == ReportStatus.READY

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
            url = await client.report.get_content_url(123)

        assert url == "https://example.com/report.pdf"

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["report_id"] == 123
