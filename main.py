# main.py

import copy
from PySide6.QtWidgets import QApplication
from src.domain.models import Portfolio, Asset
from src.use_cases.update_portfolio import UpdatePortfolioUseCase
from src.use_cases.fetch_global_market_data import FetchGlobalMarketDataUseCase
from src.ui.main_window import MainWindow
from src.infrastructure.api_client import APIClient
from src.ui.workers import UpdatePortfolioWorker, GlobalMarketWorker


def main():
    app = QApplication([])
    window = MainWindow()

    api_client = APIClient()
    update_portfolio_use_case = UpdatePortfolioUseCase(api_client)
    global_market_use_case = FetchGlobalMarketDataUseCase(api_client)
    
    portfolio = Portfolio(
        total_value=0.0,
        assets=[
            Asset(ticker="BTC", amount=1.2, asset_type="Crypto"),
            Asset(ticker="ETH", amount=5.5, asset_type="Crypto"),
            Asset(ticker="SOL", amount=50.0, asset_type="Crypto"),
        ],
    )

    # Active worker reference handles tracking dictionary
    active_workers = {"portfolio": None, "market": None}

    def trigger_async_refresh_pipeline():
        window.setLastUpdateText("Last update: refreshing...")

        # 1. LIFECYCLE FIX: Disconnect and clear prior workers safely if they exist
        if active_workers["portfolio"] is not None:
            try:
                active_workers["portfolio"].signals.result_ready.disconnect()
                active_workers["portfolio"].signals.error.disconnect()
            except (RuntimeError, AttributeError):
                pass  # C++ object or connection was already cleared
            active_workers["portfolio"] = None
                
        if active_workers["market"] is not None:
            try:
                active_workers["market"].signals.result_ready.disconnect()
            except (RuntimeError, AttributeError):
                pass
            active_workers["market"] = None

        # 2. Isolate layout thread memory footprint bounds
        isolated_portfolio_snapshot = copy.deepcopy(portfolio)

        # 3. Instantiate the execution workers
        portfolio_worker = UpdatePortfolioWorker(update_portfolio_use_case, isolated_portfolio_snapshot)
        market_worker = GlobalMarketWorker(global_market_use_case)

        # Force Qt to manage memory lifecycle internally
        portfolio_worker.setAutoDelete(True)
        market_worker.setAutoDelete(True)

        active_workers["portfolio"] = portfolio_worker
        active_workers["market"] = market_worker

        # 4. Bind closures that automatically clean up references upon completion
        def on_portfolio_ready(updated_portfolio):
            # Check if this worker instance is still the active tracked job
            if active_workers["portfolio"] == portfolio_worker:
                portfolio.total_value = updated_portfolio.total_value
                portfolio.assets = updated_portfolio.assets
                window.handle_portfolio_update(updated_portfolio)
                # Nullify reference handle immediately so it doesn't cause a dead pointer crash next click
                active_workers["portfolio"] = None

        def on_portfolio_error(exception):
            if active_workers["portfolio"] == portfolio_worker:
                window.setLastUpdateText(f"Update failed: {exception}")
                window.is_refreshing = False
                window._check_and_enable_ui()
                active_workers["portfolio"] = None

        def on_market_ready(market_assets):
            if active_workers["market"] == market_worker:
                window.handle_market_data_update(market_assets)
                active_workers["market"] = None

        portfolio_worker.signals.result_ready.connect(on_portfolio_ready)
        portfolio_worker.signals.error.connect(on_portfolio_error)
        market_worker.signals.result_ready.connect(on_market_ready)

        # 5. Execute pipeline tasks concurrently
        window.thread_pool.start(portfolio_worker)
        window.thread_pool.start(market_worker)

    window.setManualRefreshCallback(trigger_async_refresh_pipeline)

    def on_asset_added(ticker: str, amount: float):
        portfolio.assets.append(Asset(ticker=ticker, amount=amount, asset_type="Crypto"))
        
        if not window.is_refreshing:
            window.is_refreshing = True
            window.cooldown_remaining = 3
            window.setRefreshEnabled(False)
            window.refresh_button.setText(f"Refreshing ({window.cooldown_remaining}s)...")
            window.cooldown_timer.start()
            trigger_async_refresh_pipeline()

    window.setAssetAddedCallback(on_asset_added)

    # Initial boot refresh setup sequence trigger
    window.is_refreshing = True
    trigger_async_refresh_pipeline()

    window.show()
    app.exec()


if __name__ == "__main__":
    main()