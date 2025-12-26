from flanks.base import BaseClient
from flanks.entities.models import Entity


class EntitiesClient(BaseClient):
    """Client for Entities API.

    See: https://docs.flanks.io/pages/flanks-apis/entities-api/
    """

    async def list(self) -> list[Entity]:
        """List all available banking entities.

        See: https://docs.flanks.io/pages/flanks-apis/entities-api/#get-entities
        """
        response = await self._transport.api_call("/v0/bank/available", method="GET")
        if not isinstance(response, list):
            raise TypeError(f"Expected list response, got {type(response)}")
        return [Entity.model_validate(item) for item in response]
