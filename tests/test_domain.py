from src.domain.models import Asset, Portfolio

def test_asset_creation():
    asset = Asset(ticker="AAPL", amount=100.0, asset_type="Stock")
    assert asset.ticker == "AAPL"
    assert asset.amount == 100.0
    assert asset.asset_type == "Stock"

def test_portfolio_creation():
    portfolio = Portfolio(total_value=100000.0, assets=[])
    assert portfolio.total_value == 100000.0
    assert len(portfolio.assets) == 0