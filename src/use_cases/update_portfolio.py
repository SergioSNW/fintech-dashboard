# src/use_cases/update_portfolio.py

from typing import List
from src.domain.models import Asset, Portfolio
from .fetch_market_data import FetchMarketDataUseCase

class UpdatePortfolioUseCase:
    def __init__(self, api_client):
        self.fetch_market_data_use_case = FetchMarketDataUseCase(api_client)

    async def execute(self, portfolio: Portfolio) -> Portfolio:
        market_data = await self.fetch_market_data_use_case.execute(portfolio.assets)

        for asset in portfolio.assets:
            # FIXED: Get the existing price as the fallback. 
            # Only use 0.0 if the asset is completely new and has no price history yet.
            existing_price = getattr(asset, 'price', 0.0) or 0.0
            
            # If the market_data lookup fails or returns None, preserve the old price
            asset.price = market_data.get(asset.ticker, existing_price)
            asset.total_value = asset.amount * asset.price

        portfolio.total_value = sum(asset.total_value for asset in portfolio.assets)
        return portfolio