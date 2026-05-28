import aiohttp
import asyncio
from typing import List, Dict
from src.domain.models import Asset, Portfolio

class FetchMarketDataUseCase:
    def __init__(self, api_client):
        self.api_client = api_client

    async def fetch_data(self, assets: List[Asset]) -> Dict[str, float]:
        market_data = {}
        def map_ticker(ticker: str) -> str:
            t = ticker.lower()
            mapping = {
                "btc": "bitcoin",
                "btc_usd": "bitcoin",
                "bitcoin": "bitcoin",
                "eth": "ethereum",
                "ethereum": "ethereum",
                "sol": "solana",
                "solana": "solana",
                "ada": "cardano",
                "cardano": "cardano",
                "dot": "polkadot",
                "polkadot": "polkadot",
                "xrp": "ripple",
                "ripple": "ripple",
                "link": "chainlink",
                "chainlink": "chainlink",
                "doge": "dogecoin",
                "dogecoin": "dogecoin",
                "avax": "avalanche-2",
                "avalanche": "avalanche-2",
                "matic": "polygon",
                "polygon": "polygon",
            }
            return mapping.get(t, t)
        # Build a unique list of CoinGecko ids to batch into a single request
        ticker_to_id = {asset.ticker: map_ticker(asset.ticker) for asset in assets}
        unique_ids = ",".join(sorted(set(ticker_to_id.values())))

        if unique_ids:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={unique_ids}&vs_currencies=usd"
            response = await self.api_client.fetch_data(url)
        else:
            response = {}

        # Map back prices to original asset.ticker keys
        for asset in assets:
            cg_id = ticker_to_id.get(asset.ticker)
            price = 0.0
            if isinstance(response, dict) and cg_id in response:
                # response[cg_id] is like {"usd": 73000}
                price = response[cg_id].get('usd', 0.0)
            market_data[asset.ticker] = price
        return market_data
    
    async def execute(self, assets: List[Asset]) -> Dict[str, float]:
        return await self.fetch_data(assets)
