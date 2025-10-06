#!/usr/bin/env bash
set -euo pipefail

echo "Running flake8..."
flake8 src tests

echo "Running pytest..."
pytest -q
