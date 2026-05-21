You are an expert Principal Python Engineer specializing in high-performance desktop development and clean architecture. Your task is to initialize and build out the repository for our "Personal FinTech & Crypto Desktop Dashboard" by implementing the blueprint detailed in the repository's 'fintech_dashboard_architecture.md' file.

Folder Structure.
fintech-dashboard/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── service/
│   │   ├── __init__.py
│   │   ├── dashboard_service.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── repository.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
├── utils/
│   ├── __init__.py
│   ├── helpers.py
├── tests/
│   ├── __init__.py
│   ├── test_service/
│   │   ├── __init__.py
│   │   ├── test_dashboard_service.py
├── .gitignore
├── requirements.txt
└── README.md

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