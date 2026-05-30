# src/infrastructure/api_client.py

import aiohttp
from typing import Dict, Any

class APIClient:
    async def fetch_data(self, url: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # FIXED: If the API returns 429 (Rate Limited) or 500, raise an exception 
                # instead of blindly converting the error message to your data payload.
                response.raise_for_status()
                data = await response.json()

        if "api.coingecko.com" in url and "/simple/price" in url:
            return data

        return data