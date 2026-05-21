import asyncio
from PySide6.QtCore import QThread, Signal, QObject
import aiohttp
from app.backend.data_processing import process_data

class DataFetcher(QObject):
    finished = Signal(list)

    async def fetch_data(self):
        url = 'https://api.example.com/data'  # Replace with your API endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                processed_data = process_data(data)
                self.finished.emit(processed_data)

class DataFetcherThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_fetcher = DataFetcher()

    def run(self):
        asyncio.run(self.data_fetcher.fetch_data())

def fetch_data():
    thread = DataFetcherThread()
    loop = asyncio.get_event_loop()
    result = []
    thread.finished.connect(lambda data: result.extend(data))
    thread.start()
    loop.run_in_executor(None, thread.wait)
    return result