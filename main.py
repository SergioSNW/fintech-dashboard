from PySide6.QtWidgets import QApplication
from src.domain.models import Portfolio, Asset
from src.use_cases.update_portfolio import UpdatePortfolioUseCase
from src.ui.main_window import MainWindow
from src.infrastructure.api_client import APIClient
from src.ui.workers.update_portfolio_worker import UpdatePortfolioWorker


def main():
    app = QApplication([])
    window = MainWindow()

    api_client = APIClient()
    update_portfolio_use_case = UpdatePortfolioUseCase(api_client)
    portfolio = Portfolio(total_value=0.0, assets=[Asset(ticker="BTC", amount=1.0, asset_type="Crypto")])

    def start_update():
        window.setRefreshEnabled(False)
        window.setLastUpdateText("Last update: refreshing...")

        worker = UpdatePortfolioWorker(update_portfolio_use_case, portfolio)
        window.current_worker = worker

        def on_result(updated_portfolio):
            window.setPortfolio(updated_portfolio)
            window.setRefreshEnabled(True)

        def on_error(exception):
            window.setLastUpdateText(f"Update failed: {exception}")
            window.setRefreshEnabled(True)

        worker.signals.result.connect(on_result)
        worker.signals.error.connect(on_error)
        window.thread_pool.start(worker)

    window.refresh_button.clicked.connect(start_update)
    start_update()

    window.show()
    app.exec()


if __name__ == "__main__":
    main()
