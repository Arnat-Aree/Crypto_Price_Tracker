#!/usr/bin/env bash
set -euo pipefail

PORT_TO_USE="${PORT:-10000}"
echo "Starting Gunicorn on port ${PORT_TO_USE}..."
exec gunicorn -w 2 -b 0.0.0.0:"${PORT_TO_USE}" src.web:app

