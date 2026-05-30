# src/ui/workers.py

from PySide6.QtCore import QObject, QRunnable, Signal
import asyncio
from src.use_cases.update_portfolio import UpdatePortfolioUseCase
from src.use_cases.fetch_global_market_data import FetchGlobalMarketDataUseCase
from src.domain.models import Portfolio


class WorkerSignals(QObject):
    # Pass data payload AND the worker object instance to protect memory lifecycle stability
    result_ready = Signal(object, object)
    error = Signal(str, object)


class UpdatePortfolioWorker(QRunnable):
    def __init__(self, update_portfolio_use_case: UpdatePortfolioUseCase, portfolio: Portfolio):
        super().__init__()
        self.signals = WorkerSignals()
        self.update_portfolio_use_case = update_portfolio_use_case
        self.portfolio = portfolio

    def run(self) -> None:
        try:
            updated_portfolio = asyncio.run(self.update_portfolio_use_case.execute(self.portfolio))
            self.signals.result_ready.emit(updated_portfolio, self)
        except Exception as e:
            self.signals.error.emit(f"Portfolio Sync Error: {str(e)}", self)


class GlobalMarketWorker(QRunnable):
    def __init__(self, fetch_global_market_data_use_case: FetchGlobalMarketDataUseCase):
        super().__init__()
        self.signals = WorkerSignals()
        self.use_case = fetch_global_market_data_use_case

    def run(self) -> None:
        try:
            market_assets = asyncio.run(self.use_case.execute())
            self.signals.result_ready.emit(market_assets, self)
        except Exception as e:
            self.signals.error.emit(f"Market Sync Error: {str(e)}", self)