from dataclasses import dataclass

@dataclass
class Asset:
    ticker: str
    amount: float
    asset_type: str
    price: float = 0.0
    total_value: float = 0.0
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = self.ticker.upper()

@dataclass
class Portfolio:
    total_value: float
    assets: list[Asset]