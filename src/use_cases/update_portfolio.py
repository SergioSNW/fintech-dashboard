from typing import List
from src.domain.models import Asset, Portfolio
from .fetch_market_data import FetchMarketDataUseCase

class UpdatePortfolioUseCase:
    def __init__(self, api_client):
        self.fetch_market_data_use_case = FetchMarketDataUseCase(api_client)

    async def execute(self, portfolio: Portfolio) -> Portfolio:
        market_data = await self.fetch_market_data_use_case.execute(portfolio.assets)

        for asset in portfolio.assets:
            asset.price = market_data.get(asset.ticker, 0.0)
            asset.total_value = asset.amount * asset.price

        portfolio.total_value = sum(asset.total_value for asset in portfolio.assets)
        return portfolio
        