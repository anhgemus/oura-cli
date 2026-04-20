"""Summary logic tests — uses a stub client."""
from __future__ import annotations

from oura_cli.summary import build_summary, render_summary


class _StubClient:
    def __init__(self, responses: dict[str, list[dict]]):
        self._responses = responses
    def dated(self, endpoint, start, end):
        return self._responses.get(endpoint, [])
    def get(self, endpoint, params=None):
        return {"data": self._responses.get(endpoint, [])}


def test_summary_prefers_exact_day():
    stub = _StubClient({
        "daily_readiness": [
            {"day": "2024-11-18", "score": 70, "temperature_deviation": -0.3},
            {"day": "2024-11-19", "score": 81, "temperature_deviation": -0.54},
        ],
        "daily_sleep": [{"day": "2024-11-19", "score": 78}],
        "daily_activity": [{"day": "2024-11-19", "score": 68, "steps": 5358,
                             "active_calories": 267, "total_calories": 2236}],
        "daily_stress": [{"day": "2024-11-19", "day_summary": "normal",
                           "stress_high": 8100, "recovery_high": 9900}],
        "daily_spo2": [{"day": "2024-11-19", "spo2_percentage": {"average": 95.1}}],
        "sleep": [{
            "day": "2024-11-19", "type": "long_sleep",
            "efficiency": 90, "total_sleep_duration": 22248,
            "average_heart_rate": 60.5, "lowest_heart_rate": 55,
            "average_hrv": 78, "average_breath": 13.875,
            "bedtime_start": "2024-11-18T23:47:00+00:00",
            "bedtime_end":   "2024-11-19T06:40:00+00:00",
        }],
    })
    s = build_summary(stub, "2024-11-19")
    assert s["readiness"]["score"] == 81
    assert s["sleep"]["score"] == 78
    assert s["sleep"]["efficiency"] == 90
    assert s["activity"]["steps"] == 5358
    assert s["spo2"]["average_percentage"] == 95.1


def test_summary_falls_back_to_latest_available():
    stub = _StubClient({
        "daily_readiness": [{"day": "2024-11-18", "score": 70}],
        "daily_sleep": [],
        "daily_activity": [],
        "daily_stress": [],
        "daily_spo2": [],
        "sleep": [],
    })
    s = build_summary(stub, "2024-11-19")
    assert s["readiness"]["score"] == 70  # fell back to Nov 18


def test_summary_skips_naps():
    stub = _StubClient({
        "daily_readiness": [], "daily_sleep": [], "daily_activity": [],
        "daily_stress": [], "daily_spo2": [],
        "sleep": [
            {"day": "2024-11-19", "type": "sleep", "efficiency": 99, "average_hrv": 200},  # nap
            {"day": "2024-11-19", "type": "long_sleep", "efficiency": 85, "average_hrv": 72},
        ],
    })
    s = build_summary(stub, "2024-11-19")
    assert s["sleep"]["efficiency"] == 85
    assert s["sleep"]["avg_hrv"] == 72


def test_render_summary_handles_missing_data():
    # Should not raise on all-None payload
    out = render_summary({
        "target": "2024-11-19",
        "readiness": {}, "sleep": {}, "activity": {},
        "stress": {}, "spo2": {},
    })
    assert "Oura — 2024-11-19" in out
