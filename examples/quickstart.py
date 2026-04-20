"""Library usage — fetch the last 7 nights of sleep and print key stats."""
import os
from pathlib import Path

from oura_cli import OuraClient

token = os.environ.get("OURA_PAT") or Path("~/.oura_pat").expanduser().read_text().strip()
client = OuraClient(token=token)

nights = [e for e in client.dated("sleep", "2024-11-12", "2024-11-19")
          if e.get("type") == "long_sleep"]

for n in nights:
    print(f"{n['day']}  eff={n['efficiency']}%  HR={n['average_heart_rate']}  HRV={n['average_hrv']}")
