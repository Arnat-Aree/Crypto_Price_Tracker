import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request

# Support running as a package (gunicorn src.web:app) and as a script/tests
try:
    from .api_client import PriceFetcher
    from .data_logger import DataLogger
    from .trend_analyzer import TrendAnalyzer
    from .alert_engine import AlertEngine
except ImportError:  # fallback for direct script/tests
    from api_client import PriceFetcher
    from data_logger import DataLogger
    from trend_analyzer import TrendAnalyzer
    from alert_engine import AlertEngine


ALIASES = {
    "btc": "bitcoin",
    "xbt": "bitcoin",
    "eth": "ethereum",
}


def normalize_coin_id(coin: str) -> str:
    key = coin.strip().lower()
    return ALIASES.get(key, key)


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

    base_url = os.getenv("API_BASE_URL", "https://api.coingecko.com/api/v3")
    use_mock = os.getenv("USE_MOCK", "false").lower() == "true"
    coins = [normalize_coin_id(c) for c in os.getenv("COINS", "bitcoin,ethereum").split(",") if c.strip()]
    default_currency = os.getenv("CURRENCY", "usd").lower()
    prices_csv = os.getenv("PRICES_CSV", "data/prices/crypto_prices.csv")
    alerts_json = os.getenv("ALERTS_JSON", "data/alerts/price_alerts.json")
    plots_dir = os.getenv("PLOTS_DIR", "data/plots")
    mock_path = os.path.join("data", "samples", "mock_prices.json")

    fetcher = PriceFetcher(base_url=base_url, use_mock=use_mock, mock_path=mock_path)
    logger = DataLogger(prices_csv_path=prices_csv)
    analyzer = TrendAnalyzer(prices_csv_path=prices_csv, plots_dir=plots_dir)
    alerter = AlertEngine(prices_csv_path=prices_csv, alerts_json_path=alerts_json)

    @app.route("/")
    def index():
        days = int(request.args.get("days", "30"))
        currency = request.args.get("currency", default_currency).lower()
        user_coins = request.args.get("coins")
        view_coins = coins if not user_coins else [normalize_coin_id(c) for c in user_coins.split(",") if c.strip()]
        latest = None
        try:
            latest = fetcher.fetch_prices(view_coins, currency=currency)
        except Exception:
            latest = None

        charts = {}
        kpis = {}
        for coin in view_coins:
            try:
                series = analyzer.get_series(coin, days=days)
                charts[coin] = series
                kpis[coin] = analyzer.get_kpis(coin)
            except Exception:
                charts[coin] = {"labels": [], "price": [], "ma7": [], "ma30": [], "rsi14": []}
                kpis[coin] = {"last_price": None, "change_pct_1d": None}

        return render_template(
            "index.html",
            coins=view_coins,
            latest=latest,
            charts=charts,
            kpis=kpis,
            selected_days=days,
            currency=currency,
            now=datetime.utcnow(),
        )

    @app.route("/fetch-log")
    def fetch_log():
        currency = request.args.get("currency", default_currency).lower()
        user_coins = request.args.get("coins")
        view_coins = coins if not user_coins else [normalize_coin_id(c) for c in user_coins.split(",") if c.strip()]
        prices = fetcher.fetch_prices(view_coins, currency=currency)
        logger.save_price(prices)
        flash(f"Fetched and logged prices for: {', '.join(view_coins)} ({currency.upper()}).")
        return redirect(url_for("index", coins=",".join(view_coins), currency=currency))

    @app.route("/alert-check")
    def alert_check():
        alerts = []
        for coin in coins:
            alert = alerter.check_fluctuation(coin, threshold=0.10)
            if alert:
                alerts.append(alert)
        if alerts:
            flash(f"Alerts: {alerts}")
        else:
            flash("No alerts triggered.")
        return redirect(url_for("index"))

    @app.route("/sync-history")
    def sync_history():
        days = int(request.args.get("days", "7"))
        currency = request.args.get("currency", default_currency).lower()
        user_coins = request.args.get("coins")
        view_coins = coins if not user_coins else [normalize_coin_id(c) for c in user_coins.split(",") if c.strip()]
        synced = []
        for coin in view_coins:
            try:
                hist = fetcher.fetch_market_chart(coin, days=days, currency=currency)
                logger.upsert_history(coin, hist)
                synced.append(coin)
            except Exception as e:
                flash(f"Failed to sync {coin}: {e}")
        if synced:
            flash(f"Synced {days}d history for: {', '.join(synced)}")
        return redirect(url_for("index", days=days, coins=",".join(view_coins), currency=currency))

    # serve plot images from PLOTS_DIR
    from flask import send_from_directory

    @app.route("/plots/<path:filename>")
    def plots(filename):
        return send_from_directory(plots_dir, filename)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=True)
