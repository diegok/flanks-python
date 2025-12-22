from pydantic import BaseModel, ConfigDict


class Link(BaseModel):
    """A connection link for end-user authentication."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    link_token: str
    name: str | None = None
    redirect_uri: str | None = None
    is_paused: bool | None = None


class LinkCode(BaseModel):
    """An exchange code for a link."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    code: str
    expires_at: str | None = None
