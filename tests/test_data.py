import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from data_logger import DataLogger


def test_save_price_creates_csv(tmp_path):
    csv_path = tmp_path / "prices.csv"
    logger = DataLogger(prices_csv_path=str(csv_path))
    logger.save_price({"bitcoin": 123.45})

    assert csv_path.exists()
    rows = list(csv.reader(open(csv_path, newline="", encoding="utf-8")))
    assert rows[0] == ["date", "coin", "price"]
    assert rows[1][1] == "bitcoin"
    assert float(rows[1][2]) == 123.45
