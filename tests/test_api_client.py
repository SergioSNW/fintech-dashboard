# tests/test_workers.py

import unittest
from unittest.mock import MagicMock, AsyncMock
from src.ui.workers import UpdatePortfolioWorker
from src.use_cases.update_portfolio import UpdatePortfolioUseCase
from src.domain.models import Portfolio

class TestWorkers(unittest.TestCase):
    def test_update_portfolio_worker(self):
        # 1. Create a mock for the API Client that the Use Case relies on
        mock_api_client = MagicMock()
        
        # 2. Inject the mock into the use case constructor
        update_portfolio_use_case = UpdatePortfolioUseCase(api_client=mock_api_client)
        
        # 3. Stub the execute method to return a dummy Portfolio instantly without network calls
        dummy_portfolio = Portfolio(total_value=0.0, assets=[])
        update_portfolio_use_case.execute = AsyncMock(return_value=dummy_portfolio)
        
        # 4. Set up your worker with the mock use case
        input_portfolio = Portfolio(total_value=0.0, assets=[])
        worker = UpdatePortfolioWorker(update_portfolio_use_case, input_portfolio)
        
        # 5. Connect to signals and run your test asserts as normal...
        # worker.signals.result_ready.connect(...)
        # worker.run()