from oura_cli.formatters import as_csv, as_json, as_pretty


def test_json_serializes():
    out = as_json({"data": [{"day": "2024-11-19", "score": 80}]})
    assert '"score": 80' in out


def test_csv_flattens_nested():
    out = as_csv({"data": [{"day": "d", "nested": {"a": 1}}]})
    assert "day" in out and "nested" in out
    # CSV escapes " as ""; ensure the nested JSON made it in
    assert '""a""' in out


def test_csv_empty():
    assert as_csv({"data": []}) == ""


def test_pretty_handles_empty():
    assert as_pretty({"data": []}) == "(no rows)"


def test_pretty_shows_score_header():
    out = as_pretty({"data": [{"day": "2024-11-19", "score": 80, "foo": "bar"}]})
    assert "▸ 2024-11-19" in out
    assert "score=80" in out
    assert "foo: bar" in out
