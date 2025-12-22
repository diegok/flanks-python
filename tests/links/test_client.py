import httpx
import pytest
import respx

from flanks import FlanksClient
from flanks.links.models import Link, LinkCode


class TestLinksModels:
    def test_parses_link(self) -> None:
        link = Link.model_validate(
            {
                "link_token": "link_123",
                "name": "My Banking Link",
                "redirect_uri": "https://example.com/callback",
                "is_paused": False,
            }
        )
        assert link.link_token == "link_123"
        assert link.name == "My Banking Link"
        assert link.is_paused is False

    def test_parses_link_code(self) -> None:
        code = LinkCode.model_validate({"code": "code_abc", "expires_at": "2024-12-31T23:59:59Z"})
        assert code.code == "code_abc"


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

        respx.get("https://api.test.flanks.io/v0/links/list-links").mock(
            return_value=httpx.Response(
                200,
                json={
                    "links": [
                        {"link_token": "link1", "name": "Link One"},
                        {"link_token": "link2", "name": "Link Two"},
                    ]
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            links = await client.links.list()

        assert len(links) == 2
        assert links[0].link_token == "link1"
        assert links[1].name == "Link Two"

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
                    "link_token": "new_link",
                    "name": "New Link",
                    "redirect_uri": "https://example.com",
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            link = await client.links.create("https://example.com", "New Link")

        assert link.link_token == "new_link"
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
                json={"link_token": "link1", "name": "Updated Link"},
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            link = await client.links.edit("link1", name="Updated Link")

        assert link.name == "Updated Link"

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
            return_value=httpx.Response(200, json={"success": True})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            await client.links.delete("link1")

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["link_token"] == "link1"

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
            return_value=httpx.Response(200, json={"link_token": "link1", "is_paused": True})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            link = await client.links.pause("link1")

        assert link.is_paused is True

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
            return_value=httpx.Response(200, json={"link_token": "link1", "is_paused": False})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            link = await client.links.resume("link1")

        assert link.is_paused is False

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
                json={
                    "codes": [
                        {"code": "code1", "expires_at": "2024-12-31T23:59:59Z"},
                        {"code": "code2", "expires_at": "2024-12-31T23:59:59Z"},
                    ]
                },
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
                json={"credentials_token": "cred_token_123"},
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            credentials_token = await client.links.exchange_code("code1")

        assert credentials_token == "cred_token_123"

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["code"] == "code1"
