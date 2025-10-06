import csv
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from alert_engine import AlertEngine


def write_sample_csv(path: str):
    today = date.today()
    rows = [
        ["date", "coin", "price"],
        [(today - timedelta(days=1)).isoformat(), "bitcoin", 100.0],
        [today.isoformat(), "bitcoin", 85.0],  # 15% drop
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows(rows)


def test_alert_on_drop(tmp_path):
    csv_path = tmp_path / "prices.csv"
    alerts_path = tmp_path / "alerts.json"
    write_sample_csv(str(csv_path))

    engine = AlertEngine(prices_csv_path=str(csv_path), alerts_json_path=str(alerts_path))
    alert = engine.check_fluctuation("bitcoin", threshold=0.10)

    assert alert is not None
    assert alerts_path.exists()
    payload = json.loads(alerts_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list) and len(payload) == 1
    assert payload[0]["coin"] == "bitcoin"
