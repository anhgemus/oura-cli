# oura-cli

A simple, dependency-free CLI and Python client for the [Oura Ring v2 REST API](https://cloud.ouraring.com/v2/docs), using Personal Access Token auth.

- **Zero runtime dependencies.** Pure Python stdlib — no `requests`, no `pydantic`, no surprises.
- **Typed subcommands** for every documented endpoint (`sleep`, `readiness`, `activity`, `workouts`, …) plus a low-level `get` escape hatch.
- **Auto-paginates** `next_token` across all list endpoints.
- **Smart daily summary** that falls back gracefully when today's data isn't synced yet.
- **JSON, CSV, and pretty text** output — works with `jq`, spreadsheets, and the terminal.

## Install

```bash
pip install oura-cli
# or from source:
git clone https://github.com/anhdinh/oura-cli && cd oura-cli && pip install -e .
```

Python 3.9+.

## Authenticate

1. Get a Personal Access Token from https://cloud.ouraring.com/personal-access-tokens
2. Save it:

```bash
echo "YOUR_TOKEN" > ~/.oura_pat
chmod 600 ~/.oura_pat
```

Alternatively, set `OURA_PAT=<token>` or `OURA_PAT_FILE=/path/to/token` as environment variables, or pass `--token /path/to/file`.

## Quick tour

```bash
# one-glance digest for yesterday (handles sync lag gracefully)
oura summary

# recent sleep with full details
oura sleep --days 7

# yesterday's activity as JSON, piped to jq
oura activity --date 2024-11-19 --json | jq '.data[0].steps'

# raw heart-rate samples from the last 6 hours
oura hr --hours 6 --json

# bulk export every endpoint for a 30-day window
oura export --days 30 --out ./my-oura-archive

# low-level: hit any endpoint by name
oura get daily_spo2 --days 14 --json
oura get heartrate --param start_datetime=2024-11-19T00:00:00+00:00 \
                   --param end_datetime=2024-11-19T06:00:00+00:00 --json

# all known endpoints
oura endpoints
```

Example `summary` output:

```
═══ Oura — 2024-11-19 ═══
Readiness     81   temp Δ -0.54
Sleep         78   eff 90%   6.18h
           HR 60.5 (low 55)  HRV 78  br 13.875
           bed 2024-11-18T23:47 → wake 2024-11-19T06:40
Activity      68   steps 5358   cal 267/2236
Stress      normal   high 8100s  recovery 9900s
SpO2        95.106%
```

## Use as a library

```python
from oura_cli import OuraClient

client = OuraClient(token="YOUR_PAT")
sleep = client.dated("sleep", "2024-11-12", "2024-11-19")
long_nights = [e for e in sleep if e.get("type") == "long_sleep"]
for night in long_nights:
    print(night["day"], night["efficiency"], night["average_hrv"])
```

See [`examples/`](examples/) for more.

## Commands

| Command | What it does |
|---|---|
| `summary [--date]` | Join readiness / sleep / activity / stress / spo2 for a single day |
| `sleep` | Detailed sleep sessions (filter on `type == "long_sleep"`) |
| `daily-sleep` | Summary sleep scores |
| `readiness` | Daily readiness |
| `activity` | Daily activity |
| `stress` | Daily stress |
| `spo2` | Daily SpO2 |
| `workouts` | Workouts |
| `sessions` | Meditation / session logs |
| `tags` | Enhanced tags |
| `vo2` | VO2 max (404s on some subscriptions) |
| `resilience` | Daily resilience |
| `cardio-age` | Cardiovascular age |
| `sleep-time` | Sleep timing recommendations |
| `rest-mode` | Rest mode periods |
| `hr` | Raw heart rate samples (datetime window) |
| `ring` | Ring configuration |
| `me` | Personal info |
| `export` | Dump every endpoint to JSON files |
| `get <endpoint>` | Low-level request to any endpoint |
| `endpoints` | List known endpoints |

Most list commands accept:
- `--days N` (default 7) or `--date YYYY-MM-DD`
- `--json` — raw JSON
- `--csv` — flat CSV (nested fields serialized as JSON strings)
- default: human-readable pretty output

Global flags: `--token PATH`, `-v/--verbose` (prints each request URL to stderr), `--version`.

## Gotchas (the API has sharp edges)

- **Only ~6 days of data via the API.** Oura retention is short regardless of query range. For anything older, request a full export from the Oura mobile app (GDPR export).
- **Today is usually not synced yet.** `oura summary` widens its window and falls back to the latest day ≤ target so you still get numbers; single-day queries on `--date $(date +%F)` will often be empty.
- **`contributors.resting_heart_rate` is a 0–100 score, not BPM.** For actual BPM use `sleep.lowest_heart_rate` or `sleep.average_heart_rate`.
- **Readiness numerics live on raw `sleep`**, not `daily_readiness`. Join by `day`.
- **Filter `sleep` by `type == "long_sleep"`** to get the main nighttime session (skips naps).
- **`heartrate` uses `start_datetime` / `end_datetime` (ISO 8601)**, not plain dates. Keep the window ≤ 48h to avoid 400s.
- **`vo2_max` may return 404** — subscription/ring-model gated.
- **Rate limits (429) exist** — avoid hammering; the client currently does not auto-retry.

## Development

```bash
git clone https://github.com/anhdinh/oura-cli
cd oura-cli
pip install -e '.[dev]'
pytest
ruff check src tests
```

Releasing:

```bash
# bump src/oura_cli/__version__.py, then:
python -m build
python -m twine upload dist/*
```

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

Not affiliated with Oura Health Oy. "Oura" is a trademark of its owner.
