import aiohttp
from typing import Dict, Any
from urllib.parse import urlparse, parse_qs


class APIClient:
    async def fetch_data(self, url: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        # For CoinGecko simple/price endpoint, return the raw structure
        # Example response: {"bitcoin": {"usd": 73000}, "ethereum": {"usd": 3000}}
        if "api.coingecko.com" in url and "/simple/price" in url:
            return data

        # Fallback: return raw parsed JSON
        return data