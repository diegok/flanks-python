import httpx
import pytest
import respx
from pydantic import BaseModel

from flanks.base import BaseClient
from flanks.connection import FlanksConnection


class Item(BaseModel):
    id: int
    name: str


class TestBaseClient:
    def test_stores_transport(self) -> None:
        transport = FlanksConnection(client_id="id", client_secret="secret")
        client = BaseClient(transport)
        assert client._transport is transport


class TestPaginate:
    @respx.mock
    @pytest.mark.asyncio
    async def test_iterates_single_page(self) -> None:
        transport = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        transport._access_token = "token"
        transport._token_expires_at = 9999999999

        respx.post("https://api.test.flanks.io/v0/items").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [{"id": 1, "name": "one"}, {"id": 2, "name": "two"}],
                    "next_page_token": None,
                },
            )
        )

        client = BaseClient(transport)
        items = [item async for item in client._paginate("/v0/items", {}, "items", Item)]

        assert len(items) == 2
        assert items[0].id == 1
        assert items[1].name == "two"

    @respx.mock
    @pytest.mark.asyncio
    async def test_iterates_multiple_pages(self) -> None:
        transport = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        transport._access_token = "token"
        transport._token_expires_at = 9999999999

        route = respx.post("https://api.test.flanks.io/v0/items")
        route.side_effect = [
            httpx.Response(
                200,
                json={
                    "items": [{"id": 1, "name": "one"}],
                    "next_page_token": "page2",
                },
            ),
            httpx.Response(
                200,
                json={
                    "items": [{"id": 2, "name": "two"}],
                    "next_page_token": "page3",
                },
            ),
            httpx.Response(
                200,
                json={
                    "items": [{"id": 3, "name": "three"}],
                    "next_page_token": None,
                },
            ),
        ]

        client = BaseClient(transport)
        items = [item async for item in client._paginate("/v0/items", {}, "items", Item)]

        assert len(items) == 3
        assert [item.id for item in items] == [1, 2, 3]
        assert len(respx.calls) == 3

    @respx.mock
    @pytest.mark.asyncio
    async def test_passes_body_and_page_token(self) -> None:
        transport = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        transport._access_token = "token"
        transport._token_expires_at = 9999999999

        route = respx.post("https://api.test.flanks.io/v0/items")
        route.side_effect = [
            httpx.Response(
                200,
                json={"items": [{"id": 1, "name": "one"}], "next_page_token": "page2"},
            ),
            httpx.Response(
                200,
                json={"items": [], "next_page_token": None},
            ),
        ]

        client = BaseClient(transport)
        body = {"filter": "active"}
        _ = [item async for item in client._paginate("/v0/items", body, "items", Item)]

        # Check first request
        import json

        first_request = respx.calls[0].request
        first_body = json.loads(first_request.content)
        assert first_body["filter"] == "active"
        assert first_body["page_token"] is None

        # Check second request includes page token
        second_request = respx.calls[1].request
        second_body = json.loads(second_request.content)
        assert second_body["page_token"] == "page2"
