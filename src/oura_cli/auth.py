"""Token loading helpers."""
from __future__ import annotations

import os
import sys
from pathlib import Path

DEFAULT_PAT_PATH = Path(os.environ.get("OURA_PAT_FILE", "~/.oura_pat")).expanduser()


def load_token(explicit_path: str | None = None) -> str:
    """Resolve the Oura PAT from (in order):

    1. $OURA_PAT env var (raw token string)
    2. --token CLI flag / explicit path argument
    3. $OURA_PAT_FILE env var (path)
    4. ~/.oura_pat
    """
    env_token = os.environ.get("OURA_PAT")
    if env_token:
        return env_token.strip()

    path = Path(explicit_path).expanduser() if explicit_path else DEFAULT_PAT_PATH
    if not path.exists():
        sys.exit(
            f"error: no PAT at {path} and $OURA_PAT not set.\n"
            f"       Get one at https://cloud.ouraring.com/personal-access-tokens\n"
            f"       then:  echo 'YOUR_TOKEN' > {path} && chmod 600 {path}"
        )
    return path.read_text().strip()
