You are an expert Principal Python Engineer specializing in high-performance desktop development and clean architecture. Your task is to initialize and build out the repository for our "Personal FinTech & Crypto Desktop Dashboard" by implementing the blueprint detailed in the repository's 'fintech_dashboard_architecture.md' file.

Folder Structure.
fintech-dashboard/
├── .env
├── .env.example
├── .git/
├── .github/
├── .gitignore
├── Dockerfile
├── README.md
├── __pycache__/
├── docker-compose.yaml
├── fintech-dashboard-intro.md
├── fintech_dashboard_architecture.md
├── main.py
├── masterplan.md
├── notes.md
├── portfolio.db
├── requirements.txt
├── setup.py
├── venv/
├── src/
│   ├── __pycache__/
│   ├── __version__.py
│   ├── config.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   └── models.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── api_client.py
│   │   ├── portfolio_repository.py
│   │   └── repositories.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── api_service.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── main_window.py
│   │   ├── workers.py
│   │   ├── components/
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__/
│   │   │   ├── add_asset_dialog.py
│   │   │   └── edit_asset_dialog.py
│   │   ├── signals/
│   │   │   └── __init__.py
│   │   └── workers/
│   │       ├── __init__.py
│   │       ├── __pycache__/
│   │       ├── global_market_worker.py
│   │       └── update_portfolio_worker.py
│   └── use_cases/
│       ├── __init__.py
│       ├── __pycache__/
│       ├── fetch_global_market_data.py
│       ├── fetch_market_data.py
│       └── update_portfolio.py
└── tests/
    ├── __init__.py
    ├── __pycache__/
    ├── test_api_client.py
    ├── test_domain.py
    ├── test_use_cases.py
    └── test_workers.py

OBJECTIVES:
1. Workspace Initialization: Verify the workspace root directory and ensure a Python virtual environment can be mapped correctly.
2. Structure Generation: Build out the exact filesystem directory hierarchy explicitly requested in Section 3 ("Standardized Repository Layout") of the blueprint, ensuring all necessary '__init__.py' modules are created to make them true Python packages.
3. Code Population: Implement the precise, production-ready code blocks provided in Section 4 and Section 5 of the architecture document:
   - Save the dependencies to 'requirements.txt'
   - Implement the pure Python logic layer in 'app/service/dashboard_service.py'
   - Implement the async thread execution layout in 'app/ui/main_window.py'
   - Implement the main execution runtime in 'src/main.py'
   - Implement the automated validation test suites in 'tests/test_service/test_dashboard_service.py' using pytest mocks.
4. Framework Alignment: Ensure PySide6 components are properly separated from core mathematical/network functions to preserve a clean separation of concerns.

CRITICAL IMPLEMENTATION RESTRICTION: Do not truncate or stub out any logic. Code must be syntactically complete, robustly error-handled, and ready for execution. Provide clear terminal instructions at the end showing how to run the application and execute the test suites.