# Fintech Dashboard

A desktop crypto portfolio tracking dashboard built with Python, PySide6, and asyncio.

This portfolio piece demonstrates a clean architecture for a desktop application with live market data, local persistence, responsive UI, and custom styled Qt widgets.

## Key Features

- Add, edit, and delete crypto assets in a portfolio
- Real-time portfolio valuation with currency toggle support for USD, EUR, and GBP
- Market analytics for selected crypto assets and live global market data
- Asset allocation visualization with responsive charting
- Background refresh pipeline using async I/O and a non-blocking UI loop
- Local persistence with SQLite via `src/infrastructure/portfolio_repository.py`
- Custom themed PySide6 dropdowns and modal dialogs for polished desktop UX

## Architecture

- `src/domain/models.py` — domain models for `Portfolio` and `Asset`
- `src/infrastructure/api_client.py` — market data client and HTTP integration
- `src/infrastructure/portfolio_repository.py` — persistent portfolio storage
- `src/use_cases/` — business logic for fetching market data and updating portfolio values
- `src/ui/main_window.py` — main desktop window and portfolio presentation layer
- `src/ui/components/add_asset_dialog.py` — add asset modal with styled dropdowns and validation
- `src/ui/workers/` — asynchronous worker components for background sync

## Run locally

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/fintech-dashboard.git
   cd fintech-dashboard
   ```

2. Create and activate a virtual environment:

   ```sh
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

4. Start the desktop app:
   ```sh
   python main.py
   ```

## Testing

Run the unit tests with:

```sh
pytest
```

## Notes for Employers

- This project showcases clean separation of concerns between UI, business logic, and infrastructure
- The UI is built with PySide6 and custom Qt styling for a modern desktop experience
- Async and background refresh behavior is implemented using `qasync` and `aiohttp`
- The project includes a local SQLite persistence layer for saving portfolio assets
- The main entrypoint is `main.py`

## Recommended Python environment

- Python 3.10+ or 3.11+
- `PySide6`, `qasync`, `aiohttp`, `pandas`, `requests`

> Note: The Docker configuration file is present in the repository, but the primary local startup path for this app is the desktop entrypoint `python main.py`.
