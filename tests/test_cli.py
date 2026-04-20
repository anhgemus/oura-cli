"""Tests for cli.py — argparse wiring and command dispatch."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from oura_cli.cli import build_parser


def _fake_token(args):
    """Ensure args.token exists (from argparse default)."""
    if not hasattr(args, "token"):
        args.token = None
    return args


def test_parser_has_all_subcommands():
    parser = build_parser()
    # Collect actual subcommand names from the parser
    sub_names = set()
    for action in parser._subparsers._actions:
        if hasattr(action, "choices") and action.choices:
            sub_names.update(action.choices.keys())
    expected = {
        "sleep", "daily-sleep", "readiness", "activity", "stress", "spo2",
        "workouts", "sessions", "tags", "vo2", "resilience", "cardio-age",
        "sleep-time", "rest-mode", "hr", "ring", "me", "summary", "export",
        "get", "endpoints",
    }
    assert expected.issubset(sub_names)


def test_dated_subcommand_has_common_flags():
    parser = build_parser()
    args = parser.parse_args(["sleep", "--days", "3", "--date", "2024-11-19", "--json", "--csv"])
    args = _fake_token(args)
    assert args.days == 3
    assert args.date == "2024-11-19"
    assert args.json is True
    assert args.csv is True


def test_hr_subcommand_defaults():
    parser = build_parser()
    args = parser.parse_args(["hr"])
    args = _fake_token(args)
    assert args.hours == 24
    assert args.start is None
    assert args.end is None


def test_hr_subcommand_custom_hours():
    parser = build_parser()
    args = parser.parse_args(["hr", "--hours", "6"])
    args = _fake_token(args)
    assert args.hours == 6


def test_export_subcommand_flags():
    parser = build_parser()
    args = parser.parse_args(["export", "--days", "30", "--out", "/tmp/out", "--include-hr", "--include-ibi"])
    args = _fake_token(args)
    assert args.days == 30
    assert args.out == "/tmp/out"
    assert args.include_hr is True
    assert args.include_ibi is True


def test_get_subcommand_params():
    parser = build_parser()
    args = parser.parse_args([
        "get", "daily_spo2", "--start", "2024-01-01", "--end", "2024-01-07",
        "--param", "extra=value",
    ])
    args = _fake_token(args)
    assert args.start == "2024-01-01"
    assert args.end == "2024-01-07"
    assert args.param == ["extra=value"]


def test_version_flag():
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])
    assert exc.value.code == 0


def test_cmd_get_param_does_not_shadow_start():
    """--param should not be able to override --start/--end."""
    parser = build_parser()
    args = parser.parse_args([
        "get", "sleep", "--start", "2024-01-01", "--param", "start_date=2024-02-01",
    ])
    args = _fake_token(args)

    # Mock the client to capture what params were actually sent
    mock_client = MagicMock()
    mock_client.get.return_value = {"data": []}

    with patch("oura_cli.cli.make_client", return_value=mock_client):
        with patch("oura_cli.cli.write_output"):
            from oura_cli.cli import cmd_get
            cmd_get(args)

    # The actual params sent should NOT include start_date=2024-02-01
    call_args = mock_client.get.call_args
    params = call_args[0][1]  # second positional arg
    assert params["start_date"] == "2024-01-01"
    assert "start_date" not in params or params["start_date"] == "2024-01-01"


def test_cmd_get_param_works_when_no_start_end():
    """--param should work normally when --start/--end are not provided."""
    parser = build_parser()
    args = parser.parse_args([
        "get", "heartrate", "--param", "start_datetime=2024-01-01T00:00:00+00:00",
    ])
    args = _fake_token(args)

    mock_client = MagicMock()
    mock_client.get.return_value = {"data": []}

    with patch("oura_cli.cli.make_client", return_value=mock_client):
        with patch("oura_cli.cli.write_output"):
            from oura_cli.cli import cmd_get
            cmd_get(args)

    call_args = mock_client.get.call_args
    params = call_args[0][1]
    assert params["start_datetime"] == "2024-01-01T00:00:00+00:00"
