"""A small, polite, retrying client for the Internet Archive's Wayback Machine."""

import time
from collections.abc import Callable
from typing import Any

import httpx
from tenacity import (
    RetryCallState,
    RetryError,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)


class WaybackError(Exception):
    """A request to the archive failed even after all retries."""


class _ArchiveOffline(Exception):
    """The archive answered with its "temporarily offline" page instead of data."""


def looks_offline(body: bytes) -> bool:
    """Tell whether a response body is the archive's HTML outage page.

    The archive sometimes answers HTTP 200 with a page saying it is temporarily offline, so the status
    code alone is not enough.

    Args:
        body: Response bytes.

    Returns:
        True if the body is an HTML page announcing an outage.
    """
    head = body[:600].lower()
    return b"<html" in head and (b"temporarily offline" in head or b"service unavailable" in head)


def _is_retryable(error: BaseException) -> bool:
    """Decide whether a failed attempt is worth repeating (network trouble, outage page, 5xx, 429)."""
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code >= 500 or error.response.status_code == 429
    return isinstance(error, httpx.TransportError | _ArchiveOffline)


class WaybackClient:
    """Fetches index rows and stored captures, pausing before each request and retrying with backoff."""

    def __init__(
        self,
        delay: float = 2.0,
        retries: int = 5,
        timeout: float = 120.0,
        user_agent: str = "cof-archive-lister/0.2",
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Create a client.

        Args:
            delay: Seconds to pause before every request, and the base of the retry backoff.
            retries: Attempts per request before giving up.
            timeout: Seconds before a single request times out.
            user_agent: Value of the ``User-Agent`` header (generic; carries no personal details).
            transport: Replacement transport, used by tests to avoid real network traffic.
            sleep: Replacement for ``time.sleep``, used by tests.
        """
        self._delay = delay
        self._retries = retries
        self._sleep = sleep
        self._client = httpx.Client(
            headers={"User-Agent": user_agent}, timeout=timeout, follow_redirects=True, transport=transport
        )

    def close(self) -> None:
        """Release the underlying connection pool."""
        self._client.close()

    def _once(self, url: str, params: dict[str, Any] | None) -> bytes:
        """Make one attempt: pause, request, and reject error statuses and outage pages."""
        self._sleep(self._delay)  # politeness: never hammer the archive
        response = self._client.get(url, params=params)
        response.raise_for_status()
        if looks_offline(response.content):
            raise _ArchiveOffline("the archive reported it was temporarily offline")
        return response.content

    def get(self, url: str, params: dict[str, Any] | None = None) -> bytes:
        """GET a URL with retries.

        Args:
            url: Address to request.
            params: Optional query parameters.

        Returns:
            The response body.

        Raises:
            WaybackError: If every attempt failed.
        """

        def wait(state: RetryCallState) -> float:
            # Backoff doubles each time: delay, 2*delay, 4*delay ...
            return float(wait_exponential(multiplier=self._delay, exp_base=2)(state))

        retrying = Retrying(
            stop=stop_after_attempt(self._retries),
            wait=wait,
            retry=retry_if_exception(_is_retryable),
            sleep=self._sleep,
        )
        try:
            return retrying(self._once, url, params)
        except RetryError as error:
            raise WaybackError(
                f"giving up on {url} after {self._retries} attempts: {error.last_attempt.exception()!r}"
            ) from error
        except httpx.HTTPStatusError as error:  # non-retryable status such as 404
            raise WaybackError(f"{url} returned HTTP {error.response.status_code}") from error

    def cdx(self, pattern: str, fields: list[str], limit: int) -> tuple[list[str], list[list[str]]]:
        """Query the capture index for every capture matching a URL pattern.

        Args:
            pattern: URL or URL prefix pattern (a trailing ``*`` matches everything below).
            fields: Index fields to return, for example ``["timestamp", "original"]``.
            limit: Maximum number of rows.

        Returns:
            ``(header, rows)``; both empty-ish when nothing matches.
        """
        body = self.get(
            "https://web.archive.org/cdx/search/cdx",
            {"url": pattern, "output": "json", "fl": ",".join(fields), "limit": limit},
        )
        if not body.strip():
            return fields, []
        data: list[list[str]] = httpx.Response(200, content=body).json()
        return data[0], data[1:]

    def fetch_capture(self, timestamp: str, original: str) -> bytes:
        """Fetch the bytes of one capture exactly as stored.

        The ``id_`` suffix on the timestamp asks the archive not to rewrite the content.

        Args:
            timestamp: Capture time, ``YYYYMMDDhhmmss``.
            original: The captured address.

        Returns:
            The stored bytes.
        """
        return self.get(f"https://web.archive.org/web/{timestamp}id_/{original}")
