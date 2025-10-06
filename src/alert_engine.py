import json
import os
from datetime import datetime
from typing import Dict, Optional

import pandas as pd


class AlertEngine:
    def __init__(
        self,
        prices_csv_path: str = "data/prices/crypto_prices.csv",
        alerts_json_path: str = "data/alerts/price_alerts.json",
    ) -> None:
        self.prices_csv_path = prices_csv_path
        self.alerts_json_path = alerts_json_path

    def _ensure_parent_dir(self) -> None:
        directory = os.path.dirname(self.alerts_json_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _load_alerts(self) -> list:
        if not os.path.exists(self.alerts_json_path):
            return []
        with open(self.alerts_json_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []

    def _save_alerts(self, alerts: list) -> None:
        self._ensure_parent_dir()
        with open(self.alerts_json_path, "w", encoding="utf-8") as f:
            json.dump(alerts, f, ensure_ascii=False, indent=2)

    def _load_coin_series(self, coin: str) -> pd.Series:
        df = pd.read_csv(self.prices_csv_path)
        if df.empty:
            return pd.Series(dtype=float)
        df = df[df["coin"] == coin].copy()
        if df.empty:
            return pd.Series(dtype=float)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")
        return pd.to_numeric(df["price"], errors="coerce")

    def check_fluctuation(self, coin: str, threshold: float = 0.10) -> Optional[Dict]:
        if not os.path.exists(self.prices_csv_path):
            return None
        series = self._load_coin_series(coin)
        if series.empty or len(series) < 2:
            return None
        prev, curr = float(series.iloc[-2]), float(series.iloc[-1])
        if prev <= 0:
            return None
        drop_pct = (prev - curr) / prev
        if drop_pct >= threshold:
            alert = {
                "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "coin": coin,
                "previous_price": prev,
                "current_price": curr,
                "drop_pct": round(drop_pct, 4),
            }
            alerts = self._load_alerts()
            alerts.append(alert)
            self._save_alerts(alerts)
            return alert
        return None
