"""Tests for auth.py — token resolution priority."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import oura_cli.auth as auth_mod
from oura_cli.auth import load_token


def test_load_token_from_env():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pat", delete=False) as f:
        f.write("file_token")
        f.flush()
        path = f.name
    try:
        os.environ["OURA_PAT"] = "env_token"
        os.environ.pop("OURA_PAT_FILE", None)
        assert load_token(None) == "env_token"
    finally:
        os.environ.pop("OURA_PAT", None)


def test_load_token_from_explicit_path():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pat", delete=False) as f:
        f.write("explicit_token")
        f.flush()
        path = f.name
    try:
        os.environ.pop("OURA_PAT", None)
        os.environ.pop("OURA_PAT_FILE", None)
        assert load_token(path) == "explicit_token"
    finally:
        os.unlink(path)


def test_load_token_from_env_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pat", delete=False) as f:
        f.write("env_file_token")
        f.flush()
        path = f.name
    try:
        os.environ.pop("OURA_PAT", None)
        os.environ["OURA_PAT_FILE"] = path
        # DEFAULT_PAT_PATH is set at import time, so we must patch it
        with patch.object(auth_mod, "DEFAULT_PAT_PATH", Path(path)):
            assert load_token(None) == "env_file_token"
    finally:
        os.environ.pop("OURA_PAT_FILE", None)
        os.unlink(path)


def test_load_token_from_default_path():
    """Override DEFAULT_PAT_PATH directly (module-level var set at import time)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pat", delete=False) as f:
        f.write("default_token")
        f.flush()
        path = f.name
    try:
        os.environ.pop("OURA_PAT", None)
        os.environ.pop("OURA_PAT_FILE", None)
        with patch.object(auth_mod, "DEFAULT_PAT_PATH", Path(path)):
            assert load_token(None) == "default_token"
    finally:
        os.unlink(path)


def test_load_token_missing_file_exits():
    os.environ.pop("OURA_PAT", None)
    os.environ.pop("OURA_PAT_FILE", None)
    with patch.object(auth_mod, "DEFAULT_PAT_PATH", Path("/nonexistent/path/to/token")):
        with pytest.raises(SystemExit) as exc:
            load_token(None)
    assert "no PAT at" in str(exc.value.code)
    assert "/nonexistent/path/to/token" in str(exc.value.code)


def test_load_token_strips_whitespace():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pat", delete=False) as f:
        f.write("  token_with_spaces  \n")
        f.flush()
        path = f.name
    try:
        os.environ.pop("OURA_PAT", None)
        os.environ.pop("OURA_PAT_FILE", None)
        with patch.object(auth_mod, "DEFAULT_PAT_PATH", Path(path)):
            assert load_token(None) == "token_with_spaces"
    finally:
        os.unlink(path)
