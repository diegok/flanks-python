import httpx
import pytest
import respx

from flanks import FlanksClient
from flanks.connect.models import (
    Connector,
    Session,
    SessionConfig,
    SessionQuery,
    SessionStatus,
)
from flanks.pagination import PagedResponse


class TestSessionModel:
    def test_parses_session(self) -> None:
        session = Session.model_validate(
            {
                "session_id": "sess_123",
                "status": "Waiting:ProvideCredentials",
                "connection_id": "conn_456",
            }
        )
        assert session.session_id == "sess_123"
        assert session.status == SessionStatus.WAITING_CREDENTIALS
        assert session.connection_id == "conn_456"

    def test_optional_fields(self) -> None:
        session = Session.model_validate(
            {
                "session_id": "sess_123",
                "status": "Finished:OK",
            }
        )
        assert session.connection_id is None
        assert session.error_code is None


class TestConnectClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_sessions_iterator(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        route = respx.post("https://api.test.flanks.io/connect/v2/sessions/list-sessions")
        route.side_effect = [
            httpx.Response(
                200,
                json={
                    "items": [{"session_id": "s1", "status": "Finished:OK"}],
                    "next_page_token": "page2",
                },
            ),
            httpx.Response(
                200,
                json={
                    "items": [{"session_id": "s2", "status": "Finished:Error"}],
                    "next_page_token": None,
                },
            ),
        ]

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            sessions = [s async for s in client.connect.list_sessions()]

        assert len(sessions) == 2
        assert sessions[0].session_id == "s1"
        assert sessions[1].status == SessionStatus.FINISHED_ERROR

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_sessions_with_query(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/connect/v2/sessions/list-sessions").mock(
            return_value=httpx.Response(
                200,
                json={"items": [{"session_id": "s1", "status": "Finished:OK"}], "next_page_token": None},
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            query = SessionQuery(status_in=[SessionStatus.FINISHED_OK])
            sessions = [s async for s in client.connect.list_sessions(query)]

        assert len(sessions) == 1
        # Verify query was sent
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["query"]["status_in"] == ["Finished:OK"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_sessions_page(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/connect/v2/sessions/list-sessions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [{"session_id": "s1", "status": "Finished:OK"}],
                    "next_page_token": "next_token",
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            page = await client.connect.list_sessions_page()

        assert isinstance(page, PagedResponse)
        assert len(page.items) == 1
        assert page.next_page_token == "next_token"
        assert page.has_next()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_session(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/connect/v2/sessions/create-session").mock(
            return_value=httpx.Response(
                200,
                json={
                    "session": {
                        "session_id": "new_sess",
                        "status": "Waiting:ProvideCredentials",
                    }
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            config = SessionConfig(connector_id="conn_123")
            session = await client.connect.create_session(config)

        assert session.session_id == "new_sess"
        assert session.status == SessionStatus.WAITING_CREDENTIALS

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_connectors(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/connect/v2/connectors/list-connectors").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [{"connector_id": "c1", "name": "Bank One"}],
                    "next_page_token": None,
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            connectors = [c async for c in client.connect.list_connectors()]

        assert len(connectors) == 1
        assert connectors[0].connector_id == "c1"
