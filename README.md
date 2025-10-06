# Crypto Price Tracker

Lightweight, OOP-style crypto price tracker for data analysis using CoinGecko API. Saves daily prices to CSV, plots 7-day moving averages, and raises simple alerts on 10% drops.

**Websire:** https://crypto-price-tracker-xj94.onrender.com

## Features
- Fetch BTC/ETH prices (public API; no key required)
- Daily CSV logging with upsert for historical data
- Interactive web charts (Chart.js) with 7/30/90 day ranges
- Alerts on 10% daily drop, saved to JSON
- Dockerized + Render deploy (gunicorn)
- Tests (pytest) + Lint (flake8) + CI (GitHub Actions)

## Quick Start (<= 10 minutes)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
# CLI
python src/app.py --fetch --log --plot --alert
# Web GUI
python src/web.py
```

Open Web GUI: `http://localhost:8000`

## Environment
- API_BASE_URL (default: CoinGecko v3)
- USE_MOCK (true/false) – mock fallback when rate-limited
- COINS – e.g., `bitcoin,ethereum`
- PRICES_CSV, ALERTS_JSON, PLOTS_DIR

## Docker
```bash
docker build -t crypto-price-tracker .
docker run --rm -p 8000:8000 \
  -e API_BASE_URL="https://api.coingecko.com/api/v3" \
  -e USE_MOCK=false \
  -e COINS="bitcoin,ethereum" \
  -v $(pwd)/data:/app/data \
  crypto-price-tracker
```

Compose:
```bash
docker compose up --build
```

## Deploy to Render
- Use Docker web service, or `render.yaml` blueprint.
- Default command uses gunicorn: `src.web:create_app()` on port 8000.

## Project Structure
```
src/
  app.py            # CLI orchestrator
  web.py            # Flask web app (Bootstrap + Chart.js)
  api_client.py     # PriceFetcher (live + history)
  data_logger.py    # DataLogger (append + upsert)
  trend_analyzer.py # Series + KPIs + plotting
  alert_engine.py   # Alerts 10% drop
```

## Tests & Lint
```bash
bash scripts/ci_simulate.sh
```

## CI
- GitHub Actions runs flake8 + pytest on pushes and PRs to `main`.
