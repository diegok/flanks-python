from __future__ import annotations

from typing import cast

from flanks.base import BaseClient
from flanks.links.models import Link, LinkCode


class LinksClient(BaseClient):
    """Client for Links API (legacy)."""

    async def list(self) -> list[Link]:
        """List all links."""
        response = await self._transport.api_call("/v0/links/list-links", method="GET")
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Link.model_validate(item) for item in response.get("links", [])]

    async def create(self, redirect_uri: str, name: str, **kwargs: str) -> Link:
        """Create a new link."""
        response = await self._transport.api_call(
            "/v0/links/create-link",
            {
                "redirect_uri": redirect_uri,
                "name": name,
                **kwargs,
            },
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Link.model_validate(response)

    async def edit(self, link_token: str, **kwargs: str) -> Link:
        """Edit an existing link."""
        response = await self._transport.api_call(
            "/v0/links/edit-link",
            {
                "link_token": link_token,
                **kwargs,
            },
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Link.model_validate(response)

    async def delete(self, link_token: str) -> None:
        """Delete a link."""
        await self._transport.api_call(
            "/v0/links/delete-link",
            {"link_token": link_token},
        )

    async def pause(self, link_token: str) -> Link:
        """Pause a link."""
        response = await self._transport.api_call(
            "/v0/links/pause-link",
            {"link_token": link_token},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Link.model_validate(response)

    async def resume(self, link_token: str) -> Link:
        """Resume a paused link."""
        response = await self._transport.api_call(
            "/v0/links/resume-link",
            {"link_token": link_token},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Link.model_validate(response)

    async def get_unused_codes(self, link_token: str) -> list[LinkCode]:
        """Get unused exchange codes for a link."""
        response = await self._transport.api_call(
            "/v0/platform/link",
            {"link_token": link_token},
            method="GET",
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [LinkCode.model_validate(item) for item in response.get("codes", [])]

    async def exchange_code(self, code: str) -> str:
        """Exchange a code for a credentials token."""
        response = await self._transport.api_call(
            "/v0/platform/link",
            {"code": code},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return cast(str, response["credentials_token"])
