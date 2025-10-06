import csv
import os
from datetime import datetime
from typing import Dict


class DataLogger:
    def __init__(self, prices_csv_path: str = "data/prices/crypto_prices.csv") -> None:
        self.prices_csv_path = prices_csv_path

    def _ensure_parent_dir(self) -> None:
        directory = os.path.dirname(self.prices_csv_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def save_price(self, prices_by_coin: Dict[str, float]) -> None:
        if not prices_by_coin:
            return
        self._ensure_parent_dir()
        file_exists = os.path.exists(self.prices_csv_path)
        with open(self.prices_csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["date", "coin", "price"])  # header
            today = datetime.utcnow().date().isoformat()
            for coin, price in prices_by_coin.items():
                writer.writerow([today, coin, float(price)])

    def upsert_history(self, coin: str, daily_prices: Dict[str, float]) -> None:
        """Merge historical daily prices into CSV (idempotent per date+coin)."""
        if not daily_prices:
            return
        self._ensure_parent_dir()
        # load existing rows
        rows = []
        existing = {}
        if os.path.exists(self.prices_csv_path):
            with open(self.prices_csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    rows.append([r["date"], r["coin"], r["price"]])
                    existing[(r["date"], r["coin"])] = float(r["price"]) if r["price"] else None
        # upsert
        for d, p in daily_prices.items():
            existing[(d, coin)] = float(p)
        # write back
        with open(self.prices_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "coin", "price"])  # header
            # collect all keys and write sorted by date
            all_keys = sorted(existing.keys(), key=lambda x: x[0])
            for (d, c) in all_keys:
                writer.writerow([d, c, existing[(d, c)]])
