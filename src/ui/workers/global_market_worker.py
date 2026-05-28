from PySide6.QtCore import QObject, Signal, QRunnable
import asyncio
from src.use_cases.fetch_global_market_data import FetchGlobalMarketDataUseCase

class WorkerSignals(QObject):
    result_ready = Signal(object)
    error = Signal(object)


class GlobalMarketWorker(QRunnable):
    def __init__(self, fetch_global_market_data_use_case: FetchGlobalMarketDataUseCase):
        super().__init__()
        self.signals = WorkerSignals()
        self.use_case = fetch_global_market_data_use_case

    def run(self) -> None:
        try:
            market_assets = asyncio.run(self.use_case.execute())
        except Exception as e:
            self.signals.error.emit(e)
        else:
            self.signals.result_ready.emit(market_assets)
