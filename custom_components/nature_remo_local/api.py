"""Cloud API client for Nature Remo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import API_BASE_URL


class NatureRemoApiError(Exception):
    """Base error for the Nature Remo API client."""


class NatureRemoAuthenticationError(NatureRemoApiError):
    """Raised when authentication fails."""


class NatureRemoRateLimitError(NatureRemoApiError):
    """Raised when the API rate limit is exceeded."""


@dataclass(slots=True)
class NatureRemoRateLimitStatus:
    """Latest rate limit information from the API."""

    limit: int | None = None
    remaining: int | None = None
    reset_at: datetime | None = None

    @classmethod
    def from_headers(cls, headers: Any) -> "NatureRemoRateLimitStatus":
        """Build a rate limit status from response headers."""
        limit = _parse_int_header(headers.get("X-Rate-Limit-Limit"))
        remaining = _parse_int_header(headers.get("X-Rate-Limit-Remaining"))
        reset_raw = _parse_int_header(headers.get("X-Rate-Limit-Reset"))
        reset_at = (
            datetime.fromtimestamp(reset_raw, UTC) if reset_raw is not None else None
        )
        return cls(limit=limit, remaining=remaining, reset_at=reset_at)


class NatureRemoApi:
    """Thin async client around the Nature Remo Cloud API."""

    def __init__(self, session: ClientSession, access_token: str) -> None:
        self._session = session
        self._access_token = access_token
        self._rate_limit = NatureRemoRateLimitStatus()

    @property
    def rate_limit(self) -> NatureRemoRateLimitStatus:
        """Return the latest observed rate limit."""
        return self._rate_limit

    async def async_get_user(self) -> dict[str, Any]:
        """Fetch the authenticated user."""
        return await self._request("get", "/1/users/me")

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Fetch Nature Remo devices."""
        return await self._request("get", "/1/devices")

    async def async_get_appliances(self) -> list[dict[str, Any]]:
        """Fetch appliances."""
        return await self._request("get", "/1/appliances")

    async def async_set_aircon_settings(
        self, appliance_id: str, payload: dict[str, str]
    ) -> dict[str, Any]:
        """Update aircon settings."""
        return await self._request(
            "post",
            f"/1/appliances/{appliance_id}/aircon_settings",
            data=payload,
        )

    async def async_set_light_button(
        self, appliance_id: str, button_name: str
    ) -> dict[str, Any]:
        """Send a light button command."""
        return await self._request(
            "post",
            f"/1/appliances/{appliance_id}/light",
            data={"button": button_name},
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, str] | None = None,
    ) -> Any:
        """Issue an API request."""
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }

        try:
            response = await self._session.request(
                method,
                f"{API_BASE_URL}{path}",
                headers=headers,
                data=data,
            )
            self._rate_limit = NatureRemoRateLimitStatus.from_headers(response.headers)
            response.raise_for_status()
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise NatureRemoAuthenticationError from err
            if err.status == 429:
                raise NatureRemoRateLimitError("Nature Remo API rate limit exceeded") from err
            raise NatureRemoApiError(f"Nature Remo API request failed: {err.status}") from err
        except ClientError as err:
            raise NatureRemoApiError("Nature Remo API request failed") from err

        try:
            return await response.json()
        except (ValueError, TypeError) as err:
            raise NatureRemoApiError("Nature Remo API returned invalid JSON") from err


def _parse_int_header(value: str | None) -> int | None:
    """Parse an integer response header."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
