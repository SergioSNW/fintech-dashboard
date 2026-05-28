from PySide6.QtCore import QObject, Signal, QRunnable
import asyncio
from src.use_cases.update_portfolio import UpdatePortfolioUseCase
from src.domain.models import Portfolio


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(object)


class UpdatePortfolioWorker(QRunnable):
    def __init__(self, update_portfolio_use_case: UpdatePortfolioUseCase, portfolio: Portfolio):
        super().__init__()
        self.signals = WorkerSignals()
        self.update_portfolio_use_case = update_portfolio_use_case
        self.portfolio = portfolio

    def run(self) -> None:
        try:
            updated_portfolio = asyncio.run(self.update_portfolio_use_case.execute(self.portfolio))
        except Exception as e:
            self.signals.error.emit(e)
        else:
            self.signals.result.emit(updated_portfolio)
