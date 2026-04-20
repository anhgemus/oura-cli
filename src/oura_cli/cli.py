"""Argparse entry point for the `oura` command."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

from .__version__ import __version__
from .auth import load_token
from .client import KNOWN_ENDPOINTS, OuraClient
from .formatters import as_csv, as_json, as_pretty
from .summary import build_summary, render_summary

# ── date helpers ─────────────────────────────────────────────────────────────

def daterange(days: int, explicit_date: str | None) -> tuple[str, str]:
    if explicit_date:
        return explicit_date, explicit_date
    today = datetime.now().date()
    start = today - timedelta(days=max(0, days - 1))
    return start.isoformat(), today.isoformat()


def hours_range(hours: int) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=hours)
    fmt = "%Y-%m-%dT%H:%M:%S+00:00"
    return start.strftime(fmt), now.strftime(fmt)


# ── output ───────────────────────────────────────────────────────────────────

def write_output(data, args) -> None:
    if getattr(args, "json", False):
        print(as_json(data))
    elif getattr(args, "csv", False):
        print(as_csv(data))
    else:
        print(as_pretty(data))


def make_client(args) -> OuraClient:
    token = load_token(args.token)
    verbose_fn = (lambda u: print(f"GET {u}", file=sys.stderr)) if args.verbose else None
    return OuraClient(token, verbose_fn=verbose_fn)


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_dated(args, endpoint: str) -> None:
    client = make_client(args)
    start, end = daterange(args.days, args.date)
    data = client.get(endpoint, {"start_date": start, "end_date": end})
    write_output(data, args)


def cmd_hr(args) -> None:
    client = make_client(args)
    if args.start and args.end:
        s, e = args.start, args.end
    else:
        s, e = hours_range(args.hours)
    data = client.get("heartrate", {"start_datetime": s, "end_datetime": e})
    write_output(data, args)


def cmd_singleton(args, endpoint: str) -> None:
    client = make_client(args)
    write_output(client.get(endpoint), args)


def cmd_summary(args) -> None:
    client = make_client(args)
    target = args.date or (datetime.now().date() - timedelta(days=1)).isoformat()
    data = build_summary(client, target)
    if args.json:
        print(as_json(data))
    else:
        print(render_summary(data))


def cmd_export(args) -> None:
    client = make_client(args)
    start, end = daterange(args.days, None)
    out_dir = args.out or f"./oura-export-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(out_dir, exist_ok=True)

    dated = [ep for ep in KNOWN_ENDPOINTS
             if ep not in {"personal_info", "heartrate", "interbeat_interval"}]

    for ep in dated:
        print(f"  fetching {ep}...", file=sys.stderr)
        try:
            data = client.get(ep, {"start_date": start, "end_date": end})
        except Exception as e:  # noqa: BLE001
            data = {"error": str(e)}
        with open(os.path.join(out_dir, f"{ep}.json"), "w") as f:
            json.dump(data, f, indent=2, default=str)

    print("  fetching personal_info...", file=sys.stderr)
    with open(os.path.join(out_dir, "personal_info.json"), "w") as f:
        json.dump(client.get("personal_info"), f, indent=2, default=str)

    if args.include_hr:
        print("  fetching heartrate...", file=sys.stderr)
        data = client.get("heartrate", {
            "start_datetime": f"{start}T00:00:00+00:00",
            "end_datetime":   f"{end}T23:59:59+00:00",
        })
        with open(os.path.join(out_dir, "heartrate.json"), "w") as f:
            json.dump(data, f, indent=2, default=str)

    if args.include_ibi:
        print("  fetching interbeat_interval...", file=sys.stderr)
        data = client.get("interbeat_interval", {
            "start_datetime": f"{start}T00:00:00+00:00",
            "end_datetime":   f"{end}T23:59:59+00:00",
        })
        with open(os.path.join(out_dir, "interbeat_interval.json"), "w") as f:
            json.dump(data, f, indent=2, default=str)

    print(f"✓ exported {start}..{end} → {out_dir}")


def cmd_get(args) -> None:
    client = make_client(args)
    params: dict[str, str] = {}
    if args.start:
        params["start_date"] = args.start
    if args.end:
        params["end_date"] = args.end
    if args.days and not args.start:
        s, e = daterange(args.days, None)
        params["start_date"], params["end_date"] = s, e
    for kv in args.param or []:
        k, _, v = kv.partition("=")
        # Don't allow --param to shadow --start/--end
        if k in {"start_date", "end_date"} and (args.start or args.end):
            sys.stderr.write(
                f"warning: --param {k}={v} ignored (conflicts with --start/--end)\n"
            )
            continue
        params[k] = v
    write_output(client.get(args.endpoint, params), args)


def cmd_endpoints(args) -> None:
    for ep in KNOWN_ENDPOINTS:
        print(ep)


# ── parser ───────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="oura",
        description="Oura Ring v2 REST CLI (Personal Access Token).",
    )
    p.add_argument("--version", action="version", version=f"oura-cli {__version__}")
    p.add_argument("--token", help="PAT file path (default ~/.oura_pat or $OURA_PAT_FILE)")
    p.add_argument("-v", "--verbose", action="store_true", help="print request URLs to stderr")

    sub = p.add_subparsers(dest="cmd", required=True)

    def add_dated(name: str, endpoint: str, help_: str) -> None:
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("--days", type=int, default=7)
        sp.add_argument("--date", help="specific day YYYY-MM-DD")
        sp.add_argument("--json", action="store_true")
        sp.add_argument("--csv", action="store_true")
        sp.set_defaults(func=lambda a, ep=endpoint: cmd_dated(a, ep))

    add_dated("sleep",       "sleep",                    "detailed sleep sessions")
    add_dated("daily-sleep", "daily_sleep",              "daily sleep summary (scores)")
    add_dated("readiness",   "daily_readiness",          "daily readiness")
    add_dated("activity",    "daily_activity",           "daily activity")
    add_dated("stress",      "daily_stress",             "daily stress")
    add_dated("spo2",        "daily_spo2",               "daily SpO2")
    add_dated("workouts",    "workout",                  "workouts")
    add_dated("sessions",    "session",                  "meditation/session logs")
    add_dated("tags",        "enhanced_tag",             "enhanced tags")
    add_dated("vo2",         "vo2_max",                  "VO2 max (may 404)")
    add_dated("resilience",  "daily_resilience",         "daily resilience")
    add_dated("cardio-age",  "daily_cardiovascular_age", "cardiovascular age")
    add_dated("sleep-time",  "sleep_time",               "sleep time recommendations")
    add_dated("rest-mode",   "rest_mode_period",         "rest mode periods")

    sp = sub.add_parser("hr", help="raw heart rate samples (default last 24h)")
    sp.add_argument("--hours", type=int, default=24)
    sp.add_argument("--start", help="ISO start datetime")
    sp.add_argument("--end",   help="ISO end datetime")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--csv",  action="store_true")
    sp.set_defaults(func=cmd_hr)

    sp = sub.add_parser("ring", help="ring configuration")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=lambda a: cmd_singleton(a, "ring_configuration"))

    sp = sub.add_parser("me", help="personal info")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=lambda a: cmd_singleton(a, "personal_info"))

    sp = sub.add_parser("summary", help="one-glance daily summary (default yesterday)")
    sp.add_argument("--date")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_summary)

    sp = sub.add_parser("export", help="dump every endpoint to JSON files")
    sp.add_argument("--days", type=int, default=7)
    sp.add_argument("--out", help="output directory")
    sp.add_argument("--include-hr", action="store_true", help="also dump heartrate (big)")
    sp.add_argument("--include-ibi", action="store_true", help="also dump interbeat_interval (huge)")
    sp.set_defaults(func=cmd_export)

    sp = sub.add_parser("get", help="low-level: hit any endpoint")
    sp.add_argument("endpoint")
    sp.add_argument("--start")
    sp.add_argument("--end")
    sp.add_argument("--days", type=int)
    sp.add_argument("--param", action="append", help="extra k=v params (repeatable)")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--csv", action="store_true")
    sp.set_defaults(func=cmd_get)

    sp = sub.add_parser("endpoints", help="list known endpoints")
    sp.set_defaults(func=cmd_endpoints)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
