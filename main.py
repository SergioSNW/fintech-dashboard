# main.py

import sys
import copy
import asyncio
import qasync
import aiohttp
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from src.domain.models import Portfolio, Asset
from src.use_cases.update_portfolio import UpdatePortfolioUseCase
from src.use_cases.fetch_global_market_data import FetchGlobalMarketDataUseCase
from src.ui.main_window import MainWindow
from src.infrastructure.api_client import APIClient
from src.infrastructure.portfolio_repository import PortfolioRepository


def main():
    app = QApplication(sys.argv)
    
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()

    api_client = APIClient()
    update_portfolio_use_case = UpdatePortfolioUseCase(api_client)
    global_market_use_case = FetchGlobalMarketDataUseCase(api_client)
    
    db_repo = PortfolioRepository("portfolio.db")
    saved_assets = db_repo.get_all_assets()
    
    master_portfolio = Portfolio(
        total_value=0.0,
        assets=saved_assets
    )
    
    window.portfolio_reference = master_portfolio

    async def async_refresh_pipeline():
        window.setLastUpdateText("Last update: refreshing...")
        window.watchdog_timer.start()

        current_assets_snapshot = copy.deepcopy(master_portfolio)

        try:
            updated_portfolio_task = update_portfolio_use_case.execute(current_assets_snapshot)
            market_assets_task = global_market_use_case.execute()

            updated_portfolio, market_assets = await asyncio.gather(
                updated_portfolio_task, 
                market_assets_task
            )

            master_portfolio.total_value = updated_portfolio.total_value
            master_portfolio.assets = updated_portfolio.assets
            
            window.setPortfolio(master_portfolio)
            window.setMarketData(market_assets)
            
            window.watchdog_timer.stop()
            window.is_refreshing = False
            window._check_and_enable_ui()

        except Exception as e:
            window.watchdog_timer.stop()
            window.is_refreshing = False
            window._check_and_enable_ui()
            
            if isinstance(e, aiohttp.ClientResponseError) and e.status == 429:
                friendly_error = "Rate limited (try again soon)"
            else:
                friendly_error = str(e).split('\n')[0][:30]
                
            window.handle_refresh_failure(friendly_error)

    def trigger_async_refresh_pipeline():
        asyncio.ensure_future(async_refresh_pipeline(), loop=loop)

    window.setManualRefreshCallback(trigger_async_refresh_pipeline)

    # AUTOMATIC BACKGROUND SYNC LOGIC
    def on_auto_refresh_timeout():
        # Only run background loops if the user is not executing a manual cooldown cycle
        if not window.is_refreshing and getattr(window, "cooldown_remaining", 0) == 0:
            trigger_async_refresh_pipeline()

    # Set up a background QTimer synchronized with the active event loop
    auto_refresh_timer = QTimer(window)
    # 300,000 milliseconds = 5 minutes
    auto_refresh_timer.setInterval(300000)
    auto_refresh_timer.timeout.connect(on_auto_refresh_timeout)
    auto_refresh_timer.start()

    def on_asset_added(ticker: str, amount: float):
        formatted_ticker = ticker.strip().upper()
        existing_asset = next((a for a in master_portfolio.assets if a.ticker == formatted_ticker), None)
        
        if existing_asset:
            existing_asset.amount += amount
            db_repo.save_or_update_asset(existing_asset)
        else:
            new_asset = Asset(ticker=formatted_ticker, amount=amount, asset_type="Crypto")
            master_portfolio.assets.append(new_asset)
            db_repo.save_or_update_asset(new_asset)
            
        window.setPortfolio(master_portfolio)
        window.start_direct_refresh_pipeline()

    def on_asset_edited(ticker: str, new_amount: float):
        formatted_ticker = ticker.strip().upper()
        asset = next((a for a in master_portfolio.assets if a.ticker == formatted_ticker), None)
        
        if asset:
            asset.amount = new_amount
            db_repo.save_or_update_asset(asset)
            window.setPortfolio(master_portfolio)
            window.start_direct_refresh_pipeline()

    def on_asset_deleted(ticker: str):
        formatted_ticker = ticker.strip().upper()
        asset = next((a for a in master_portfolio.assets if a.ticker == formatted_ticker), None)
        
        if asset:
            master_portfolio.assets.remove(asset)
            db_repo.delete_asset(formatted_ticker)
            window.setPortfolio(master_portfolio)
            window.start_direct_refresh_pipeline()

    window.setAssetAddedCallback(on_asset_added)
    window.setAssetEditedCallback(on_asset_edited)
    window.setAssetDeletedCallback(on_asset_deleted)

    window.setPortfolio(master_portfolio)
    window.start_direct_refresh_pipeline()

    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()