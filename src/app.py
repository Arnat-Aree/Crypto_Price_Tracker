import argparse
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from api_client import PriceFetcher
from data_logger import DataLogger
from trend_analyzer import TrendAnalyzer
from alert_engine import AlertEngine


def ensure_dirs(paths):
    for path in paths:
        directory = path if os.path.splitext(path)[1] == '' else os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


def parse_env():
    load_dotenv()
    base_url = os.getenv("API_BASE_URL", "https://api.coingecko.com/api/v3")
    use_mock = os.getenv("USE_MOCK", "false").lower() == "true"
    coins = [c.strip() for c in os.getenv("COINS", "bitcoin,ethereum").split(",") if c.strip()]
    prices_csv = os.getenv("PRICES_CSV", "data/prices/crypto_prices.csv")
    alerts_json = os.getenv("ALERTS_JSON", "data/alerts/price_alerts.json")
    plots_dir = os.getenv("PLOTS_DIR", "data/plots")
    mock_path = os.path.join("data", "samples", "mock_prices.json")
    return base_url, use_mock, coins, prices_csv, alerts_json, plots_dir, mock_path


def main():
    parser = argparse.ArgumentParser(description="Crypto Price Tracker")
    parser.add_argument("--fetch", action="store_true", help="Fetch prices")
    parser.add_argument("--log", action="store_true", help="Append prices to CSV")
    parser.add_argument("--plot", action="store_true", help="Plot 7-day moving averages")
    parser.add_argument("--alert", action="store_true", help="Check 10% drop alerts")
    parser.add_argument("--threshold", type=float, default=0.10, help="Drop threshold for alerts (e.g., 0.10)")
    args = parser.parse_args()

    base_url, use_mock, coins, prices_csv, alerts_json, plots_dir, mock_path = parse_env()

    ensure_dirs([prices_csv, alerts_json, plots_dir])

    fetcher = PriceFetcher(base_url=base_url, use_mock=use_mock, mock_path=mock_path)
    logger = DataLogger(prices_csv_path=prices_csv)
    analyzer = TrendAnalyzer(prices_csv_path=prices_csv, plots_dir=plots_dir)
    alerter = AlertEngine(prices_csv_path=prices_csv, alerts_json_path=alerts_json)

    latest_prices = None

    if args.fetch or args.log:
        latest_prices = fetcher.fetch_prices(coins)
        print(f"Fetched: {latest_prices}")

    if args.log and latest_prices:
        logger.save_price(latest_prices)
        print(f"Logged prices to {prices_csv}")

    if args.plot:
        for coin in coins:
            try:
                out = analyzer.plot_trend(coin)
                print(f"Plotted {coin}: {out}")
            except Exception as e:
                print(f"Plot failed for {coin}: {e}", file=sys.stderr)

    if args.alert:
        for coin in coins:
            alert = alerter.check_fluctuation(coin, threshold=args.threshold)
            if alert:
                print(f"ALERT: {alert}")
            else:
                print(f"No alert for {coin}")


if __name__ == "__main__":
    main()
