"""Unit tests for OuraClient with urllib mocked."""
from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest

from oura_cli.client import OuraClient, OuraError


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        self.close()
        return False


def _make_response(payload: dict) -> _FakeResponse:
    return _FakeResponse(json.dumps(payload).encode())


def test_get_single_page():
    client = OuraClient(token="tok")
    with patch("urllib.request.urlopen", return_value=_make_response({"data": [{"day": "2024-11-19"}]})):
        result = client.get("daily_sleep", {"start_date": "2024-11-19", "end_date": "2024-11-19"})
    assert result == {"data": [{"day": "2024-11-19"}]}


def test_get_paginates_next_token():
    client = OuraClient(token="tok")
    responses = [
        _make_response({"data": [{"day": "d1"}], "next_token": "abc"}),
        _make_response({"data": [{"day": "d2"}]}),
    ]
    with patch("urllib.request.urlopen", side_effect=responses):
        result = client.get("sleep", {"start_date": "d1", "end_date": "d2"})
    assert [e["day"] for e in result["data"]] == ["d1", "d2"]


def test_get_raises_oura_error_on_http_error():
    import urllib.error
    client = OuraClient(token="tok")
    err = urllib.error.HTTPError("url", 404, "Not Found", hdrs=None, fp=io.BytesIO(b"nope"))
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(OuraError) as exc:
            client.get("vo2_max")
    assert exc.value.status == 404
    assert exc.value.endpoint == "vo2_max"


def test_index_by_day_groups_entries():
    entries = [
        {"day": "2024-11-18", "score": 80},
        {"day": "2024-11-19", "score": 75},
        {"day": "2024-11-19", "score": 70},
    ]
    idx = OuraClient.index_by_day(entries)
    assert set(idx.keys()) == {"2024-11-18", "2024-11-19"}
    assert len(idx["2024-11-19"]) == 2


def test_index_by_day_falls_back_to_bedtime_start():
    entries = [{"bedtime_start": "2024-11-19T23:00:00+00:00"}]
    idx = OuraClient.index_by_day(entries)
    assert "2024-11-19" in idx


def test_client_requires_token():
    with pytest.raises(ValueError):
        OuraClient(token="")
