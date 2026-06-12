# src/infrastructure/portfolio_repository.py

import sqlite3
from typing import List
from src.domain.models import Asset

class PortfolioRepository:
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                ticker TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                asset_type TEXT NOT NULL
            )
        """)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM assets")
        if cursor.fetchone()[0] == 0:
            initial_assets = [
                ("BTC", 1.2, "Crypto"),
                ("ETH", 5.5, "Crypto"),
                ("SOL", 50.0, "Crypto")
            ]
            cursor.executemany("INSERT INTO assets (ticker, amount, asset_type) VALUES (?, ?, ?)", initial_assets)
            conn.commit()
        conn.close()

    def get_all_assets(self) -> List[Asset]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ticker, amount, asset_type FROM assets")
        rows = cursor.fetchall()
        conn.close()
        return [Asset(ticker=row[0], amount=row[1], asset_type=row[2]) for row in rows]

    def save_or_update_asset(self, asset: Asset):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO assets (ticker, amount, asset_type)
            VALUES (?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET amount = excluded.amount
        """, (asset.ticker, asset.amount, asset.asset_type))
        conn.commit()
        conn.close()

    # NEW: Remove an asset entirely from database storage
    def delete_asset(self, ticker: str):
        """Removes an asset recording completely from the SQLite table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assets WHERE ticker = ?", (ticker.upper().strip(),))
        conn.commit()
        conn.close()