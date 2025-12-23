from __future__ import annotations

import builtins

from flanks.base import BaseClient
from flanks.links.models import Link, LinkCode, LinkCodeExchangeResult


class LinksClient(BaseClient):
    """Client for Links API (legacy)."""

    async def list(self) -> list[Link]:
        """List all links."""
        response = await self._transport.api_call("/v0/links/list-links", {})
        if not isinstance(response, list):
            raise TypeError(f"Expected list response, got {type(response)}")
        return [Link.model_validate(item) for item in response]

    async def create(
        self,
        redirect_uri: str,
        *,
        name: str | None = None,
        company_name: str | None = None,
        terms_and_conditions_url: str | None = None,
        privacy_policy_url: str | None = None,
    ) -> Link:
        """Create a new link."""
        body: dict[str, str] = {"redirect_uri": redirect_uri}
        if name is not None:
            body["name"] = name
        if company_name is not None:
            body["company_name"] = company_name
        if terms_and_conditions_url is not None:
            body["terms_and_conditions_url"] = terms_and_conditions_url
        if privacy_policy_url is not None:
            body["privacy_policy_url"] = privacy_policy_url

        response = await self._transport.api_call("/v0/links/create-link", body)
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Link.model_validate(response)

    async def edit(
        self,
        token: str,
        *,
        redirect_uri: str | None = None,
        name: str | None = None,
        company_name: str | None = None,
        terms_and_conditions_url: str | None = None,
        privacy_policy_url: str | None = None,
    ) -> Link:
        """Edit an existing link. Pass None to remove an attribute."""
        body: dict[str, str | None] = {"token": token}
        if redirect_uri is not None:
            body["redirect_uri"] = redirect_uri
        if name is not None:
            body["name"] = name
        if company_name is not None:
            body["company_name"] = company_name
        if terms_and_conditions_url is not None:
            body["terms_and_conditions_url"] = terms_and_conditions_url
        if privacy_policy_url is not None:
            body["privacy_policy_url"] = privacy_policy_url

        response = await self._transport.api_call("/v0/links/edit-link", body)
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Link.model_validate(response)

    async def delete(self, token: str) -> None:
        """Delete a link. Only links with no pending codes can be deleted."""
        await self._transport.api_call("/v0/links/delete-link", {"token": token})

    async def pause(self, token: str) -> Link:
        """Pause a link."""
        response = await self._transport.api_call("/v0/links/pause-link", {"token": token})
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Link.model_validate(response)

    async def resume(self, token: str) -> Link:
        """Resume a paused link."""
        response = await self._transport.api_call("/v0/links/resume-link", {"token": token})
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Link.model_validate(response)

    async def get_unused_codes(self, link_token: str | None = None) -> builtins.list[LinkCode]:
        """Get unused exchange codes, optionally filtered by link_token."""
        params = {"link_token": link_token} if link_token else None
        response = await self._transport.api_call(
            "/v0/platform/link",
            method="GET",
            params=params,
        )
        if not isinstance(response, list):
            raise TypeError(f"Expected list response, got {type(response)}")
        return [LinkCode.model_validate(item) for item in response]

    async def exchange_code(self, code: str) -> LinkCodeExchangeResult:
        """Exchange a code for credentials. The code is single-use."""
        response = await self._transport.api_call("/v0/platform/link", {"code": code})
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return LinkCodeExchangeResult.model_validate(response)
