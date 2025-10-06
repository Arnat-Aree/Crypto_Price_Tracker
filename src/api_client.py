import json
import os
from typing import Dict, List

import requests
from tenacity import retry, stop_after_attempt, wait_exponential
import math


class PriceFetcher:
    def __init__(
        self,
        base_url: str = "https://api.coingecko.com/api/v3",
        use_mock: bool = False,
        mock_path: str = "data/samples/mock_prices.json",
    ) -> None:
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    )
    def _fetch_live(self, coins: List[str], vs_currency: str) -> Dict[str, float]:
        ids = ",".join(coins)
        url = f"{self.base_url}/simple/price"
        resp = requests.get(
            url,
            params={"ids": ids, "vs_currencies": vs_currency},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()  # e.g., {"bitcoin": {"usd": 12345.67}}
        return {
            coin: float(data.get(coin, {}).get(vs_currency, 0.0))
            for coin in coins
        }

    def fetch_prices(self, coins: List[str], currency: str = "usd") -> Dict[str, float]:
        if not coins:
            return {}
        vs_currency = currency.lower()
        if self.use_mock:
            base = self._read_mock(coins)
            if vs_currency == "usd":
                return base
            # simple mock conversion (approx.): USD->THB ~ 36
            rate = 36.0 if vs_currency == "thb" else 1.0
            return {k: float(v) * rate for k, v in base.items()}
        try:
            return self._fetch_live(coins, vs_currency)
        except Exception:
            # fallback to mock on error
            base = self._read_mock(coins)
            if vs_currency == "usd":
                return base
            rate = 36.0 if vs_currency == "thb" else 1.0
            return {k: float(v) * rate for k, v in base.items()}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    def fetch_market_chart(self, coin: str, days: int = 7, currency: str = "usd") -> Dict[str, float]:
        """
        Fetch historical prices for coin over N days.
        Returns dict: {date_iso: price} keeping the last price per day.
        """
        if self.use_mock:
            # If in mock mode, synthesize a varied history from mock value (non-flat)
            mock = self._read_mock([coin]).get(coin, 0.0)
            base = mock or (60000.0 if coin == "bitcoin" else 3000.0 if coin == "ethereum" else 100.0)
            from datetime import date, timedelta
            out = {}
            seed = (sum(ord(c) for c in coin) % 100) / 50.0
            for i in reversed(range(days)):
                d = (date.today() - timedelta(days=i)).isoformat()
                # +/-2% smooth oscillation
                factor = 1.0 + 0.02 * math.sin(i * 0.7 + seed)
                out[d] = base * factor
            return out
        try:
            url = f"{self.base_url}/coins/{coin}/market_chart"
            resp = requests.get(url, params={"vs_currency": currency, "days": str(days)}, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
            prices = payload.get("prices", [])  # list of [timestamp_ms, price]
            from datetime import datetime
            per_day: Dict[str, float] = {}
            for ts_ms, price in prices:
                d = datetime.utcfromtimestamp(ts_ms / 1000.0).date().isoformat()
                per_day[d] = float(price)  # keep last of the day
            if per_day:
                return per_day
        except Exception:
            pass
        # Fallback: synthesize varied history to avoid flat UI
        mock = self._read_mock([coin]).get(coin, 0.0)
        base = mock or (60000.0 if coin == "bitcoin" else 3000.0 if coin == "ethereum" else 100.0)
        from datetime import date, timedelta
        out = {}
        seed = (sum(ord(c) for c in coin) % 100) / 50.0
        for i in reversed(range(days)):
            d = (date.today() - timedelta(days=i)).isoformat()
            factor = 1.0 + 0.02 * math.sin(i * 0.7 + seed)
            out[d] = base * factor
        return out

    def get_usd_to(self, currency: str = "usd") -> float:
        """Return conversion factor to convert USD->currency. 1 for USD.
        Uses USDT (tether) as proxy when live; mock falls back to ~36 for THB.
        """
        cur = currency.lower()
        if cur == "usd":
            return 1.0
        if self.use_mock:
            return 36.0 if cur == "thb" else 1.0
        try:
            url = f"{self.base_url}/simple/price"
            resp = requests.get(url, params={"ids": "tether", "vs_currencies": cur}, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            return float(data.get("tether", {}).get(cur, 1.0)) or 1.0
        except Exception:
            return 36.0 if cur == "thb" else 1.0
