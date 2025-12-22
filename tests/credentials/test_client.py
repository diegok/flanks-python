import httpx
import pytest
import respx

from flanks import FlanksClient
from flanks.credentials.models import Credential, CredentialStatus, CredentialStatusResponse


class TestCredentialModels:
    def test_parses_credential(self) -> None:
        credential = Credential.model_validate(
            {
                "credentials_token": "cred_123",
                "entity_id": "bank_456",
                "status": "active",
            }
        )
        assert credential.credentials_token == "cred_123"
        assert credential.entity_id == "bank_456"
        assert credential.status == CredentialStatus.ACTIVE

    def test_parses_status_response(self) -> None:
        response = CredentialStatusResponse.model_validate(
            {
                "credentials_token": "cred_123",
                "status": "pending",
                "entity_id": "bank_456",
            }
        )
        assert response.credentials_token == "cred_123"
        assert response.status == CredentialStatus.PENDING


class TestCredentialsClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_get_status(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/status").mock(
            return_value=httpx.Response(
                200,
                json={
                    "credentials_token": "cred_123",
                    "status": "active",
                    "entity_id": "bank_456",
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            status = await client.credentials.get_status("cred_123")

        assert status.credentials_token == "cred_123"
        assert status.status == CredentialStatus.ACTIVE

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_credentials(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/list").mock(
            return_value=httpx.Response(
                200,
                json={
                    "credentials": [
                        {"credentials_token": "c1", "entity_id": "b1", "status": "active"},
                        {"credentials_token": "c2", "entity_id": "b2", "status": "error"},
                    ]
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            credentials = await client.credentials.list(page=1)

        assert len(credentials) == 2
        assert credentials[0].credentials_token == "c1"
        assert credentials[1].status == CredentialStatus.ERROR

    @respx.mock
    @pytest.mark.asyncio
    async def test_force_sca(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.put("https://api.test.flanks.io/v0/bank/credentials/status").mock(
            return_value=httpx.Response(
                200,
                json={"credentials_token": "cred_123", "status": "pending"},
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            result = await client.credentials.force_sca("cred_123")

        assert result.status == CredentialStatus.PENDING

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.delete("https://api.test.flanks.io/v0/bank/credentials").mock(
            return_value=httpx.Response(200, json={})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            await client.credentials.delete("cred_123")

        # Verify DELETE was called
        assert respx.calls.last.request.method == "DELETE"
