import httpx
import pytest
import respx

from flanks import FlanksClient
from flanks.links.models import Link, LinkCode, LinkCodeExchangeResult


class TestLinksModels:
    def test_parses_link(self) -> None:
        link = Link.model_validate(
            {
                "token": "link_123",
                "name": "My Banking Link",
                "redirect_uri": "https://example.com/callback",
                "active": True,
                "company_name": "Test Corp",
                "pending_code_count": 5,
            }
        )
        assert link.token == "link_123"
        assert link.name == "My Banking Link"
        assert link.active is True
        assert link.company_name == "Test Corp"
        assert link.pending_code_count == 5

    def test_parses_link_code(self) -> None:
        code = LinkCode.model_validate(
            {"code": "code_abc", "link_token": "link_123", "extra": {"user_id": "u1"}}
        )
        assert code.code == "code_abc"
        assert code.link_token == "link_123"
        assert code.extra == {"user_id": "u1"}

    def test_parses_exchange_result(self) -> None:
        result = LinkCodeExchangeResult.model_validate(
            {
                "credentials_token": "cred_123",
                "link_token": "link_456",
                "extra": {"key": "value"},
                "message": "Success",
            }
        )
        assert result.credentials_token == "cred_123"
        assert result.link_token == "link_456"


class TestLinksClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_links(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/links/list-links").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"token": "link1", "name": "Link One", "active": True},
                    {"token": "link2", "name": "Link Two", "active": False},
                ],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            links = await client.links.list()

        assert len(links) == 2
        assert links[0].token == "link1"
        assert links[1].name == "Link Two"
        assert links[1].active is False

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_link(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/links/create-link").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": "new_link",
                    "name": "New Link",
                    "redirect_uri": "https://example.com",
                    "active": True,
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            link = await client.links.create("https://example.com", name="New Link")

        assert link.token == "new_link"
        assert link.name == "New Link"

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["redirect_uri"] == "https://example.com"
        assert request_body["name"] == "New Link"

    @respx.mock
    @pytest.mark.asyncio
    async def test_edit_link(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/links/edit-link").mock(
            return_value=httpx.Response(
                200,
                json={"token": "link1", "name": "Updated Link", "active": True},
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            link = await client.links.edit("link1", name="Updated Link")

        assert link.name == "Updated Link"

        # Verify request uses 'token' not 'link_token'
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["token"] == "link1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_link(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/links/delete-link").mock(
            return_value=httpx.Response(200, json={"token": "link1"})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            await client.links.delete("link1")

        # Verify request uses 'token'
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["token"] == "link1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_pause_link(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/links/pause-link").mock(
            return_value=httpx.Response(200, json={"token": "link1", "active": False})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            link = await client.links.pause("link1")

        assert link.active is False

    @respx.mock
    @pytest.mark.asyncio
    async def test_resume_link(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/links/resume-link").mock(
            return_value=httpx.Response(200, json={"token": "link1", "active": True})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            link = await client.links.resume("link1")

        assert link.active is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_unused_codes(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.get("https://api.test.flanks.io/v0/platform/link").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"code": "code1", "link_token": "link1", "extra": {}},
                    {"code": "code2", "link_token": "link1", "extra": {}},
                ],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            codes = await client.links.get_unused_codes("link1")

        assert len(codes) == 2
        assert codes[0].code == "code1"

        # Verify query parameter was sent
        request = respx.calls.last.request
        assert "link_token=link1" in str(request.url)

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_unused_codes_no_filter(self) -> None:
        """Test get_unused_codes without link_token filter."""
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.get("https://api.test.flanks.io/v0/platform/link").mock(
            return_value=httpx.Response(200, json=[])
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            codes = await client.links.get_unused_codes()

        assert codes == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_exchange_code(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/platform/link").mock(
            return_value=httpx.Response(
                200,
                json={
                    "credentials_token": "cred_token_123",
                    "link_token": "link1",
                    "extra": {},
                    "message": "Success",
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            result = await client.links.exchange_code("code1")

        assert result.credentials_token == "cred_token_123"
        assert result.link_token == "link1"

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["code"] == "code1"
