import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from api_client import PriceFetcher


def test_fetch_prices_with_mock(tmp_path):
    mock = tmp_path / "mock_prices.json"
    mock.write_text(json.dumps({"bitcoin": 100.0, "ethereum": 50.0}), encoding="utf-8")

    fetcher = PriceFetcher(use_mock=True, mock_path=str(mock))
    result = fetcher.fetch_prices(["bitcoin", "ethereum"]) 
    assert set(result.keys()) == {"bitcoin", "ethereum"}
    assert result["bitcoin"] == 100.0
    assert result["ethereum"] == 50.0
