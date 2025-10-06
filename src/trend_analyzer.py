import os
from typing import Dict, Any

# Force non-GUI backend for headless servers (e.g., Render)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


class TrendAnalyzer:
    def __init__(self, prices_csv_path: str = "data/prices/crypto_prices.csv", plots_dir: str = "data/plots") -> None:
        self.prices_csv_path = prices_csv_path
        self.plots_dir = plots_dir

    def _load_coin_df(self, coin: str) -> pd.DataFrame:
        df = pd.read_csv(self.prices_csv_path)
        if df.empty:
            return df
        df = df[df["coin"] == coin].copy()
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"])  # parse dates
        # in case multiple entries per day, keep the last
        df = df.sort_values(["date"]).drop_duplicates(subset=["date"], keep="last")
        df.set_index("date", inplace=True)
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        return df

    def plot_trend(self, coin: str) -> str:
        if not os.path.exists(self.prices_csv_path):
            raise FileNotFoundError(self.prices_csv_path)
        df = self._load_coin_df(coin)
        if df.empty:
            raise ValueError(f"No data for coin: {coin}")
        df["ma7"] = df["price"].rolling(window=7, min_periods=1).mean()

        os.makedirs(self.plots_dir, exist_ok=True)
        out_path = os.path.join(self.plots_dir, f"{coin}_trend.png")

        plt.figure(figsize=(8, 4))
        plt.plot(df.index, df["price"], label="Price", linewidth=1.5)
        plt.plot(df.index, df["ma7"], label="7d MA", linewidth=2)
        plt.title(f"{coin} - Price & 7d Moving Average")
        plt.xlabel("Date")
        plt.ylabel("USD")
        plt.legend()
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()
        return out_path

    def get_series(self, coin: str, days: int = 30) -> Dict[str, Any]:
        """Return time-series for Chart.js: labels and datasets (price, ma7)."""
        df = self._load_coin_df(coin)
        if df.empty:
            return {"labels": [], "price": [], "ma7": []}
        df = df.tail(days)
        df["ma7"] = df["price"].rolling(window=7, min_periods=1).mean()
        labels = [d.strftime("%Y-%m-%d") for d in df.index]
        return {
            "labels": labels,
            "price": [round(float(x), 4) if pd.notna(x) else None for x in df["price"].tolist()],
            "ma7": [round(float(x), 4) if pd.notna(x) else None for x in df["ma7"].tolist()],
        }

    def get_kpis(self, coin: str) -> Dict[str, Any]:
        """Return simple KPIs: last price and 1-day change percent."""
        df = self._load_coin_df(coin)
        if df.empty or len(df) == 0:
            return {"last_price": None, "change_pct_1d": None}
        prices = df["price"].dropna()
        if prices.empty:
            return {"last_price": None, "change_pct_1d": None}
        last_price = float(prices.iloc[-1])
        if len(prices) < 2:
            return {"last_price": last_price, "change_pct_1d": None}
        prev = float(prices.iloc[-2])
        change_pct = None if prev == 0 else (last_price - prev) / prev
        return {"last_price": last_price, "change_pct_1d": change_pct}
