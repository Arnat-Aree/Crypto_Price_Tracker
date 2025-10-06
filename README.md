# Crypto Price Tracker

Lightweight, OOP-style crypto price tracker for data analysis using CoinGecko API. Saves daily prices to CSV, plots 7-day moving averages, and raises simple alerts on 10% drops.

## Quick Start (<= 10 minutes)

```bash
# From repo root
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# CLI
python src/app.py --fetch --log --plot --alert
# Web GUI
python src/web.py
```

Open Web GUI: `http://localhost:8000`

## Docker
```bash
# Build image
docker build -t crypto-price-tracker .
# Run container (gunicorn server)
docker run --rm -p 8000:8000 \
  -e API_BASE_URL="https://api.coingecko.com/api/v3" \
  -e USE_MOCK=false \
  -e COINS="bitcoin,ethereum" \
  -v $(pwd)/data:/app/data \
  crypto-price-tracker
```

Using docker-compose:
```bash
docker compose up --build
```

## Deploy to Render (Docker)
1) Push repo to GitHub
2) In Render dashboard → New → Web Service → Select repo → Environment: Docker
3) Render will use `Dockerfile` and port `8000` automatically
4) Set Environment Variables (optional overrides):
   - `API_BASE_URL`, `USE_MOCK`, `COINS`, `PRICES_CSV`, `ALERTS_JSON`, `PLOTS_DIR`, `FLASK_SECRET_KEY`
5) Click Deploy

Alternatively, add `render.yaml` to the repo root and create via Blueprint. Render will provision using free plan by default (edit `plan` if needed).

## Commands (CLI)
```bash
python src/app.py --fetch --log
python src/app.py --plot
python src/app.py --alert --threshold 0.10
```

## Tests & Lint
```bash
bash scripts/ci_simulate.sh
```

## Notes
- Public CoinGecko API (no key) is used by default; enable `USE_MOCK=true` if rate-limited.
- The web server runs with `gunicorn` in Docker/Render.
