"""Output formatters: pretty, JSON, CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import Any


def as_json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


def as_csv(data: Any) -> str:
    if not (isinstance(data, dict) and isinstance(data.get("data"), list)):
        raise ValueError("CSV requires a {'data': [...]} payload")
    items = data["data"]
    if not items:
        return ""
    flat = []
    for e in items:
        row = {}
        for k, v in e.items():
            row[k] = json.dumps(v, default=str) if isinstance(v, (dict, list)) else v
        flat.append(row)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=sorted({k for r in flat for k in r}))
    writer.writeheader()
    writer.writerows(flat)
    return buf.getvalue()


def as_pretty(data: Any) -> str:
    """Human-readable ▸ DATE  score=N  / k: v lines for list payloads."""
    if not (isinstance(data, dict) and isinstance(data.get("data"), list)):
        return json.dumps(data, indent=2, default=str)
    items = data["data"]
    if not items:
        return "(no rows)"
    out = []
    for e in items:
        day = (
            e.get("day")
            or e.get("date")
            or (e.get("bedtime_start") or "")[:10]
            or (e.get("timestamp") or "")[:10]
        )
        score = e.get("score")
        head = f"▸ {day}"
        if score is not None:
            head += f"  score={score}"
        out.append(head)
        for k, v in e.items():
            if k in {"id", "day", "date", "score", "timestamp"}:
                continue
            if isinstance(v, (dict, list)):
                v_str = json.dumps(v, default=str)
                if len(v_str) > 120:
                    v_str = v_str[:117] + "..."
                out.append(f"    {k}: {v_str}")
            else:
                out.append(f"    {k}: {v}")
        out.append("")
    return "\n".join(out)
