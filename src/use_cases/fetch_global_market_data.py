from typing import List
from src.domain.models import MarketAsset

class FetchGlobalMarketDataUseCase:
    def __init__(self, api_client):
        self.api_client = api_client

    async def execute(self, vs_currency: str = "usd", per_page: int = 8) -> List[MarketAsset]:
        url = (
            f"https://api.coingecko.com/api/v3/coins/markets?"
            f"vs_currency={vs_currency}&order=market_cap_desc&per_page={per_page}&page=1&sparkline=false&price_change_percentage=24h"
        )
        response = await self.api_client.fetch_data(url)
        if not isinstance(response, list):
            return []

        assets = []
        for item in response:
            assets.append(
                MarketAsset(
                    name=item.get("name", ""),
                    ticker=item.get("symbol", "").upper(),
                    price=float(item.get("current_price", 0.0) or 0.0),
                    change_24h=float(item.get("price_change_percentage_24h", 0.0) or 0.0),
                )
            )
        return assets
