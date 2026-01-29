"""Tests for webhook retry logic."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atlas.api.security.webhooks import dispatch_webhook


@pytest.mark.asyncio
async def test_dispatch_webhook_success():
    """Successful delivery returns True."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = await dispatch_webhook(
            "https://example.com/hook",
            {"event": "test"},
            max_retries=0,
        )
    assert result is True


@pytest.mark.asyncio
async def test_dispatch_webhook_retries_on_failure():
    """Retries with exponential backoff on failure."""
    call_count = 0

    def failing_urlopen(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise ConnectionError("refused")

    with patch("urllib.request.urlopen", side_effect=failing_urlopen):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await dispatch_webhook(
                "https://example.com/hook",
                {"event": "test"},
                max_retries=2,
                base_delay=0.01,
            )
    assert result is False
    assert call_count == 3  # initial + 2 retries


@pytest.mark.asyncio
async def test_dispatch_webhook_succeeds_on_retry():
    """Succeeds after initial failure."""
    call_count = 0

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    def intermittent(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("temp failure")
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=intermittent):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await dispatch_webhook(
                "https://example.com/hook",
                {"event": "test"},
                max_retries=2,
                base_delay=0.01,
            )
    assert result is True
    assert call_count == 2
