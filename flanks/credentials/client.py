from flanks.base import BaseClient
from flanks.credentials.models import Credential, CredentialStatusResponse


class CredentialsClient(BaseClient):
    """Client for Credentials API."""

    async def get_status(self, credentials_token: str) -> CredentialStatusResponse:
        """Get status of a credential."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/status",
            {"credentials_token": credentials_token},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return CredentialStatusResponse.model_validate(response)

    async def list(self, page: int = 1) -> list[Credential]:
        """List credentials with page-number pagination."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/list",
            {"page": page},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Credential.model_validate(item) for item in response.get("credentials", [])]

    async def force_sca(self, credentials_token: str) -> CredentialStatusResponse:
        """Force SCA (Strong Customer Authentication) refresh."""
        return await self._update_status(credentials_token, "force_sca")

    async def force_reset(self, credentials_token: str) -> CredentialStatusResponse:
        """Force credential reset."""
        return await self._update_status(credentials_token, "force_reset")

    async def force_transaction(self, credentials_token: str) -> CredentialStatusResponse:
        """Force transaction data refresh."""
        return await self._update_status(credentials_token, "force_transaction")

    async def _update_status(self, credentials_token: str, action: str) -> CredentialStatusResponse:
        """Internal helper for status update operations."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/status",
            {"credentials_token": credentials_token, "action": action},
            method="PUT",
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return CredentialStatusResponse.model_validate(response)

    async def delete(self, credentials_token: str) -> None:
        """Delete a credential."""
        await self._transport.api_call(
            "/v0/bank/credentials",
            {"credentials_token": credentials_token},
            method="DELETE",
        )
