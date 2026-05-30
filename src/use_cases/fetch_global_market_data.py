# src/use_cases/fetch_global_market_data.py

from typing import List
from src.domain.models import MarketAsset

class FetchGlobalMarketDataUseCase:
    def __init__(self, api_client):
        self.api_client = api_client

    async def execute(self, vs_currency: str = "usd", per_page: int = 8) -> List[MarketAsset]:
        # CHANGED: sparkline=true inside the query URL string
        url = (
            f"https://api.coingecko.com/api/v3/coins/markets?"
            f"vs_currency={vs_currency}&order=market_cap_desc&per_page={per_page}&page=1&sparkline=true&price_change_percentage=24h"
        )
        
        try:
            response = await self.api_client.fetch_data(url)
            if not isinstance(response, list):
                return []

            assets = []
            for item in response:
                if not isinstance(item, dict):
                    continue

                raw_symbol = item.get("symbol", "").upper()
                raw_name = item.get("name", "")

                if isinstance(raw_name, dict):
                    raw_name = raw_name.get("en", raw_name.get("id", raw_symbol))

                if not raw_name or str(raw_name).strip() == "" or raw_name.upper() == raw_symbol:
                    ticker_mapping = {
                        "BTC": "Bitcoin", "ETH": "Ethereum", "USDT": "Tether", 
                        "SOL": "Solana", "XRP": "Ripple", "ADA": "Cardano", 
                        "DOGE": "Dogecoin", "DOT": "Polkadot", "AVAX": "Avalanche",
                        "MATIC": "Polygon", "LINK": "Chainlink"
                    }
                    clean_name = ticker_mapping.get(raw_symbol, raw_symbol.title())
                else:
                    clean_name = str(raw_name).strip().title()

                # NEW: Extract the sparkline array data safely out of CoinGecko's nested structure
                sparkline_data = []
                sparkline_obj = item.get("sparkline_in_7d", {})
                if isinstance(sparkline_obj, dict):
                    sparkline_data = sparkline_obj.get("price", [])

                assets.append(
                    MarketAsset(
                        name=clean_name,
                        ticker=raw_symbol,
                        price=float(item.get("current_price", 0.0) or 0.0),
                        change_24h=float(item.get("price_change_percentage_24h", 0.0) or 0.0),
                        sparkline_prices=sparkline_data # Injected here
                    )
                )
            return assets

        except Exception:
            return []