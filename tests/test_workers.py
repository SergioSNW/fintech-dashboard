import unittest
from src.ui.workers.update_portfolio_worker import UpdatePortfolioWorker
from src.use_cases.update_portfolio import UpdatePortfolioUseCase
from src.domain.models import Portfolio

class TestUpdatePortfolioWorker(unittest.TestCase):
    def test_update_portfolio_worker(self):
        update_portfolio_use_case = UpdatePortfolioUseCase()
        portfolio = Portfolio(total_value=100000.0, assets=[Asset(ticker="AAPL", amount=100.0, asset_type="Stock")])
        
        worker = UpdatePortfolioWorker(update_portfolio_use_case, portfolio)
        worker.run()

if __name__ == "__main__":
    unittest.main()