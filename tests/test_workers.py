# tests/test_workers.py

import unittest
from unittest.mock import MagicMock, AsyncMock
from PySide6.QtWidgets import QApplication
from src.ui.workers import UpdatePortfolioWorker
from src.use_cases.update_portfolio import UpdatePortfolioUseCase
from src.domain.models import Portfolio

# We need a dummy QApplication instance so Qt Signals can emit safely during the test
app = QApplication.instance() or QApplication([])

class TestUpdatePortfolioWorker(unittest.TestCase):
    def test_update_portfolio_worker(self):
        # 1. Mock the API client dependency required by the use case
        mock_api_client = MagicMock()
        
        # 2. Inject the mock client into the use case constructor
        update_portfolio_use_case = UpdatePortfolioUseCase(api_client=mock_api_client)
        
        # 3. Create a dummy portfolio data structure matching your domain
        dummy_portfolio = Portfolio(total_value=12500.0, assets=[])
        
        # 4. Stub the use case's execute method to instantly return our dummy portfolio asynchronously
        update_portfolio_use_case.execute = AsyncMock(return_value=dummy_portfolio)
        
        # 5. Initialize the worker with our mocked use case
        worker = UpdatePortfolioWorker(update_portfolio_use_case, dummy_portfolio)
        
        # 6. Set up a tracking variable and callback to catch the emitted signal
        received_portfolio = None
        def on_result_ready(result):
            nonlocal received_portfolio
            received_portfolio = result

        worker.signals.result_ready.connect(on_result_ready)
        
        # 7. Execute the worker's synchronous run wrapper
        worker.run()
        
        # 8. Assert that the worker ran flawlessly and emitted the correct data object
        self.assertIsNotNone(received_portfolio)
        self.assertEqual(received_portfolio.total_value, 12500.0)


if __name__ == "__main__":
    unittest.main()