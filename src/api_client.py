import json
import os
from typing import Dict, List

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class PriceFetcher:
    def __init__(self, base_url: str = "https://api.coingecko.com/api/v3", use_mock: bool = False, mock_path: str = "data/samples/mock_prices.json") -> None:
        self.base_url = base_url.rstrip("/")
        self.use_mock = use_mock
        self.mock_path = mock_path

    def _read_mock(self, coins: List[str]) -> Dict[str, float]:
        if not os.path.exists(self.mock_path):
            # minimal default mock if missing
            return {coin: 0.0 for coin in coins}
        with open(self.mock_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return {coin: float(payload.get(coin, 0.0)) for coin in coins}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    def _fetch_live(self, coins: List[str]) -> Dict[str, float]:
        ids = ",".join(coins)
        url = f"{self.base_url}/simple/price"
        resp = requests.get(url, params={"ids": ids, "vs_currencies": "usd"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()  # e.g., {"bitcoin": {"usd": 12345.67}}
        return {coin: float(data.get(coin, {}).get("usd", 0.0)) for coin in coins}

    def fetch_prices(self, coins: List[str]) -> Dict[str, float]:
        if not coins:
            return {}
        if self.use_mock:
            return self._read_mock(coins)
        try:
            return self._fetch_live(coins)
        except Exception:
            # fallback to mock on error
            return self._read_mock(coins)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    def fetch_market_chart(self, coin: str, days: int = 7) -> Dict[str, float]:
        """
        Fetch historical prices for coin over N days.
        Returns dict: {date_iso: price} keeping the last price per day.
        """
        if self.use_mock:
            # If in mock mode, synthesize a flat history from mock value
            mock = self._read_mock([coin]).get(coin, 0.0)
            from datetime import date, timedelta
            out = {}
            for i in reversed(range(days)):
                d = (date.today() - timedelta(days=i)).isoformat()
                out[d] = mock
            return out
        url = f"{self.base_url}/coins/{coin}/market_chart"
        resp = requests.get(url, params={"vs_currency": "usd", "days": str(days)}, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        prices = payload.get("prices", [])  # list of [timestamp_ms, price]
        from datetime import datetime
        per_day: Dict[str, float] = {}
        for ts_ms, price in prices:
            d = datetime.utcfromtimestamp(ts_ms / 1000.0).date().isoformat()
            per_day[d] = float(price)  # keep last of the day
        return per_day
