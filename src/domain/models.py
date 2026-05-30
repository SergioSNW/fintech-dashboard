# src/domain/models.py
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Asset:
    ticker: str
    amount: float
    asset_type: str
    name: Optional[str] = None
    price: Optional[float] = None
    total_value: Optional[float] = None

@dataclass
class Portfolio:
    total_value: float
    assets: List[Asset] = field(default_factory=list)

@dataclass
class MarketAsset:
    name: str
    ticker: str
    price: float
    change_24h: float
    # NEW: Field to store the array of float prices for rendering the sparkline
    sparkline_prices: List[float] = field(default_factory=list)