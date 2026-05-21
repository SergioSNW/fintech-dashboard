import asyncio
from app.backend.tasks import fetch_data, DataFetcherThread

async def test_fetch_data(mocker):
    async def mock_fetch():
        return [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]

    mocker.patch('app.backend.tasks.aiohttp.ClientSession.get', side_effect=mock_fetch)
    data = asyncio.run(fetch_data())
    assert data == [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]