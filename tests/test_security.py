"""Tests for security fixes — path traversal, endpoint validation, api_base."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from oura_cli.cli import build_parser, cmd_export, make_client
from oura_cli.client import OuraClient, OuraError


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        pass
    def read(self):
        import json
        return json.dumps(self._payload).encode()


def test_endpoint_rejects_path_traversal():
    client = OuraClient(token="tok")
    for bad in ["../../admin", "sleep/../../config", "daily_sleep/../admin"]:
        with pytest.raises(ValueError) as exc:
            client.get(bad)
        assert "invalid endpoint" in str(exc.value)


def test_endpoint_rejects_empty():
    client = OuraClient(token="tok")
    with pytest.raises(ValueError) as exc:
        client.get("")
    assert "invalid endpoint" in str(exc.value)


def test_endpoint_accepts_valid():
    client = OuraClient(token="tok")
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _FakeResponse({"data": []})
        result = client.get("daily_sleep")
    assert result == {"data": []}


def test_export_rejects_path_traversal():
    """--out ../../../etc should be rejected."""
    parser = build_parser()
    args = parser.parse_args(["export", "--out", "../../../etc/cron.d"])
    args = _fake_token(args)
    args.days = 1
    args.include_hr = False
    args.include_ibi = False

    mock_client = MagicMock()
    mock_client.get.return_value = {"data": []}

    with patch("oura_cli.cli.make_client", return_value=mock_client):
        with pytest.raises(SystemExit) as exc:
            cmd_export(args)
    assert "must be inside the current directory" in str(exc.value.code)


def test_export_rejects_absolute_outside_cwd():
    """--out /tmp should be rejected (outside cwd)."""
    parser = build_parser()
    args = parser.parse_args(["export", "--out", "/tmp/oura-test"])
    args = _fake_token(args)
    args.days = 1
    args.include_hr = False
    args.include_ibi = False

    mock_client = MagicMock()
    mock_client.get.return_value = {"data": []}

    with patch("oura_cli.cli.make_client", return_value=mock_client):
        with pytest.raises(SystemExit) as exc:
            cmd_export(args)
    assert "must be inside the current directory" in str(exc.value.code)


def test_export_accepts_relative_path():
    """--out ./my-dir should be accepted."""
    parser = build_parser()
    args = parser.parse_args(["export", "--out", "./my-test-dir"])
    args = _fake_token(args)
    args.days = 1
    args.include_hr = False
    args.include_ibi = False

    mock_client = MagicMock()
    mock_client.get.return_value = {"data": []}

    with patch("oura_cli.cli.make_client", return_value=mock_client):
        with patch("os.makedirs"):
            with patch("builtins.open", MagicMock()):
                with patch("json.dump"):
                    cmd_export(args)  # should not raise


def test_make_client_forces_production_api_base():
    """CLI make_client should always use production API_BASE, not user-provided."""
    parser = build_parser()
    args = parser.parse_args(["summary"])
    args = _fake_token(args)

    with patch("oura_cli.cli.load_token", return_value="tok"):
        client = make_client(args)
    assert client.api_base == "https://api.ouraring.com/v2/usercollection"


def test_oura_error_body_truncated():
    """OuraError should truncate response body to prevent log flooding."""
    large_body = "x" * 10000
    err = OuraError(500, "sleep", large_body)
    assert len(str(err)) < 500


def _fake_token(args):
    if not hasattr(args, "token"):
        args.token = None
    return args
