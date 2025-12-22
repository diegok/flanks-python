import httpx
import pytest
import respx

from flanks import FlanksClient
from flanks.entities.models import Entity


class TestEntity:
    def test_parses_entity(self) -> None:
        entity = Entity.model_validate(
            {
                "id": "bank_123",
                "name": "Test Bank",
                "country": "ES",
                "logo_url": "https://example.com/logo.png",
            }
        )
        assert entity.id == "bank_123"
        assert entity.name == "Test Bank"
        assert entity.country == "ES"
        assert entity.logo_url == "https://example.com/logo.png"

    def test_ignores_extra_fields(self) -> None:
        entity = Entity.model_validate(
            {
                "id": "bank_123",
                "name": "Test Bank",
                "unknown_field": "ignored",
            }
        )
        assert entity.id == "bank_123"
        assert not hasattr(entity, "unknown_field")


class TestEntitiesClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_entities(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.get("https://api.test.flanks.io/v0/bank/available").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": "bank_1", "name": "Bank One", "country": "ES"},
                    {"id": "bank_2", "name": "Bank Two", "country": "PT"},
                ],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            entities = await client.entities.list()

        assert len(entities) == 2
        assert entities[0].id == "bank_1"
        assert entities[1].country == "PT"
