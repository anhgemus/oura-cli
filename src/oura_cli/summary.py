"""One-glance daily summary — joins data from multiple endpoints."""
from __future__ import annotations

from datetime import date, timedelta

from .client import OuraClient


def _pick(items: list[dict], target: str) -> dict:
    """Prefer exact-day match, else the latest entry with day ≤ target."""
    by_day: dict[str, dict] = {}
    for e in items:
        day = (
            e.get("day")
            or e.get("date")
            or (e.get("bedtime_end") or e.get("bedtime_start") or "")[:10]
        )
        if day:
            by_day[day] = e
    if target in by_day:
        return by_day[target]
    candidates = sorted(d for d in by_day if d <= target)
    return by_day[candidates[-1]] if candidates else {}


def build_summary(client: OuraClient, target: str) -> dict:
    """Return a dict with the key metrics for `target` (YYYY-MM-DD).

    Widens the query window because endpoints lag by 1+ days — we want the
    most recent available data, not blanks when today isn't synced.
    """
    t = date.fromisoformat(target)
    start = (t - timedelta(days=3)).isoformat()
    end = (t + timedelta(days=1)).isoformat()

    r  = _pick(client.dated("daily_readiness", start, end), target)
    s  = _pick(client.dated("daily_sleep",     start, end), target)
    a  = _pick(client.dated("daily_activity",  start, end), target)
    st = _pick(client.dated("daily_stress",    start, end), target)
    sp = _pick(client.dated("daily_spo2",      start, end), target)

    # Raw sleep: filter long_sleep, sort, pick exact day else latest
    long_sleeps = [e for e in client.dated("sleep", start, end) if e.get("type") == "long_sleep"]
    long_sleeps.sort(key=lambda e: (e.get("day") or (e.get("bedtime_end") or "")[:10] or ""))
    exact = [e for e in long_sleeps if e.get("day") == target
             or (e.get("bedtime_end") or "")[:10] == target]
    ls = exact[-1] if exact else (long_sleeps[-1] if long_sleeps else {})

    spo2_avg = None
    if isinstance(sp.get("spo2_percentage"), dict):
        spo2_avg = sp["spo2_percentage"].get("average")

    return {
        "target": target,
        "readiness": {
            "score": r.get("score"),
            "temperature_deviation": r.get("temperature_deviation"),
        },
        "sleep": {
            "score": s.get("score"),
            "efficiency": ls.get("efficiency"),
            "duration_s": ls.get("total_sleep_duration"),
            "avg_heart_rate": ls.get("average_heart_rate"),
            "lowest_heart_rate": ls.get("lowest_heart_rate"),
            "avg_hrv": ls.get("average_hrv"),
            "avg_breath": ls.get("average_breath"),
            "bedtime_start": ls.get("bedtime_start"),
            "bedtime_end": ls.get("bedtime_end"),
        },
        "activity": {
            "score": a.get("score"),
            "steps": a.get("steps"),
            "active_calories": a.get("active_calories"),
            "total_calories": a.get("total_calories"),
        },
        "stress": {
            "day_summary": st.get("day_summary"),
            "stress_high_s": st.get("stress_high"),
            "recovery_high_s": st.get("recovery_high"),
        },
        "spo2": {"average_percentage": spo2_avg},
    }


def render_summary(summary: dict) -> str:
    s  = summary["sleep"]
    r  = summary["readiness"]
    a  = summary["activity"]
    st = summary["stress"]
    sp = summary["spo2"]
    out = []
    out.append(f"═══ Oura — {summary['target']} ═══")
    out.append(f"Readiness   {r.get('score','—'):>4}   temp Δ {r.get('temperature_deviation','—')}")
    base = f"Sleep       {s.get('score','—'):>4}   eff {s.get('efficiency','—')}%"
    if s.get("duration_s"):
        base += f"   {(s['duration_s']/3600):.2f}h"
    out.append(base)
    out.append(f"           HR {s.get('avg_heart_rate','—')} (low {s.get('lowest_heart_rate','—')})"
               f"  HRV {s.get('avg_hrv','—')}  br {s.get('avg_breath','—')}")
    out.append(f"           bed {(s.get('bedtime_start') or '—')[:16]} → wake {(s.get('bedtime_end') or '—')[:16]}")
    out.append(f"Activity    {a.get('score','—'):>4}   steps {a.get('steps','—')}"
               f"   cal {a.get('active_calories','—')}/{a.get('total_calories','—')}")
    out.append(f"Stress      {st.get('day_summary','—')}   high {st.get('stress_high_s','—')}s"
               f"  recovery {st.get('recovery_high_s','—')}s")
    out.append(f"SpO2        {sp.get('average_percentage','—')}%")
    return "\n".join(out)
